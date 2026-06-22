import React, { useEffect } from "react";

const ARCH_LAYERS = [
  { title: 'Ingestion Layer',   tag: 'PyMuPDF · LangChain',       description: 'Documents are loaded by format-specific parsers, split into parent/child chunk hierarchies, embedded with BGE, and stored with HNSW indexing in ChromaDB.' },
  { title: 'Retrieval Layer',   tag: 'BM25 + Dense + RRF',         description: 'Hybrid sparse+dense retrieval with Reciprocal Rank Fusion merges keyword and semantic signals. Child chunks are retrieved; parent context is returned to the LLM.' },
  { title: 'Reranking Layer',   tag: 'BGE-Reranker-Base',          description: 'A cross-encoder model jointly scores query+chunk pairs, reordering candidates by precision before context injection.' },
  { title: 'Generation Layer',  tag: 'Ollama · llama3.2:3b',       description: 'Context-window-fit prompt with strict grounding instructions passed to a quantized local LLM. Session memory persisted in SQLite.' },
  { title: 'Evaluation Layer',  tag: 'RAGAS · mistral:7b judge',   description: 'Automated quality measurement across faithfulness, relevancy, context precision, and recall. Parameter sweeps via ablation study framework.' },
];

const TECH_STACK = [
  { category: 'LLM',        name: 'Ollama',              detail: 'llama3.2:3b · mistral:7b' },
  { category: 'Embedding',  name: 'sentence-transformers',detail: 'BAAI/bge-base-en-v1.5' },
  { category: 'Reranker',   name: 'Cross-Encoder',       detail: 'BAAI/bge-reranker-base' },
  { category: 'Vector DB',  name: 'ChromaDB',            detail: 'Cosine · HNSW · Persistent' },
  { category: 'RAG',        name: 'LangChain 0.2+',      detail: 'Chains · Loaders · Splitters' },
  { category: 'RAG',        name: 'LlamaIndex 0.10+',    detail: 'Query Engines · Node Parsers' },
  { category: 'Retrieval',  name: 'rank-bm25',           detail: 'BM25Okapi · RRF Fusion' },
  { category: 'Evaluation', name: 'RAGAS',               detail: 'Faithfulness · Recall · Precision' },
  { category: 'API',        name: 'FastAPI',             detail: 'Python 3.11 · Pydantic v2' },
  { category: 'Frontend',   name: 'React 18 + Vite',     detail: 'Three.js · Lucide · DM Mono' },
  { category: 'Deploy',     name: 'Docker Compose',      detail: 'arm64 · Python + Node containers' },
  { category: 'Platform',   name: 'Apple Silicon M4',    detail: 'MPS acceleration · 16GB unified' },
];

