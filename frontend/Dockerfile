# Multi-stage build for CivicPulse Frontend
# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production with nginx
FROM nginx:1.25-alpine

# Copy entrypoint script (generates nginx.conf at runtime)
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r$//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Copy built assets from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Create writable directories for non-root nginx
RUN mkdir -p /tmp/client_temp /tmp/proxy_temp_path /tmp/fastcgi_temp \
             /tmp/uwsgi_temp /tmp/scgi_temp /var/cache/nginx \
    && chown -R nginx:nginx /tmp/client_temp /tmp/proxy_temp_path \
       /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp \
       /var/cache/nginx /usr/share/nginx/html /etc/nginx

# Switch to non-root user
USER nginx

# Expose port 8080 (unprivileged port)
EXPOSE 8080

# Health check on unprivileged port
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/nginx-health || exit 1

# Start nginx
ENTRYPOINT ["/docker-entrypoint.sh"]
