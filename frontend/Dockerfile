# Dockerfile — DocuMind React frontend (production build with Nginx)

# Stage 1: Build the React app
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build the production bundle
# API_PROXY_TARGET is only needed at runtime (nginx proxy), not build time
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Add our custom config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built React app
COPY --from=builder /app/dist /usr/share/nginx/html

# Use a startup script so we can template the backend URL at runtime
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8501

CMD ["/entrypoint.sh"]
