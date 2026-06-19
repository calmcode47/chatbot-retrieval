import React from "react";
import { Server, Database, GitBranch, Cpu, Eye, FileText } from "lucide-react";

export default function About() {
  const steps = [
    {
      icon: FileText,
      title: "1. Hierarchical Chunking",
      desc: "Documents are split into 512-token parent chunks and 128-token child chunks. Only the smaller child chunks get embedded, keeping vector matches highly focused.",
    },
    {
      icon: Database,
      title: "2. Vector & Sparse Storage",
      desc: "Child chunks are indexed inside ChromaDB. Concurrently, a sparse BM25 keyword index is rebuilt dynamically to safeguard search matching for specific codes/names.",
    },
    {
      icon: GitBranch,
      title: "3. Reciprocal Rank Fusion (RRF)",
      desc: "A search query generates candidates from both dense vector distance (cosines) and sparse keyword rank. RRF fuses these rankings seamlessly into a single candidate pool.",
    },
    {
      icon: Eye,
      title: "4. Cross-Encoder Reranking",
      desc: "Top 20 candidates are re-scored using BAAI/bge-reranker-base. It reviews the query and content together, sorting context by absolute relevance.",
    },
    {
      icon: Cpu,
      title: "5. Context Stitching",
      desc: "The high-scoring children are mapped back to their original 512-token parent chunks. The full parent text is stitched together as context for the LLM prompt.",
    },
    {
      icon: Server,
      title: "6. Grounded Generation",
      desc: "The prompt is dispatched to llama3.2:3b via Ollama. The model generates a factual answer referencing the provided context strictly, preventing hallucinations.",
    },
  ];

  return (
    <div className="about-container">
      <h1 className="about-title">
        {"Inside the "}
        <span className="gradient-text">DocuMind Pipeline</span>
      </h1>
      <p className="about-subtitle">
        A step-by-step breakdown of how our private Retrieval-Augmented Generation engine processes your documents.
      </p>

      <div className="architecture-timeline">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div key={idx} className="timeline-node glass-panel">
              <div className="node-icon-container">
                <Icon size={24} className="node-icon" />
              </div>
              <div className="node-content">
                <h3 className="node-title">{step.title}</h3>
                <p className="node-desc">{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
