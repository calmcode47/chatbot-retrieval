import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { ArrowRight, Shield, Zap, Search, Layers, Database, Lock, Cpu } from "lucide-react";

export default function Home({ setActivePage }) {
  const threeRef = useRef(null);

  useEffect(() => {
    if (!threeRef.current) return;

    // --- Knowledge Globe Scene Setup ---
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 20);
    camera.position.z = 6;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(380, 380);
    renderer.setPixelRatio(window.devicePixelRatio);
    threeRef.current.appendChild(renderer.domElement);

    // Master Group for tilt effect
    const masterGroup = new THREE.Group();
    scene.add(masterGroup);

    // --- 1. Glowing Central Core ---
    const coreGroup = new THREE.Group();
    masterGroup.add(coreGroup);

    // Core solid sphere
    const coreSphereGeom = new THREE.SphereGeometry(0.7, 32, 32);
    const coreSphereMat = new THREE.MeshBasicMaterial({
      color: 0x6784ff, // Royal Blue
      transparent: true,
      opacity: 0.1,
    });
    const coreSphere = new THREE.Mesh(coreSphereGeom, coreSphereMat);
    coreGroup.add(coreSphere);

    // Core wireframe sphere for technical grid feel
    const coreWireGeom = new THREE.SphereGeometry(0.72, 16, 16);
    const coreWireMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe, // Cyan
      wireframe: true,
      transparent: true,
      opacity: 0.25,
    });
    const coreWire = new THREE.Mesh(coreWireGeom, coreWireMat);
    coreGroup.add(coreWire);

    // --- 2. Orbital Process Rings ---
    // Ring 1 (Dense Vector Retrieval - Royal Blue)
    const ring1Geom = new THREE.RingGeometry(1.1, 1.13, 64);
    const ring1Mat = new THREE.MeshBasicMaterial({
      color: 0x6784ff,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5,
    });
    const ring1 = new THREE.Mesh(ring1Geom, ring1Mat);
    ring1.rotation.x = Math.PI / 2.5;
    masterGroup.add(ring1);

    // Ring 2 (Sparse Keyword Search - Cyan)
    const ring2Geom = new THREE.RingGeometry(1.3, 1.32, 64);
    const ring2Mat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.4,
    });
    const ring2 = new THREE.Mesh(ring2Geom, ring2Mat);
    ring2.rotation.x = -Math.PI / 3;
    ring2.rotation.y = Math.PI / 6;
    masterGroup.add(ring2);

    // Ring 3 (Cross-Encoder Rerank - Purple)
    const ring3Geom = new THREE.RingGeometry(1.5, 1.51, 64);
    const ring3Mat = new THREE.MeshBasicMaterial({
      color: 0xa855f7, // Purple
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.3,
    });
    const ring3 = new THREE.Mesh(ring3Geom, ring3Mat);
    ring3.rotation.y = Math.PI / 4;
    masterGroup.add(ring3);

    // --- 3. Constellation Node Cloud & Connection Filaments ---
    const nodeGroup = new THREE.Group();
    masterGroup.add(nodeGroup);

    const nodeCount = 16;
    const nodeMeshes = [];
    const lineMaterials = [];

    for (let i = 0; i < nodeCount; i++) {
      // Position nodes in a shell around the core
      const phi = Math.acos(-1 + (2 * i) / nodeCount);
      const theta = Math.sqrt(nodeCount * Math.PI) * phi;
      const radius = 1.2 + Math.random() * 0.4;

      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);

      // Node mesh
      const nodeGeom = new THREE.SphereGeometry(0.04, 8, 8);
      const nodeMat = new THREE.MeshBasicMaterial({
        color: i % 2 === 0 ? 0x00f2fe : 0x6784ff,
        transparent: true,
        opacity: 0.8,
      });
      const node = new THREE.Mesh(nodeGeom, nodeMat);
      node.position.set(x, y, z);
      nodeGroup.add(node);
      nodeMeshes.push(node);

      // Filament line linking node to core center
      const points = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(x, y, z)];
      const lineGeom = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({
        color: 0x6784ff,
        transparent: true,
        opacity: 0.15,
      });
      const line = new THREE.Line(lineGeom, lineMat);
      nodeGroup.add(line);
      lineMaterials.push(lineMat);
    }

    // --- 4. Interactive Mouse Tilting ---
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const handleMouseMove = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const clientX = event.clientX - rect.left;
      const clientY = event.clientY - rect.top;
      
      // Calculate relative position to container center
      targetX = (clientX - rect.width / 2) * 0.0025;
      targetY = (clientY - rect.height / 2) * 0.0025;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // --- Animation Loop ---
    let animationId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Slow orbital rotations
      coreGroup.rotation.y += 0.004;
      coreGroup.rotation.x += 0.002;

      ring1.rotation.z -= 0.006;
      ring2.rotation.z += 0.005;
      ring3.rotation.z -= 0.003;

      nodeGroup.rotation.y += 0.003;
      nodeGroup.rotation.x += 0.001;

      // Pulsing node opacity
      nodeMeshes.forEach((mesh, index) => {
        mesh.material.opacity = 0.5 + Math.sin(time * 2 + index) * 0.3;
      });

      // Smooth mouse tracking interpolation
      currentX += (targetX - currentX) * 0.05;
      currentY += (targetY - currentY) * 0.05;

      masterGroup.rotation.y = currentX;
      masterGroup.rotation.x = currentY;

      // Gentle floating animation
      masterGroup.position.y = Math.sin(time) * 0.08;

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
      title: "Private Ingestion",
      desc: "Documents stay fully localized inside your local container workspace with zero external API key requirements.",
    },
    {
      icon: Cpu,
      title: "Hardware Accelerated",
      desc: "Leverages local Apple Silicon GPU (MPS) acceleration to generate high-performance embeddings locally.",
    },
    {
      icon: Search,
      title: "Hybrid Search Core",
      desc: "Combines dense vector search (ChromaDB) and sparse keyword indices (BM25) using Reciprocal Rank Fusion (RRF).",
    },
    {
      icon: Layers,
      title: "Cross-Encoder Rerank",
      desc: "Utilizes deep cross-attention reranking (BAAI/bge-reranker-base) to prioritize high-fidelity context passages.",
    },
  ];

  return (
    <div className="home-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-text-content">
          <div className="hero-badge">
            <Shield size={14} className="badge-icon" />
            <span>Secure Local RAG System</span>
          </div>
          <h1 className="hero-title">
            The Private Intelligence <br />
            <span className="gradient-text">For Your Documents</span>
          </h1>
          <p className="hero-subtitle">
            Perform enterprise-grade Retrieval-Augmented Generation (RAG) over PDF, TXT, and MD datasets. All computations run 100% locally.
          </p>
          <div className="hero-actions">
            <button
              className="cta-button"
              onClick={() => setActivePage("dashboard")}
            >
              <span>Enter Workspace</span>
              <ArrowRight size={20} />
            </button>
          </div>
        </div>
        <div className="hero-3d-visual">
          <div ref={threeRef} className="spinning-octahedron" />
          <div className="glow-shadow" />
        </div>
      </section>

      {/* Tech Architecture Overview Cards */}
      <section className="features-section">
        <h2 className="features-title">Technical Architecture Highlights</h2>
        <p className="features-subtitle">
          Engineered for privacy, speed, and high-fidelity factual context matching.
        </p>
        <div className="features-grid">
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div key={idx} className="feature-card glass-panel">
                <div className="feature-icon-wrapper">
                  <Icon size={24} className="feature-icon" />
                </div>
                <h3 className="feature-card-title">{feat.title}</h3>
                <p className="feature-card-desc">{feat.desc}</p>
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
            <p>Ollama runs LLM inference on the host machine to compose precise answers.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
