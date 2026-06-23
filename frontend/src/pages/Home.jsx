import React, { useState } from "react";
import {
  Search,
  Layers,
  SlidersHorizontal,
  Cpu,
  MessageSquare,
  Zap,
  FileText,
  Scissors,
  Braces,
  Sparkles
} from "lucide-react";
import LogicCore from "../components/LogicCore";

const FEATURES = [
  { title:'Hybrid Retrieval',  description:'BM25 keyword search fused with BGE dense embeddings using Reciprocal Rank Fusion — captures both exact matches and semantic similarity.', tech:'BM25Okapi · BGE-base · RRF k=60', Icon: Search },
  { title:'Hierarchical Chunks', description:'Parent-child chunking: 128-token children for precise embedding, 512-token parents returned to the LLM for rich contextual answers.', tech:'RecursiveTextSplitter · PyMuPDF', Icon: Layers },
  { title:'Cross-Encoder Reranking', description:'After retrieval, BGE-Reranker-Base jointly scores every (query, chunk) pair to re-order candidates by true relevance.', tech:'BAAI/bge-reranker-base', Icon: SlidersHorizontal },
  { title:'On-Device LLM',    description:'Qwen2.5-0.5B runs directly inside the Python process. No Ollama, no API keys, no external calls. The model loads once and stays resident.', tech:'Qwen2.5-0.5B · HuggingFace transformers', Icon: Cpu },
  { title:'Session Memory',   description:'Conversation history persists in SQLite across page refreshes. Sessions survive container restarts via mounted volume.', tech:'SQLite · session_store.py', Icon: MessageSquare },
  { title:'Embedding Cache',  description:'Disk-based cache skips recomputation for previously embedded text. Critical for fast re-ingestion during ablation studies.', tech:'diskcache · sha256 keying', Icon: Zap },
];

const PIPELINE = [
  { title:'Parse',    desc:'PyMuPDF, TextLoader, and WebLoader extract raw text preserving structure.', Icon: FileText },
  { title:'Chunk',    desc:'Recursive splitter creates 512-token parent and 128-token child hierarchies.', Icon: Scissors },
  { title:'Embed',    desc:'BGE-base-en-v1.5 converts each child chunk to a 768-dim normalized vector.', Icon: Braces },
  { title:'Retrieve', desc:'Hybrid BM25+dense search with RRF merge surfaces the most relevant parents.', Icon: Search },
  { title:'Generate', desc:'Qwen2.5-0.5B produces a grounded answer strictly from retrieved context.', Icon: Sparkles },
];

