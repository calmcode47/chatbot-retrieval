import React, { useState, useEffect } from "react";
import { FileText, Hash, AlignLeft, FileStack, Globe, BookOpen, Database, Search, Layers, Shield, Cpu } from "lucide-react";
import LogicCore from "../components/LogicCore";

const DOC_TYPES = [
  { Icon: FileText, label: ".PDF", type: "PDF Documents", parser: "PyMuPDF (fitz) Parser", description: "Full page text and layout extraction with section preservation." },
  { Icon: Hash, label: ".MD", type: "Markdown Files", parser: "Unstructured MD Compiler", description: "Heading-aware parsing with markdown syntax and frontmatter isolation." },
  { Icon: AlignLeft, label: ".TXT", type: "Plain Text", parser: "UTF-8 Stream Reader", description: "Clean text reader with paragraph detection and formatting cleanup." },
  { Icon: FileStack, label: ".DOCX", type: "Word Documents", parser: "Unstructured Docx Parser", description: "Style-preserving text extraction for standard docx document packages." },
  { Icon: Globe, label: "URL", type: "Web Pages", parser: "WebBaseLoader Scraper", description: "Web scrape with sanitization and HTML boilerplate tag stripping." },
  { Icon: BookOpen, label: "Research", type: "Academic Papers", parser: "PyMuPDF + spaCy NER", description: "Scientific papers with metadata, citations, and entity extraction." },
];

const PIPELINE_STEPS = [
  { id: "ingest", Icon: Database, label: "INGEST", title: "Ingestion Core", description: "Format loaders parse, split, and embed documents into ChromaDB." },
  { id: "retrieve", Icon: Search, label: "RETRIEVE", title: "Hybrid Search", description: "Parallel BM25 and dense retrieval merged using Reciprocal Rank Fusion." },
  { id: "rerank", Icon: Layers, label: "RERANK", title: "Neural Rerank", description: "A Cross-Encoder model scores query-chunk relationships for factual alignment." },
  { id: "ground", Icon: Shield, label: "GROUND", title: "Prompt Grounding", description: "Context is fitted to the window and injected into strict system guidelines." },
  { id: "generate", Icon: Cpu, label: "GENERATE", title: "Local Synthesis", description: "Local model pipeline executes text generation inside Python on CPU/GPU." },
];

