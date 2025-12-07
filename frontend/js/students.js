// Student Management JavaScript

let editingStudentId = null;

// Load students on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStudents();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('student-form').addEventListener('submit', handleStudentSubmit);
    document.getElementById('refresh-btn').addEventListener('click', loadStudents);
    document.getElementById('cancel-btn').addEventListener('click', cancelEdit);
}

// Load all students
async function loadStudents() {
    const loading = document.getElementById('loading');
    const listContainer = document.getElementById('students-list');
    
    loading.style.display = 'block';
    
    try {
        const students = await apiCall(`${API_CONFIG.STUDENT_SERVICE}/students`);
        
        if (students.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon" aria-hidden="true"></div>
                    <p class="empty-state-title">No students registered yet</p>
                    <p>Add a student using the form above to get started.</p>
                </div>
            `;
        } else {
            listContainer.innerHTML = students.map(student => createStudentCard(student)).join('');
        }
    } catch (error) {
        showError('form-message', 'Failed to load students: ' + error.message);
    } finally {
        loading.style.display = 'none';
    }
}

// Create student card HTML
function createStudentCard(student) {
    return `
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">${student.name}</div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-warning" onclick="editStudent(${student.student_id})">Edit</button>
                    <button class="btn btn-danger" onclick="deleteStudent(${student.student_id})">Delete</button>
                </div>
            </div>
            <div class="card-body">
                <p><strong>Email:</strong> ${student.email}</p>
                <p><strong>Phone:</strong> ${student.phone || 'N/A'}</p>
                <p><strong>Student ID:</strong> ${student.student_id}</p>
                <p><strong>Registered:</strong> ${formatDate(student.registration_date)}</p>
            </div>
        </div>
    `;
}

// Handle form submission
async function handleStudentSubmit(e) {
    e.preventDefault();
    
    const studentData = {
        name: document.getElementById('student-name').value,
        email: document.getElementById('student-email').value,
        phone: document.getElementById('student-phone').value || null,
    };
    
    try {
        if (editingStudentId) {
            // Update existing student
            await apiCall(`${API_CONFIG.STUDENT_SERVICE}/students/${editingStudentId}`, {
                method: 'PUT',
                body: JSON.stringify(studentData),
            });
            showSuccess('form-message', 'Student updated successfully!');
            cancelEdit();
        } else {
            // Create new student
            await apiCall(`${API_CONFIG.STUDENT_SERVICE}/students`, {
                method: 'POST',
                body: JSON.stringify(studentData),
            });
            showSuccess('form-message', 'Student registered successfully!');
            document.getElementById('student-form').reset();
        }
        
        loadStudents();
    } catch (error) {
        showError('form-message', 'Error: ' + error.message);
    }
}

// Edit student
async function editStudent(studentId) {
    try {
        const student = await apiCall(`${API_CONFIG.STUDENT_SERVICE}/students/${studentId}`);
        
        editingStudentId = studentId;
        document.getElementById('student-id').value = studentId;
        document.getElementById('student-name').value = student.name;
        document.getElementById('student-email').value = student.email;
        document.getElementById('student-phone').value = student.phone || '';
        
        document.getElementById('form-title').textContent = 'Edit Student';
        document.getElementById('submit-btn').textContent = 'Update Student';
        document.getElementById('cancel-btn').style.display = 'inline-block';
        
        // Scroll to form
        document.getElementById('student-form').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showError('form-message', 'Failed to load student: ' + error.message);
    }
}

// Cancel edit
function cancelEdit() {
    editingStudentId = null;
    document.getElementById('student-form').reset();
    document.getElementById('form-title').textContent = 'Register New Student';
    document.getElementById('submit-btn').textContent = 'Register Student';
    document.getElementById('cancel-btn').style.display = 'none';
}

// Delete student
async function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to delete this student? This will also remove all their enrollments.')) {
        return;
    }
    
    try {
        await apiCall(`${API_CONFIG.STUDENT_SERVICE}/students/${studentId}`, {
            method: 'DELETE',
        });
        showSuccess('form-message', 'Student deleted successfully!');
        loadStudents();
    } catch (error) {
        showError('form-message', 'Failed to delete student: ' + error.message);
    }
}
