-- EduTrack Database Schema
-- PostgreSQL Compatible

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- Students Table
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registration_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_email ON students(email);

-- Courses Table
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    description TEXT,
    credits INT DEFAULT 3,
    instructor VARCHAR(100),
    max_capacity INT DEFAULT 50,
    current_enrollment INT DEFAULT 0,
    created_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(16) DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
);

CREATE INDEX idx_courses_code ON courses(course_code);
CREATE INDEX idx_courses_status ON courses(status);

-- Enrollments Table
CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrollment_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    grade VARCHAR(2) DEFAULT NULL,
    status VARCHAR(16) DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'completed', 'dropped')),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE (student_id, course_id)
);

CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);

-- Admin User Table (for course management)
CREATE TABLE admins (
    admin_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_admins_username ON admins(username);

-- Insert default admin user
-- Username: 
-- Password: 

-- Insert sample data (optional - for testing)
INSERT INTO students (name, email, phone) VALUES 
('John Doe', 'john.doe@example.com', '+92-300-1234567'),
('Jane Smith', 'jane.smith@example.com', '+92-301-2345678'),
('Ali Khan', 'ali.khan@example.com', '+92-302-3456789');

INSERT INTO courses (course_code, course_name, description, credits, instructor, max_capacity, status) VALUES 
('CS101', 'Introduction to Programming', 'Learn the basics of programming using Python', 3, 'Dr. Ahmad', 50, 'active'),
('CS201', 'Data Structures', 'Advanced data structures and algorithms', 4, 'Dr. Sarah', 40, 'active'),
('CS301', 'Database Systems', 'Relational database design and SQL', 3, 'Dr. Hassan', 45, 'active');

-- Verify tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
