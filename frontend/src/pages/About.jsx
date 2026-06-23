import React from "react";
import ConstellationDome from "../components/ConstellationDome";

const ARCH_LAYERS = [
  { title:'Ingestion',   tag:'PyMuPDF · LangChain',    desc:'Documents parsed by format-specific loaders, split into 512/128-token parent-child hierarchies, embedded with BGE.' },
  { title:'Indexing',    tag:'ChromaDB · BM25',        desc:'768-dim vectors stored with HNSW indexing. BM25 sparse index rebuilt after each ingestion for keyword coverage.' },
  { title:'Retrieval',   tag:'RRF k=60 · Reranker',    desc:'Dense and sparse retrieval merged with Reciprocal Rank Fusion. Cross-encoder reranks shortlist for precision.' },
  { title:'Generation',  tag:'Qwen2.5-0.5B · HF',      desc:'Context-fit prompt passed to a resident SLM. Model stays in memory after first load. No external calls.' },
  { title:'Evaluation',  tag:'RAGAS · mistral:7b',     desc:'Faithfulness, answer relevancy, context precision, and recall measured against synthetic eval dataset.' },
];

const TECH_STACK = [
  { category:'SLM',       name:'Qwen2.5-0.5B', detail:'Local HF inference' },
  { category:'Embedding', name:'bge-base-en',  detail:'768-dim · MPS' },
  { category:'Reranker',  name:'bge-reranker', detail:'Cross-encoder' },
  { category:'Vector DB', name:'ChromaDB',     detail:'HNSW · Cosine' },
  { category:'Retrieval', name:'LangChain 0.2',detail:'Chains · Loaders' },
  { category:'Sparse',    name:'rank-bm25',    detail:'BM25Okapi · RRF' },
  { category:'Eval',      name:'RAGAS',        detail:'4 RAG metrics' },
  { category:'API',       name:'FastAPI',      detail:'Pydantic v2' },
  { category:'Frontend',  name:'React+Vite',   detail:'Three.js · Lucide' },
  { category:'Deploy',    name:'Railway',      detail:'Cloud containers' },
  { category:'Cache',     name:'diskcache',    detail:'Embedding cache' },
  { category:'Memory',    name:'SQLite',       detail:'Session store' },
];

