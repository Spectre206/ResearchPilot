import os
import requests
from html import escape
import streamlit as st
import streamlit.components.v1 as components

API_URL = os.getenv("API_URL", "http://localhost:8000")

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
        --purple: #7C3AED;
        --purple-bg: #211538;
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
    .rp-card.accent-purple { border-left: 3px solid var(--purple); }

    .rp-evidence-card {
        background: var(--teal-bg);
        border: 1px solid var(--teal);
        border-radius: 9px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.55rem;
    }
    .rp-step-card {
        background: var(--purple-bg);
        border: 1px solid var(--purple);
        border-radius: 9px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.55rem;
    }
    .rp-meta {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #8AE0D6;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .rp-meta-purple {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #C084FC;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .rp-text {
        font-size: 0.9rem;
        color: var(--text);
        line-height: 1.5;
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
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------
# API Helper Functions
# ------------------------------
def fetch_papers():
    """Fetch registered papers from backend API."""
    try:
        res = requests.get(f"{API_URL}/papers", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []


def upload_paper_api(uploaded_file):
    """Upload PDF file to backend API."""
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    res = requests.post(f"{API_URL}/papers/upload", files=files, timeout=60)
    if res.status_code == 201:
        return res.json()
    else:
        st.error(f"Upload failed: {res.text}")
        return None


def ask_api(paper_id: str, question: str, mode: str):
    """Query FastAPI backend using selected mode."""
    if mode == "agent":
        res = requests.post(
            f"{API_URL}/ask-agent",
            json={"paper_id": paper_id, "question": question},
            timeout=120,
        )
    else:
        res = requests.post(
            f"{API_URL}/ask",
            json={"paper_id": paper_id, "question": question, "mode": mode},
            timeout=120,
        )

    if res.status_code == 200:
        return res.json()
    else:
        st.error(f"Error ({res.status_code}): {res.text}")
        return None


def render_evidence(evidence):
    """Render evidence items as formatted cards."""
    for item in evidence:
        page = item.get("page", "?")
        section = item.get("section", "Unknown")
        text = item.get("text", "")
        st.markdown(
            f"""
            <div class="rp-evidence-card">
                <div class="rp-meta">Page {escape(str(page))} &nbsp;·&nbsp; {escape(str(section))}</div>
                <div class="rp-text">{escape(str(text))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_agent_steps(steps):
    """Render agent tool-calling execution steps."""
    for step in steps:
        turn = step.get("turn", "?")
        tool = step.get("tool", "")
        args = step.get("args", {})
        query = args.get("query", "")
        results_count = step.get("results_count", 0)

        st.markdown(
            f"""
            <div class="rp-step-card">
                <div class="rp-meta-purple">Turn {turn} &nbsp;·&nbsp; Tool: <code>{escape(tool)}</code> &nbsp;·&nbsp; {results_count} chunks retrieved</div>
                <div class="rp-text"><b>Query:</b> "{escape(query)}"</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_mermaid(mermaid_code: str, height: int = 500):
    """Render a centered Mermaid diagram."""
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

    page = st.radio(
        "Navigation",
        ["Chat", "About"],
        label_visibility="collapsed",
        key="nav_radio",
    )

    if page == "Chat":
        st.markdown("---")
        st.markdown("**Answer Mode**")
        mode = st.radio(
            "Select mode",
            ["rag", "pipeline", "agent"],
            format_func=lambda x: {
                "rag": "⚡ RAG (Fast)",
                "pipeline": "🛡️ Pipeline (Verified)",
                "agent": "🤖 Agent (Tool Calling)",
            }[x],
            label_visibility="collapsed",
            key="mode_radio",
        )
    else:
        mode = None


# ------------------------------
# Chat Page
# ------------------------------
if page == "Chat":
    st.title("Chat with Research Papers")

    # Fetch available papers from backend
    papers = fetch_papers()

    st.subheader("1. Select or Upload Paper")
    paper_options = {p["id"]: f"{p['title']} ({p['filename']})" for p in papers}

    selected_paper_id = None
    if paper_options:
        selected_paper_id = st.selectbox(
            "Select registered paper:",
            options=list(paper_options.keys()),
            format_func=lambda x: paper_options[x],
            key="paper_select",
        )

    with st.expander("➕ Upload a New Paper PDF"):
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="pdf_uploader")
        if uploaded_file is not None:
            if st.button("Ingest Paper"):
                with st.spinner("Uploading and indexing paper via FastAPI backend..."):
                    result = upload_paper_api(uploaded_file)
                    if result:
                        st.success(f"Ingested {result['chunk_count']} chunks from {result['filename']}")
                        st.session_state.messages = []
                        st.rerun()

    if selected_paper_id:
        active_paper = next((p for p in papers if p["id"] == selected_paper_id), None)
        if active_paper:
            c1, c2, c3 = st.columns(3)
            c1.metric("Chunks indexed", active_paper.get("chunk_count", 0))
            c2.metric("Questions asked", len([m for m in st.session_state.get("messages", []) if m["role"] == "user"]))
            c3.metric(
                "Mode",
                {"rag": "RAG", "pipeline": "Pipeline", "agent": "Agent"}[mode],
            )

        st.session_state.setdefault("messages", [])

        # Display history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("evidence"):
                    with st.expander("📚 Evidence used"):
                        render_evidence(msg["evidence"])
                if msg.get("steps"):
                    with st.expander("🛠️ Agent Tool Calls"):
                        render_agent_steps(msg["steps"])

        question = st.chat_input("Ask a question about the selected paper…")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner(f"Generating answer using {mode.upper()} mode..."):
                    api_resp = ask_api(selected_paper_id, question, mode)

                if api_resp:
                    answer = ""
                    evidence = None
                    steps = None

                    if mode == "rag":
                        answer = api_resp.get("answer", "")
                    elif mode == "pipeline":
                        pipeline_res = api_resp.get("result", {})
                        answer = pipeline_res.get("answer", "")
                        evidence = pipeline_res.get("evidence", [])
                    elif mode == "agent":
                        answer = api_resp.get("answer", "")
                        steps = api_resp.get("steps", [])

                    st.markdown(answer)

                    if evidence:
                        with st.expander("📚 Evidence used"):
                            render_evidence(evidence)

                    if steps:
                        with st.expander("🛠️ Agent Tool Calls"):
                            render_agent_steps(steps)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "evidence": evidence,
                        "steps": steps,
                    })

    else:
        st.info("No paper selected. Please select or upload a PDF paper above to get started.")


# ------------------------------
# About Page
# ------------------------------
elif page == "About":
    st.title("About ResearchPilot")

    st.markdown(
        """
        <div class="rp-card">
        ResearchPilot is an evidence-grounded AI research assistant with FastAPI web backend supporting:
        <ul>
            <li><b>Retrieval-Augmented Generation (RAG)</b></li>
            <li><b>Multi-agent verification pipeline</b> (Analyst → Evidence → Critic → Report)</li>
            <li><b>Native Tool-Calling Agent</b> via Groq function calling</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.header("Architecture")

    st.subheader("🤖 Native Tool-Calling Agent Mode")
    render_mermaid(
        """
flowchart TD
    A[User Question] --> B[Groq Agent Executor]
    B -->|Tool Call: search_paper| C[ChromaDB Multi-Paper Collection]
    C -->|Retrieved Chunks| B
    B -->|Iterate until complete| D[Final Grounded Answer with Citations]
""",
        height=500,
    )