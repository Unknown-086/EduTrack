from fastapi import FastAPI, HTTPException, status, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import psycopg
from psycopg import OperationalError, DatabaseError
from psycopg.rows import dict_row
import os
from datetime import datetime, timedelta
import secrets
import bcrypt

app = FastAPI(title="Course Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory token storage (in production, use Redis or database)
active_tokens = {}

# Pydantic models
class AdminLogin(BaseModel):
    username: str
    password: str

class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    description: Optional[str] = None
    credits: int = 3
    instructor: Optional[str] = None
    max_capacity: int = 50

class CourseUpdate(BaseModel):
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    instructor: Optional[str] = None
    max_capacity: Optional[int] = None
    status: Optional[str] = None

# Database connection
def get_db_connection():
    try:
        connection = psycopg.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "5433")),
            user=os.getenv("DB_USER", "edutrack"),
            password=os.getenv("DB_PASSWORD", "password"),
            dbname=os.getenv("DB_NAME", "edutrack"),
            row_factory=dict_row
        )
        return connection
    except OperationalError as e:
        print(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

# Token validation dependency
def verify_admin_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    token = authorization.replace("Bearer ", "")
    
    if token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Check token expiry
    if datetime.now() > active_tokens[token]["expires_at"]:
        del active_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    
    return active_tokens[token]["username"]

# Health check
@app.get("/health")
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "healthy", "service": "course-service"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

# Admin login
@app.post("/admin/login", response_model=dict)
def admin_login(credentials: AdminLogin):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM admins WHERE username = %s", (credentials.username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password (bcrypt)
        if not bcrypt.checkpw(credentials.password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Generate token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=8)
        
        active_tokens[token] = {
            "username": admin['username'],
            "expires_at": expires_at
        }
        
        return {
            "message": "Login successful",
            "token": token,
            "expires_at": expires_at.isoformat(),
            "username": admin['username']
        }
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Get all courses (public)
@app.get("/courses", response_model=List[dict])
def get_courses(active_only: bool = True):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM courses WHERE status = 'active' ORDER BY course_code")
        else:
            cursor.execute("SELECT * FROM courses ORDER BY course_code")
        
        courses = cursor.fetchall()
        cursor.close()
        conn.close()
        return courses
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Get course by ID (public)
@app.get("/courses/{course_id}", response_model=dict)
def get_course(course_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        course = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        return course
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Create course (admin only)
@app.post("/courses", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, admin: str = Depends(verify_admin_token)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if course code already exists
        cursor.execute("SELECT course_id FROM courses WHERE course_code = %s", (course.course_code,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course code already exists"
            )
        
        # Insert new course
        query = """
            INSERT INTO courses (course_code, course_name, description, credits, instructor, max_capacity) 
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING course_id
        """
        cursor.execute(query, (
            course.course_code,
            course.course_name,
            course.description,
            course.credits,
            course.instructor,
            course.max_capacity
        ))
        course_id = cursor.fetchone()["course_id"]
        conn.commit()

        # Get the created course
        cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        new_course = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Course created successfully",
            "course": new_course
        }
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Update course (admin only)
@app.put("/courses/{course_id}", response_model=dict)
def update_course(course_id: int, course: CourseUpdate, admin: str = Depends(verify_admin_token)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if course exists
        cursor.execute("SELECT course_id FROM courses WHERE course_id = %s", (course_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Build update query
        update_fields = []
        values = []
        
        if course.course_code is not None:
            update_fields.append("course_code = %s")
            values.append(course.course_code)
        if course.course_name is not None:
            update_fields.append("course_name = %s")
            values.append(course.course_name)
        if course.description is not None:
            update_fields.append("description = %s")
            values.append(course.description)
        if course.credits is not None:
            update_fields.append("credits = %s")
            values.append(course.credits)
        if course.instructor is not None:
            update_fields.append("instructor = %s")
            values.append(course.instructor)
        if course.max_capacity is not None:
            update_fields.append("max_capacity = %s")
            values.append(course.max_capacity)
        if course.status is not None:
            update_fields.append("status = %s")
            values.append(course.status)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        values.append(course_id)
        query = f"UPDATE courses SET {', '.join(update_fields)} WHERE course_id = %s"
        cursor.execute(query, values)
        conn.commit()
        
        # Get updated course
        cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        updated_course = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Course updated successfully",
            "course": updated_course
        }
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Delete course (admin only)
@app.delete("/courses/{course_id}", response_model=dict)
def delete_course(course_id: int, admin: str = Depends(verify_admin_token)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if course exists
        cursor.execute("SELECT course_id FROM courses WHERE course_id = %s", (course_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Delete course (cascades to enrollments)
        cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"Course {course_id} deleted successfully"}
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Admin logout
@app.post("/admin/logout")
def admin_logout(admin: str = Depends(verify_admin_token), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    if token in active_tokens:
        del active_tokens[token]
    return {"message": "Logged out successfully"}

# Root endpoint
@app.get("/")
def root():
    return {
        "service": "Course Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "admin_login": "/admin/login",
            "courses": "/courses",
            "course_by_id": "/courses/{course_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
