from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import psycopg
from psycopg import OperationalError, DatabaseError
from psycopg.rows import dict_row
import os
from datetime import datetime

app = FastAPI(title="Student Service", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class Student(BaseModel):
    student_id: int
    name: str
    email: str
    phone: Optional[str]
    registration_date: datetime

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

# Health check endpoint
@app.get("/health")
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "healthy", "service": "student-service"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

# Get all students
@app.get("/students", response_model=List[dict])
def get_students():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY registration_date DESC")
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        return students
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Get student by ID
@app.get("/students/{student_id}", response_model=dict)
def get_student(student_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        return student
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Create new student
@app.post("/students", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT student_id FROM students WHERE email = %s", (student.email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Insert new student
        query = """
            INSERT INTO students (name, email, phone) 
            VALUES (%s, %s, %s)
            RETURNING student_id
        """
        cursor.execute(query, (student.name, student.email, student.phone))
        student_id = cursor.fetchone()["student_id"]
        conn.commit()

        # Get the created student
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        new_student = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Student created successfully",
            "student": new_student
        }
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Update student
@app.put("/students/{student_id}", response_model=dict)
def update_student(student_id: int, student: StudentUpdate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        if student.name is not None:
            update_fields.append("name = %s")
            values.append(student.name)
        if student.email is not None:
            update_fields.append("email = %s")
            values.append(student.email)
        if student.phone is not None:
            update_fields.append("phone = %s")
            values.append(student.phone)
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        values.append(student_id)
        query = f"UPDATE students SET {', '.join(update_fields)} WHERE student_id = %s"
        cursor.execute(query, values)
        conn.commit()
        
        # Get updated student
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        updated_student = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Student updated successfully",
            "student": updated_student
        }
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Delete student
@app.delete("/students/{student_id}", response_model=dict)
def delete_student(student_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        
        # Delete student (cascades to enrollments)
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"Student {student_id} deleted successfully"}
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Get student's enrollments
@app.get("/students/{student_id}/enrollments", response_model=List[dict])
def get_student_enrollments(student_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        
        # Get enrollments with course details
        query = """
            SELECT e.*, c.course_code, c.course_name, c.credits
            FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.student_id = %s
            ORDER BY e.enrollment_date DESC
        """
        cursor.execute(query, (student_id,))
        enrollments = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return enrollments
    except HTTPException:
        raise
    except Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Root endpoint
@app.get("/")
def root():
    return {
        "service": "Student Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "students": "/students",
            "student_by_id": "/students/{student_id}",
            "student_enrollments": "/students/{student_id}/enrollments"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
