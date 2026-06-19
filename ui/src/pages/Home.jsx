import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { ArrowRight, Shield, Zap, Search, Layers } from "lucide-react";

export default function Home({ setActivePage }) {
  const threeRef = useRef(null);

  useEffect(() => {
    if (!threeRef.current) return;

    // --- Octahedron Setup ---
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 1, 10);
    camera.position.z = 5;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(220, 220);
    renderer.setPixelRatio(window.devicePixelRatio);
    threeRef.current.appendChild(renderer.domElement);

    // Create 3D wireframe octahedron
    const geometry = new THREE.OctahedronGeometry(1.5, 0);
    const wireframe = new THREE.WireframeGeometry(geometry);
    const line = new THREE.LineSegments(wireframe);
    line.material.depthTest = true;
    line.material.opacity = 0.85;
    line.material.transparent = true;
    line.material.color.setHex(0x6784ff); // Royal blue

    scene.add(line);

    // Gentler inner glowing sphere
    const sphereGeom = new THREE.SphereGeometry(0.8, 16, 16);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe, // Cyan
      wireframe: true,
      transparent: true,
      opacity: 0.15,
    });
    const sphere = new THREE.Mesh(sphereGeom, sphereMat);
    scene.add(sphere);

    let animationId;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      line.rotation.y += 0.008;
      line.rotation.x += 0.004;
      sphere.rotation.y -= 0.003;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      if (renderer && renderer.domElement && threeRef.current) {
        threeRef.current.removeChild(renderer.domElement);
      }
      scene.clear();
    };
  }, []);

  const features = [
    {
      icon: Shield,
      title: "100% Private & Local",
      desc: "All ingestion, chunking, and generation runs strictly inside your local container. No third-party API keys or external data transmission required.",
    },
    {
      icon: Zap,
      title: "Apple Silicon GPU Acceleration",
      desc: "Uses MPS acceleration for embedding generation (Sentence Transformers) on the macOS host, offering 10x faster indexing.",
    },
    {
      icon: Search,
      title: "Hybrid Sparse/Dense Retrieval",
      desc: "Combines high-precision BM25 keyword matching with ChromaDB vector search using Reciprocal Rank Fusion (RRF).",
    },
    {
      icon: Layers,
      title: "Cross-Encoder Reranking",
      desc: "Integrates BAAI/bge-reranker-base to score candidate context relevance, drastically improving final response faithfulness.",
    },
  ];

  return (
    <div className="home-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-text-content">
          <h1 className="hero-title">
            The Secure, Private <br />
            <span className="gradient-text">Document Brain</span>
          </h1>
          <p className="hero-subtitle">
            Perform high-accuracy Retrieval-Augmented Generation (RAG) over your PDF, TXT, and MD files fully locally.
          </p>
          <button
            className="cta-button"
            onClick={() => setActivePage("dashboard")}
          >
            <span>Enter Dashboard</span>
            <ArrowRight size={20} />
          </button>
        </div>
        <div className="hero-3d-visual">
          <div ref={threeRef} className="spinning-octahedron" />
          <div className="glow-shadow" />
        </div>
      </section>

      {/* Features Grid */}
      <section className="features-section">
        <h2 className="features-title">Technical Architecture Features</h2>
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
    </div>
  );
}
