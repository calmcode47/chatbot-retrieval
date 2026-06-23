# DocuMind: React Frontend Status Report
## Technical Architecture and Implementation Details — June 23, 2026

This document provides a comprehensive report of the frontend codebase for the DocuMind RAG Q&A platform. The user interface is built as a dark-themed React Single Page Application (SPA) powered by Vite, utilizing Three.js for interactive 3D visualizations.

---

## 1. Core Technology Stack

*   **Framework**: React 18
*   **Build Tool**: Vite 8
*   **3D Rendering**: Three.js (WebGL)
*   **Icons**: Lucide React
*   **Styling**: Custom Vanilla CSS (Design Tokens, Glassmorphism, Responsive Grid Layouts)
*   **Development Server**: Runs on Port 8501 (local development environment)

---

## 2. Design System and Styling Tokens (Nordic Ice Theme)

The UI utilizes a cold, high-contrast dark theme named Nordic Ice. All colors, borders, and shadows are defined in the global stylesheet:

*   **Background**: Pitch-black Slate (`#030712`)
*   **Primary Colors**: Icy Teal/Mint (`#2dd4bf` to `#0d9488`)
*   **Accent Colors**: Frosted Cobalt (`#3b82f6` to `#1d4ed8`)
*   **Card and Panel Bases**: Translucent Slate (`rgba(15, 23, 42, 0.7)`) with a blur filter (`backdrop-filter: blur(12px)`)
*   **Borders**: Frosted silver-indigo (`rgba(99, 102, 241, 0.15)`)
*   **Animations**: Glowing drop shadows for key logos, rotational translations, and floating animations for 3D elements.

---

## 3. Visual Components and Pages

The application is structured into a main container layout with a persistent navigation header and three pages:

### A. Navigation Header (Navbar.jsx)
*   Displays the glowing brain icon logo and the "DocuMind" title.
*   Contains navigation triggers for switching between the Home, Dashboard, and About pages.
*   Features active states highlighted by teal-tinted border outlines and translucent backgrounds.

### B. Live Background (ThreeBackground.jsx)
*   Constructs a perspective grid plane at the base of the viewport using wireframe geometry.
*   Animates grid vertices dynamically using overlapping sine and cosine waves to create a rolling cyber-grid motion.
*   Scatters 100 glowing point particles (data packets) above the floor that drift upwards and recycle upon reaching the viewport ceiling.
*   Listens to mouse movement coordinates to apply smooth parallax shifts on the camera angle.

### C. Home Page (Home.jsx)
*   **Hero Grid**: A double-column section featuring the main tagline, local RAG security badge, and description on the left, and the 3D Dome viewport on the right.
*   **3D Dome Document Gallery**:
    *   *Central Core*: A double-layered sphere (one solid, one wireframe icosahedron) representing the vectorized document index database.
    *   *Dome Sheets*: 18 flat 3D plane meshes representing sheets of paper (PDFs in teal, Markdown in cobalt, TXT in silver) orbiting the core in a hemispherical dome.
    *   *Connection Filaments*: Line segments linking each paper sheet back to the database center.
    *   *Tilt Physics*: Listens to mouse position relative to the viewport to rotate and tilt the dome assembly.
*   **Supported Compilers**: Detailed panels explaining parsing methods for PDF, Markdown, and TXT files.
*   **Pipeline Flowchart**: An educational step-by-step layout explaining the document's path from upload to indexing, reranking, and generation.

### D. Dashboard Page (Dashboard.jsx)
*   **Document Management Sidebar**:
    *   Upload Dropzone: Drag-and-drop region for uploading PDF, TXT, and Markdown files.
    *   Total indexed document count and total chunk metrics boxes.
    *   Document list showing filenames, file sizes, and chunk numbers, with interactive delete buttons.
*   **Chat Viewport**:
    *   Displays conversational turn histories in alternating bubble sides.
    *   Includes citation cards showing the source document name, matching score, and page number for retrieved context.
    *   Floating input bar with status loader states.
    *   Supports dynamic session history loading and page refresh persistence.

---

## 4. Development and Containerized Configuration

### A. Local Execution (Development)
*   The dev server is started via Vite (`npm run dev`).
*   The proxy configurations are defined in `vite.config.js` to route all `/api/v1` calls to the local FastAPI backend (defaulting to port 8000).

### B. Production Containerization (Railway Cloud)
*   **Dockerfile**: Uses a two-stage build.
    1.  *Stage 1 (Builder)*: Installs Node dependencies using `npm ci` and runs `npm run build` to generate the production React bundle in the `/dist` folder.
    2.  *Stage 2 (Nginx)*: Uses a lightweight Nginx-alpine image, copies the built assets, and serves them.
*   **Nginx Configuration (nginx.conf)**: Configures a reverse-proxy for the `/api/v1/` route to redirect calls to the backend API URL.
*   **Dynamic Startup Entrypoint (entrypoint.sh)**: Solves cloud routing by dynamically replacing `PORT_PLACEHOLDER` with the port assigned by Railway at startup and `BACKEND_URL_PLACEHOLDER` with the public API URL:
    ```sh
    sed -i "s|BACKEND_URL_PLACEHOLDER|${BACKEND_URL}|g" /etc/nginx/conf.d/default.conf
    sed -i "s|PORT_PLACEHOLDER|${PORT}|g" /etc/nginx/conf.d/default.conf
    ```

---

## 5. Deployed Production Status

*   **Service URL**: [https://documind-frontend-production-15cf.up.railway.app](https://documind-frontend-production-15cf.up.railway.app)
*   **Status**: Online (Green)
*   **Environment**: Production (Railway cloud container)
