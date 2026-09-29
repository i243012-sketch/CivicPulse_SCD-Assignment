# CivicPulse Operations Runbook

## Quick Reference

### Deploy to Production
```bash
# Deploy using kustomize
kubectl apply -k k8s/overlays/prod

# Watch rollout
kubectl rollout status deployment/prod-backend -n civicpulse-prod
kubectl rollout status deployment/prod-frontend -n civicpulse-prod
```

### Check Health
```bash
# All pods
kubectl get pods -n civicpulse-prod

# Backend health
kubectl exec -n civicpulse-prod deploy/prod-backend -- curl http://localhost:8000/api/meta/health

# Frontend health
curl http://<frontend-loadbalancer-ip>/nginx-health
```

### View Logs
```bash
# Backend logs
kubectl logs -n civicpulse-prod -l app=backend --tail=100

# Frontend logs
kubectl logs -n civicpulse-prod -l app=frontend --tail=100

# Database logs
kubectl logs -n civicpulse-prod -l app=postgres --tail=100

# Follow logs
kubectl logs -n civicpulse-prod -l app=backend -f
```

### Rollback Deployment
```bash
# Check rollout history
kubectl rollout history deployment/prod-backend -n civicpulse-prod

# Rollback to previous version
kubectl rollout undo deployment/prod-backend -n civicpulse-prod

# Rollback to specific revision
kubectl rollout undo deployment/prod-backend --to-revision=3 -n civicpulse-prod
```

### Scale Services
```bash
# Manual scaling (HPA will override)
kubectl scale deployment/prod-backend --replicas=5 -n civicpulse-prod

# Check HPA status
kubectl get hpa -n civicpulse-prod
kubectl describe hpa prod-backend-hpa -n civicpulse-prod
```

### Database Operations
```bash
# Connect to database
kubectl exec -it -n civicpulse-prod statefulset/prod-postgres -- psql -U postgres -d civicpulse

# Run migrations manually
kubectl exec -n civicpulse-prod deploy/prod-backend -- alembic upgrade head

# Backup database
kubectl exec -n civicpulse-prod statefulset/prod-postgres -- pg_dump -U postgres civicpulse > backup.sql
```

### Redis Operations
```bash
# Connect to Redis
kubectl exec -it -n civicpulse-prod deploy/prod-redis -- redis-cli

# Clear cache
kubectl exec -n civicpulse-prod deploy/prod-redis -- redis-cli FLUSHDB

# Check cache keys
kubectl exec -n civicpulse-prod deploy/prod-redis -- redis-cli KEYS '*'
```

### Troubleshooting

#### Backend Pod CrashLooping
```bash
# Check logs
kubectl logs -n civicpulse-prod -l app=backend --previous

# Check init container logs
kubectl logs -n civicpulse-prod <pod-name> -c run-migrations
kubectl logs -n civicpulse-prod <pod-name> -c wait-for-db

# Common causes:
# 1. Database not ready → check postgres pod
# 2. Migration failed → check alembic version
# 3. Missing env var → check configmap/secrets
```

#### High Response Times
```bash
# Check HPA
kubectl get hpa -n civicpulse-prod

# Check pod resources
kubectl top pods -n civicpulse-prod

# Check database connections
kubectl exec -n civicpulse-prod statefulset/prod-postgres -- psql -U postgres -d civicpulse -c "SELECT count(*) FROM pg_stat_activity;"

# Clear Redis cache (if stale)
kubectl exec -n civicpulse-prod deploy/prod-redis -- redis-cli FLUSHDB
```

#### Database Connection Issues
```bash
# Check postgres pod
kubectl get pod -n civicpulse-prod -l app=postgres

# Check postgres logs
kubectl logs -n civicpulse-prod -l app=postgres

# Test connectivity from backend
kubectl exec -n civicpulse-prod deploy/prod-backend -- nc -zv prod-postgres 5432
```

### Monitoring
```bash
# Prometheus metrics
curl http://<backend-ip>:8000/api/metrics

# Watch HPA scaling
kubectl get hpa -n civicpulse-prod -w

# Watch pod count
watch kubectl get pods -n civicpulse-prod
```

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Backend 503 | Database not ready | Check postgres pod, wait for readiness |
| High latency | Low resources | Check HPA scaling, adjust limits |
| Cache stale | Long TTL | Flush Redis or wait 60s |
| Migration failed | Schema conflict | Check alembic logs, fix manually |
