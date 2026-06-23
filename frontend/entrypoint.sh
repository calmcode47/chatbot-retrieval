#!/bin/sh
# Inject the backend API URL into the Nginx config at container startup.
# Railway sets BACKEND_URL env var to the backend service's public URL.
# e.g. https://documind-api-production.up.railway.app

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "Starting frontend — backend URL: $BACKEND_URL"

# Replace placeholder in nginx config with the actual backend URL
sed -i "s|BACKEND_URL_PLACEHOLDER|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf

# Start Nginx in foreground
nginx -g "daemon off;"
