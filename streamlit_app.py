import streamlit as st
from pathlib import Path
import tempfile
from html import escape
import streamlit.components.v1 as components

from app.rag.ingestion import extract_pdf
from app.rag.chunking import chunk_pages
from app.rag.vector_store import add_chunks, reset_collection
from app.rag.rag_qa import ask as rag_ask
from app.agents.research_agent import run_full_pipeline

st.set_page_config(
    page_title="ResearchPilot",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------
# Dark Theme CSS
# ------------------------------
st.markdown(
    """
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600;700&display=swap');

    :root {
        --bg: #0B1220;
        --surface: #141B2E;
        --surface-2: #1A2333;
        --border: rgba(255,255,255,0.09);
        --text: #F0F2F5;
        --muted: #8B92A5;
        --amber: #B9812E;
        --amber-bg: #2A2116;
        --teal: #1C7A72;
        --teal-bg: #112B28;
        --caution-bg: #2A2116;
        --caution-text: #E0A45B;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }

    .stApp {
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }

    #MainMenu, footer { visibility: hidden; }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text) !important;
    }

    p, span, label, div {
        color: var(--text) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1220 0%, #141B2E 100%) !important;
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] * {
        color: #E7E9EE !important;
    }

    /* Radio buttons */
    div[role="radiogroup"] label {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid var(--border) !important;
        border-radius: 9px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.35rem;
    }
    div[role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.1) !important;
    }

    /* File uploader */
    [data-testid="stFileUploaderDropzone"] {
        background-color: var(--surface-2) !important;
        border: 1px dashed var(--border) !important;
        color: var(--text) !important;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px;
        padding: 1rem;
        color: var(--text) !important;
    }
    [data-testid="stChatMessage"] p {
        color: var(--text) !important;
    }

    /* Inputs */
    input, textarea {
        color: var(--text) !important;
        background-color: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: var(--teal) !important;
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background-color: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 11px;
        padding: 0.85rem 0.95rem;
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--text) !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background-color: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px;
    }

    /* Custom cards */
    .rp-card {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
        color: var(--text);
    }
    .rp-card.accent-teal { border-left: 3px solid var(--teal); }
    .rp-card.accent-amber { border-left: 3px solid var(--amber); }

    .rp-evidence-card {
        background: var(--teal-bg);
        border: 1px solid var(--teal);
        border-radius: 9px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.55rem;
    }
    .rp-evidence-meta {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #8AE0D6;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .rp-evidence-text {
        font-size: 0.9rem;
        color: var(--text);
        line-height: 1.5;
    }

    .rp-note {
        background: var(--caution-bg);
        border: 1px solid var(--caution-text);
        border-radius: 10px;
        padding: 0.85rem 1.05rem;
        font-size: 0.86rem;
        color: var(--caution-text);
    }

    /* Mermaid container */
    .mermaid-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.2rem 0.6rem;
        margin-bottom: 1rem;
    }
    .mermaid {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------
# Helper functions
# ------------------------------
def ingest_pdf_file(uploaded_file):
    """Save uploaded PDF temporarily, ingest it, and return chunk count."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = Path(tmp_file.name)

    try:
        pages, toc = extract_pdf(tmp_path)
        chunks = chunk_pages(pages, toc)
        reset_collection()
        add_chunks(chunks)
        return len(chunks)
    finally:
        tmp_path.unlink(missing_ok=True)


def render_evidence(evidence):
    """Render evidence items as cards."""
    for item in evidence:
        page = item.get("page", "?")
        section = item.get("section", "Unknown")
        text = item.get("text", "")
        st.markdown(
            f"""
            <div class="rp-evidence-card">
                <div class="rp-evidence-meta">Page {escape(str(page))} &nbsp;·&nbsp; {escape(str(section))}</div>
                <div class="rp-evidence-text">{escape(str(text))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_mermaid(mermaid_code: str, height: int = 500):
    """Render a centered Mermaid diagram without scrollbars."""
    components.html(
        f"""
        <div class="mermaid-wrapper" style="overflow: visible;">
            <pre class="mermaid" style="margin:0;">
{mermaid_code}
            </pre>
        </div>
        <script type="module">
          import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
          mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose',
            themeVariables: {{
              primaryColor: '#141B2E',
              primaryTextColor: '#F0F2F5',
              primaryBorderColor: '#1C7A72',
              lineColor: '#8B92A5',
              fontFamily: 'IBM Plex Mono, monospace',
              fontSize: '13px'
            }}
          }});
        </script>
        """,
        height=height,
        scrolling=False,
    )


# ------------------------------
# Sidebar
# ------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:0.65rem; padding-bottom:1.1rem; border-bottom:1px solid rgba(255,255,255,0.09); margin-bottom:1.2rem;">
            <div style="width:40px;height:40px;border-radius:10px;background:#141B2E;border:1px solid rgba(255,255,255,0.09);display:flex;align-items:center;justify-content:center;font-size:1.25rem;">✈️</div>
            <div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.15rem;font-weight:800;line-height:1.1;">ResearchPilot</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:0.66rem;color:#8B92A5;margin-top:3px;text-transform:uppercase;letter-spacing:0.03em;">Evidence-grounded reading</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Navigate**")
    page = st.radio(
        "Navigate",
        ["Chat", "About"],
        label_visibility="collapsed",
        key="nav_radio",
    )

    if page == "Chat":
        st.markdown("---")
        st.markdown("**Answer Mode**")
        mode = st.radio(
            "Select mode",
            ["rag", "pipeline"],
            format_func=lambda x: "⚡ RAG (Fast)" if x == "rag" else "🛡️ Pipeline (Verified)",
            label_visibility="collapsed",
            key="mode_radio",
        )
    else:
        mode = None


# ------------------------------
# Chat Page
# ------------------------------
if page == "Chat":
    st.title("Chat with Paper")

    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])

    if uploaded_file is not None:
        is_new_file = (
            "last_file_name" not in st.session_state
            or st.session_state.last_file_name != uploaded_file.name
        )
        if is_new_file:
            with st.spinner("Ingesting PDF..."):
                chunk_count = ingest_pdf_file(uploaded_file)
                st.session_state.last_file_name = uploaded_file.name
                st.session_state.chunk_count = chunk_count
                st.session_state.messages = []
            st.success(f"Ingested {chunk_count} chunks from {uploaded_file.name}")
        else:
            st.info(f"Using already ingested PDF: {uploaded_file.name}")

        st.session_state.setdefault("messages", [])
        st.session_state.setdefault("chunk_count", 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("Chunks indexed", st.session_state.chunk_count)
        c2.metric("Questions asked", len([m for m in st.session_state.messages if m["role"] == "user"]))
        c3.metric("Mode", "RAG" if mode == "rag" else "Pipeline")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("evidence"):
                    with st.expander("📚 Evidence used"):
                        render_evidence(msg["evidence"])

        question = st.chat_input("Ask a question about the paper…")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                evidence = None
                with st.spinner("Generating answer..."):
                    if mode == "rag":
                        answer = rag_ask(question, k=8)
                    else:
                        result = run_full_pipeline(question)
                        answer = result.get("answer", "No answer produced.")
                        evidence = result.get("evidence", [])

                st.markdown(answer)
                if evidence:
                    with st.expander("📚 Evidence used"):
                        render_evidence(evidence)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "evidence": evidence,
            })

    else:
        st.info("Please upload a PDF to start.")


# ------------------------------
# About Page
# ------------------------------
elif page == "About":
    st.title("About ResearchPilot")

    st.markdown(
        """
        <div class="rp-card">
        ResearchPilot is an evidence-grounded AI research assistant that combines:
        <ul>
            <li><b>Retrieval-Augmented Generation (RAG)</b></li>
            <li><b>Local/Cloud LLMs</b> (Ollama or Groq)</li>
            <li><b>Multi-agent verification</b> (Analyst → Evidence → Critic → Report)</li>
        </ul>
        It processes academic PDFs, retrieves relevant passages, and produces answers
        with explicit citations to the source document.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.header("Architecture")

    st.subheader("⚡ RAG Mode")
    render_mermaid(
        """
flowchart TD
    A[PDF] --> B[Text Extraction]
    B --> C[Chunking]
    C --> D[Embeddings via Ollama]
    D --> E[(ChromaDB)]
    E --> F[Semantic Retrieval]
    F --> G[LLM Answer]
    G --> H[Final Response with Evidence]
""",
        height=730,
    )

    st.subheader("🛡️ Pipeline Mode")
    render_mermaid(
        """
flowchart TD
    A[PDF] --> B[Text Extraction]
    B --> C[Chunking]
    C --> D[Embeddings via Ollama]
    D --> E[(ChromaDB)]
    E --> F[Question + Retrieval]
    F --> G[Research Agent]
    G --> H[Analyst Agent]
    H --> I[Evidence Agent]
    I --> J[Critic Agent]
    J --> K[Report Agent]
    K --> L[Final Structured Response]
""",
        height=1000,
    )

    st.header("Baseline Results")
    st.markdown(
        """
        | Metric | RAG Mode | Pipeline Mode |
        |--------|----------|---------------|
        | Recall@5 | 1.00 | 1.00 |
        | Precision@5 | 0.52 | 0.52 |
        | MRR | 0.853 | 0.853 |
        | Answer Score | 4.0 | 3.7 |

        > The pipeline adds verification but may produce slightly lower scores because the
        > critic sometimes removes valid details. Future tuning will improve this.
        """
    )

    st.header("Mode Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="rp-card accent-amber">
                <b>⚡ RAG Mode</b><br><br>
                Simple and fast. Retrieves top-k chunks and passes them to the LLM with a prompt
                to answer and cite evidence. Good for quick fact‑checking.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="rp-card accent-teal">
                <b>🛡️ Pipeline Mode</b><br><br>
                Multi‑agent workflow:
                <ol>
                    <li>Initial retrieval based on the question.</li>
                    <li>Analyst drafts an answer.</li>
                    <li>Evidence Agent retrieves supporting passages for the draft.</li>
                    <li>Critic reviews the answer against evidence.</li>
                    <li>Report Agent produces a final structured report.</li>
                </ol>
                This adds verification and reduces hallucinations, but may be slower and
                occasionally over‑filters valid information.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.header("Model Configuration")
    st.markdown(
        """
        - **LLM Provider:** Groq (`openai/gpt-oss-20b`)
        - **Embedding Model:** Ollama (`nomic-embed-text`)
        - **Vector DB:** ChromaDB (persistent)
        - **Paper:** Self-Healing.pdf
        """
    )