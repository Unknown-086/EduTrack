from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import psycopg
from psycopg import OperationalError, DatabaseError
from psycopg.rows import dict_row
import os
from datetime import datetime

app = FastAPI(title="Enrollment Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int

class EnrollmentUpdate(BaseModel):
    grade: Optional[str] = None
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
        return {"status": "healthy", "service": "enrollment-service"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

# Get all enrollments
@app.get("/enrollments", response_model=List[dict])
def get_enrollments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT e.*, 
                   s.name as student_name, s.email as student_email,
                   c.course_code, c.course_name, c.credits
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY e.enrollment_date DESC
        """
        cursor.execute(query)
        enrollments = cursor.fetchall()
        cursor.close()
        conn.close()
        return enrollments
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Get enrollment by ID
@app.get("/enrollments/{enrollment_id}", response_model=dict)
def get_enrollment(enrollment_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT e.*, 
                   s.name as student_name, s.email as student_email,
                   c.course_code, c.course_name, c.credits
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.enrollment_id = %s
        """
        cursor.execute(query, (enrollment_id,))
        enrollment = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment with ID {enrollment_id} not found"
            )
        return enrollment
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Create new enrollment
@app.post("/enrollments", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_enrollment(enrollment: EnrollmentCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (enrollment.student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {enrollment.student_id} not found"
            )
        
        # Check if course exists and is active
        cursor.execute(
            "SELECT course_id, status, max_capacity, current_enrollment FROM courses WHERE course_id = %s",
            (enrollment.course_id,)
        )
        course = cursor.fetchone()
        if not course:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {enrollment.course_id} not found"
            )
        
        if course['status'] != 'active':
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course is not active"
            )
        
        # Check if course is full
        if course['current_enrollment'] >= course['max_capacity']:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course is full"
            )
        
        # Check if already enrolled
        cursor.execute(
            "SELECT enrollment_id FROM enrollments WHERE student_id = %s AND course_id = %s",
            (enrollment.student_id, enrollment.course_id)
        )
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is already enrolled in this course"
            )
        
        # Create enrollment
        cursor.execute(
            "INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s) RETURNING enrollment_id",
            (enrollment.student_id, enrollment.course_id)
        )
        enrollment_id = cursor.fetchone()["enrollment_id"]
        
        # Update course enrollment count
        cursor.execute(
            "UPDATE courses SET current_enrollment = current_enrollment + 1 WHERE course_id = %s",
            (enrollment.course_id,)
        )
        
        conn.commit()
        
        # Get the created enrollment with details
        query = """
            SELECT e.*, 
                   s.name as student_name, s.email as student_email,
                   c.course_code, c.course_name, c.credits
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.enrollment_id = %s
        """
        cursor.execute(query, (enrollment_id,))
        new_enrollment = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Enrollment created successfully",
            "enrollment": new_enrollment
        }
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Update enrollment (for grades)
@app.put("/enrollments/{enrollment_id}", response_model=dict)
def update_enrollment(enrollment_id: int, enrollment: EnrollmentUpdate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if enrollment exists
        cursor.execute("SELECT enrollment_id FROM enrollments WHERE enrollment_id = %s", (enrollment_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment with ID {enrollment_id} not found"
            )
        
        # Build update query
        update_fields = []
        values = []
        
        if enrollment.grade is not None:
            update_fields.append("grade = %s")
            values.append(enrollment.grade)
        if enrollment.status is not None:
            update_fields.append("status = %s")
            values.append(enrollment.status)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        values.append(enrollment_id)
        query = f"UPDATE enrollments SET {', '.join(update_fields)} WHERE enrollment_id = %s"
        cursor.execute(query, values)
        conn.commit()
        
        # Get updated enrollment
        query = """
            SELECT e.*, 
                   s.name as student_name, s.email as student_email,
                   c.course_code, c.course_name, c.credits
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.enrollment_id = %s
        """
        cursor.execute(query, (enrollment_id,))
        updated_enrollment = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Enrollment updated successfully",
            "enrollment": updated_enrollment
        }
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Delete enrollment (drop course)
@app.delete("/enrollments/{enrollment_id}", response_model=dict)
def delete_enrollment(enrollment_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get enrollment details before deleting
        cursor.execute("SELECT student_id, course_id FROM enrollments WHERE enrollment_id = %s", (enrollment_id,))
        enrollment = cursor.fetchone()
        
        if not enrollment:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment with ID {enrollment_id} not found"
            )
        
        # Delete enrollment
        cursor.execute("DELETE FROM enrollments WHERE enrollment_id = %s", (enrollment_id,))
        
        # Update course enrollment count
        cursor.execute(
            "UPDATE courses SET current_enrollment = GREATEST(current_enrollment - 1, 0) WHERE course_id = %s",
            (enrollment['course_id'],)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"Enrollment {enrollment_id} deleted successfully"}
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Get enrollments by student
@app.get("/enrollments/student/{student_id}", response_model=List[dict])
def get_enrollments_by_student(student_id: int):
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
        
        query = """
            SELECT e.*, 
                   c.course_code, c.course_name, c.credits, c.instructor
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
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Get enrollments by course
@app.get("/enrollments/course/{course_id}", response_model=List[dict])
def get_enrollments_by_course(course_id: int):
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
        
        query = """
            SELECT e.*, 
                   s.name as student_name, s.email as student_email, s.phone as student_phone
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            WHERE e.course_id = %s
            ORDER BY e.enrollment_date DESC
        """
        cursor.execute(query, (course_id,))
        enrollments = cursor.fetchall()
        cursor.close()
        conn.close()
        return enrollments
    except HTTPException:
        raise
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# Root endpoint
@app.get("/")
def root():
    return {
        "service": "Enrollment Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "enrollments": "/enrollments",
            "enrollment_by_id": "/enrollments/{enrollment_id}",
            "enrollments_by_student": "/enrollments/student/{student_id}",
            "enrollments_by_course": "/enrollments/course/{course_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
