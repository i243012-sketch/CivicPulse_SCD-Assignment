# CivicPulse Kubernetes Manifests

This directory contains Kustomize-based Kubernetes manifests for deploying CivicPulse.

## Structure

```
k8s/
├── base/                          # Base manifests
│   ├── namespace.yaml            # civicpulse namespace
│   ├── configmap.yaml            # Non-secret configuration
│   ├── secret.yaml               # Secrets (with placeholder values)
│   ├── postgres-statefulset.yaml # PostgreSQL StatefulSet with PVC
│   ├── redis-deployment.yaml     # Redis Deployment with PVC
│   ├── backend-deployment.yaml   # Backend API (≥2 replicas)
│   ├── backend-hpa.yaml          # HorizontalPodAutoscaler
│   ├── backend-vpa.yaml          # VerticalPodAutoscaler (Off mode)
│   ├── backend-pdb.yaml          # PodDisruptionBudget
│   ├── frontend-deployment.yaml  # Frontend (≥2 replicas)
│   ├── ingress.yaml              # Ingress routing
│   └── kustomization.yaml        # Base kustomization
├── overlays/
│   ├── dev/                      # Development overlay
│   │   ├── kustomization.yaml
│   │   ├── backend-dev-patch.yaml
│   │   └── ingress-dev-patch.yaml
│   └── prod/                     # Production overlay
│       ├── kustomization.yaml
│       ├── backend-prod-patch.yaml
│       ├── postgres-prod-patch.yaml
│       └── ingress-prod-patch.yaml
└── README.md                     # This file
```

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl CLI tool
- kustomize (or kubectl with kustomize support)
- NGINX Ingress Controller
- cert-manager (for production TLS)
- metrics-server (for HPA)
- VPA operator (optional, for VPA)

## Deployment

### Before Deployment

**CRITICAL: Update secrets before deploying!**

Edit `k8s/base/secret.yaml` and replace placeholder values:
- `DATABASE_PASSWORD`: Strong password for PostgreSQL
- `GROQ_API_KEY`: Your actual Groq API key

**Never commit real secrets to version control!**

### Deploy to Development

```bash
# Build and preview manifests
kubectl kustomize k8s/overlays/dev

# Apply to cluster
kubectl apply -k k8s/overlays/dev

# Check deployment status
kubectl get pods -n civicpulse-dev
kubectl get svc -n civicpulse-dev
kubectl get ingress -n civicpulse-dev
```

### Deploy to Production

```bash
# Build and preview manifests
kubectl kustomize k8s/overlays/prod

# Apply to cluster
kubectl apply -k k8s/overlays/prod

# Check deployment status
kubectl get pods -n civicpulse-prod
kubectl get svc -n civicpulse-prod
kubectl get ingress -n civicpulse-prod
```

## Backend Pod Specifications

### Health Checks

- **Startup Probe** (`/health`):
  - `failureThreshold: 30`
  - `periodSeconds: 2`
  - Total startup timeout: 60 seconds
  - Does NOT depend on database

- **Liveness Probe** (`/health`):
  - Checks if application is alive
  - Does NOT depend on database or cache
  - Restarts pod if failing

- **Readiness Probe** (`/ready`):
  - Checks if application is ready to serve traffic
  - MUST depend on database and Redis connectivity
  - Removes pod from Service endpoints if failing

### Rolling Update Strategy

- `maxSurge: 1` - Allow 1 extra pod during updates
- `maxUnavailable: 0` - Never reduce capacity below desired replicas
- `terminationGracePeriodSeconds: 30` - Grace period for shutdown
- `preStop: sleep 15` - Delay before shutdown to drain connections

### Resource Specifications

**Development:**
- Requests: 100m CPU, 256Mi memory
- Limits: 500m CPU, 512Mi memory

**Production:**
- Requests: 500m CPU, 1Gi memory
- Limits: 2000m CPU, 2Gi memory

### Autoscaling

**HorizontalPodAutoscaler (HPA):**
- Min replicas: 2
- Max replicas: 10
- CPU target: 60% utilization
- Scale down stabilization: 300 seconds (5 minutes)
- Scale up stabilization: 0 seconds (immediate)

