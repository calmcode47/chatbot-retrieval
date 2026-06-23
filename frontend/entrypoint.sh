#!/bin/sh
# Inject the backend API URL into the Nginx config at container startup.
# Railway sets BACKEND_URL env var to the backend service's public URL.
# e.g. https://documind-api-production.up.railway.app

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PORT="${PORT:-8501}"

echo "Starting frontend — backend URL: $BACKEND_URL, port: $PORT"

# Replace placeholders in nginx config with the actual values
sed -i "s|BACKEND_URL_PLACEHOLDER|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf
sed -i "s|PORT_PLACEHOLDER|${PORT}|g" /etc/nginx/conf.d/default.conf

# Start Nginx in foreground
nginx -g "daemon off;"
