// Course Management JavaScript

let editingCourseId = null;

// Load courses on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAdminSession();
    loadCourses();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('admin-login-form').addEventListener('submit', handleAdminLogin);
    document.getElementById('course-form').addEventListener('submit', handleCourseSubmit);
    document.getElementById('refresh-courses-btn').addEventListener('click', loadCourses);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('course-cancel-btn').addEventListener('click', cancelCourseEdit);
}

// Check if admin is already logged in
function checkAdminSession() {
    const token = getAdminToken();
    if (token) {
        showAdminPanel();
    }
}

// Handle admin login
async function handleAdminLogin(e) {
    e.preventDefault();
    
    const credentials = {
        username: document.getElementById('admin-username').value,
        password: document.getElementById('admin-password').value,
    };
    
    try {
        const response = await apiCall(`${API_CONFIG.COURSE_SERVICE}/admin/login`, {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
        
        setAdminToken(response.token);
        document.getElementById('admin-name').textContent = response.username;
        showAdminPanel();
        showSuccess('login-message', 'Login successful!');
        document.getElementById('admin-login-form').reset();
    } catch (error) {
        showError('login-message', 'Login failed: ' + error.message);
    }
}

// Show admin panel
function showAdminPanel() {
    document.getElementById('admin-login-section').style.display = 'none';
    document.getElementById('admin-panel').style.display = 'block';
}

// Handle logout
async function handleLogout() {
    try {
        const token = getAdminToken();
        await apiCall(`${API_CONFIG.COURSE_SERVICE}/admin/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        clearAdminToken();
        document.getElementById('admin-login-section').style.display = 'block';
        document.getElementById('admin-panel').style.display = 'none';
        loadCourses();
    }
}

// Load all courses
async function loadCourses() {
    const loading = document.getElementById('loading');
    const listContainer = document.getElementById('courses-list');
    
    loading.style.display = 'block';
    
    try {
        const courses = await apiCall(`${API_CONFIG.COURSE_SERVICE}/courses?active_only=false`);
        
        if (courses.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon" aria-hidden="true"></div>
                    <p class="empty-state-title">No courses available yet</p>
                    <p>Add a new course to populate the catalog.</p>
                </div>
            `;
        } else {
            listContainer.innerHTML = courses.map(course => createCourseCard(course)).join('');
        }
    } catch (error) {
        showError('course-form-message', 'Failed to load courses: ' + error.message);
    } finally {
        loading.style.display = 'none';
    }
}

// Create course card HTML
function createCourseCard(course) {
    const statusBadge = course.status === 'active' 
        ? '<span class="badge badge-success">Active</span>' 
        : '<span class="badge badge-danger">Inactive</span>';
    
    const isAdmin = getAdminToken() !== null;
    const adminButtons = isAdmin ? `
        <button class="btn btn-warning" onclick="editCourse(${course.course_id})">Edit</button>
        <button class="btn btn-danger" onclick="deleteCourse(${course.course_id})">Delete</button>
    ` : '';
    
    const enrollmentStatus = course.current_enrollment >= course.max_capacity
        ? '<span class="badge badge-danger">Full</span>'
        : `<span class="badge badge-info">${course.current_enrollment}/${course.max_capacity} enrolled</span>`;
    
    return `
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">${course.course_code} - ${course.course_name}</div>
                    ${statusBadge} ${enrollmentStatus}
                </div>
                <div class="card-actions">
                    ${adminButtons}
                </div>
            </div>
            <div class="card-body">
                <p><strong>Description:</strong> ${course.description || 'N/A'}</p>
                <p><strong>Credits:</strong> ${course.credits}</p>
                <p><strong>Instructor:</strong> ${course.instructor || 'N/A'}</p>
                <p><strong>Capacity:</strong> ${course.current_enrollment} / ${course.max_capacity}</p>
                <p><strong>Course ID:</strong> ${course.course_id}</p>
            </div>
        </div>
    `;
}

// Handle course form submission
async function handleCourseSubmit(e) {
    e.preventDefault();
    
    const token = getAdminToken();
    if (!token) {
        showError('course-form-message', 'Please login as admin first');
        return;
    }
    
    const courseData = {
        course_code: document.getElementById('course-code').value,
        course_name: document.getElementById('course-name').value,
        description: document.getElementById('course-description').value || null,
        credits: parseInt(document.getElementById('course-credits').value),
        instructor: document.getElementById('course-instructor').value || null,
        max_capacity: parseInt(document.getElementById('course-capacity').value),
    };
    
    try {
        if (editingCourseId) {
            // Update existing course
            await apiCall(`${API_CONFIG.COURSE_SERVICE}/courses/${editingCourseId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(courseData),
            });
            showSuccess('course-form-message', 'Course updated successfully!');
            cancelCourseEdit();
        } else {
            // Create new course
            await apiCall(`${API_CONFIG.COURSE_SERVICE}/courses`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(courseData),
            });
            showSuccess('course-form-message', 'Course created successfully!');
            document.getElementById('course-form').reset();
        }
        
        loadCourses();
    } catch (error) {
        showError('course-form-message', 'Error: ' + error.message);
    }
}

// Edit course
async function editCourse(courseId) {
    try {
        const course = await apiCall(`${API_CONFIG.COURSE_SERVICE}/courses/${courseId}`);
        
        editingCourseId = courseId;
        document.getElementById('course-id').value = courseId;
        document.getElementById('course-code').value = course.course_code;
        document.getElementById('course-name').value = course.course_name;
        document.getElementById('course-description').value = course.description || '';
        document.getElementById('course-credits').value = course.credits;
        document.getElementById('course-instructor').value = course.instructor || '';
        document.getElementById('course-capacity').value = course.max_capacity;
        
        document.getElementById('course-form-title').textContent = 'Edit Course';
        document.getElementById('course-submit-btn').textContent = 'Update Course';
        document.getElementById('course-cancel-btn').style.display = 'inline-block';
        
        // Scroll to form
        document.getElementById('course-form').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showError('course-form-message', 'Failed to load course: ' + error.message);
    }
}

// Cancel course edit
function cancelCourseEdit() {
    editingCourseId = null;
    document.getElementById('course-form').reset();
    document.getElementById('course-form-title').textContent = 'Create New Course';
    document.getElementById('course-submit-btn').textContent = 'Create Course';
    document.getElementById('course-cancel-btn').style.display = 'none';
}

// Delete course
async function deleteCourse(courseId) {
    if (!confirm('Are you sure you want to delete this course? This will also remove all enrollments.')) {
        return;
    }
    
    const token = getAdminToken();
    if (!token) {
        showError('course-form-message', 'Please login as admin first');
        return;
    }
    
    try {
        await apiCall(`${API_CONFIG.COURSE_SERVICE}/courses/${courseId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        showSuccess('course-form-message', 'Course deleted successfully!');
        loadCourses();
    } catch (error) {
        showError('course-form-message', 'Failed to delete course: ' + error.message);
    }
}