**VerticalPodAutoscaler (VPA):**
- Update mode: `Off` (recommendations only, no automatic updates)
- Min allowed: 100m CPU, 256Mi memory
- Max allowed: 2000m CPU, 2Gi memory

**PodDisruptionBudget (PDB):**
- `minAvailable: 1` - Always keep at least 1 pod available during voluntary disruptions

## Database (PostgreSQL)

- Deployed as **StatefulSet** (NOT Deployment)
- Uses `volumeClaimTemplates` for persistent storage
- Storage: 10Gi (dev), 50Gi (prod)
- Headless Service for stable network identity

## Redis

- Deployed as Deployment with PVC
- Storage: 5Gi
- AOF persistence enabled
- Appendfsync: everysec

## Ingress Routing

- `/api` → Backend Service (port 8000)
- `/` → Frontend Service (port 80)

**Development:** `dev.civicpulse.example.com`
**Production:** `civicpulse.example.com` (with TLS via cert-manager)

## Configuration

### ConfigMap (Non-sensitive)

All non-secret configuration is stored in `civicpulse-config` ConfigMap:
- Database host, port, name, user
- Redis host, port
- Application settings (debug, log level, triage provider)
- Rate limiting configuration

### Secret (Sensitive)

Sensitive data is stored in `civicpulse-secrets` Secret:
- `DATABASE_PASSWORD`
- `GROQ_API_KEY`

## Monitoring

```bash
# Watch HPA status
kubectl get hpa -n civicpulse-prod -w

# View VPA recommendations
kubectl describe vpa backend-vpa -n civicpulse-prod

# Check pod resource usage
kubectl top pods -n civicpulse-prod

# View backend logs
kubectl logs -f deployment/backend -n civicpulse-prod

# Check readiness/liveness probe status
kubectl describe pod <pod-name> -n civicpulse-prod
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n civicpulse-prod

# View pod events
kubectl describe pod <pod-name> -n civicpulse-prod

# Check logs
kubectl logs <pod-name> -n civicpulse-prod

# Check previous container logs (if crashed)
kubectl logs <pod-name> -n civicpulse-prod --previous
```

### Backend failing readiness probe

The `/ready` endpoint depends on:
1. Database connectivity (PostgreSQL)
2. Redis connectivity

Check:
```bash
# Verify database is running
kubectl get statefulset postgres -n civicpulse-prod

# Verify redis is running
kubectl get deployment redis -n civicpulse-prod

# Check database connection from backend pod
kubectl exec -it <backend-pod> -n civicpulse-prod -- env | grep DATABASE

# Check redis connection
kubectl exec -it <backend-pod> -n civicpulse-prod -- env | grep REDIS
```

### Secrets not loading

```bash
# Verify secret exists
kubectl get secret civicpulse-secrets -n civicpulse-prod

# View secret keys (not values)
kubectl describe secret civicpulse-secrets -n civicpulse-prod

# Check if backend pod has secret mounted
kubectl describe pod <backend-pod> -n civicpulse-prod | grep -A 5 "Environment:"
```

## Cleanup

```bash
# Delete development environment
kubectl delete -k k8s/overlays/dev

# Delete production environment
kubectl delete -k k8s/overlays/prod

# WARNING: This deletes PVCs and all data!
# To preserve data, back up before deletion
```

## Security Notes

1. **Secrets Management**: The `secret.yaml` file contains placeholder values only. Never commit real secrets to git.

2. **Production Secrets**: Use external secret management (e.g., HashiCorp Vault, AWS Secrets Manager, Kubernetes External Secrets Operator) for production deployments.

3. **Network Policies**: Consider adding NetworkPolicies to restrict pod-to-pod communication.

4. **RBAC**: Ensure appropriate RBAC policies are configured for the namespace.

5. **Image Tags**: Production uses specific version tags (e.g., `v1.0.0`), development uses `dev-latest`.

## Next Steps

1. Update `k8s/base/secret.yaml` with actual secrets (do not commit!)
2. Build and push Docker images with appropriate tags
3. Update `k8s/base/ingress.yaml` with your actual domain
4. Deploy to development environment first
5. Test thoroughly before promoting to production
6. Set up monitoring and alerting (Prometheus, Grafana)
7. Configure backup strategy for PostgreSQL StatefulSet
