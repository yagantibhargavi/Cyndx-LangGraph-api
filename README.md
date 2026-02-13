Cyndx Engineering Assessment – LangGraph API Deployment
Overview

This project implements a containerized FastAPI service and deployment workflow using Docker, AWS (ECR + App Runner), and Terraform for infrastructure provisioning.

The goal is to demonstrate:
Backend API development
Containerization
Cloud deployment
Infrastructure as Code (IaC)
Production-ready health monitoring

#Tech Stack

Python
FastAPI
Docker
AWS ECR
AWS App Runner
Terraform
LangGraph

#Project Structure
.
├── app/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   │
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── ecr.tf
│   │   └── .terraform.lock.hcl
│   │
│   └── main.py
│
├── Dockerfile
├── requirements.txt
├── .env
└── README.md


#Running Locally
1) Create virtual environment
python -m venv venv
source venv/bin/activate
2) Install dependencies
pip install -r requirements.txt
3) Run API
uvicorn app.main:app --host 0.0.0.0 --port 8000
4) Health Check
http://localhost:8000/health

Response example:

{
  "status": "healthy",
  "version": "1.0.0"
}

#Docker Setup
Build Docker image
docker build -t cyndx-langgraph-api .
Run container
docker run -p 8000:8000 cyndx-langgraph-api
Test
http://localhost:8000/health

#AWS Deployment
Container Registry (ECR)
Create repository in AWS ECR
Authenticate Docker to AWS
aws ecr get-login-password --region us-east-1 \
| docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
Tag image
docker tag cyndx-langgraph-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/cyndx-langgraph-api:latest
Push image
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/cyndx-langgraph-api:latest

#AWS App Runner
App Runner is used to deploy the containerized API.
Configuration:
Image source: ECR
Port: 8000
Health check path: /health
Protocol: HTTP
App Runner provisions infrastructure and exposes a public endpoint automatically.

Terraform (Infrastructure as Code)
Terraform is used to provision:
AWS ECR repository
App Runner service
IAM roles

Setup
cd infra
terraform init
terraform plan
terraform apply

Outputs include:
ECR repository URL
App Runner service reference

#API Documentation (Swagger UI)

Interactive API documentation is automatically generated using FastAPI.
After running the service locally:
Swagger UI:
http://localhost:8000/docs
ReDoc:
http://localhost:8000/redoc

#Health Monitoring

The service exposes:
GET /health
Used by:
Load balancer checks
App Runner readiness
Monitoring systems
Design Decisions
FastAPI chosen for performance and async support
Docker ensures reproducible deployment
App Runner simplifies container hosting
Terraform provides version-controlled infrastructure
Health endpoint ensures production readiness

#LangGraph Agent Execution
POST /run
Request:

{
  "query": "Analyze company growth signals"
}

Response:

{
  "result": "Agent reasoning output"
}

#Challenges & Notes

Deployment health checks require correct port mapping
Container must bind to 0.0.0.0
Health endpoint must respond quickly
AWS IAM permissions required for ECR access

#Future Improvements

CI/CD pipeline (GitHub Actions)
CloudWatch logging
Auto scaling policies
API authentication
Monitoring dashboards

Author
Bhargavi

Submission Notes

API runs locally
Docker container built successfully
Infrastructure defined via Terraform
Deployment configured using AWS App Runner
Health endpoint implemented for service monitoring
This repository demonstrates full-stack backend deployment readiness including containerization and infrastructure automation.
