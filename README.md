# 🎓 EduTrack - Cloud-Native Education Management System

A microservices-based education management system built with Python FastAPI, deployed on Google Kubernetes Engine (GKE) with Cloud SQL integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [GCP Deployment](#gcp-deployment)
- [API Documentation](#api-documentation)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

EduTrack is a cloud-native application that demonstrates modern microservices architecture principles. The system supports:

- ✅ **Student Management** - CRUD operations for student profiles
- ✅ **Course Management** - Admin-controlled course catalog
- ✅ **Enrollment System** - Student course enrollment with capacity management
- ✅ **Admin Authentication** - Token-based authentication for course management
- ✅ **Responsive Frontend** - Simple HTML/CSS/JavaScript interface

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Nginx)                    │
│                    Port 80 (LoadBalancer)                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Ingress Controller                    │
│              (Optional - Single Entry Point)             │
└─────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Student Service │ │ Course Service  │ │Enrollment Service│
│   Port 8081     │ │   Port 8082     │ │   Port 8083     │
│  (ClusterIP)    │ │  (ClusterIP)    │ │  (ClusterIP)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            ▼
                  ┌──────────────────┐
                  │   Cloud SQL      │
                  │  (MySQL 8.0)     │
                  │  + Auth Proxy    │
                  └──────────────────┘
```

### Components:

1. **Student Service** - Manages student CRUD operations
2. **Course Service** - Handles course catalog with admin authentication
3. **Enrollment Service** - Processes enrollments and validates capacity
4. **Frontend** - Nginx-served static HTML/CSS/JS application
5. **Cloud SQL** - Managed MySQL database with automatic backups
6. **GKE** - Kubernetes cluster with autoscaling and load balancing

---

## 💻 Technology Stack

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI 0.109.0
- **Database**: MySQL 8.0
- **Authentication**: bcrypt + Token-based

### Frontend
- **HTML5** / **CSS3** / **Vanilla JavaScript**
- **Web Server**: Nginx Alpine

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (GKE)
- **Database**: Cloud SQL (MySQL)
- **Registry**: Artifact Registry
- **Monitoring**: Cloud Monitoring & Logging

### DevOps
- **CI/CD**: GitHub Actions (optional)
- **IaC**: Kubernetes YAML manifests
- **Secrets**: Kubernetes Secrets / Secret Manager

---

## 📁 Project Structure

```
edutrack/
├── student-service/          # Student microservice
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Container definition
│   └── .env.example         # Environment template
│
├── course-service/           # Course microservice
│   ├── main.py              # FastAPI application with admin auth
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Container definition
│   └── .env.example         # Environment template
│
├── enrollment-service/       # Enrollment microservice
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Container definition
│   └── .env.example         # Environment template
│
├── frontend/                 # Frontend application
│   ├── index.html           # Landing page
│   ├── students.html        # Student management UI
│   ├── courses.html         # Course management UI
│   ├── enrollments.html     # Enrollment UI
│   ├── css/
│   │   └── style.css        # Styles
│   ├── js/
│   │   ├── config.js        # API configuration
│   │   ├── students.js      # Student operations
│   │   ├── courses.js       # Course operations
│   │   └── enrollments.js   # Enrollment operations
│   ├── nginx.conf           # Nginx configuration
│   └── Dockerfile           # Container definition
│
├── k8s/                      # Kubernetes manifests
│   ├── secrets.yaml         # Database credentials
│   ├── student-deployment.yaml
│   ├── course-deployment.yaml
│   ├── enrollment-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── ingress.yaml         # Ingress controller config
│   └── hpa.yaml             # Horizontal Pod Autoscaler
│
├── sql/                      # Database
│   └── schema.sql           # Database schema & sample data
│
├── docs/                     # Documentation & scripts
│   ├── docker-compose.yaml  # Local development
│   ├── build-and-push.sh    # Build script (Linux/Mac)
│   └── build-and-push.ps1   # Build script (Windows)
│
└── README.md                 # This file
```

---

## ✅ Prerequisites

### Required Tools:
- **Docker Desktop** (with Kubernetes enabled for local testing)
- **Google Cloud SDK** (`gcloud` CLI)
- **kubectl** (Kubernetes CLI)
- **Git**
- **Python 3.11+** (for local development)

### GCP Requirements:
- Active GCP Project with billing enabled
- APIs enabled:
  - Compute Engine API
  - Kubernetes Engine API
  - Cloud SQL Admin API
  - Artifact Registry API
  - Cloud Monitoring API
  - Cloud Logging API

---

## 🚀 Local Development

### Step 1: Clone Repository

```bash
git clone https://github.com/Unknown-086/EduTrack.git
cd EduTrack
```

### Step 2: Start Services with Docker Compose

```bash
cd docs
docker-compose up -d
```

This will start:
- MySQL database (port 3306)
- Student Service (port 8081)
- Course Service (port 8082)
- Enrollment Service (port 8083)
- Frontend (port 80)

### Step 3: Access Application

- **Frontend**: http://localhost
- **Student API**: http://localhost:8081/docs (Swagger UI)
- **Course API**: http://localhost:8082/docs
- **Enrollment API**: http://localhost:8083/docs

### Step 4: Test APIs

**Register a Student:**
```bash
curl -X POST http://localhost:8081/students \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "phone": "+92-300-1234567"}'
```

**Admin Login (for course management):**
```bash
curl -X POST http://localhost:8082/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Step 5: Stop Services

```bash
docker-compose down
```

---

## ☁️ GCP Deployment

### Phase 1: Setup Cloud SQL

#### 1.1 Create Cloud SQL Instance

```bash
gcloud sql instances create edutrack-db \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --root-password=YOUR_ROOT_PASSWORD
```

#### 1.2 Create Database and User

```bash
# Connect to Cloud SQL
gcloud sql connect edutrack-db --user=root

# In MySQL prompt:
CREATE DATABASE edutrack_db;
CREATE USER 'edutrack_user'@'%' IDENTIFIED BY 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON edutrack_db.* TO 'edutrack_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

#### 1.3 Import Database Schema

```bash
gcloud sql import sql edutrack-db gs://YOUR_BUCKET/schema.sql \
  --database=edutrack_db
```

Or manually:
```bash
mysql -u edutrack_user -p edutrack_db < sql/schema.sql
```

---

### Phase 2: Setup Artifact Registry

#### 2.1 Create Repository

```bash
gcloud artifacts repositories create edutrack-repo \
  --repository-format=docker \
  --location=asia-south1 \
  --description="EduTrack Docker images"
```

#### 2.2 Configure Docker Authentication

```bash
gcloud auth configure-docker asia-south1-docker.pkg.dev
```

---

### Phase 3: Build and Push Docker Images

#### 3.1 Update Build Script

Edit `docs/build-and-push.ps1` (Windows) or `docs/build-and-push.sh` (Linux/Mac):

```powershell
$PROJECT_ID = "your-gcp-project-id"  # Change this!
```

#### 3.2 Run Build Script

**Windows:**
```powershell
cd docs
.\build-and-push.ps1
```

**Linux/Mac:**
```bash
cd docs
chmod +x build-and-push.sh
./build-and-push.sh
```

Or manually:
```bash
# Student Service
cd student-service
docker build -t asia-south1-docker.pkg.dev/PROJECT-ID/edutrack-repo/student-service:v1 .
docker push asia-south1-docker.pkg.dev/PROJECT-ID/edutrack-repo/student-service:v1

# Repeat for course-service, enrollment-service, frontend
```

---

### Phase 4: Create GKE Cluster

```bash
gcloud container clusters create edutrack-cluster \
  --zone=asia-south1-a \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=5 \
  --enable-cloud-logging \
  --enable-cloud-monitoring
```

#### Get Cluster Credentials

```bash
gcloud container clusters get-credentials edutrack-cluster --zone=asia-south1-a
```

---

### Phase 5: Setup Cloud SQL Auth Proxy

#### 5.1 Create Service Account

```bash
gcloud iam service-accounts create cloudsql-proxy \
  --display-name="Cloud SQL Proxy"
```

#### 5.2 Grant Permissions

```bash
gcloud projects add-iam-policy-binding PROJECT-ID \
  --member="serviceAccount:cloudsql-proxy@PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

#### 5.3 Create Key

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=cloudsql-proxy@PROJECT-ID.iam.gserviceaccount.com
```

#### 5.4 Create Kubernetes Secret

```bash
kubectl create secret generic cloudsql-instance-credentials \
  --from-file=key.json=key.json
```

---

### Phase 6: Deploy to GKE

#### 6.1 Update Kubernetes Manifests

Edit all files in `k8s/` folder:
- Replace `PROJECT-ID` with your GCP project ID
- Replace `REGION` with your region (e.g., `asia-south1`)
- Replace `INSTANCE-NAME` with your Cloud SQL instance name

#### 6.2 Create Database Secret

Edit `k8s/secrets.yaml`:
```yaml
stringData:
  DB_HOST: "127.0.0.1"
  DB_PORT: "3306"
  DB_USER: "edutrack_user"
  DB_PASSWORD: "YOUR_ACTUAL_PASSWORD"  # Change this!
  DB_NAME: "edutrack_db"
```

Apply:
```bash
kubectl apply -f k8s/secrets.yaml
```

#### 6.3 Deploy Microservices

```bash
# Deploy all services
kubectl apply -f k8s/student-deployment.yaml
kubectl apply -f k8s/course-deployment.yaml
kubectl apply -f k8s/enrollment-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Optional: Setup Ingress and Autoscaling
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

#### 6.4 Verify Deployment

```bash
# Check pods
kubectl get pods

# Check services
kubectl get services

# Get frontend external IP
kubectl get service frontend
```

Wait for `EXTERNAL-IP` to be assigned (may take 2-5 minutes).

#### 6.5 Update Frontend Configuration

Once you have external IPs, update `frontend/js/config.js`:

```javascript
const API_CONFIG = {
    STUDENT_SERVICE: 'http://<STUDENT_SERVICE_IP>:8081',
    COURSE_SERVICE: 'http://<COURSE_SERVICE_IP>:8082',
    ENROLLMENT_SERVICE: 'http://<ENROLLMENT_SERVICE_IP>:8083',
};
```

Rebuild and redeploy frontend:
```bash
docker build -t asia-south1-docker.pkg.dev/PROJECT-ID/edutrack-repo/frontend:v2 frontend/
docker push asia-south1-docker.pkg.dev/PROJECT-ID/edutrack-repo/frontend:v2
kubectl set image deployment/frontend frontend=asia-south1-docker.pkg.dev/PROJECT-ID/edutrack-repo/frontend:v2
```

---

## 📚 API Documentation

### Student Service (Port 8081)

#### Endpoints:

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/students` | List all students | No |
| GET | `/students/{id}` | Get student by ID | No |
| POST | `/students` | Create new student | No |
| PUT | `/students/{id}` | Update student | No |
| DELETE | `/students/{id}` | Delete student | No |
| GET | `/students/{id}/enrollments` | Get student's enrollments | No |
| GET | `/health` | Health check | No |

#### Example: Create Student

```json
POST /students
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+92-300-1234567"
}
```

---

### Course Service (Port 8082)

#### Endpoints:

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/courses` | List all courses | No |
| GET | `/courses/{id}` | Get course by ID | No |
| POST | `/courses` | Create course | **Yes (Admin)** |
| PUT | `/courses/{id}` | Update course | **Yes (Admin)** |
| DELETE | `/courses/{id}` | Delete course | **Yes (Admin)** |
| POST | `/admin/login` | Admin login | No |
| POST | `/admin/logout` | Admin logout | Yes |
| GET | `/health` | Health check | No |

