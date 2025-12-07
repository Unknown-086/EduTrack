// Enrollment Management JavaScript

let currentFilter = { student: null, course: null };

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadEnrollments();
    loadStudentsForDropdown();
    loadCoursesForDropdown();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('enrollment-form').addEventListener('submit', handleEnrollmentSubmit);
    document.getElementById('refresh-enrollments-btn').addEventListener('click', loadEnrollments);
    document.getElementById('filter-btn').addEventListener('click', applyFilter);
    document.getElementById('reset-filter-btn').addEventListener('click', resetFilter);
}

// Load students for dropdown
async function loadStudentsForDropdown() {
    try {
        const students = await apiCall(`${API_CONFIG.STUDENT_SERVICE}/students`);
        
        const enrollmentSelect = document.getElementById('enrollment-student');
        const filterSelect = document.getElementById('filter-student');
        
        const options = students
            .map(s => `<option value="${s.student_id}">${s.name} (${s.email})</option>`)
            .join('');
        
        enrollmentSelect.innerHTML += options;
        filterSelect.innerHTML += options;
    } catch (error) {
        console.error('Failed to load students:', error);
    }
}

// Load courses for dropdown
async function loadCoursesForDropdown() {
    try {
        const courses = await apiCall(`${API_CONFIG.COURSE_SERVICE}/courses?active_only=true`);
        
        const enrollmentSelect = document.getElementById('enrollment-course');
        const filterSelect = document.getElementById('filter-course');
        
        const options = courses.map(c => 
            `<option value="${c.course_id}">${c.course_code} - ${c.course_name}</option>`
        ).join('');
        
        enrollmentSelect.innerHTML += options;
        filterSelect.innerHTML += options;
    } catch (error) {
        console.error('Failed to load courses:', error);
    }
}

// Load all enrollments
async function loadEnrollments() {
    const loading = document.getElementById('loading');
    const listContainer = document.getElementById('enrollments-list');
    
    loading.style.display = 'block';
    
    try {
        let enrollments;
        
        if (currentFilter.student) {
            enrollments = await apiCall(
                `${API_CONFIG.ENROLLMENT_SERVICE}/enrollments/student/${currentFilter.student}`
            );
        } else if (currentFilter.course) {
            enrollments = await apiCall(
                `${API_CONFIG.ENROLLMENT_SERVICE}/enrollments/course/${currentFilter.course}`
            );
        } else {
            enrollments = await apiCall(`${API_CONFIG.ENROLLMENT_SERVICE}/enrollments`);
        }
        
        if (enrollments.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon" aria-hidden="true"></div>
                    <p class="empty-state-title">No enrollments found</p>
                    <p>Enroll a student above or adjust the filters to broaden your results.</p>
                </div>
            `;
        } else {
            listContainer.innerHTML = enrollments.map(enrollment => 
                createEnrollmentCard(enrollment)
            ).join('');
        }
    } catch (error) {
        showError('enrollment-form-message', 'Failed to load enrollments: ' + error.message);
    } finally {
        loading.style.display = 'none';
    }
}

// Create enrollment card HTML
function createEnrollmentCard(enrollment) {
    const statusBadges = {
        'enrolled': '<span class="badge badge-info">Enrolled</span>',
        'completed': '<span class="badge badge-success">Completed</span>',
        'dropped': '<span class="badge badge-danger">Dropped</span>',
    };
    
    const statusBadge = statusBadges[enrollment.status] || '';
    const gradeBadge = enrollment.grade 
        ? `<span class="badge badge-warning">Grade: ${enrollment.grade}</span>` 
        : '';
    
    return `
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">
                        ${enrollment.student_name || 'Student'} &rarr; ${enrollment.course_code} - ${enrollment.course_name}
                    </div>
                    ${statusBadge} ${gradeBadge}
                </div>
                <div class="card-actions">
                    <button class="btn btn-danger" onclick="dropEnrollment(${enrollment.enrollment_id})">
                        Drop Course
                    </button>
                </div>
            </div>
            <div class="card-body">
                <p><strong>Student:</strong> ${enrollment.student_name} (${enrollment.student_email})</p>
                <p><strong>Course:</strong> ${enrollment.course_code} - ${enrollment.course_name}</p>
                <p><strong>Credits:</strong> ${enrollment.credits}</p>
                <p><strong>Enrolled On:</strong> ${formatDate(enrollment.enrollment_date)}</p>
                <p><strong>Enrollment ID:</strong> ${enrollment.enrollment_id}</p>
            </div>
        </div>
    `;
}

// Handle enrollment form submission
async function handleEnrollmentSubmit(e) {
    e.preventDefault();
    
    const enrollmentData = {
        student_id: parseInt(document.getElementById('enrollment-student').value),
        course_id: parseInt(document.getElementById('enrollment-course').value),
    };
    
    try {
        await apiCall(`${API_CONFIG.ENROLLMENT_SERVICE}/enrollments`, {
            method: 'POST',
            body: JSON.stringify(enrollmentData),
        });
        
        showSuccess('enrollment-form-message', 'Student enrolled successfully!');
        document.getElementById('enrollment-form').reset();
        loadEnrollments();
    } catch (error) {
        showError('enrollment-form-message', 'Enrollment failed: ' + error.message);
    }
}

// Drop enrollment
async function dropEnrollment(enrollmentId) {
    if (!confirm('Are you sure you want to drop this enrollment?')) {
        return;
    }
    
    try {
        await apiCall(`${API_CONFIG.ENROLLMENT_SERVICE}/enrollments/${enrollmentId}`, {
            method: 'DELETE',
        });
        
        showSuccess('enrollment-form-message', 'Enrollment dropped successfully!');
        loadEnrollments();
    } catch (error) {
        showError('enrollment-form-message', 'Failed to drop enrollment: ' + error.message);
    }
}

// Apply filter
function applyFilter() {
    const studentId = document.getElementById('filter-student').value;
    const courseId = document.getElementById('filter-course').value;
    
    if (studentId && courseId) {
        showError('enrollment-form-message', 'Please select only one filter at a time');
        return;
    }
    
    currentFilter = {
        student: studentId || null,
        course: courseId || null,
    };
    
    loadEnrollments();
}

// Reset filter
function resetFilter() {
    currentFilter = { student: null, course: null };
    document.getElementById('filter-student').value = '';
    document.getElementById('filter-course').value = '';
    loadEnrollments();
}
