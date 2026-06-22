import React, { useEffect, useRef } from "react";
import { ArrowRight, Shield, Zap, Search, Layers, Database, Lock, Cpu, FileText, Code, CheckCircle } from "lucide-react";
import * as THREE from "three";

export default function Home({ setActivePage }) {
  const threeRef = useRef(null);

  useEffect(() => {
    if (!threeRef.current) return;

    // --- 3D Dome Document Gallery Setup ---
    const scene = new THREE.Scene();
    
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 20);
    camera.position.set(0, 1.8, 4.0);
    camera.lookAt(0, 0.2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(400, 400);
    renderer.setPixelRatio(window.devicePixelRatio);
    threeRef.current.appendChild(renderer.domElement);

    // Master Group
    const masterGroup = new THREE.Group();
    scene.add(masterGroup);

    // --- 1. Glowing Database Core ---
    const coreGroup = new THREE.Group();
    masterGroup.add(coreGroup);

    // Solid core
    const coreSphereGeom = new THREE.SphereGeometry(0.5, 32, 32);
    const coreSphereMat = new THREE.MeshBasicMaterial({
      color: 0x3b82f6, // Cobalt Blue
      transparent: true,
      opacity: 0.15,
    });
    const coreSphere = new THREE.Mesh(coreSphereGeom, coreSphereMat);
    coreGroup.add(coreSphere);

    // Wireframe core
    const coreWireGeom = new THREE.IcosahedronGeometry(0.52, 2);
    const coreWireMat = new THREE.MeshBasicMaterial({
      color: 0x2dd4bf, // Teal/Mint
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const coreWire = new THREE.Mesh(coreWireGeom, coreWireMat);
    coreGroup.add(coreWire);

    // --- 2. Dome Document Sheets Gallery ---
    const domeGroup = new THREE.Group();
    masterGroup.add(domeGroup);

    const docCount = 18;
    const documentMeshes = [];
    const filamentLines = [];

    // Position meshes in a hemisphere (dome)
    for (let i = 0; i < docCount; i++) {
      // Golden ratio placement on a hemisphere
      const phi = Math.acos((i / docCount) * 0.9); // 0 to ~Math.PI/2 (dome shape)
      const theta = Math.sqrt(docCount * Math.PI) * phi;
      const radius = 1.3;

      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);

      // Create a 3D Plane representing a document paper sheet
      const sheetGeom = new THREE.PlaneGeometry(0.18, 0.24);
      
      // Alternate document colors: PDF (Teal), Markdown (Cobalt), TXT (Silver)
      let sheetColor = 0x2dd4bf; // Teal
      if (i % 3 === 1) sheetColor = 0x3b82f6; // Cobalt Blue
      if (i % 3 === 2) sheetColor = 0x94a3b8; // Silver

      const sheetMat = new THREE.MeshBasicMaterial({
        color: sheetColor,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.6,
      });

      const sheet = new THREE.Mesh(sheetGeom, sheetMat);
      sheet.position.set(x, y, z);
      
      // Force sheets to face the central database core
      sheet.lookAt(0, 0, 0);
      sheet.rotateX(Math.PI / 2); // Orient flat-face outwards
      
      domeGroup.add(sheet);
      documentMeshes.push(sheet);

      // Connect each sheet back to the database center with line filaments
      const points = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(x, y, z)];
      const lineGeom = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({
        color: sheetColor,
        transparent: true,
        opacity: 0.15,
      });
      const line = new THREE.Line(lineGeom, lineMat);
      domeGroup.add(line);
      filamentLines.push(lineMat);
    }

    // --- 3. Mouse Tilt Interaction ---
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const handleMouseMove = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const clientX = event.clientX - rect.left;
      const clientY = event.clientY - rect.top;

      targetX = (clientX - rect.width / 2) * 0.0022;
      targetY = (clientY - rect.height / 2) * 0.0022;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // --- Animation Loop ---
    let animationId;
    const clock = new THREE.Clock();

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Spin the database core
      coreGroup.rotation.y += 0.006;
      coreGroup.rotation.x += 0.003;

      // Orbit the dome gallery of documents
      domeGroup.rotation.y = time * 0.05;

      // Pulsing effect for the documents
      documentMeshes.forEach((mesh, index) => {
        mesh.material.opacity = 0.45 + Math.sin(time * 2.5 + index) * 0.2;
      });

      // Smooth tracking interpolation
      currentX += (targetX - currentX) * 0.06;
      currentY += (targetY - currentY) * 0.06;

      masterGroup.rotation.y = currentX;
      masterGroup.rotation.x = currentY;

      // Gentle hover floating
      masterGroup.position.y = Math.sin(time * 0.8) * 0.06;

      renderer.render(scene, camera);
    };

    animate();

    // --- Cleanup ---
    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("mousemove", handleMouseMove);
      if (renderer && renderer.domElement && threeRef.current) {
        threeRef.current.removeChild(renderer.domElement);
      }
      scene.clear();
    };
  }, []);

  const features = [
    {
      icon: Lock,
      title: "100% Local Ingestion",
      desc: "All indexing, token parsing, and vector calculations run strictly inside your local Docker workspace.",
    },
    {
      icon: Cpu,
      title: "Host GPU Routing",
      desc: "Leverages the host's Apple Silicon GPU (MPS) to speed up Sentence-Transformer embedding computations.",
    },
    {
      icon: Search,
      title: "Hybrid Sparse/Dense Core",
      desc: "Integrates ChromaDB dense embeddings and BM25 sparse indexes with Reciprocal Rank Fusion.",
    },
    {
      icon: Layers,
      title: "Attention-Based Rerank",
      desc: "Scores retrieved passages with a Cross-Encoder transformer to prevent LLM hallucinations.",
    },
  ];

  const docTypes = [
    {
      icon: FileText,
      type: "PDF Files",
      parsing: "PyMuPDF (fitz) Extractor",
      strategy: "Extracts textual contents, structures raw table grids, and parses semantic layout hierarchies.",
    },
    {
      icon: Code,
      type: "Markdown Docs",
      parsing: "Unstructured MD Parser",
      strategy: "Identifies heading hierarchies, isolates bullet listings, and maintains code-snippet block formatting.",
    },
    {
      icon: FileText,
      type: "Plain Text (TXT)",
      parsing: "UTF-8 Stream Reader",
      strategy: "Processes raw log outputs, configuration sheets, and plain textual descriptions line-by-line.",
    },
  ];

  return (
    <div className="home-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-text-content">
          <div className="hero-badge">
            <Shield size={13} className="badge-icon" />
            <span>Local RAG Pipeline</span>
          </div>
          <h1 className="hero-title">
            Frictionless Q&A <br />
            <span className="gradient-text">Fully Encrypted</span>
          </h1>
          <p className="hero-subtitle">
            An isolated Retrieval-Augmented Generation workspace for indexing and exploring PDF, TXT, and Markdown files locally.
          </p>
          <div className="hero-actions">
            <button
              className="cta-button"
              onClick={() => setActivePage("dashboard")}
            >
              <span>Enter Workspace</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
        <div className="hero-3d-visual">
          <div ref={threeRef} className="spinning-octahedron" />
          <div className="glow-shadow" />
        </div>
      </section>

      {/* RAG Deep Dive & Architecture Section */}
      <section className="features-section">
        <h2 className="features-title">Technical Highlights</h2>
        <p className="features-subtitle">
          Constructed with a privacy-centric pipeline for rapid factual document retrieval.
        </p>
        <div className="features-grid">
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div key={idx} className="feature-card glass-panel">
                <div className="feature-icon-wrapper">
                  <Icon size={22} className="feature-icon" />
                </div>
                <h3 className="feature-card-title">{feat.title}</h3>
                <p className="feature-card-desc">{feat.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Expanded Document Gallery Section */}
      <section className="document-types-section">
        <h2 className="features-title">Supported Document Compilers</h2>
        <p className="features-subtitle">
          Custom ingestion engines process and map unique layouts into vectorized chunks.
        </p>
        <div className="doc-types-grid">
          {docTypes.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="doc-type-card glass-panel">
                <div className="doc-type-header">
                  <div className="doc-type-icon-box">
                    <Icon size={20} className="doc-type-icon" />
                  </div>
                  <div>
                    <h4>{item.type}</h4>
                    <span className="doc-compiler-label">{item.parsing}</span>
                  </div>
                </div>
                <p className="doc-type-desc">{item.strategy}</p>
                <div className="doc-status-checklist">
                  <div className="status-item">
                    <CheckCircle size={14} className="status-check-icon" />
                    <span>Parent-Child Chunking</span>
                  </div>
                  <div className="status-item">
                    <CheckCircle size={14} className="status-check-icon" />
                    <span>Metadata Registration</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* RAG Processing Visual Flow */}
      <section className="flow-section glass-panel">
        <h2 className="flow-title">Pipeline Architecture</h2>
        <div className="flow-steps">
          <div className="flow-step">
            <div className="step-num">1</div>
            <h4>Ingestion & Chunking</h4>
            <p>Documents are split into hierarchical parent-child context structures.</p>
          </div>
          <div className="flow-arrow">➔</div>
          <div className="flow-step">
            <div className="step-num">2</div>
            <h4>Hybrid Indexing</h4>
            <p>Parallel processing creates ChromaDB vectors and BM25 sparse indices.</p>
          </div>
          <div className="flow-arrow">➔</div>
          <div className="flow-step">
            <div className="step-num">3</div>
            <h4>Rerank & Fusion</h4>
            <p>Reciprocal Rank Fusion and Cross-Encoders filter the highest relevance passages.</p>
          </div>
          <div className="flow-arrow">➔</div>
          <div className="flow-step">
            <div className="step-num">4</div>
            <h4>Local LLM Generation</h4>
            <p>Ollama runs LLM inference locally on the host machine to compose precise answers.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