export default function Home({ setPage }) {
  const [coreHovered, setCoreHovered] = useState(false);

  return (
    <div className="home-container" style={{ padding: 0 }}>
      {/* Section 1 — Hero */}
      <section style={{ minHeight:'100vh', display:'flex', alignItems:'center' }}>
        <div className="container">
          <div className="hero-grid">

            {/* Left */}
            <div className="hero-left">
              <p className="eyebrow reveal">// PRIVATE  ·  LOCAL  ·  INTELLIGENT</p>

              <h1 className="display-xl hero-title reveal reveal-delay-1">
                KNOW<span style={{ color:'var(--violet-soft)' }}>LEDGE</span><br />
                THAT STAYS<br />
                <span style={{ color:'var(--violet)' }}>WITH YOU</span>
              </h1>

              <p className="body-lg reveal reveal-delay-2"
                 style={{ color:'var(--text-secondary)', maxWidth:440, marginTop:'var(--sp-lg)' }}>
                Ask questions across your documents. Runs entirely offline on Apple Silicon.
                No data leaves your machine — ever.
              </p>

              <div className="hero-chips reveal reveal-delay-3">
                <span className="chip">◈ Zero Cloud APIs</span>
                <span className="chip">⬡ Qwen2.5 · BGE · ChromaDB</span>
                <span className="chip">✦ MPS Accelerated</span>
              </div>

              <div className="hero-ctas reveal reveal-delay-4">
                <button className="btn-primary" onClick={() => setPage('dashboard')}>
                  Open Dashboard
                </button>
                <button className="btn-ghost"
                        onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior:'smooth' })}>
                  How it Works
                </button>
              </div>

              <p className="mono-sm reveal reveal-delay-4"
                 style={{ color:'var(--text-muted)', marginTop:'var(--sp-xl)' }}>
                v1.7.0  ·  Qwen2.5-0.5B  ·  BAAI/bge-base-en-v1.5  ·  Railway
              </p>
            </div>

            {/* Right — Logic Core */}
            <div className="hero-right"
                 onMouseEnter={() => setCoreHovered(true)}
                 onMouseLeave={() => setCoreHovered(false)}>
              <LogicCore isHovered={coreHovered} />
            </div>

          </div>
        </div>
      </section>

      {/* Section 2 — How it Works */}
      <section id="how-it-works" className="section">
        <div className="container">
          <p className="eyebrow reveal">// Core Capabilities</p>
          <h2 className="display-md reveal reveal-delay-1" style={{ marginTop:'var(--sp-md)', marginBottom:'var(--sp-2xl)' }}>
            BUILT DIFFERENT
          </h2>
          <div className="features-grid">
            {FEATURES.map((f, i) => (
              <div key={f.title} className={`prism-card reveal reveal-delay-${i + 1}`}>
                <div className="icon-box" style={{ marginBottom:'var(--sp-lg)' }}>
                  <f.Icon size={20} />
                </div>
                <p className="heading-ui" style={{ fontSize:'1rem' }}>{f.title}</p>
                <p className="body-base" style={{ color:'var(--text-secondary)', marginTop:'var(--sp-sm)', fontSize:'0.875rem' }}>
                  {f.description}
                </p>
                <p className="mono-sm" style={{ color:'var(--text-muted)', marginTop:'var(--sp-lg)' }}>
                  {f.tech}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 3 — Pipeline */}
      <section className="section" style={{ background:'linear-gradient(180deg,var(--void) 0%,rgba(124,58,237,0.025) 50%,var(--void) 100%)' }}>
        <div className="container">
          <p className="eyebrow reveal">// Processing Pipeline</p>
          <h2 className="display-md reveal reveal-delay-1" style={{ marginTop:'var(--sp-md)', marginBottom:'var(--sp-2xl)' }}>
            FROM UPLOAD TO ANSWER
          </h2>
          <div className="pipeline-grid">
            {PIPELINE.map((step, i) => (
              <div key={step.title} className={`reveal reveal-delay-${i+1}`}>
                <p className="mono-sm" style={{ color:'var(--violet-soft)', marginBottom:'var(--sp-sm)' }}>
                  {String(i+1).padStart(2,'0')}
                </p>
                <div className="prism-card pipeline-step-card">
                  <div className="icon-box" style={{ marginBottom:'var(--sp-md)' }}>
                    <step.Icon size={18} />
                  </div>
                  <p className="heading-ui" style={{ fontSize:'0.95rem' }}>{step.title}</p>
                  <p style={{ color:'var(--text-secondary)', fontSize:'0.83rem', marginTop:'var(--sp-sm)', lineHeight:1.6 }}>
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 4 — Metrics */}
      <section className="section">
        <div className="container">
          <div className="divider" style={{ marginBottom:'var(--sp-2xl)' }} />
          <div className="metrics-grid">
            {[
              { value:'0',      label:'External API Calls',  note:'All inference on-device.' },
              { value:'768',    label:'Embedding Dimensions', note:'BAAI/bge-base-en-v1.5' },
              { value:'0.5B',   label:'Model Parameters',    note:'Runs on 512 MB RAM.' },
              { value:'RAGAS',  label:'Evaluated',           note:'Faithfulness · Recall · Precision' },
            ].map((m, i) => (
              <div key={i} className={`prism-card reveal reveal-delay-${i+1}`} style={{ textAlign:'center' }}>
                <p className="display-md" style={{ color:'var(--violet-soft)' }}>{m.value}</p>
                <p className="mono-base"  style={{ marginTop:'var(--sp-xs)' }}>{m.label}</p>
                <p className="mono-sm"    style={{ color:'var(--text-muted)', marginTop:'var(--sp-sm)' }}>{m.note}</p>
              </div>
            ))}
          </div>
          <div className="divider" style={{ marginTop:'var(--sp-2xl)' }} />
        </div>
      </section>

      {/* Section 5 — CTA */}
      <section className="section" style={{ textAlign:'center', minHeight:'36vh', display:'flex', alignItems:'center' }}>
        <div className="container">
          <p className="eyebrow reveal">// Start now</p>
          <h2 className="display-lg reveal reveal-delay-1" style={{ marginTop:'var(--sp-md)', marginBottom:'var(--sp-lg)' }}>
            UPLOAD A DOCUMENT.<br />
            <span style={{ color:'var(--text-secondary)' }}>ASK ANYTHING.</span>
          </h2>
          <div className="reveal reveal-delay-2">
            <button className="btn-primary" onClick={() => setPage('dashboard')} style={{ fontSize:'1.1rem', padding:'14px 36px' }}>
              Open Dashboard
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
