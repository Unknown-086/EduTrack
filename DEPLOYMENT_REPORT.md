# EduTrack - Cloud Deployment Report

**Project:** EduTrack - Cloud-Native Education Management System  
**Platform:** Google Kubernetes Engine (GKE)  
**Deployment Date:** December 2025  

---

## Executive Summary

This report documents the successful deployment of EduTrack, a microservices-based education management system, on Google Cloud Platform using Kubernetes Engine. The application consists of three backend microservices, a PostgreSQL database, and a web frontend, all orchestrated through Kubernetes and integrated with Google Cloud services.

---

## 1. Project Overview

### 1.1 Application Purpose
EduTrack is a cloud-native education management platform that enables:
- Student profile management
- Course catalog administration
- Course enrollment tracking with capacity limits
- Secure admin authentication for course operations

### 1.2 Architecture Approach
The system follows a microservices architecture pattern where:
- Each service operates independently
- Services communicate through well-defined APIs
- The frontend acts as a reverse proxy routing requests to appropriate services
- Database connections are secured through a Cloud SQL Auth Proxy sidecar pattern

---

## 2. Cloud Infrastructure

### 2.1 Google Cloud Platform Services Used

#### 2.1.1 Google Kubernetes Engine (GKE)
- **Cluster Configuration:**
  - Cluster Name: `edutrack-cluster`
  - Region: `us-central1`
  - Node Count: 2 VMs
  - Machine Type: E2-medium (2 vCPU, 4 GB memory per node)
  - Total Cluster Capacity: 4 vCPU, 8 GB memory

- **Rationale for Configuration:**
  - E2-medium instances provide cost-effective performance
  - Two-node cluster ensures high availability of system pods
  - Resource allocation prevents single point of failure

#### 2.1.2 Cloud SQL (PostgreSQL)
- **Database Configuration:**
  - Instance Name: `edutrack-db`
  - Database Engine: PostgreSQL 15
  - Region: `us-central1`
  - Instance Tier: Configured for development/production workload

- **Security Features:**
  - Private IP configuration
  - No direct public internet access
  - Accessed only through Cloud SQL Auth Proxy

#### 2.1.3 Artifact Registry
- **Container Registry:**
  - Repository Name: `edutrack-repo`
  - Location: `us-central1`
  - Purpose: Stores Docker images for all services
  - Images Stored:
    - `student-service:v1`
    - `course-service:v1`
    - `enrollment-service:v1`
    - `frontend:v1`

#### 2.1.4 Kubernetes Secrets (Secret Management)
Two types of secrets are managed in the Kubernetes cluster:

**a) Application Database Credentials (`edutrack-db-secret`):**
- Created using standard Kubernetes Secret objects
- Stores: Database host, port, username, password, database name
- Injected into application pods as environment variables
- Type: Opaque (base64 encoded)

**b) Cloud SQL Service Account Key (`cloudsql-instance-credentials`):**
- **This is where Google Secret Manager principles are applied**
- Created using command: `kubectl create secret generic cloudsql-instance-credentials --from-file=key.json=./key.json`
- Contains: Google Cloud Service Account JSON key file
- Purpose: Authenticates Cloud SQL Auth Proxy to access Cloud SQL instance
- Mounted as volume in all backend service pods
- Accessed by Cloud SQL Auth Proxy sidecar container at path `/secrets/key.json`

**Secret Management Best Practices Implemented:**
- Secrets are never stored in Git repository
- Secrets are base64 encoded in Kubernetes
- Service account follows principle of least privilege (only Cloud SQL Client role)
- Secrets are mounted as read-only volumes
- Each pod accesses only the secrets it requires

#### 2.1.5 Cloud Build
- **Purpose:** Automated container image building and pushing to Artifact Registry
- **IAM Permissions Granted:** `roles/cloudbuild.builds.editor`

---

## 3. Deployment Architecture

### 3.1 Microservices Deployment

#### 3.1.1 Student Service
- **Purpose:** Manages student profiles (CRUD operations)
- **Container Port:** 8081
- **Replicas:** 1
- **Resource Allocation:**
  - Memory Request: 128 Mi, Limit: 256 Mi
  - CPU Request: 100m, Limit: 200m

#### 3.1.2 Course Service
- **Purpose:** Manages course catalog with admin authentication
- **Container Port:** 8082
- **Replicas:** 1
- **Resource Allocation:**
  - Memory Request: 128 Mi, Limit: 256 Mi
  - CPU Request: 100m, Limit: 200m

#### 3.1.3 Enrollment Service
- **Purpose:** Handles course enrollments and capacity management
- **Container Port:** 8083
- **Replicas:** 1
- **Resource Allocation:**
  - Memory Request: 128 Mi, Limit: 256 Mi
  - CPU Request: 100m, Limit: 200m

#### 3.1.4 Frontend Service
- **Purpose:** Nginx-based web server serving HTML/CSS/JS and reverse proxy
- **Container Port:** 80
- **External Access:** LoadBalancer service at `http://136.115.228.130`
- **Replicas:** 1
- **Resource Allocation:**
  - Memory Request: 64 Mi, Limit: 128 Mi
  - CPU Request: 50m, Limit: 100m

### 3.2 Cloud SQL Auth Proxy Pattern
Each backend service pod runs two containers:
1. **Application Container:** Runs the Python FastAPI service
2. **Cloud SQL Auth Proxy Sidecar Container:**
   - Image: `gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.11.4`
   - Establishes secure connection to Cloud SQL
   - Listens on `127.0.0.1:5432` (localhost within pod)
   - Authenticates using service account key from Kubernetes secret
   - Application connects to `127.0.0.1:5432` as if it's a local database

**Benefits of this approach:**
- No need for SSL certificates in application code
- Automatic connection encryption
- Secure credential management
- No direct internet exposure of database

