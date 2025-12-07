// API Configuration
// Update these URLs based on your deployment environment

const API_CONFIG = {
    // For GKE deployment (using Nginx Reverse Proxy)
    // This allows us to use relative paths, so we don't need to know the IPs!
    STUDENT_SERVICE: '/api/student',
    COURSE_SERVICE: '/api/course',
    ENROLLMENT_SERVICE: '/api/enrollment',
    
    // For GKE deployment with LoadBalancer services
    // Uncomment and update these with your actual service IPs/domains
    // STUDENT_SERVICE: 'http://<STUDENT_SERVICE_EXTERNAL_IP>',
    // COURSE_SERVICE: 'http://<COURSE_SERVICE_EXTERNAL_IP>',
    // ENROLLMENT_SERVICE: 'http://<ENROLLMENT_SERVICE_EXTERNAL_IP>',
    
};

// Helper function to make API calls
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Show success message
function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = 'message success';
    element.style.display = 'block';
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

// Show error message
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = 'message error';
    element.style.display = 'block';
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Store admin token in session storage
function setAdminToken(token) {
    sessionStorage.setItem('adminToken', token);
}

function getAdminToken() {
    return sessionStorage.getItem('adminToken');
}

function clearAdminToken() {
    sessionStorage.removeItem('adminToken');
}

console.log('EduTrack Frontend loaded successfully!');
console.log('API Configuration:', API_CONFIG);
