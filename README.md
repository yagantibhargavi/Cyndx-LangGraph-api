Cyndx Engineering Assessment — LangGraph Agent API

This project implements a FastAPI-based conversational agent service powered by LangGraph, containerized with Docker, and provisioned using Terraform.
It supports session-based interactions, message history, and agent-driven responses.

🧭 Architecture Overview
flowchart TD
    User --> FastAPI
    FastAPI --> SessionStore
    FastAPI --> LangGraphAgent
    LangGraphAgent --> LLM
    Terraform --> AWSInfra
    Docker --> AppRunner

# Components

* FastAPI service
REST endpoints
Session management
Swagger UI

*LangGraph agent
Planner + execution nodes
Maintains conversational state

*Session store
In-memory session/message state

*Docker
Containerized runtime

*Terraform
Infrastructure provisioning
Container registry + compute setup

*Cloud
AWS ECR / App Runner (deployment-ready)

# 🗂 Project Structure
app/
  main.py                → FastAPI app
  agent/
    graph.py             → LangGraph workflow
    nodes.py             → agent nodes
    state.py             → state schema

terraform/
  main.tf                → infra resources
  ecr.tf                 → container registry

Dockerfile
requirements.txt
README.md

🚀 Local Development Guide
1. Clone repo
git clone <repo-url>
cd cyndx-langgraph-api

2. Setup environment
python -m venv venv
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Configure env
Create .env
GROQ_API_KEY=your_key_here

5. Run locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Swagger:
http://localhost:8000/docs

Health:
http://localhost:8000/health

🐳 Run with Docker
Build:
docker build -t cyndx-langgraph-api .
Run:
docker run -p 8000:8000 cyndx-langgraph-api

☁️ Deployment Guide (Terraform)
Prerequisites
AWS account
Terraform installed
Docker installed
AWS CLI configured

* Steps
1. Initialize Terraform
cd terraform
terraform init

2. Plan infrastructure
terraform plan

3. Apply infra
terraform apply

*Creates:
ECR repository
Container runtime environment

4. Push Docker image
docker tag cyndx-langgraph-api:latest <ECR_URI>
docker push <ECR_URI>

5. Deployment Status (Current)
Terraform infra provisioning: ✅ completed
Container build/push: ✅ completed
App Runner deployment: ❌ failing due to health check failure
Error: Health check failed on protocol HTTP [Path: '/health'] [Port: '8000']
Local Docker + Swagger: ✅ working

* What I attempted
Verified /health locally: ✅
Configured App Runner health check: HTTP /health port 8000
Rebuilt and pushed image to ECR multiple times
Next step would be aligning App Runner port with container port using PORT env var

🧠 Design Decisions
* Why FastAPI?
async-first
lightweight
built-in Swagger
production ready

* Why LangGraph?
explicit graph-based agent flows
stateful conversation modeling
modular node design

*Why in-memory session store?
fast iteration
minimal infra dependency
easy debugging

*Future improvement:
Redis / DynamoDB

*Why Docker?
reproducibility
deployment portability
cloud-ready

*Why Terraform?
infra as code
repeatable deployment
scalable cloud provisioning

⚖️ Trade-offs & Limitations
* In-memory sessions
lost on restart
not horizontally scalable

* No authentication
API open
needs auth layer

* No observability stack
logs local only
no tracing/metrics

* Limited CI/CD
manual deploy
future: GitHub Actions

* LLM dependency
response latency
cost considerations

📡 API Reference
Swagger UI:
/docs

Endpoints
Health
GET /health

Create session
POST /sessions

Response:

{
  "session_id": "...",
  "status": "active"
}

Get session history
GET /sessions/{session_id}/history

Send message
POST /sessions/{session_id}/messages

Delete session
DELETE /sessions/{session_id}

🧪 Example Request
curl -X POST http://localhost:8000/sessions
curl -X POST http://localhost:8000/sessions/{id}/messages \
-H "Content-Type: application/json" \
-d '{"content":"Hello"}'

📘 Swagger
Auto-generated docs available at:
http://localhost:8000/docs

🔮 Future Improvements
persistent session store
CI/CD pipeline
authentication
monitoring
autoscaling infra
streaming LLM responses

👩‍💻 Author
Bhargavi

