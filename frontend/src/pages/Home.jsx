import React, { useEffect, useRef } from "react";
import { ArrowRight, Shield, Zap, Search, Layers, Database, Lock, Cpu } from "lucide-react";
import * as THREE from "three";

export default function Home({ setActivePage }) {
  const threeRef = useRef(null);

  useEffect(() => {
    if (!threeRef.current) return;

    // --- Vector Space Wave Setup ---
    const scene = new THREE.Scene();
    
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 20);
    camera.position.set(0, 2.2, 4.2);
    camera.lookAt(0, -0.2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(400, 400);
    renderer.setPixelRatio(window.devicePixelRatio);
    threeRef.current.appendChild(renderer.domElement);

    // Grid Dimensions
    const numX = 26;
    const numZ = 26;
    const gap = 0.16;
    const particleCount = numX * numZ;

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let x = 0; x < numX; x++) {
      for (let z = 0; z < numZ; z++) {
        const i = x * numZ + z;
        positions[i * 3] = (x - numX / 2) * gap;
        positions[i * 3 + 1] = 0;
        positions[i * 3 + 2] = (z - numZ / 2) * gap;
      }
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    // Custom circle glowing particle texture
    const canvas = document.createElement("canvas");
    canvas.width = 16;
    canvas.height = 16;
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
    gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
    gradient.addColorStop(0.2, "rgba(99, 102, 241, 0.8)"); // Indigo
    gradient.addColorStop(0.6, "rgba(139, 92, 246, 0.2)"); // Violet
    gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 16, 16);
    const texture = new THREE.CanvasTexture(canvas);

    const material = new THREE.PointsMaterial({
      size: 0.15,
      map: texture,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      transparent: true,
      opacity: 0.85,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // --- Interactive Mouse Coordinates mapping ---
    let targetMouseX = 100; 
    let targetMouseZ = 100;
    let currentMouseX = 100;
    let currentMouseZ = 100;

    const handleMouseMove = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      targetMouseX = x * 2.2;
      targetMouseZ = -y * 2.2;
    };

    const handleMouseLeave = () => {
      targetMouseX = 100;
      targetMouseZ = 100;
    };

    renderer.domElement.addEventListener("mousemove", handleMouseMove);
    renderer.domElement.addEventListener("mouseleave", handleMouseLeave);

    // --- Animation Loop ---
    let animationId;
    const clock = new THREE.Clock();

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime() * 1.4;

      const positionsAttr = points.geometry.attributes.position;
      const array = positionsAttr.array;

      // Smooth mouse coordinates interpolation
      currentMouseX += (targetMouseX - currentMouseX) * 0.08;
      currentMouseZ += (targetMouseZ - currentMouseZ) * 0.08;

      for (let x = 0; x < numX; x++) {
        for (let z = 0; z < numZ; z++) {
          const i = x * numZ + z;
          const posX = (x - numX / 2) * gap;
          const posZ = (z - numZ / 2) * gap;

          // Compute mathematical wave equation
          let y = Math.sin(posX * 1.5 + time) * 0.15 + 
                  Math.cos(posZ * 1.5 + time * 0.7) * 0.1;

          // Compute distance to pointer to create a ripple/indentation effect
          const dx = posX - currentMouseX;
          const dz = posZ - currentMouseZ;
          const dist = Math.sqrt(dx * dx + dz * dz);
          if (dist < 1.2) {
            const pullForce = (1.2 - dist) * 0.28;
            y -= pullForce; // indentation
          }

          array[i * 3 + 1] = y;
        }
      }

      positionsAttr.needsUpdate = true;

      // Rotate points grid slightly over time
      points.rotation.y = time * 0.04;

      renderer.render(scene, camera);
    };

    animate();

    // --- Cleanup ---
    return () => {
      cancelAnimationFrame(animationId);
      if (renderer && renderer.domElement) {
        renderer.domElement.removeEventListener("mousemove", handleMouseMove);
        renderer.domElement.removeEventListener("mouseleave", handleMouseLeave);
        if (threeRef.current) {
          threeRef.current.removeChild(renderer.domElement);
        }
      }
      scene.clear();
    };
  }, []);

  const features = [
    {
      icon: Lock,
      title: "Isolated Security",
      desc: "Documents are processed locally in your container environment, avoiding third-party servers and cloud API leaks.",
    },
    {
      icon: Cpu,
      title: "Metal & CUDA Acceleration",
      desc: "Automatically routes embedding generation pipelines to host-native hardware acceleration (MPS/CPU).",
    },
    {
      icon: Search,
      title: "Hybrid Match Index",
      desc: "Balances semantic vectors and sparse text index channels using Reciprocal Rank Fusion.",
    },
    {
      icon: Layers,
      title: "Attention-Based Rerank",
      desc: "Refines candidates through a local Cross-Encoder transformer before drafting context prompts.",
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
            Enterprise Q&A <br />
            <span className="gradient-text">Fully Encrypted</span>
          </h1>
          <p className="hero-subtitle">
            An isolated Retrieval-Augmented Generation workspace for indexing and exploring private PDF, TXT, and Markdown files locally.
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

      {/* Highlights Grid */}
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

      {/* Process Architecture Flow */}
      <section className="flow-section glass-panel">
        <h2 className="flow-title">Pipeline Architecture</h2>
        <div className="flow-steps">
          <div className="flow-step">
            <div className="step-num">1</div>
            <h4>Ingest</h4>
            <p>Documents are split into hierarchical parent-child context structures.</p>
          </div>
          <div className="flow-arrow">➔</div>
          <div className="flow-step">
            <div className="step-num">2</div>
            <h4>Index</h4>
            <p>Parallel processing creates ChromaDB vectors and BM25 sparse indices.</p>
          </div>
          <div className="flow-arrow">➔</div>
          <div className="flow-step">
            <div className="step-num">3</div>
            <h4>Rerank</h4>
            <p>RRF and Cross-Encoder layers filter candidate chunks to extract top matches.</p>
          </div>
          <div className="flow-arrow">➔</div>
          <div className="flow-step">
            <div className="step-num">4</div>
            <h4>Compose</h4>
            <p>Ollama runs LLM inference locally on the host machine to synthesize answers.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
