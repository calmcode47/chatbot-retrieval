// ui/src/settings.js
// Use a relative path so all API calls go through the Vite dev-server proxy.
// In Docker, the proxy target (set via VITE_API_PROXY_TARGET) routes to the
// backend container by its service name — the browser never needs to know it.
export const API_BASE = "/api/v1";