export default function Home({ setActivePage }) {
  const [coreHovered, setCoreHovered] = useState(false);

  useEffect(() => {
    // Basic Intersection Observer for Scroll Reveals
    const reveals = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
          }
        });
      },
      { threshold: 0.1 }
    );
    reveals.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="home-container" style={{ padding: 0 }}>
      {/* Section 1 — Hero */}
      <section className="section hero-section" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center' }}>
        <div className="container">
          <div className="hero-grid">
            {/* Left column */}
            <div className="hero-left">
              <p className="eyebrow reveal">// DISPERSED  ·  CONTAINED  ·  SECURE</p>

              <h1 className="display-xl hero-title reveal reveal-delay-1">
                DOCU<span style={{ color: 'var(--violet)' }}>MIND</span>
              </h1>
              <h2 className="display-lg hero-subtitle reveal reveal-delay-2">
                KNOWLEDGE<br />DISPERSED PRECISELY
              </h2>

              <p className="body-lg hero-body reveal reveal-delay-3" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-lg)' }}>
                A fully self-contained RAG system that processes your files and 
                answers questions locally on your CPU/GPU. No external API calls, 
                no cloud storage leakage, absolute data containment.
              </p>

              <div className="hero-chips reveal reveal-delay-4">
                <span className="chip">◉ 100% Self-Contained</span>
                <span className="chip">✦ Zero APIs</span>
                <span className="chip">⬡ Local Inference</span>
              </div>

              <div className="hero-ctas reveal reveal-delay-4">
                <button className="btn-primary" onClick={() => setActivePage('dashboard')}>
                  Enter Dashboard
                </button>
                <button className="btn-ghost" onClick={() => setActivePage('about')}>
                  View Architecture
                </button>
              </div>

              {/* DM Mono build metadata */}
              <p className="mono-sm" style={{ color: 'var(--text-muted)', marginTop: 'var(--sp-xl)' }}>
                v1.8.0  ·  Qwen2.5-0.5B-Instruct  ·  BAAI/bge-base-en-v1.5  ·  ChromaDB
              </p>
            </div>

            {/* Right column — Logic Core */}
            <div
              className="hero-right"
              onMouseEnter={() => setCoreHovered(true)}
              onMouseLeave={() => setCoreHovered(false)}
              style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}
            >
              <LogicCore isHovered={coreHovered} />
            </div>
          </div>
        </div>
      </section>

      {/* Section 2 — Document Gallery */}
      <section className="section" style={{ background: 'linear-gradient(180deg, var(--void) 0%, rgba(124,58,237,0.015) 50%, var(--void) 100%)' }}>
        <div className="container">
          <div style={{ marginBottom: 'var(--sp-2xl)' }}>
            <p className="eyebrow reveal">// Supported Formats</p>
            <h2 className="display-lg reveal reveal-delay-1" style={{ marginTop: 'var(--sp-md)' }}>
              EVERY FORMAT.<br />
              <span style={{ color: 'var(--text-secondary)' }}>FULLY PARSED.</span>
            </h2>
            <p className="body-base reveal reveal-delay-2" style={{ color: 'var(--text-secondary)', maxWidth: 480, marginTop: 'var(--sp-md)' }}>
              DocuMind extracts content from your documents using structure-aware parsers, not raw text dumps.
            </p>
          </div>

          <div className="doc-gallery-grid">
            {DOC_TYPES.map((doc, i) => (
              <div
                key={doc.label}
                className={`prism-card doc-card reveal reveal-delay-${i % 4 + 1}`}
              >
                <div className="doc-card-header">
                  <div className="doc-card-icon" style={{ color: 'var(--violet)' }}>
                    <doc.Icon size={22} />
                  </div>
                  <span className="mono-sm" style={{ color: 'var(--cyan)' }}>
                    {doc.label}
                  </span>
                </div>
                <p className="heading-ui" style={{ marginTop: 'var(--sp-md)', fontSize: '1.1rem' }}>
                  {doc.type}
                </p>
                <p className="body-base" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-sm)', fontSize: '0.875rem' }}>
                  {doc.description}
                </p>
                <p className="mono-sm" style={{ color: 'var(--text-muted)', marginTop: 'var(--sp-lg)' }}>
                  {doc.parser}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 3 — Pipeline */}
      <section className="section pipeline-section">
        <div className="container">
          <p className="eyebrow reveal">// Under the hood</p>
          <h2 className="display-lg reveal reveal-delay-1" style={{ marginTop: 'var(--sp-md)', marginBottom: 'var(--sp-2xl)' }}>
            THE PIPELINE
          </h2>

          <div className="pipeline-track">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={step.id} className={`pipeline-step reveal reveal-delay-${i + 1}`}>
                {/* Step number */}
                <div className="pipeline-num">
                  <span className="mono-sm" style={{ color: 'var(--violet-soft)' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                </div>

                {/* Connector line (not after last item) */}
                {i < PIPELINE_STEPS.length - 1 && (
                  <div className="pipeline-connector" style={{ background: 'var(--border-violet)' }} />
                )}

                {/* Card */}
                <div className="prism-card pipeline-card">
                  <div className="doc-card-icon" style={{ marginBottom: 'var(--sp-md)', color: 'var(--violet)' }}>
                    <step.Icon size={20} />
                  </div>
                  <p className="mono-sm" style={{ color: 'var(--cyan)' }}>{step.label}</p>
                  <p className="heading-ui" style={{ marginTop: 'var(--sp-xs)', fontSize: '1rem' }}>
                    {step.title}
                  </p>
                  <p className="body-base" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-sm)', fontSize: '0.85rem' }}>
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 4 — Metrics */}
      <section className="section" style={{ paddingTop: 'var(--sp-2xl)', paddingBottom: 'var(--sp-2xl)' }}>
        <div className="container">
          <div className="divider" style={{ marginBottom: 'var(--sp-2xl)' }} />
          <div className="metrics-grid">
            {[
              { value: '0',           unit: 'External APIs',     label: 'All inference runs on-device.' },
              { value: '100%',        unit: 'Local Processing',  label: 'No data leaves your machine.' },
              { value: 'CPU/GPU',     unit: 'Hardware Fallback', label: 'Runs locally on CPU/CUDA/MPS.' },
              { value: 'PRISM',       unit: 'Dispersed RAG',     label: 'Isolated search & context extraction.' },
            ].map((m, i) => (
              <div key={i} className={`prism-card metrics-card reveal reveal-delay-${i + 1}`}>
                <p className="display-md" style={{ color: 'var(--violet)' }}>{m.value}</p>
                <p className="mono-base"  style={{ marginTop: 'var(--sp-xs)', color: 'var(--text-primary)' }}>{m.unit}</p>
                <p className="mono-sm"   style={{ marginTop: 'var(--sp-sm)', color: 'var(--text-muted)' }}>{m.label}</p>
              </div>
            ))}
          </div>
          <div className="divider" style={{ marginTop: 'var(--sp-2xl)' }} />
        </div>
      </section>

      {/* Section 5 — CTA */}
      <section className="section" style={{ textAlign: 'center', minHeight: '40vh', display: 'flex', alignItems: 'center' }}>
        <div className="container">
          <p className="eyebrow reveal">// Ready to use</p>
          <h2 className="display-lg reveal reveal-delay-1" style={{ marginTop: 'var(--sp-md)', marginBottom: 'var(--sp-lg)' }}>
            UPLOAD. ASK. GET ANSWERS.
          </h2>
          <p className="body-lg reveal reveal-delay-2" style={{ color: 'var(--text-secondary)', maxWidth: 520, margin: '0 auto var(--sp-xl)' }}>
            Drop in your documents and start asking questions. No setup beyond what you've already built.
          </p>
          <div className="reveal reveal-delay-3" style={{ display: 'flex', gap: 'var(--sp-md)', justifyContent: 'center' }}>
            <button className="btn-primary" onClick={() => setActivePage('dashboard')}>
              Open Dashboard
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
