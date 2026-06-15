"""
Streamlit chat interface for DocuMind.
Run with: streamlit run ui/app.py
"""

import streamlit as st
import requests
import json

API_BASE = "http://localhost:8000/api/v1"


st.set_page_config(
    page_title="DocuMind",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 DocuMind")
st.caption("Local RAG Document Q&A — 100% private, no external APIs")

# ── Sidebar: Document Management ────────────────────────────────────
with st.sidebar:
    st.header("📂 Documents")

    uploaded = st.file_uploader(
        "Upload a document",
        type=["pdf", "txt", "md"],
        help="PDF, TXT, or Markdown files are supported",
    )

    if uploaded is not None:
        with st.spinner("Indexing document..."):
            response = requests.post(
                f"{API_BASE}/ingest",
                files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
            )
            if response.status_code == 200:
                data = response.json()
                st.success(f"✓ {data['chunks_indexed']} chunks indexed from '{uploaded.name}'")
            else:
                st.error(f"Ingestion failed: {response.text}")

    st.divider()
    st.subheader("Indexed Documents")
    try:
        docs_resp = requests.get(f"{API_BASE}/documents")
        if docs_resp.status_code == 200:
            docs = docs_resp.json().get("documents", [])
            if docs:
                for doc in docs:
                    col1, col2 = st.columns([4, 1])
                    col1.text(doc)
                    if col2.button("✕", key=f"del_{doc}"):
                        requests.delete(f"{API_BASE}/documents/{doc}")
                        st.rerun()
            else:
                st.info("No documents indexed yet.")
    except:
        st.warning("API not reachable. Start the backend first.")

    st.divider()
    try:
        health = requests.get(f"{API_BASE}/health").json()
        st.metric("Chunks in store", health.get("vector_store_count", 0))
    except:
        st.metric("Chunks in store", "—")

# ── Main: Chat Interface ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📎 Sources"):
                for src in message["sources"]:
                    st.markdown(
                        f"**{src['source_file']}** — Page {src['page']} "
                        f"(relevance: {src['score']:.2f})\n\n> {src['excerpt']}"
                    )

# Chat input
if question := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Get RAG response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Build chat_history from session state (all previous turns)
                # Only include complete turns (user + assistant pairs)
                history = []
                messages = st.session_state.messages
                i = 0
                while i < len(messages) - 1:  # -1 because last is current user msg
                    if messages[i]["role"] == "user" and messages[i+1]["role"] == "assistant":
                        history.append({
                            "user": messages[i]["content"],
                            "assistant": messages[i+1]["content"],
                        })
                        i += 2
                    else:
                        i += 1

                response = requests.post(
                    f"{API_BASE}/chat",
                    json={
                        "question": question,
                        "top_k": 5,
                        "chat_history": history,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])
                    latency = data.get("latency_ms", 0)
                    condensed = data.get("condensed_question", question)

                    st.markdown(answer)

                    # Show if question was condensed (useful for debugging)
                    if condensed != question:
                        st.caption(f"🔄 Condensed: *'{condensed}'*")

                    st.caption(
                        f"⚡ {latency:.0f}ms  |  "
                        f"{data['chunks_used']} chunks  |  "
                        f"{data.get('history_turns_used', 0)} history turns"
                    )

                    if sources:
                        with st.expander("📎 Sources"):
                            for src in sources:
                                st.markdown(
                                    f"**{src['source_file']}** — Page {src.get('page', '?')} "
                                    f"(relevance: {src['score']:.2f})\n\n> {src['excerpt']}"
                                )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                elif response.status_code == 400:
                    st.warning("No documents indexed. Please upload a document first.")
                else:
                    st.error(f"Error {response.status_code}: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the API. Run: `make serve` in your terminal.")
