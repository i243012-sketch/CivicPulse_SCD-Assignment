# ADR-0002: Frontend Runtime Configuration via Environment Variables

## Status
Accepted

## Context

The frontend React application needs to communicate with the backend API. The backend URL varies across environments:
- Local development: `http://localhost:8000`
- Docker Compose: `http://backend:8000` (internal service name)
- Kubernetes: `http://prod-backend:8000` (k8s service name)
- Production: Custom domain or LoadBalancer IP

Traditional approaches have significant drawbacks:

1. **Build-time configuration**: Requires separate builds for each environment (dev, staging, prod), increasing CI/CD complexity and deployment time.

2. **Hardcoded values**: Makes the container image environment-specific and not portable.

3. **ConfigMap mounting**: Requires Kubernetes-specific configuration and doesn't work in Docker Compose or bare-metal deployments.

The frontend is served by nginx, and the React application runs entirely in the browser. This means we cannot use traditional server-side environment variables after the container starts.

## Decision

We inject backend configuration at **container startup time** using a shell script (`docker-entrypoint.sh`) that:

1. Reads environment variables (`BACKEND_HOST`, `BACKEND_PORT`)
2. Generates an nginx configuration file (`/etc/nginx/nginx.conf`) with environment-specific values
3. Generates a JavaScript configuration file (`/usr/share/nginx/html/config.js`) that the React app can import
4. Starts nginx to serve the application

This approach provides:
- **Single container image** that works across all environments
- **Runtime flexibility** - same image for dev, staging, prod
- **No rebuild required** when backend URLs change
- **Works everywhere** - Docker Compose, Kubernetes, bare metal, cloud

### Implementation Details

**File**: `frontend/docker-entrypoint.sh`, lines 1-95

Key sections:
```bash
# Read environment variables with defaults
BACKEND_HOST=${BACKEND_HOST:-backend}
BACKEND_PORT=${BACKEND_PORT:-8000}

# Generate nginx.conf with proxy_pass to backend
cat > /etc/nginx/nginx.conf <<EOF
location /api {
    proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT};
}
EOF

# Generate config.js for React app
cat > /usr/share/nginx/html/config.js <<EOF
window.APP_CONFIG = {
    API_BASE_URL: '/api'
};
EOF
```

**File**: `frontend/src/api/client.ts`, lines 3-5
```typescript
// Import runtime config
const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || '/api';
```

## Consequences

### Positive

✅ **Portability**: Single Docker image works in any environment  
✅ **Simplicity**: No build-time configuration or multiple Dockerfiles  
✅ **Security**: Backend URL not exposed in JavaScript bundle  
✅ **Flexibility**: Change backend URL with environment variables only  
✅ **Performance**: nginx handles reverse proxy efficiently  
✅ **CORS avoided**: Same-origin requests via nginx proxy  

### Negative

❌ **Container startup dependency**: nginx.conf generated at runtime  
❌ **Debugging complexity**: Config not visible in image layers  
❌ **Shell script required**: Entrypoint script adds maintenance overhead  

### Mitigations

- Comprehensive comments in `docker-entrypoint.sh` for maintainability
- Default values prevent startup failures if env vars missing
- Startup logs show generated configuration for debugging
- `set -e` ensures script fails fast on errors

### Trade-offs Considered

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Build-time config** | Simple, static | Multiple builds, not portable | ❌ Rejected |
| **Runtime injection (chosen)** | Portable, flexible | Startup complexity | ✅ Accepted |
| **ConfigMap mounting** | Kubernetes-native | Vendor lock-in, doesn't work in Compose | ❌ Rejected |
| **Service mesh** | Advanced features | Overcomplicated for our needs | ❌ Rejected |

## References

- **Implementation**: `frontend/docker-entrypoint.sh`, lines 1-95
- **Nginx config generation**: `frontend/docker-entrypoint.sh`, lines 44-82
- **React config consumption**: `frontend/src/api/client.ts`, lines 3-5
- **Dockerfile entrypoint**: `frontend/Dockerfile`, line 29
- **Kubernetes deployment**: `k8s/base/frontend-deployment.yaml`, lines 20-23 (env vars)
- **Compose configuration**: `compose.yaml`, lines 88-91 (env vars)

## Related Decisions

- **ADR-0001**: Triage provider abstraction (similar pattern for backend flexibility)
- **ADR-0003**: Redis caching strategy (also uses runtime environment variables)

## Revision History

- 2024-09-28: Initial decision documented
