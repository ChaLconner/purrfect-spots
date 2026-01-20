# ==============================================================================
# Purrfect Spots Frontend - Production Dockerfile
# ==============================================================================
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM node:25-alpine as builder

WORKDIR /build

# Copy package files first for caching
COPY package*.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_BASE_URL
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_GOOGLE_MAPS_API_KEY

# Set environment variables for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY

# Build the application
RUN npm run build

# Stage 2: Production with nginx
FROM nginx:alpine as production

LABEL maintainer="Purrfect Spots Team <support@purrfectspots.com>"
LABEL description="Purrfect Spots Frontend - Vue.js application"
LABEL version="1.0.0"

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

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
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