#### Admin Credentials:
- **Username**: `admin`
- **Password**: `admin123`

#### Example: Admin Login

```json
POST /admin/login
{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "message": "Login successful",
  "token": "abc123...",
  "expires_at": "2025-12-08T10:00:00",
  "username": "admin"
}
```

#### Example: Create Course (with token)

```json
POST /courses
Headers:
  Authorization: Bearer abc123...

Body:
{
  "course_code": "CS101",
  "course_name": "Introduction to Programming",
  "description": "Learn Python basics",
  "credits": 3,
  "instructor": "Dr. Smith",
  "max_capacity": 50
}
```

---

### Enrollment Service (Port 8083)

#### Endpoints:

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/enrollments` | List all enrollments | No |
| GET | `/enrollments/{id}` | Get enrollment by ID | No |
| POST | `/enrollments` | Enroll student in course | No |
| DELETE | `/enrollments/{id}` | Drop enrollment | No |
| GET | `/enrollments/student/{student_id}` | Get enrollments by student | No |
| GET | `/enrollments/course/{course_id}` | Get enrollments by course | No |
| GET | `/health` | Health check | No |

#### Example: Enroll Student

```json
POST /enrollments
{
  "student_id": 1,
  "course_id": 1
}
```

---

## 📊 Monitoring & Logging

### View Logs

```bash
# View pod logs
kubectl logs -f deployment/student-service

