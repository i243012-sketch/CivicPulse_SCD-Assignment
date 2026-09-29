# CivicPulse

## Architecture Diagram
```
┌─────────┐      ┌──────────┐      ┌──────────┐
│ Frontend│─────▶│  Backend │─────▶│ Postgres │
│  Nginx  │      │  FastAPI │      │ Database │
└─────────┘      └──────────┘      └──────────┘
                       │
                       ▼
                  ┌─────────┐
                  │  Redis  │
                  │  Cache  │
                  └─────────┘
```

## Quickstart Guide
```bash
# Clone and run locally
git clone <repo>
cd CivicPulse_SCD-Assignment
cp backend/.env.example backend/.env  # Edit GROQ_API_KEY
docker compose up -d

# Access
Frontend: http://localhost:8080
Backend API: http://localhost:8000/api
API Docs: http://localhost:8000/docs
```

## API Endpoints Table

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/complaints` | Create new complaint |
| GET | `/api/complaints` | List all complaints |
| GET | `/api/complaints/{id}` | Get complaint by ID |
| PATCH | `/api/complaints/{id}` | Update complaint status |
| GET | `/api/stats` | Get statistics (cached) |
| GET | `/api/meta/health` | Health check |

## Deployment Instructions
```bash
# Deploy to Kubernetes
kubectl apply -k k8s/overlays/prod

# Check status
kubectl get pods -n civicpulse-prod

# View logs
kubectl logs -n civicpulse-prod -l app=backend
```

## Environment Variables
- `DATABASE_URL`
- `REDIS_URL`
- `TRIAGE_PROVIDER`
- `GROQ_API_KEY`