export default function About() {
  useEffect(() => {
    // Scroll reveal triggers
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
    <div className="about-page-container" style={{ padding: 0 }}>
      {/* Section A — Project Identity */}
      <section className="section" style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
        <div className="container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <p className="eyebrow reveal" style={{ width: '100%' }}>// About DocuMind</p>

          <blockquote className="display-xl reveal reveal-delay-1" style={{
            maxWidth:   1000,
            marginTop:  'var(--sp-xl)',
            lineHeight: 1.0,
          }}>
            AN AI SYSTEM THAT KNOWS
            <span style={{ color: 'var(--amber)' }}> ONLY WHAT YOU TEACH IT</span>
            — AND KEEPS IT
            <span style={{ color: 'var(--amber)' }}> ENTIRELY TO ITSELF.</span>
          </blockquote>

          <div className="reveal reveal-delay-2" style={{
            display:      'flex',
            gap:          'var(--sp-2xl)',
            marginTop:    'var(--sp-3xl)',
            flexWrap:     'wrap',
            justifyContent: 'center',
            width: '100%',
          }}>
            {[
              ['VERSION',   'v1.7.0'],
              ['BUILT',     'June 2026'],
              ['PLATFORM',  'macOS M4 · Apple Silicon'],
              ['INFERENCE', 'Ollama · Llama 3.2 3B'],
              ['EMBEDDING', 'BAAI/bge-base-en-v1.5'],
            ].map(([k, v]) => (
              <div key={k} style={{ minWidth: '180px' }}>
                <p className="mono-base" style={{ color: 'var(--text-muted)' }}>{k}</p>
                <p className="display-md" style={{ color: 'var(--amber)', marginTop: 'var(--sp-sm)', fontSize: '2rem' }}>{v}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section B — Architecture Breakdown */}
      <section className="section" style={{ background: 'rgba(245,158,11,0.015)' }}>
        <div className="container">
          <p className="eyebrow reveal">// System Architecture</p>
          <h2 className="display-md reveal reveal-delay-1" style={{ marginTop: 'var(--sp-md)', marginBottom: 'var(--sp-2xl)' }}>
            HOW IT WORKS
          </h2>

          <div className="about-grid">
            {/* Left — Architecture layer descriptions */}
            <div>
              {ARCH_LAYERS.map((layer, i) => (
                <div key={layer.title} className={`reveal reveal-delay-${i + 1}`} style={{
                  padding:      'var(--sp-lg) 0',
                  borderBottom: '1px solid var(--border-subtle)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <p className="heading-ui" style={{ fontSize: '0.95rem' }}>{layer.title}</p>
                    <span className="mono-sm" style={{ color: 'var(--amber)' }}>{layer.tag}</span>
                  </div>
                  <p className="body-base" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-sm)', fontSize: '0.875rem' }}>
                    {layer.description}
                  </p>
                </div>
              ))}
            </div>

            {/* Right — ASCII flow diagram in axiom-card */}
            <div className="axiom-card reveal reveal-delay-2" style={{ overflowX: 'auto' }}>
              <p className="mono-sm" style={{ color: 'var(--amber)', marginBottom: 'var(--sp-md)' }}>
                // pipeline flow
              </p>
              <pre className="mono-sm" style={{ color: 'var(--text-secondary)', lineHeight: 1.9, whiteSpace: 'pre' }}>
{`[Document Upload]
      │
      ▼
[PyMuPDF / TextLoader]
      │ Raw text
      ▼
[Parent Chunker]  512 tok
      │
[Child Chunker]   128 tok
      │
[BGE Embedder]    768-dim
      │
      ▼
[ChromaDB]  ──  [BM25 Index]
      │                │
      └────── RRF ─────┘
                │
      [Cross-Encoder Reranker]
                │
      [Context Window Fit]
                │
      [Ollama: llama3.2:3b]
                │
                ▼
         [Answer + Sources]`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Section C — Technology Stack */}
      <section className="section">
        <div className="container">
          <p className="eyebrow reveal">// Technology Stack</p>
          <h2 className="display-md reveal reveal-delay-1" style={{ marginTop: 'var(--sp-md)', marginBottom: 'var(--sp-2xl)' }}>
            BUILT WITH
          </h2>
          <div className="tech-grid">
            {TECH_STACK.map((tech, i) => (
              <div key={tech.name} className={`axiom-card tech-card reveal reveal-delay-${i % 4 + 1}`}>
                <span className="mono-sm" style={{ color: 'var(--amber)' }}>{tech.category}</span>
                <p className="heading-ui" style={{ marginTop: 'var(--sp-xs)', fontSize: '1rem' }}>{tech.name}</p>
                <p className="mono-sm" style={{ color: 'var(--text-muted)', marginTop: 'var(--sp-xs)' }}>{tech.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section D — Build Philosophy */}
      <section className="section" style={{ paddingBottom: 'var(--sp-4xl)' }}>
        <div className="container" style={{ maxWidth: 720, textAlign: 'center' }}>
          <div className="divider" style={{ marginBottom: 'var(--sp-2xl)' }} />
          <p className="eyebrow reveal">// Engineering Philosophy</p>
          <h2 className="display-md reveal reveal-delay-1" style={{ marginTop: 'var(--sp-md)', marginBottom: 'var(--sp-lg)' }}>
            SEALED DEVICE INTELLIGENCE
          </h2>
          <p className="body-lg reveal reveal-delay-2" style={{ color: 'var(--text-secondary)' }}>
            True data custody requires running model architectures locally. DocuMind guarantees absolute containment, running standard quantizations on local processors, proving that document search doesn't require cloud data leaks.
          </p>
        </div>
      </section>
    </div>
  );
}