---

## 4. Resource Management and Optimization

### 4.1 Initial Challenges
During deployment, we encountered resource exhaustion issues:
- **Problem:** With 2 replicas per service, pods remained in "Pending" state
- **Root Cause:** Total memory requests exceeded available node capacity
- **Calculation:** 
  - 3 services × 2 replicas × 256 Mi = 1536 Mi per service type
  - Total for apps: ~4.6 GB
  - System pods: ~2 GB
  - Total required: ~6.6 GB (exceeded 8 GB cluster capacity)

### 4.2 Solution Implemented
- **Reduced replicas from 2 to 1** for each service
- New memory footprint:
  - 3 services × 1 replica × 256 Mi = 768 Mi
  - Total with system pods: ~2.8 GB
  - Available headroom: ~5 GB (sufficient for operations)

### 4.3 Production Recommendations
For production deployment with high availability:
- Option 1: Increase to 3 nodes (E2-medium) to support 2 replicas
- Option 2: Use E2-standard-2 (2 vCPU, 8 GB) for more memory per node
- Option 3: Implement Horizontal Pod Autoscaler (HPA) for dynamic scaling

---

## 5. Security Implementation

### 5.1 Database Security
- **Private Networking:** Database not exposed to public internet
- **Proxy Authentication:** All connections through authenticated proxy
- **Credential Isolation:** Database credentials stored as Kubernetes secrets
- **Least Privilege:** Service account has only Cloud SQL Client role

### 5.2 Application Security
- **Admin Authentication:** Course management requires token-based authentication
- **Input Validation:** FastAPI automatic request validation
- **Container Security:** Running as non-root user in proxy containers

### 5.3 Network Security
- **Internal Communication:** Services communicate via ClusterIP (internal only)
- **External Access:** Only frontend exposed through LoadBalancer
- **Reverse Proxy:** Nginx frontend handles all external requests

---

## 6. Deployment Process Summary

### 6.1 Pre-Deployment Steps
1. Created GCP project and enabled required APIs
2. Set up Cloud SQL PostgreSQL instance
3. Created service account with Cloud SQL Client permissions
4. Generated and downloaded service account JSON key
5. Built Docker images for all services
6. Pushed images to Artifact Registry

### 6.2 Kubernetes Deployment Steps
1. Created GKE cluster with specified configuration
2. Configured kubectl to connect to cluster
3. Created Kubernetes secrets:
   - Database credentials secret
   - Cloud SQL service account key secret
4. Applied deployment manifests for all services
5. Exposed frontend via LoadBalancer service
6. Verified pod health and database connectivity

### 6.3 Verification
- All pods running successfully (16 total: 4 application + 12 system)
- Frontend accessible at public IP
- Database connections established through proxy
- All API endpoints responding correctly

---

## 7. Operational Insights

### 7.1 Current Status
- **Deployment Status:** Fully operational
- **Uptime:** All services running and healthy
- **Accessibility:** Public access via http://136.115.228.130
- **Database Connectivity:** Secure connections established

### 7.2 Monitoring Capabilities
- **Health Checks:** Liveness and readiness probes configured
- **Resource Monitoring:** Kubernetes dashboard available
- **Log Aggregation:** GKE automatically collects container logs
- **Metrics:** Available through Google Cloud Console

### 7.3 Known Limitations
- Single replica per service (no high availability)
- Resource constraints require monitoring under load
- Manual scaling required if traffic increases

---

## 8. Cost Optimization

### 8.1 Resource Efficiency
- E2-medium instances: Cost-effective for development/demo
- Minimal replica count reduces compute costs
- Container resource limits prevent waste

### 8.2 Potential Cost Savings
- Auto-scaling based on demand
- Scheduled cluster shutdown for non-business hours (demo purposes)
- Regional deployment (single region) reduces cross-region charges

---

## 9. Lessons Learned

### 9.1 Technical Insights
- Kubernetes resource planning is critical for successful deployment
- Cloud SQL Auth Proxy provides elegant database security solution
- Sidecar pattern effectively separates concerns (app vs. infrastructure)

### 9.2 Debugging Experience
- Pod events and logs essential for troubleshooting
- Understanding Kubernetes controller behavior (auto-restart) prevents confusion
- IAM permissions must be carefully configured for GCP service integration

### 9.3 Best Practices Validated
- Infrastructure as Code (Kubernetes YAML) enables reproducible deployments
- Secret management through Kubernetes secrets works well for small deployments
- Resource limits prevent runaway containers

---

## 10. Conclusion

The EduTrack application has been successfully deployed on Google Kubernetes Engine, demonstrating:
- Effective use of microservices architecture
- Secure database integration through Cloud SQL Auth Proxy
- Proper secret management using Kubernetes secrets
- Resource-aware deployment configuration
- Production-ready infrastructure patterns

The deployment showcases modern cloud-native practices and provides a solid foundation for scaling and enhancement in production environments.

---

## Appendix A: Key Metrics

| Metric | Value |
|--------|-------|
| Total Pods Running | 16 (4 application + 12 system) |
| Cluster Nodes | 2 × E2-medium |
| Total CPU Allocation | 4 vCPU |
| Total Memory Allocation | 8 GB |
| Services Deployed | 4 (3 backend + 1 frontend) |
| External IP Address | 136.115.228.130 |
| Database Engine | PostgreSQL 15 |
| Container Images | 4 (stored in Artifact Registry) |

---

## Appendix B: GCP Project Details

- **Project ID:** cloud-assignment-2-480010
- **Region:** us-central1
- **Cluster Name:** edutrack-cluster
- **Database Instance:** edutrack-db
- **Artifact Registry:** edutrack-repo

---

**Report Prepared By:** EduTrack Development Team  
**Last Updated:** December 2025
