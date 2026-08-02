# syntax=docker/dockerfile:1
# check=skip=SecretsUsedInArgOrEnv
# ==============================================================================
# Purrfect Spots Frontend - Production Dockerfile
# ==============================================================================
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM node:24.18.0-alpine3.24 AS builder

WORKDIR /build

# The frontend image builds from the repository root so npm can use the
# canonical monorepo lockfile.
COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/package.json

# Install exactly the dependency graph recorded in the root lockfile.
RUN npm ci

# Copy only frontend build inputs.
COPY frontend ./frontend
WORKDIR /build/frontend

# Build arguments for environment variables (non-secret config)
# nosec docker:S6472 - These are public build-time configurations, not secrets
ARG VITE_API_BASE_URL
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_GOOGLE_MAPS_API_KEY
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

# Set environment variables for build (public config only)
# nosec docker:S6472 - ENV values are public API endpoints, not credentials
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY \
    VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Build the application
RUN npm run build

# Stage 2: Production with nginx
FROM nginx:1.28.3-alpine3.23 AS production

LABEL maintainer="Purrfect Spots Team <support@purrfectspots.com>"
LABEL description="Purrfect Spots Frontend - Vue.js application"
LABEL version="3.1.0"

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /build/frontend/dist /usr/share/nginx/html

# Add non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup && \
    chown -R appuser:appgroup /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appgroup /var/run/nginx.pid && \
    chown -R appuser:appgroup /usr/share/nginx/html

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