export default function About() {
  return (
    <div className="about-page-container" style={{ padding: 0 }}>
      {/* ── Section A: Hero with Dome ─────────────────────────── */}
      <section className="section" style={{
        minHeight:'90vh', display:'flex', alignItems:'center',
        background:'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(124,58,237,0.06) 0%, transparent 70%)'
      }}>
        <div className="container">
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'var(--sp-2xl)', alignItems:'center' }}>

            {/* Dome */}
            <div style={{ display:'flex', justifyContent:'center' }}>
              <ConstellationDome width={520} height={420} />
            </div>

            {/* Title */}
            <div>
              <p className="eyebrow reveal">// Project Identity</p>
              <h1 className="display-xl reveal reveal-delay-1" style={{ marginTop:'var(--sp-md)', lineHeight:0.92 }}>
                DOCU<br /><span style={{ color:'var(--violet-soft)' }}>MIND</span>
              </h1>
              <p className="body-lg reveal reveal-delay-2" style={{ color:'var(--text-secondary)', maxWidth:400, marginTop:'var(--sp-xl)' }}>
                A local RAG system that treats your documents as a sealed knowledge vault —
                indexed, searchable, and answerable without a single external API call.
              </p>
              {/* Metadata strip */}
              <div className="reveal reveal-delay-3" style={{ display:'flex', gap:'var(--sp-xl)', flexWrap:'wrap', marginTop:'var(--sp-xl)' }}>
                {[
                  ['VERSION',   'v1.7.0'],
                  ['DEPLOYED',  'Railway'],
                  ['SLM',       'Qwen2.5-0.5B'],
                  ['EMBEDDING', 'bge-base-en-v1.5'],
                ].map(([k,v]) => (
                  <div key={k}>
                    <p className="mono-sm" style={{ color:'var(--text-muted)' }}>{k}</p>
                    <p className="mono-base" style={{ color:'var(--violet-soft)', marginTop:2 }}>{v}</p>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── Section B: Mission ────────────────────────────────── */}
      <section className="section">
        <div className="container" style={{ maxWidth:840 }}>
          <div className="divider" style={{ marginBottom:'var(--sp-3xl)' }} />
          <p className="eyebrow reveal">// Mission</p>
          <blockquote className="display-md reveal reveal-delay-1" style={{ marginTop:'var(--sp-lg)', lineHeight:1.15 }}>
            "THE MODEL SHOULD KNOW ONLY
            <span style={{ color:'var(--violet-soft)' }}> WHAT YOU TAUGHT IT</span>,
            AND KEEP THAT KNOWLEDGE
            <span style={{ color:'var(--violet-soft)' }}> COMPLETELY TO ITSELF</span>."
          </blockquote>
          <div className="divider" style={{ marginTop:'var(--sp-3xl)' }} />
        </div>
      </section>

      {/* ── Section C: Architecture ───────────────────────────── */}
      <section className="section">
        <div className="container">
          <p className="eyebrow reveal">// System Architecture</p>
          <h2 className="display-md reveal reveal-delay-1" style={{ marginTop:'var(--sp-md)', marginBottom:'var(--sp-2xl)' }}>
            FIVE LAYERS
          </h2>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'var(--sp-2xl)', alignItems:'start' }}>

            {/* Left: layer descriptions */}
            <div>
              {ARCH_LAYERS.map((layer, i) => (
                <div key={layer.title} className={`reveal reveal-delay-${i+1}`}
                     style={{ padding:'var(--sp-lg) 0', borderBottom:'1px solid var(--border-subtle)' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                    <p className="heading-ui" style={{ fontSize:'0.95rem' }}>{layer.title}</p>
                    <span className="mono-sm" style={{ color:'var(--violet-soft)' }}>{layer.tag}</span>
                  </div>
                  <p style={{ color:'var(--text-secondary)', fontSize:'0.875rem', marginTop:'var(--sp-sm)', lineHeight:1.6 }}>
                    {layer.desc}
                  </p>
                </div>
              ))}
            </div>

            {/* Right: ASCII diagram */}
            <div className="prism-card reveal reveal-delay-2">
              <p className="mono-sm" style={{ color:'var(--violet-soft)', marginBottom:'var(--sp-md)' }}>
                // query flow
              </p>
              <pre className="mono-sm" style={{ color:'var(--text-secondary)', lineHeight:1.9 }}>
{`User Query
    │
    ▼
BGE Embed Query  →  768-dim vec
    │
    ├──▶ ChromaDB (dense)
    │
    ├──▶ BM25 (sparse)
    │
    └──▶ RRF Merge
              │
    Cross-Encoder Reranker
              │
    Context Window Fit
              │
    Qwen2.5-0.5B (local)
              │
              ▼
    Answer + Source Citations`}
              </pre>
            </div>

          </div>
        </div>
      </section>

      {/* ── Section D: Tech Stack ─────────────────────────────── */}
      <section className="section">
        <div className="container">
          <p className="eyebrow reveal">// Stack</p>
          <h2 className="display-md reveal reveal-delay-1" style={{ marginTop:'var(--sp-md)', marginBottom:'var(--sp-2xl)' }}>
            TECHNOLOGIES
          </h2>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:'var(--sp-md)' }}>
            {TECH_STACK.map((t, i) => (
              <div key={t.name} className={`prism-card reveal reveal-delay-${i%4+1}`}
                   style={{ padding:'var(--sp-lg)' }}>
                <p className="mono-sm" style={{ color:'var(--violet-soft)' }}>{t.category}</p>
                <p className="heading-ui" style={{ marginTop:'var(--sp-xs)', fontSize:'0.9rem' }}>{t.name}</p>
                <p className="mono-sm"    style={{ color:'var(--text-muted)', marginTop:'var(--sp-xs)' }}>{t.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section E: Philosophy ─────────────────────────────── */}
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
