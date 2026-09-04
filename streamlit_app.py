import os
import requests
from html import escape
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="ResearchPilot",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------
# Custom SVG Definitions
# ------------------------------
SVG_LOGO = """
<svg width="38" height="38" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="42" height="42" rx="12" fill="url(#logo-grad)"/>
  <path d="M12 21L28 13L22 29L19 23L12 21Z" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M19 23L28 13" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round"/>
  <defs>
    <linearGradient id="logo-grad" x1="0" y1="0" x2="42" y2="42" gradientUnits="userSpaceOnUse">
      <stop stop-color="#38BDF8"/>
      <stop offset="1" stop-color="#0284C7"/>
    </linearGradient>
  </defs>
</svg>
"""

SVG_RAG = """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="rgba(56, 189, 248, 0.15)"/>
</svg>
"""

SVG_PIPELINE = """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 22S20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" stroke="#2DD4BF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="rgba(45, 212, 191, 0.15)"/>
  <path d="M9 12L11 14L15 10" stroke="#2DD4BF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

SVG_AGENT = """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="6" width="18" height="13" rx="4" stroke="#C084FC" stroke-width="2" fill="rgba(192, 132, 252, 0.15)"/>
  <circle cx="8.5" cy="11.5" r="1.5" fill="#C084FC"/>
  <circle cx="15.5" cy="11.5" r="1.5" fill="#C084FC"/>
  <path d="M9 15.5C9.5 16 11 16.5 12 16.5C13 16.5 14.5 16 15 15.5" stroke="#C084FC" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M12 2V6" stroke="#C084FC" stroke-width="2" stroke-linecap="round"/>
