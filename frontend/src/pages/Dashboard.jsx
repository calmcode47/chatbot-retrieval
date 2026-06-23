import React, { useState, useEffect, useRef } from "react";
import { API_BASE } from "../settings";
import {
  Upload,
  File,
  Trash2,
  Send,
  Loader2,
  Sparkles,
  Link,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const DocumentCard = ({ doc, onDelete }) => {
  const fileIcons = {
    pdf:  "📄",
    txt:  "📝",
    md:   "📋",
    docx: "📄",
  };
  const icon = fileIcons[doc.file_type] || "📁";

  // Format timestamp: "2026-06-18T10:30:00" → "Jun 18, 2026 10:30"
  const formatDate = (iso) => {
    if (!iso || iso === "unknown") return "Unknown";
    try {
      return new Date(iso).toLocaleString("en-US", {
        month: "short", day: "numeric", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
    } catch { return iso; }
  };

  return (
    <div style={{
      background: "rgba(255, 255, 255, 0.03)",
      border: "1px solid rgba(255, 255, 255, 0.06)",
      borderRadius: "8px",
      padding: "12px 14px",
      marginBottom: "8px",
      display: "flex",
      flexDirection: "column",
      gap: "4px",
      textAlign: "left",
    }}>
      {/* Filename row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ color: "#e2e8f0", fontWeight: 600, fontSize: "13px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginRight: "8px" }} title={doc.source_file}>
          {icon} {doc.source_file}
        </span>
        <button
          onClick={() => onDelete(doc.source_file)}
          title="Remove document"
          style={{
            background: "none",
            border: "none",
            color: "#ef4444",
            cursor: "pointer",
            fontSize: "14px",
            padding: "0 4px",
          }}
        >
          ✕
        </button>
      </div>

      {/* Metadata row */}
      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
        <span style={{ color: "#94a3b8", fontSize: "11px" }}>
          {doc.file_type.toUpperCase()}
        </span>
        <span style={{ color: "#94a3b8", fontSize: "11px" }}>
          {doc.file_size_display}
        </span>
        <span style={{ color: "#94a3b8", fontSize: "11px" }}>
          {doc.chunk_count} chunks
        </span>
      </div>

      {/* Timestamp */}
      <div style={{ color: "#64748b", fontSize: "11px" }}>
        {formatDate(doc.upload_timestamp)}
      </div>
    </div>
  );
};

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [vectorCount, setVectorCount] = useState(0);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});
  const [uploadError, setUploadError] = useState("");

  const chatEndRef = useRef(null);

  // Clear any stale session from localStorage on mount (page refresh = clean slate)
  useEffect(() => {
    localStorage.removeItem("documind_session_id");
  }, []);

  // Fetch session stats when session_id is set
  useEffect(() => {
    if (!sessionId) {
      setSessionInfo(null);
      return;
    }
    fetch(`${API_BASE}/sessions/${sessionId}`)
      .then((r) => r.json())
      .then((data) => setSessionInfo(data))
      .catch(() => {});
  }, [sessionId, messages]);

  // --- Fetch System Status & Loaded Docs ---
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setVectorCount(data.vector_store_count || 0);
      }
    } catch (err) {
      console.error("Health check failed", err);
    }
  };

  const fetchDocs = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error("Failed to load documents", err);
    }
  };

  // Load existing chat history from SQLite when session is active
  useEffect(() => {
    if (sessionId) {
      fetch(`${API_BASE}/sessions/${sessionId}/history`)
        .then((r) => {
          if (!r.ok) {
            throw new Error("Session history not found");
          }
          return r.json();
        })
        .then((data) => {
          if (data.messages) {
            const formatted = data.messages.map((m) => {
              const baseMsg = {
                role: m.role,
                content: m.content,
                timestamp: m.timestamp,
              };
              if (m.role === "assistant" && m.metadata) {
                baseMsg.sources = m.metadata.sources || [];
                baseMsg.latency = m.metadata.latency_ms;
                baseMsg.chunks = m.metadata.chunks_used;
                baseMsg.condensed = m.metadata.condensed_question;
              }
              return baseMsg;
            });
            setMessages(formatted);
          }
        })
        .catch((err) => {
          console.error("Failed to load history:", err);
          localStorage.removeItem("documind_session_id");
          setSessionId(null);
          setMessages([]);
        });
    } else {
      setMessages([]);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchStatus();
    fetchDocs();
  }, []);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  // --- Actions ---
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        fetchDocs();
        fetchStatus();
      } else {
        const text = await res.text();
        setUploadError(`Failed: ${text}`);
      }
    } catch (err) {
      setUploadError("Connection error during upload.");
    } finally {
      setIsUploading(false);
      // Reset file input
      event.target.value = null;
    }
  };

  const handleDeleteDoc = async (filename) => {
    try {
      const res = await fetch(`${API_BASE}/documents/${filename}`, {
        method: "DELETE",
      });
      if (res.ok) {
        fetchDocs();
        fetchStatus();
      }
    } catch (err) {
      console.error("Failed to delete document", err);
    }
  };

  const handleNewChat = async () => {
    const oldSessionId = sessionId;
    localStorage.removeItem("documind_session_id");
    setSessionId(null);
    setMessages([]);

    if (oldSessionId) {
      try {
        await fetch(`${API_BASE}/sessions/${oldSessionId}`, {
          method: "DELETE",
        });
      } catch (err) {
        console.error("Failed to delete session on backend", err);
      }
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isThinking) return;

    const userQuestion = inputValue;
    setInputValue("");

    // Add user message to thread
    const newMessages = [...messages, { role: "user", content: userQuestion }];
    setMessages(newMessages);
    setIsThinking(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userQuestion,
          top_k: 5,
          session_id: sessionId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id);
        }
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.answer,
            sources: data.sources || [],
            latency: data.latency_ms,
            chunks: data.chunks_used,
            condensed: data.condensed_question,
          },
        ]);
        fetchStatus(); // Update vector count just in case
      } else if (res.status === 400) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "⚠️ No documents are currently indexed. Please upload a file in the sidebar first.",
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "❌ An error occurred on the server side. Please check your Ollama backend.",
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "❌ Connection refused. Please ensure the DocuMind API is running.",
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const toggleSources = (index) => {
    setExpandedSources((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  return (
    <div className="dashboard-container">
      {/* Sidebar Panel */}
      <aside className="sidebar-panel glass-panel">
        <h2 className="sidebar-section-title">📂 Document Ingestion</h2>

        <label className="upload-dropzone">
          <Upload size={24} className="upload-icon" />
          <span className="upload-text">
            {isUploading ? "Uploading & Indexing..." : "Choose PDF, TXT, or MD"}
          </span>
          <input
            type="file"
            accept=".pdf,.txt,.md"
            onChange={handleFileUpload}
            disabled={isUploading}
            style={{ display: "none" }}
          />
        </label>

        {uploadError && <p className="upload-error">{uploadError}</p>}

        <div className="metrics-box">
          <span className="metrics-label">Vector Store Count</span>
          <span className="metrics-value">{vectorCount} chunks</span>
        </div>

        <div className="doc-list-section">
          <h3 className="doc-list-title" style={{ marginBottom: "8px" }}>Indexed Files</h3>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ color: "#94a3b8", fontSize: "12px" }}>
              {documents.length} document{documents.length !== 1 ? "s" : ""}
            </span>
          </div>

          {documents.length === 0 ? (
            <p className="no-docs-text">No documents uploaded yet.</p>
          ) : (
            <div className="doc-list" style={{ overflowY: "auto", maxHeight: "calc(100vh - 480px)", paddingRight: "4px" }}>
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.source_file}
                  doc={doc}
                  onDelete={handleDeleteDoc}
                />
              ))}
            </div>
          )}
        </div>

        <div style={{ marginTop: "auto", paddingTop: "16px", borderTop: "1px solid rgba(255, 255, 255, 0.06)", display: "flex", flexDirection: "column", gap: "8px" }}>
          <button
            onClick={handleNewChat}
            style={{
              width: "100%",
              padding: "10px",
              background: "rgba(245, 158, 11, 0.1)",
              border: "1px solid rgba(245, 158, 11, 0.25)",
              borderRadius: "6px",
              color: "var(--amber)",
              fontFamily: "var(--font-condensed)",
              fontWeight: "600",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              cursor: "pointer",
              transition: "all var(--t-fast) var(--ease-out)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--amber)";
              e.currentTarget.style.color = "#000";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(245, 158, 11, 0.1)";
              e.currentTarget.style.color = "var(--amber)";
            }}
          >
            New Chat
          </button>
          {sessionInfo && (
            <div className="mono-sm" style={{ color: "var(--text-muted)", fontSize: "11px", textAlign: "center" }}>
              Session: {sessionInfo.turn_count} turns · Active
            </div>
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-area">
        <div className="chat-history">
          {messages.length === 0 ? (
            <div className="chat-placeholder">
              <Sparkles size={48} className="placeholder-icon" />
              <h2>Hello! I'm DocuMind.</h2>
              <p>Upload files in the sidebar and ask questions about them. I'll summarize context and cite references.</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message-bubble-wrapper ${msg.role}`}>
                <div className={`message-bubble ${msg.role}`}>
                  <div className="message-content">{msg.content}</div>

                  {msg.role === "assistant" && msg.latency !== undefined && (
                    <div className="message-footer">
                      <span>⚡ {Math.round(msg.latency)}ms</span>
                      <span>•</span>
                      <span>{msg.chunks} chunks used</span>
                      {msg.condensed && msg.condensed !== messages[idx - 1]?.content && (
                        <>
                          <span>•</span>
                          <span className="condensed-badge">🔄 Query Condensed</span>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                  <div className="sources-container">
                    <button
                      className="sources-toggle"
                      onClick={() => toggleSources(idx)}
                    >
                      <Link size={14} />
                      <span>Sources & Citations ({msg.sources.length})</span>
                      {expandedSources[idx] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>

                    {expandedSources[idx] && (
                      <div className="sources-list-wrapper">
                        {msg.sources.map((src, sIdx) => (
                          <div key={sIdx} className="source-citation-card glass-panel">
                            <div className="source-card-header">
                              <span className="source-filename">{src.source_file}</span>
                              <span className="source-score">Relevance: {Math.round(src.score * 100)}%</span>
                            </div>
                            <blockquote className="source-excerpt">
                              "{src.excerpt}"
                            </blockquote>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}

          {isThinking && (
            <div className="message-bubble-wrapper assistant">
              <div className="message-bubble assistant thinking">
                <Loader2 className="spinning-loader" size={20} />
                <span>Thinking and scanning documents...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSendMessage} className="chat-input-bar">
          <input
            type="text"
            className="chat-text-input"
            placeholder="Ask a question about your documents..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isThinking}
          />
          <button
            type="submit"
            className="chat-submit-button"
            disabled={!inputValue.trim() || isThinking}
          >
            <Send size={18} />
          </button>
        </form>
      </main>
    </div>
  );
}
