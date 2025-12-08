# EduTrack - Technical Documentation

**Document Type:** Technical Implementation Details  
**Audience:** Developers, DevOps Engineers  
**Last Updated:** December 2025

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Application Architecture](#2-application-architecture)
3. [Docker Configuration](#3-docker-configuration)
4. [Kubernetes Manifests](#4-kubernetes-manifests)
5. [Database Schema](#5-database-schema)
6. [API Specifications](#6-api-specifications)
7. [Cloud SQL Integration](#7-cloud-sql-integration)
8. [Security Implementation](#8-security-implementation)
9. [Deployment Commands](#9-deployment-commands)
10. [Troubleshooting Guide](#10-troubleshooting-guide)

---

## 1. Technology Stack

### 1.1 Backend Services
- **Framework:** FastAPI 0.104.1
- **Language:** Python 3.11
- **Database Driver:** psycopg (PostgreSQL adapter) v3
- **HTTP Client:** requests 2.31.0
- **ASGI Server:** Uvicorn
- **Container Base Image:** python:3.11-alpine

### 1.2 Frontend
- **Web Server:** Nginx (Alpine-based)
- **UI:** Vanilla JavaScript, HTML5, CSS3
- **Configuration:** Custom nginx.conf for reverse proxy

### 1.3 Database
- **Engine:** PostgreSQL 15
- **Hosting:** Google Cloud SQL
- **Connection Method:** Cloud SQL Auth Proxy (sidecar pattern)

### 1.4 Infrastructure
- **Orchestration:** Kubernetes (GKE)
- **Container Registry:** Google Artifact Registry
- **Secret Management:** Kubernetes Secrets
- **Proxy:** Cloud SQL Auth Proxy 2.11.4

---

## 2. Application Architecture

### 2.1 Service Communication Flow

```
                                     ┌──────────────────────────┐
                                     │        End User          │
                                     │   (Browser / Client)     │
                                     └─────────────┬────────────┘
                                                   │  HTTP/HTTPS
                                                   ▼
                                 ┌────────────────────────────────────┐
                                 │      Google Cloud Load Balancer    │
                                 │   (External IP: 136.115.228.130)   │
                                 └──────────────────┬─────────────────┘
                                                    │
                                                    ▼
            ┌─────────────────────────────────────────────────────────────────────────────────────┐
            │                           GKE Cluster (us-central1)                                 │
            │─────────────────────────────────────────────────────────────────────────────────────│
            │                                                                                     │
            │  ┌─────────────────────────────────────┐                                            │
            │  │             Frontend Pod            │                                            │
            │  │  ┌──────────────────────────────┐   │    Internal Service: 80                    │
            │  │  │      NGINX Web Server        │   │◀──────────────────────────┐                │
            │  │  └──────────────────────────────┘   │                           │                │
            │  └─────────────────────────────────────┘                           │                │
            │                                                                    │                │
            │                                                                    │                │
            │  ┌──────────────────────┐    ┌──────────────────────┐    ┌───────────────────────┐  │
            │  │ Student Service Pod  │    │ Course Service Pod   │    │Enrollment Service Pod │  │
            │  │──────────┬───────────│    │──────────┬───────────│    │──────────┬────────────│  │
            │  │ FastAPI  │ Sidecar   │    │ FastAPI  │ Sidecar   │    │ FastAPI  │ Sidecar    │  │
            │  │ Backend  │ Cloud SQL │    │ Backend  │ Cloud SQL │    │ Backend  │ Cloud SQL  │  │
            │  │ Container│ Proxy     │    │ Container│ Proxy     │    │ Container│ Proxy      │  │
            │  └───────┬──┴───────────┘    └───────┬──┴───────────┘    └───────┬──┴────────────┘  │
            │          │                           │                           │                  │
            │          └───────────────(5432 secure, IAM-auth)─────────────────┘                  │
            │                                                                                     │
            └─────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
                     ┌────────────────────────────────────────────────────┐
                     │            Cloud SQL (PostgreSQL Instance)         │
                     │   - Private IP (future use)                        │
                     │   - Public IP enabled for proxy connection         │
                     │   - Connected ONLY through Cloud SQL Proxy         │
                     └────────────────────────────────────────────────────┘


                                 ┌─────────────────────────────┐
                                 │      Artifact Registry      │
                                 │  Stores all Docker Images   │
                                 │  GKE pulls images from here │
                                 └─────────────────────────────┘
```

### 2.2 Pod Architecture (Backend Services)

Each backend service pod contains:

```yaml
Pod: student-service-xxxxxxxxxx
├── Container 1: student-service
│   ├── Port: 8081
│   ├── Environment Variables: (from secrets)
│   │   ├── DB_HOST=127.0.0.1
│   │   ├── DB_PORT=5432
│   │   ├── DB_USER=edutrack
│   │   ├── DB_PASSWORD=xxxxx
│   │   └── DB_NAME=edutrack
│   └── Connects to: localhost:5432
│
└── Container 2: cloudsql-proxy (Sidecar)
    ├── Image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.11.4
    ├── Args:
    │   ├── --port=5432
    │   ├── --address=0.0.0.0
    │   ├── --credentials-file=/secrets/key.json
    │   └── cloud-assignment-2-480010:us-central1:edutrack-db
    └── Volume Mount: /secrets (from cloudsql-instance-credentials secret)
```

---

## 3. Docker Configuration

### 3.1 Backend Service Dockerfile Structure

```dockerfile
FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 808X

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "808X"]
```

**Key Points:**
- Alpine base reduces image size (~50 MB vs ~900 MB for standard Python)
- No-cache pip install minimizes layer size
- Port varies per service (8081, 8082, 8083)

### 3.2 Frontend Dockerfile

```dockerfile
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3.3 Building and Pushing Images

```bash
# Set project variables
PROJECT_ID="cloud-assignment-2-480010"
REGION="us-central1"
REPO="edutrack-repo"

# Build student service
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/student-service:v1 ./student-service

# Push to Artifact Registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/student-service:v1

# Repeat for course-service, enrollment-service, and frontend
```

---

## 4. Kubernetes Manifests

### 4.1 Deployment Configuration

**Key Configuration Parameters:**

```yaml
spec:
  replicas: 1  # Limited by resource constraints
  selector:
    matchLabels:
      app: student-service
  template:
    spec:
      containers:
      - name: student-service
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 10
```

**Probe Configuration Explained:**
- **Liveness Probe:** Restarts container if health check fails
- **Readiness Probe:** Removes pod from service endpoints if not ready
- **Initial Delay:** Gives app time to start before first check
- **Period:** Check interval

### 4.2 Service Configuration

```yaml
# ClusterIP (Internal only)
apiVersion: v1
kind: Service
metadata:
  name: student-service
spec:
  type: ClusterIP
  ports:
  - port: 8081
    targetPort: 8081
  selector:
    app: student-service
```

```yaml
# LoadBalancer (External access)
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: frontend
```

### 4.3 Secret Configuration

**Database Credentials Secret:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: edutrack-db-secret
type: Opaque
stringData:
  DB_HOST: "127.0.0.1"
  DB_PORT: "5432"
  DB_USER: "edutrack"
  DB_PASSWORD: "password"
  DB_NAME: "edutrack"
```

**Cloud SQL Service Account Secret (Created via CLI):**

```bash
kubectl create secret generic cloudsql-instance-credentials \
  --from-file=key.json=./key.json
```

This creates:
- Secret name: `cloudsql-instance-credentials`
- Key: `key.json`
- Value: Base64-encoded service account JSON

---

## 5. Database Schema

### 5.1 Students Table

```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    date_of_birth DATE NOT NULL,
    major VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Courses Table

```sql
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    instructor VARCHAR(100),
    credits INTEGER NOT NULL,
    max_capacity INTEGER NOT NULL DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3 Enrollments Table

```sql
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    grade VARCHAR(2),
    UNIQUE(student_id, course_id)
);
```

**Relationships:**
- One-to-Many: Student → Enrollments
- One-to-Many: Course → Enrollments
- Many-to-Many: Students ↔ Courses (through Enrollments)

---

## 6. API Specifications

### 6.1 Student Service (Port 8081)

#### Endpoints:

**GET /students**
- Returns all students
- Response: `[{id, name, email, date_of_birth, major, created_at}]`

**GET /students/{id}**
- Returns single student by ID
- Response: `{id, name, email, date_of_birth, major, created_at}`

**POST /students**
- Creates new student
- Request Body: `{name, email, date_of_birth, major}`
- Response: `{id, name, email, date_of_birth, major, created_at}`

**PUT /students/{id}**
- Updates student
- Request Body: `{name, email, date_of_birth, major}`
- Response: `{id, name, email, date_of_birth, major, created_at}`

**DELETE /students/{id}**
- Deletes student (cascade deletes enrollments)
- Response: `{message: "Student deleted successfully"}`

**GET /health**
- Health check endpoint
- Response: `{status: "healthy", service: "student-service"}`

### 6.2 Course Service (Port 8082)

#### Endpoints:

**GET /courses**
- Returns all courses with enrollment count
- Response: `[{id, title, code, description, instructor, credits, max_capacity, enrolled_count}]`

**POST /courses**
- Creates new course (requires admin token)
- Headers: `Authorization: Bearer <token>`
- Request Body: `{title, code, description, instructor, credits, max_capacity}`
- Response: `{id, title, code, ...}`

**PUT /courses/{id}**
- Updates course (requires admin token)
- Headers: `Authorization: Bearer <token>`
- Request Body: `{title, code, description, instructor, credits, max_capacity}`

**DELETE /courses/{id}**
- Deletes course (requires admin token)
- Headers: `Authorization: Bearer <token>`

**POST /admin/login**
- Admin authentication
- Request Body: `{username, password}`
- Response: `{access_token, token_type: "bearer"}`
- Default credentials: admin/admin123

**GET /health**
- Health check endpoint

### 6.3 Enrollment Service (Port 8083)

#### Endpoints:

**GET /enrollments**
- Returns all enrollments with student and course details
- Response: `[{id, student_id, course_id, enrollment_date, grade, student_name, course_title}]`

**POST /enrollments**
- Enrolls student in course (checks capacity)
- Request Body: `{student_id, course_id}`
- Validates:
  - Student exists
  - Course exists
  - Course not full
  - No duplicate enrollment
- Response: `{id, student_id, course_id, enrollment_date}`

**DELETE /enrollments/{id}**
- Removes enrollment
- Response: `{message: "Enrollment deleted successfully"}`

**GET /students/{student_id}/enrollments**
- Returns all enrollments for a student
- Response: `[{enrollment details}]`

**GET /health**
- Health check endpoint

---

## 7. Cloud SQL Integration

### 7.1 Cloud SQL Auth Proxy Configuration

**Proxy Container Arguments:**

```yaml
args:
- "--port=5432"                    # Listen port in pod
- "--address=0.0.0.0"              # Listen on all interfaces in pod
- "--credentials-file=/secrets/key.json"  # Service account key
- "cloud-assignment-2-480010:us-central1:edutrack-db"  # Instance connection name
```

**Volume Mount:**

```yaml
volumeMounts:
- name: cloudsql-instance-credentials
  mountPath: /secrets
  readOnly: true

volumes:
- name: cloudsql-instance-credentials
  secret:
    secretName: cloudsql-instance-credentials
```

### 7.2 Application Database Connection

**Python Connection Code (psycopg):**

```python
import os
import psycopg

def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),      # 127.0.0.1
        port=os.getenv("DB_PORT"),      # 5432
        user=os.getenv("DB_USER"),      # edutrack
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")     # edutrack
    )
```

### 7.3 Connection Flow

1. Application container reads environment variables from secret
2. Application attempts connection to `127.0.0.1:5432`
3. Request intercepted by Cloud SQL Proxy sidecar (listening on same pod)
4. Proxy authenticates using service account key from `/secrets/key.json`
5. Proxy establishes encrypted connection to Cloud SQL instance
6. Proxy forwards application queries to Cloud SQL
7. Results returned to application

**Benefits:**
- No SSL configuration in application
- Automatic credential rotation support
- Encrypted connections
- IAM-based access control

---

## 8. Security Implementation

### 8.1 Service Account Creation

```bash
# Create service account
gcloud iam service-accounts create edutrack-sa \
  --display-name="EduTrack Cloud SQL Client"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding cloud-assignment-2-480010 \
  --member="serviceAccount:edutrack-sa@cloud-assignment-2-480010.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Generate key
gcloud iam service-accounts keys create key.json \
  --iam-account=edutrack-sa@cloud-assignment-2-480010.iam.gserviceaccount.com
```

### 8.2 Admin Authentication (Course Service)

**Token Generation:**
- Algorithm: HS256 (HMAC with SHA-256)
- Secret Key: Configured in environment
- Payload: `{sub: username, exp: expiration_time}`
- Expiration: 30 minutes

**Validation:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 8.3 Network Security

**Ingress Rules:**
- Frontend: Exposed via LoadBalancer (port 80)
- Backend Services: ClusterIP only (internal)

**Egress Rules:**
- Application containers: Can reach Cloud SQL proxy (localhost)
- Proxy containers: Can reach Cloud SQL instance (GCP internal network)

---

## 9. Deployment Commands

### 9.1 Prerequisites Setup

```bash
# Set project
gcloud config set project cloud-assignment-2-480010

# Enable APIs
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry
gcloud artifacts repositories create edutrack-repo \
  --repository-format=docker \
  --location=us-central1

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 9.2 Cloud SQL Setup

```bash
# Create instance
gcloud sql instances create edutrack-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create edutrack --instance=edutrack-db

# Create user
gcloud sql users create edutrack \
  --instance=edutrack-db \
  --password=password
```

### 9.3 Build and Push Images

```bash
# Navigate to project root
cd EduTrack

# Build all images
docker build -t us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/student-service:v1 ./student-service
docker build -t us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/course-service:v1 ./course-service
docker build -t us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/enrollment-service:v1 ./enrollment-service
docker build -t us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/frontend:v1 ./frontend

# Push all images
docker push us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/student-service:v1
docker push us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/course-service:v1
docker push us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/enrollment-service:v1
docker push us-central1-docker.pkg.dev/cloud-assignment-2-480010/edutrack-repo/frontend:v1
```

### 9.4 GKE Cluster Setup

```bash
# Create cluster
gcloud container clusters create edutrack-cluster \
  --zone=us-central1-a \
  --num-nodes=2 \
  --machine-type=e2-medium

# Get credentials
gcloud container clusters get-credentials edutrack-cluster \
  --zone=us-central1-a
```

### 9.5 Deploy to Kubernetes

```bash
# Create secrets
kubectl apply -f k8s/secrets.yaml
kubectl create secret generic cloudsql-instance-credentials \
  --from-file=key.json=./key.json

# Deploy services
kubectl apply -f k8s/student-deployment.yaml
kubectl apply -f k8s/course-deployment.yaml
kubectl apply -f k8s/enrollment-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Check status
kubectl get pods
kubectl get services
```

### 9.6 Get External IP

```bash
# Wait for LoadBalancer IP assignment
kubectl get service frontend --watch

# Once EXTERNAL-IP shows an IP address (not <pending>), access via:
# http://<EXTERNAL-IP>
```

---

## 10. Troubleshooting Guide

### 10.1 Common Issues and Solutions

#### Issue: Pods Stuck in Pending State
**Symptoms:**
```bash
NAME                                  READY   STATUS    RESTARTS   AGE
student-service-xxxxxxxxxx-xxxxx      0/2     Pending   0          5m
```

**Diagnosis:**
```bash
kubectl describe pod student-service-xxxxxxxxxx-xxxxx
# Look for: "Insufficient memory" or "Insufficient cpu"
```

**Solution:**
- Reduce replicas from 2 to 1
- Or increase cluster size
- Or reduce resource requests in deployment YAML

#### Issue: Cloud SQL Auth Proxy Authentication Failed
**Symptoms:**
```bash
kubectl logs student-service-xxx -c cloudsql-proxy
# Error: ACCESS_TOKEN_SCOPE_INSUFFICIENT or Error 403
```

**Solution:**
```bash
# Verify service account has correct role
gcloud projects get-iam-policy cloud-assignment-2-480010 \
  --flatten="bindings[].members" \
  --filter="bindings.members:edutrack-sa@"

# Ensure --credentials-file argument is present
kubectl get pod student-service-xxx -o yaml | grep credentials-file
```

#### Issue: Application Can't Connect to Database
**Symptoms:**
- Logs show connection timeout or refused
- Health checks failing

**Diagnosis:**
```bash
kubectl logs student-service-xxx -c student-service
kubectl logs student-service-xxx -c cloudsql-proxy
```

**Solution:**
- Verify DB_HOST is set to "127.0.0.1" (not Cloud SQL IP)
- Check proxy is running: `kubectl get pod student-service-xxx -o jsonpath='{.status.containerStatuses[*].name}'`
- Verify secret exists: `kubectl get secret edutrack-db-secret -o yaml`

#### Issue: 502 Bad Gateway from Frontend
**Symptoms:**
- Frontend loads but API calls fail
- Browser console shows 502 errors

**Diagnosis:**
```bash
# Check if backend pods are running
kubectl get pods -l app=student-service

# Check backend logs
kubectl logs -l app=student-service -c student-service --tail=50
```

**Solution:**
- Verify backend services are running and ready
- Check nginx.conf proxy_pass URLs match service names
- Ensure backend health endpoints respond: `kubectl exec -it frontend-xxx -- wget -O- http://student-service:8081/health`

#### Issue: Image Pull Errors
**Symptoms:**
```bash
Failed to pull image "us-central1-docker.pkg.dev/.../student-service:v1"
```

**Solution:**
```bash
# Grant GKE access to Artifact Registry
gcloud projects add-iam-policy-binding cloud-assignment-2-480010 \
  --member="serviceAccount:$(gcloud iam service-accounts list --filter="displayName:Compute Engine default service account" --format="value(email)")" \
  --role="roles/artifactregistry.reader"
```

### 10.2 Debugging Commands

```bash
# View all resources
kubectl get all

# Check pod details
kubectl describe pod <pod-name>

# View logs (specific container)
kubectl logs <pod-name> -c <container-name>

# View logs (follow mode)
kubectl logs -f <pod-name> -c <container-name>

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/sh

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check resource usage
kubectl top nodes
kubectl top pods

# Port forward for local testing
kubectl port-forward svc/student-service 8081:8081
```

### 10.3 Health Check Verification

```bash
# From Cloud Shell or local terminal
curl http://<EXTERNAL-IP>/api/student/health
curl http://<EXTERNAL-IP>/api/course/health
curl http://<EXTERNAL-IP>/api/enrollment/health

# Expected response: {"status":"healthy","service":"<service-name>"}
```

---

## 11. Performance Considerations

### 11.1 Resource Sizing

**Current Configuration:**
- CPU Request: 100m (0.1 CPU core)
- CPU Limit: 200m (0.2 CPU core)
- Memory Request: 128 Mi
- Memory Limit: 256 Mi

**Rationale:**
- FastAPI is async and efficient (low CPU usage)
- psycopg connection pooling reduces memory overhead
- Alpine base images minimize footprint
- Limits prevent resource hogging

### 11.2 Scaling Recommendations

**Horizontal Pod Autoscaler (HPA):**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: student-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: student-service
  minReplicas: 1
  maxReplicas: 3
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Apply:**
```bash
kubectl apply -f k8s/hpa.yaml
```

### 11.3 Database Connection Pooling

For production, implement connection pooling:

```python
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}",
    min_size=2,
    max_size=10
)

def get_db():
    with pool.connection() as conn:
        yield conn
```

---

## 12. Nginx Configuration Details

### 12.1 Frontend nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Reverse proxy for backend services
    location /api/student/ {
        proxy_pass http://student-service:8081/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/course/ {
        proxy_pass http://course-service:8082/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/enrollment/ {
        proxy_pass http://enrollment-service:8083/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static file serving
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Key Features:**
- **URL Rewriting:** `/api/student/` → `http://student-service:8081/`
- **Service Discovery:** Uses Kubernetes DNS (service-name resolves to ClusterIP)
- **Header Forwarding:** Preserves original client IP
- **SPA Support:** `try_files` directive serves index.html for all routes

---

## 13. Local Development Setup

### 13.1 Using Docker Compose (MySQL Version)

```bash
# From project root
cd docs

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:**
- Frontend: http://localhost
- Student API: http://localhost:8081
- Course API: http://localhost:8082
- Enrollment API: http://localhost:8083

### 13.2 Direct Python Execution

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd student-service
pip install -r requirements.txt

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=edutrack
export DB_PASSWORD=password
export DB_NAME=edutrack

# Run service
uvicorn main:app --reload --port 8081
```

---

## 14. CI/CD Considerations

### 14.1 Potential Pipeline (Google Cloud Build)

```yaml
steps:
# Build images
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/edutrack-repo/student-service:$SHORT_SHA', './student-service']

# Push images
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/edutrack-repo/student-service:$SHORT_SHA']

# Deploy to GKE
- name: 'gcr.io/cloud-builders/kubectl'
  args:
  - 'set'
  - 'image'
  - 'deployment/student-service'
  - 'student-service=us-central1-docker.pkg.dev/$PROJECT_ID/edutrack-repo/student-service:$SHORT_SHA'
  env:
  - 'CLOUDSDK_COMPUTE_ZONE=us-central1-a'
  - 'CLOUDSDK_CONTAINER_CLUSTER=edutrack-cluster'
```

### 14.2 Rollback Strategy

```bash
# View deployment history
kubectl rollout history deployment/student-service

# Rollback to previous version
kubectl rollout undo deployment/student-service

# Rollback to specific revision
kubectl rollout undo deployment/student-service --to-revision=2
```

---

## 15. Monitoring and Logging

### 15.1 Viewing Logs

```bash
# GKE automatically collects logs
# View in Cloud Console: Kubernetes Engine > Workloads > Select Pod > Logs

# Or via kubectl
kubectl logs -l app=student-service -c student-service --tail=100 --follow
```

### 15.2 Metrics

Access via:
- Google Cloud Console > Kubernetes Engine > Clusters > Metrics
- Prometheus (if installed): Configure ServiceMonitor for scraping

### 15.3 Application-Level Logging

Each service implements structured logging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/students")
async def get_students():
    logger.info("Fetching all students")
    # ... code ...
    logger.info(f"Retrieved {len(students)} students")
```

---

## 16. Security Hardening (Production)

### 16.1 Recommendations

1. **Use Secret Manager instead of Kubernetes Secrets**
   ```bash
   gcloud secrets create db-password --data-file=-
   ```

2. **Enable Workload Identity** (instead of service account keys)
   ```bash
   gcloud iam service-accounts add-iam-policy-binding \
     --role roles/iam.workloadIdentityUser \
     --member "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]" \
     GSA_NAME@PROJECT_ID.iam.gserviceaccount.com
   ```

3. **Network Policies** (restrict pod-to-pod communication)
4. **Pod Security Policies** (enforce security standards)
5. **Regular Image Scanning** (Artifact Registry vulnerability scanning)

---

**Document Maintained By:** EduTrack Development Team  
**For Questions:** Refer to deployment logs and kubectl describe outputs
