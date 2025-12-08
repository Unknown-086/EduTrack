# EduTrack - Cloud-Native Education Management System

A microservices-based education management system built with Python FastAPI, deployed on Google Kubernetes Engine with Cloud SQL integration.

---

## Overview

EduTrack demonstrates modern cloud-native microservices architecture with:

- Student Management - CRUD operations for student profiles
- Course Management - Admin-controlled course catalog
- Enrollment System - Course enrollment with capacity management
- Admin Authentication - Token-based authentication
- Responsive Frontend - Nginx reverse proxy serving static assets

---

## Architecture

```
Frontend (Nginx LoadBalancer :80)
    |
    +---> /api/student/*    --> Student Service :8081
    +---> /api/course/*     --> Course Service :8082
    +---> /api/enrollment/* --> Enrollment Service :8083
             |
             v
    Cloud SQL Auth Proxy (Sidecar)
             |
             v
    Cloud SQL PostgreSQL Instance
```

### Components

- **Student Service** - Manages student CRUD operations
- **Course Service** - Handles course catalog with admin authentication
- **Enrollment Service** - Processes enrollments and validates capacity
- **Frontend** - Nginx-served static application with reverse proxy
- **Cloud SQL** - Managed PostgreSQL 15 database
- **GKE** - Kubernetes cluster (2x E2-medium nodes)

---

## Technology Stack

### Backend
- Python 3.11 (Alpine)
- FastAPI
- psycopg (PostgreSQL adapter)
- Uvicorn ASGI server

### Frontend
- HTML5 / CSS3 / JavaScript
- Nginx (Alpine)

### Infrastructure
- Google Kubernetes Engine (GKE)
- Cloud SQL (PostgreSQL 15)
- Artifact Registry
- Cloud SQL Auth Proxy
- Kubernetes Secrets

---

## Current Deployment

- **Cluster:** edutrack-cluster (us-central1)
- **Nodes:** 2x E2-medium (2 vCPU, 4 GB each)
- **Replicas:** 1 per service (resource-optimized)
- **Database:** Cloud SQL PostgreSQL (private IP)

---

## Project Structure

```
EduTrack/
├── student-service/          # Student microservice
├── course-service/           # Course microservice
├── enrollment-service/       # Enrollment microservice
├── frontend/                 # Nginx frontend with reverse proxy
├── k8s/                      # Kubernetes manifests
├── sql/                      # Database schema
├── docs/                     # Docker Compose for local dev
├── DEPLOYMENT_REPORT.md      # High-level deployment report
├── TECHNICAL_DOCUMENTATION.md # Detailed technical documentation
└── README.md                 # This file
```

---

## Local Development

### Using Docker Compose

```bash
cd docs
docker-compose up -d
```

This starts all services locally with MySQL database.

**Access:**
- Frontend: http://localhost
- Student API: http://localhost:8081/docs
- Course API: http://localhost:8082/docs
- Enrollment API: http://localhost:8083/docs

### Stop Services

```bash
docker-compose down
```

---

## GCP Deployment

### Prerequisites

1. GCP project with billing enabled
2. Required APIs enabled:
   - Kubernetes Engine API
   - Cloud SQL Admin API
   - Artifact Registry API

### Quick Deployment

```bash
# 1. Create Artifact Registry
gcloud artifacts repositories create edutrack-repo \
  --repository-format=docker \
  --location=us-central1

# 2. Build and push images
docker build -t us-central1-docker.pkg.dev/PROJECT-ID/edutrack-repo/student-service:v1 ./student-service
docker push us-central1-docker.pkg.dev/PROJECT-ID/edutrack-repo/student-service:v1
# Repeat for course-service, enrollment-service, frontend

# 3. Create GKE cluster
gcloud container clusters create edutrack-cluster \
  --zone=us-central1-a \
  --num-nodes=2 \
  --machine-type=e2-medium

# 4. Get credentials
gcloud container clusters get-credentials edutrack-cluster --zone=us-central1-a

# 5. Create secrets
kubectl create secret generic cloudsql-instance-credentials --from-file=key.json=./key.json
kubectl apply -f k8s/secrets.yaml

# 6. Deploy services
kubectl apply -f k8s/student-deployment.yaml
kubectl apply -f k8s/course-deployment.yaml
kubectl apply -f k8s/enrollment-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 7. Get external IP
kubectl get service frontend
```

---

## API Documentation

### Student Service (Port 8081)

- `GET /students` - List all students
- `GET /students/{id}` - Get student by ID
- `POST /students` - Create new student
- `PUT /students/{id}` - Update student
- `DELETE /students/{id}` - Delete student
- `GET /health` - Health check

### Course Service (Port 8082)

- `GET /courses` - List all courses
- `POST /courses` - Create course (requires admin token)
- `PUT /courses/{id}` - Update course (requires admin token)
- `DELETE /courses/{id}` - Delete course (requires admin token)
- `POST /admin/login` - Admin login (username: admin, password: admin123)
- `GET /health` - Health check

### Enrollment Service (Port 8083)

- `GET /enrollments` - List all enrollments
- `POST /enrollments` - Enroll student in course
- `DELETE /enrollments/{id}` - Drop enrollment
- `GET /enrollments/student/{student_id}` - Get enrollments by student
- `GET /health` - Health check

---

## Monitoring

### View Logs

```bash
# View pod logs
kubectl logs -f deployment/student-service

# View all service logs
kubectl logs -l app=student-service --tail=100
```

### Health Checks

All services expose `/health` endpoints accessible via the frontend LoadBalancer:

```bash
curl http://136.115.228.130/api/student/health
curl http://136.115.228.130/api/course/health
curl http://136.115.228.130/api/enrollment/health
```

---

## Secret Management

### Kubernetes Secrets Used

1. **Database Credentials (`edutrack-db-secret`)**
   - Created via `kubectl apply -f k8s/secrets.yaml`
   - Stores: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
   - Injected as environment variables into application pods

2. **Cloud SQL Service Account (`cloudsql-instance-credentials`)**
   - Created via `kubectl create secret generic cloudsql-instance-credentials --from-file=key.json=./key.json`
   - Contains: Google Cloud Service Account JSON key
   - Mounted as volume in all backend pods at `/secrets/key.json`
   - Used by Cloud SQL Auth Proxy to authenticate to Cloud SQL instance

### How Secrets Are Used

The Cloud SQL Auth Proxy sidecar container reads the service account key from the mounted secret and uses it to establish a secure, encrypted connection to the Cloud SQL instance. Applications connect to `127.0.0.1:5432` (localhost), where the proxy listens.

---

## Troubleshooting

### Pods Not Starting

```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Database Connection Issues

```bash
# Check proxy logs
kubectl logs <pod-name> -c cloudsql-proxy

# Check application logs
kubectl logs <pod-name> -c student-service
```

### Get Service Status

```bash
kubectl get all
kubectl get services
```

---

## Documentation

For detailed information, see:

- **DEPLOYMENT_REPORT.md** - High-level deployment overview, architecture decisions, and cloud services configuration
- **TECHNICAL_DOCUMENTATION.md** - Complete technical details including code structure, API specifications, deployment commands, and troubleshooting guide

---

## License

Created for educational purposes as part of a Cloud Computing assignment.

---

## Contributors

- Unknown-086

---

Built with Python FastAPI and Google Cloud Platform