# View all service logs
kubectl logs -l app=student-service --tail=100

# Stream logs in real-time
kubectl logs -f -l app=course-service
```

### Cloud Monitoring

Access in GCP Console:
- **Monitoring** → **Dashboards** → Create custom dashboard
- **Logging** → **Logs Explorer** → Filter by resource

### Health Checks

All services expose `/health` endpoints:
```bash
curl http://EXTERNAL_IP:8081/health
```

---

## 🔧 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods

# Describe pod for events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Database Connection Issues

```bash
# Test Cloud SQL connection
kubectl exec -it <pod-name> -- sh
# Inside pod:
mysql -h 127.0.0.1 -u edutrack_user -p edutrack_db
```

### Image Pull Errors

```bash
# Verify image exists
gcloud artifacts docker images list asia-south1-docker.pkg.dev/PROJECT-ID/edutrack-repo

# Check GKE service account permissions
kubectl describe pod <pod-name> | grep -A 5 "Events"
```

### Frontend Can't Connect to Backend

1. Check if services have external IPs:
   ```bash
   kubectl get services
   ```

2. Update `frontend/js/config.js` with correct IPs

3. Rebuild and redeploy frontend

### Common Issues:

| Issue | Solution |
|-------|----------|
| `ImagePullBackOff` | Check Artifact Registry permissions |
| `CrashLoopBackOff` | Check application logs and DB connection |
| `Pending` pods | Check cluster resources with `kubectl describe nodes` |
| 503 errors | Check if pods are ready: `kubectl get pods` |

---

## 📝 Assignment Deliverables Checklist

✅ **Source Code**
- All microservices implemented
- Frontend included
- Database schema provided

✅ **Dockerfiles**
- All services containerized
- Optimized for size (Alpine base images)

✅ **Kubernetes Manifests**
- Deployments for all services
- Services (ClusterIP/LoadBalancer)
- Secrets for database
- Optional: Ingress and HPA

✅ **Working GKE Deployment**
- Services running on GKE
- Cloud SQL connected
- Frontend accessible

✅ **README Documentation**
- Setup instructions
- API documentation
- Troubleshooting guide

✅ **Video Demo** (Create separately)
- Show local development
- Demonstrate GKE deployment
- Test all features
- Show monitoring/logs

---

## 🎬 Creating Video Demo

### Suggested Structure (10-15 minutes):

1. **Introduction** (1 min)
   - Project overview
   - Architecture diagram

2. **Local Development** (3 min)
   - Show docker-compose up
   - Test APIs with Swagger
   - Demonstrate frontend

3. **GCP Deployment** (5 min)
   - Show GCP Console (Cloud SQL, GKE, Artifact Registry)
   - Display kubectl commands
   - Show running pods

4. **Testing** (3 min)
   - Register students
   - Admin login & create courses
   - Enroll students
   - Show database records

5. **Monitoring** (2 min)
   - Cloud Logging
   - Health checks
   - Autoscaling demo (optional)

6. **Conclusion** (1 min)
   - Recap features
   - Mention best practices followed

---

## 📄 License

This project is created for educational purposes as part of a Cloud Computing assignment.

---

## 👥 Contributors

- **Your Name** - Initial work

---

## 🙏 Acknowledgments

- FastAPI Documentation
- Google Cloud Platform Documentation
- Kubernetes Documentation

---

## 📧 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review GCP logs: `kubectl logs <pod-name>`
3. Contact your instructor

---

**Built with ❤️ using Python FastAPI and Google Cloud Platform**