</svg>
"""

# ------------------------------
# Modern Custom Styling
# ------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600;700&display=swap');

    :root {
        --bg: #0B1120;
        --surface: #1E293B;
        --surface-card: #151F32;
        --border: #334155;
        --text: #F8FAFC;
        --muted: #94A3B8;
        --primary: #38BDF8;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
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

    /* Modernized Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1120 0%, #151F32 100%) !important;
        border-right: 1px solid var(--border) !important;
    }

    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.25rem;
    }
    .sidebar-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #F8FAFC;
        line-height: 1.1;
    }
    .sidebar-sub {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        color: #38BDF8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 3px;
    }

    /* Top Banner Header */
    .rp-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.9rem 1.3rem;
        background: linear-gradient(90deg, #1E293B 0%, #0F111A 100%);
        border: 1px solid var(--border);
        border-radius: 14px;
        margin-bottom: 1.2rem;
    }
    .rp-title-wrap {
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }
    .rp-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .rp-badge-online {
        background: rgba(20, 184, 166, 0.12);
        color: #2DD4BF;
        border: 1px solid #14B8A6;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.65rem;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* Cards */
    .rp-card {
        background: var(--surface-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
    }
    .rp-evidence-card {
        background: rgba(20, 184, 166, 0.08);
        border: 1px solid #14B8A6;
        border-radius: 9px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.65rem;
    }
    .rp-step-card {
        background: rgba(168, 85, 247, 0.08);
        border: 1px solid #A855F7;
        border-radius: 9px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.65rem;
    }
    .rp-meta-teal {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #2DD4BF;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .rp-meta-purple {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        color: #C084FC;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    .rp-text {
        font-size: 0.92rem;
        color: #E2E8F0;
        line-height: 1.5;
    }

    /* Custom Radio Option Cards */
    div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.85rem !important;
        margin-bottom: 0.45rem !important;
        transition: all 0.2s ease;
    }
    div[role="radiogroup"] label:hover {
        background: rgba(56, 189, 248, 0.08) !important;
        border-color: #38BDF8 !important;
    }

    /* Custom Chat Styling */
    [data-testid="stChatMessage"] {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------
# API Helpers
# ------------------------------
def check_api_health() -> bool:
    try:
        res = requests.get(f"{API_URL}/", timeout=3)
        return res.status_code == 200
    except Exception:
        return False


def fetch_papers():
    try:
        res = requests.get(f"{API_URL}/papers", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []


def fetch_traces(limit: int = 50):
    try:
        res = requests.get(f"{API_URL}/traces?limit={limit}", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []


def upload_paper_api(uploaded_file):
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    res = requests.post(f"{API_URL}/papers/upload", files=files, timeout=60)
    if res.status_code == 201:
        return res.json()
    else:
        st.error(f"Upload failed: {res.text}")
        return None


def ask_api(paper_id: str, question: str, mode: str):
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
    for item in evidence:
        page = item.get("page", "?")
        section = item.get("section", "Unknown")
        text = item.get("text", "")
        st.html(
            f"""
            <div class="rp-evidence-card">
                <div class="rp-meta-teal">Page {escape(str(page))} &nbsp;·&nbsp; {escape(str(section))}</div>
                <div class="rp-text">{escape(str(text))}</div>
            </div>
            """
        )


def render_agent_steps(steps):
    for step in steps:
        turn = step.get("turn", "?")
        tool = step.get("tool", "")
        args = step.get("args", {})
        query = args.get("query", "")
        results_count = step.get("results_count", 0)

        st.html(
            f"""
            <div class="rp-step-card">
                <div class="rp-meta-purple">Turn {turn} &nbsp;·&nbsp; Tool: <code>{escape(tool)}</code> &nbsp;·&nbsp; {results_count} chunks retrieved</div>
                <div class="rp-text"><b>Query:</b> "{escape(query)}"</div>
            </div>
            """
        )



def render_mermaid(mermaid_code: str, height: int = 400):
    st.html(
        f"""
        <div style="display:flex;justify-content:center;background:#1E293B;padding:1rem;border-radius:10px;border:1px solid #334155;height:{height}px;">
            <pre class="mermaid" style="margin:0;">
{mermaid_code}
            </pre>
        </div>
        <script type="module">
          import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
          mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose'
          }});
        </script>
        """
    )



# ------------------------------
# Top Header Banner
# ------------------------------
is_online = check_api_health()
status_badge = (
    '<span class="rp-badge-online">🟢 FastAPI Backend Online</span>'
    if is_online
    else '<span class="rp-badge-online" style="color:#EF4444;border-color:#EF4444;background:rgba(239,68,68,0.15)">🔴 Backend Offline</span>'
)

st.html(
    f"""
    <div class="rp-header">
        <div class="rp-title-wrap">
            {SVG_LOGO}
            <div>
                <div class="rp-title">ResearchPilot</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#94A3B8;">Evidence-Grounded AI Research Assistant</div>
            </div>
        </div>
        <div>{status_badge}</div>
    </div>
    """
)

# ------------------------------
# Sidebar Navigation
# ------------------------------
with st.sidebar:
    st.html(
        f"""
        <div class="sidebar-header">
            {SVG_LOGO}
            <div>
                <div class="sidebar-title">ResearchPilot</div>
                <div class="sidebar-sub">AI Research Engine</div>
            </div>
        </div>
        """
    )

    nav_page = st.radio(
        "Navigation Menu",
        ["💬 Research Chat", "📚 Paper Registry", "⚡ Observability & Tracing", "ℹ️ Architecture & About"],
        label_visibility="collapsed",
    )

    st.divider()

    if nav_page == "💬 Research Chat":
        st.markdown("**Select Answering Engine**")

        mode = st.radio(
            "Answering Engine Mode",
            ["rag", "pipeline", "agent"],
            format_func=lambda x: {
                "rag": "⚡ RAG (Hybrid Retrieval)",
                "pipeline": "🛡️ Pipeline (Multi-Agent)",
                "agent": "🤖 Native Tool Agent",
            }[x],
            label_visibility="collapsed",
        )

        mode_svg = SVG_RAG if mode == 'rag' else (SVG_PIPELINE if mode == 'pipeline' else SVG_AGENT)
        mode_title = 'RAG Mode' if mode == 'rag' else ('Pipeline Mode' if mode == 'pipeline' else 'Agent Mode')
        mode_desc = 'Combines dense vector search + BM25 keyword matching with RRF fusion.' if mode == 'rag' else ('4-agent verification workflow: Analyst → Evidence → Critic → Report.' if mode == 'pipeline' else 'Autonomous Groq tool-calling agent with iterative search loop.')

        st.html(
            f"""
            <div style="background:rgba(15,23,42,0.6);border:1px solid #334155;border-radius:10px;padding:0.75rem;margin-top:0.75rem;">
                <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.25rem;">
                    {mode_svg}
                    <span style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:0.88rem;color:#F8FAFC;">
                        {mode_title}
                    </span>
                </div>
                <div style="font-size:0.78rem;color:#94A3B8;line-height:1.4;">
                    {mode_desc}
                </div>
            </div>
            """
        )
    else:
        mode = "rag"


# ------------------------------
# View 1: 💬 Research Chat
# ------------------------------
if nav_page == "💬 Research Chat":
    papers = fetch_papers()

    c_left, c_right = st.columns([3, 1])

    with c_left:
        st.subheader("1. Paper Selection")
        paper_options = {p["id"]: f"📄 {p['title']} ({p['filename']})" for p in papers}

        selected_paper_id = None
        if paper_options:
            selected_paper_id = st.selectbox(
                "Select active paper collection:",
                options=list(paper_options.keys()),
                format_func=lambda x: paper_options[x],
            )
        else:
            st.info("No papers registered yet. Upload a PDF paper below to get started!")

    with c_right:
        st.subheader("Upload Paper")
        with st.popover("➕ Add New PDF"):
            uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])
            if uploaded_file is not None:
                if st.button("Ingest & Index Paper", type="primary"):
                    with st.spinner("Parsing layout, extracting tables, and storing vector embeddings..."):
                        res = upload_paper_api(uploaded_file)
                        if res:
                            st.success(f"Ingested {res['chunk_count']} chunks from {res['filename']}!")
                            st.session_state.messages = []
                            st.rerun()

    if selected_paper_id:
        active_paper = next((p for p in papers if p["id"] == selected_paper_id), None)
        if active_paper:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Indexed Chunks", active_paper.get("chunk_count", 0))
            m2.metric("Questions Asked", len([m for m in st.session_state.get("messages", []) if m["role"] == "user"]))
            m3.metric("Selected Mode", {"rag": "⚡ RAG", "pipeline": "🛡️ Pipeline", "agent": "🤖 Agent"}[mode])
            m4.metric("Paper ID", selected_paper_id[:8] + "...")

        st.divider()
        st.subheader("2. Evidence-Grounded Conversation")

        st.session_state.setdefault("messages", [])

        # Render message history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("evidence"):
                    with st.expander("📚 Evidence Chunks Used"):
                        render_evidence(msg["evidence"])
                if msg.get("steps"):
                    with st.expander("🛠️ Native Tool Call Trace"):
                        render_agent_steps(msg["steps"])

        question = st.chat_input("Ask a question about the active paper...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner(f"Querying backend via {mode.upper()} mode..."):
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
                        with st.expander("📚 Evidence Chunks Used"):
                            render_evidence(evidence)

                    if steps:
                        with st.expander("🛠️ Native Tool Call Trace"):
                            render_agent_steps(steps)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "evidence": evidence,
                        "steps": steps,
                    })

# ------------------------------
# View 2: 📚 Paper Registry
# ------------------------------
elif nav_page == "📚 Paper Registry":
    st.header("📚 Registered Research Papers")
    st.write("SQLite Metadata Registry & ChromaDB Collections")

    papers = fetch_papers()

    if papers:
        st.dataframe(
            papers,
            column_config={
                "id": "Paper ID",
                "title": "Title",
                "filename": "File Name",
                "chunk_count": "Chunk Count",
                "created_at": "Ingested At",
            },
            hide_index=True,
        )
    else:
        st.info("No papers currently registered in SQLite database.")

# ------------------------------
# View 3: ⚡ Observability & Tracing
# ------------------------------
elif nav_page == "⚡ Observability & Tracing":
    st.header("⚡ Observability & Execution Tracing")
    st.write("Real-time execution duration, parameters, and status logged in SQLite (`traces` table)")

    traces = fetch_traces(limit=50)

    if traces:
        t_total = len(traces)
        t_success = len([t for t in traces if t["status"] == "success"])
        t_error = len([t for t in traces if t["status"] == "error"])
        avg_dur = sum([t["duration_ms"] for t in traces]) / t_total if t_total > 0 else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spans Traced", t_total)
        c2.metric("Success Rate", f"{(t_success / t_total * 100):.1f}%" if t_total > 0 else "N/A")
        c3.metric("Failed Spans", t_error)
        c4.metric("Avg Latency", f"{avg_dur:.1f} ms")

        st.divider()
        st.subheader("Trace Spans Table")

        table_data = []
        for t in traces:
            table_data.append({
                "Timestamp": t.get("timestamp", "")[:19].replace("T", " "),
                "Span Name": t.get("name", ""),
                "Duration (ms)": t.get("duration_ms", 0.0),
                "Status": "✅ Success" if t.get("status") == "success" else "❌ Error",
                "ID": t.get("id", "")[:8],
            })

        st.dataframe(table_data, hide_index=True)

        with st.expander("🔍 Inspect Full Trace Spans JSON"):
            st.json(traces)
    else:
        st.info("No execution traces logged yet. Ask questions in the chat to record execution spans!")

# ------------------------------
# View 4: ℹ️ Architecture & About
# ------------------------------
elif nav_page == "ℹ️ Architecture & About":
    st.header("ℹ️ Architecture & System Design")

    c_r, c_p, c_a = st.columns(3)
    with c_r:
        st.html(
            f"""
            <div class="rp-card">
                <div style="display:flex;align-items:center;gap:0.5rem;">{SVG_RAG}<b>RAG Mode</b></div>
                <div style="font-size:0.85rem;color:#94A3B8;margin-top:0.4rem;">Dense vector search + BM25 keyword matching fused via Reciprocal Rank Fusion.</div>
            </div>
            """
        )
    with c_p:
        st.html(
            f"""
            <div class="rp-card">
                <div style="display:flex;align-items:center;gap:0.5rem;">{SVG_PIPELINE}<b>Pipeline Mode</b></div>
                <div style="font-size:0.85rem;color:#94A3B8;margin-top:0.4rem;">Deterministic 4-agent verification loop ensuring zero hallucinated claims.</div>
            </div>
            """
        )
    with c_a:
        st.html(
            f"""
            <div class="rp-card">
                <div style="display:flex;align-items:center;gap:0.5rem;">{SVG_AGENT}<b>Agent Mode</b></div>
                <div style="font-size:0.85rem;color:#94A3B8;margin-top:0.4rem;">Groq native function-calling agent with autonomous multi-turn reasoning loops.</div>
            </div>
            """
        )


    st.subheader("🤖 Native Tool-Calling Agent Loop")
    render_mermaid(
        """
flowchart TD
    A[User Query] --> B[Groq Agent Executor]
    B -->|Function Call: search_paper| C[Hybrid Retrieval Engine]
    C -->|Dense + Sparse Fusion| D[ChromaDB & BM25 Index]
    D -->|Evidence Chunks| B
    B -->|Iterate until satisfied| E[Final Answer + Citations]
""",
        height=380,
    )