"""
app.py  ─  AI Resume Analyzer
──────────────────────────────
Main Streamlit application entry-point.

Run locally:
    streamlit run app.py
"""

from blob_storage import upload_to_blob
# ── Standard library ──────────────────────────────────────────────────────
import time

# ── Third-party ───────────────────────────────────────────────────────────
import streamlit as st
from dotenv import load_dotenv

# ── Local modules ─────────────────────────────────────────────────────────
from pdf_reader import extract_resume_text, get_pdf_metadata
from analyzer import (
    analyze_resume,
    get_score_color,
    get_score_label,
    get_priority_color,
)

# Load .env early so env-vars are available everywhere
load_dotenv()


# ══════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG  (must be the FIRST Streamlit call)
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════════════
#  CUSTOM CSS  — polished dark theme
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Font ──────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Root variables ───────────────────────────────────────────────────── */
:root {
    --bg:        #0d1117;
    --surface:   #161b22;
    --border:    #30363d;
    --accent:    #58a6ff;
    --accent2:   #3fb950;
    --text:      #e6edf3;
    --muted:     #8b949e;
    --danger:    #f85149;
    --warning:   #d29922;
    --radius:    12px;
    --font:      'DM Sans', sans-serif;
    --mono:      'DM Mono', monospace;
}

/* ── Global resets ────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: var(--font) !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Main area ────────────────────────────────────────────────────────── */
.main .block-container {
    padding: 2rem 3rem;
    max-width: 1100px;
}

/* ── Header ───────────────────────────────────────────────────────────── */
.app-header {
    text-align: center;
    padding: 2.5rem 0 1rem;
}
.app-header h1 {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff 0%, #3fb950 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.4rem;
}
.app-header p {
    color: var(--muted);
    font-size: 1.1rem;
}

/* ── Upload card ──────────────────────────────────────────────────────── */
.upload-card {
    background: var(--surface);
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    margin: 1.5rem 0;
    transition: border-color .3s;
}
.upload-card:hover { border-color: var(--accent); }

/* ── Metric card ──────────────────────────────────────────────────────── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem 1.5rem;
    text-align: center;
    height: 100%;
}
.metric-card .label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--muted);
    margin-bottom: .4rem;
}
.metric-card .value {
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--accent);
}

/* ── Score ring ───────────────────────────────────────────────────────── */
.score-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    margin: 1.5rem 0;
}
.score-ring {
    width: 160px;
    height: 160px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.6rem;
    font-weight: 700;
    margin-bottom: 1rem;
    box-shadow: 0 0 30px rgba(88,166,255,.2);
}
.score-label {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: .3rem;
}
.score-summary {
    color: var(--muted);
    font-size: 0.9rem;
    text-align: center;
    max-width: 500px;
}

/* ── Section header ───────────────────────────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: .6rem;
    font-size: 1.2rem;
    font-weight: 600;
    margin: 1.8rem 0 .8rem;
    padding-bottom: .5rem;
    border-bottom: 1px solid var(--border);
}

/* ── Skill pill ───────────────────────────────────────────────────────── */
.skill-pill {
    display: inline-block;
    background: rgba(88,166,255,.12);
    border: 1px solid rgba(88,166,255,.3);
    color: var(--accent);
    padding: .3rem .8rem;
    border-radius: 999px;
    font-size: .82rem;
    font-weight: 500;
    margin: .2rem .15rem;
}
.missing-pill {
    background: rgba(248,81,73,.10);
    border-color: rgba(248,81,73,.3);
    color: var(--danger);
}
.strength-pill {
    background: rgba(63,185,80,.10);
    border-color: rgba(63,185,80,.3);
    color: var(--accent2);
}

/* ── Experience card ──────────────────────────────────────────────────── */
.exp-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 1rem 1.3rem;
    margin-bottom: .8rem;
}
.exp-card .exp-title {
    font-weight: 600;
    font-size: 1rem;
}
.exp-card .exp-meta {
    font-size: .82rem;
    color: var(--muted);
    margin: .15rem 0 .4rem;
}
.exp-card .exp-impact {
    font-size: .88rem;
    color: var(--text);
}

/* ── Priority badge ───────────────────────────────────────────────────── */
.priority-badge {
    display: inline-block;
    padding: .15rem .55rem;
    border-radius: 999px;
    font-size: .72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .05em;
}

/* ── Suggestion card ──────────────────────────────────────────────────── */
.suggestion-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin-bottom: .65rem;
    display: flex;
    gap: .9rem;
    align-items: flex-start;
}
.suggestion-card .icon { font-size: 1.3rem; }
.suggestion-card .content .cat {
    font-size: .75rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-bottom: .2rem;
}
.suggestion-card .content .text { font-size: .92rem; }

/* ── Career card ──────────────────────────────────────────────────────── */
.career-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.4rem;
    margin-bottom: .7rem;
}
.career-card .role {
    font-weight: 600;
    font-size: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.career-card .reason { font-size: .86rem; color: var(--muted); margin-top: .3rem; }
.match-pct {
    font-size: .82rem;
    font-weight: 600;
    color: var(--accent2);
    background: rgba(63,185,80,.12);
    border: 1px solid rgba(63,185,80,.3);
    padding: .15rem .5rem;
    border-radius: 999px;
}

/* ── Progress bar ─────────────────────────────────────────────────────── */
.prog-bar-wrap { margin: .4rem 0 .9rem; }
.prog-label {
    display: flex;
    justify-content: space-between;
    font-size: .8rem;
    color: var(--muted);
    margin-bottom: .2rem;
}
.prog-bar {
    height: 8px;
    background: var(--border);
    border-radius: 999px;
    overflow: hidden;
}
.prog-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transition: width .8s ease;
}

/* ── ATS tip ──────────────────────────────────────────────────────────── */
.ats-tip {
    padding: .65rem 1rem;
    background: rgba(210,153,34,.07);
    border-left: 3px solid var(--warning);
    border-radius: 0 var(--radius) var(--radius) 0;
    font-size: .88rem;
    margin-bottom: .5rem;
}

/* ── Streamlit widget overrides ───────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg,#58a6ff,#3fb950) !important;
    color: #0d1117 !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: .6rem 1.8rem !important;
    font-size: 1rem !important;
    cursor: pointer;
    transition: opacity .2s;
    width: 100%;
}
.stButton > button:hover { opacity: .88 !important; }

[data-testid="stFileUploader"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
}

div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}

.stSpinner > div { border-top-color: var(--accent) !important; }

/* Scrollbar ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Divider ────────────────────────────────────────────────────────────── */
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📄 AI Resume Analyzer")
    st.markdown("---")

    st.markdown("""
    ### How it works
    1. 📂 Upload your PDF resume
    2. 🎯 (Optional) Enter target role
    3. 🔍 Click **Analyze Resume**
    4. 📊 Review detailed feedback
    """)

    st.markdown("---")
    st.markdown("### 🛠️ Tech Stack")
    for tech in ["Python 3.10+", "Streamlit", "Groq AI (Llama 3)",
                 "pdfplumber", "PyPDF2", "python-dotenv"]:
        st.markdown(f"- {tech}")

    st.markdown("---")
    st.markdown("### 📌 Tips for best results")
    st.info(
        "✅ Use a text-based PDF (not scanned)\n\n"
        "✅ Include all sections: Skills, Experience, Education\n\n"
        "✅ Enter your target job role for tailored keywords"
    )

    st.markdown("---")
    st.markdown(
        "<small style='color:#8b949e'>Built with ❤️ using Azure OpenAI & Streamlit</small>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════
#  MAIN HEADER
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
    <h1>📄 AI Resume Analyzer</h1>
    <p>Get instant, AI-powered feedback on your resume — score, skills, gaps & career paths</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════
#  INPUT SECTION
# ══════════════════════════════════════════════════════════════════════════
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("#### 📂 Upload Your Resume")
    uploaded_file = st.file_uploader(
        label="Upload PDF",
        type=["pdf"],
        help="Upload a text-based PDF resume. Scanned images are not supported.",
        label_visibility="collapsed",
    )

with col2:
    st.markdown("#### 🎯 Target Job Role *(optional)*")
    job_role = st.text_input(
        label="Target Job Role",
        placeholder="e.g. Software Engineer, Data Scientist, Product Manager…",
        help="Providing a target role gives you tailored keyword suggestions.",
        label_visibility="collapsed",
    )
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🔍 Analyze Resume", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
#  METADATA PREVIEW  (shown once PDF is uploaded, before analysis)
# ══════════════════════════════════════════════════════════════════════════
if uploaded_file is not None and not analyze_btn:
    # ── Read bytes HERE so they're available for both upload & metadata ──
    pdf_bytes = uploaded_file.read()
 
    # ── Upload to Azure Blob Storage ─────────────────────────────────────
    upload_result = upload_to_blob(uploaded_file.name, pdf_bytes)
    if upload_result.startswith("✅"):
        st.sidebar.success(upload_result)
    else:
        st.sidebar.warning(upload_result)
 
    meta = get_pdf_metadata(pdf_bytes)
 
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">📄 File Name</div>
            <div class="value" style="font-size:1rem">{uploaded_file.name}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">📑 Pages</div>
            <div class="value">{meta["page_count"]}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">📝 Word Count</div>
            <div class="value">{meta["word_count"]:,}</div>
        </div>""", unsafe_allow_html=True)
 
    st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════
#  ANALYSIS PIPELINE
# ══════════════════════════════════════════════════════════════════════════
if analyze_btn:
    # ── Guard: file must be uploaded ───────────────────────────────────
    if uploaded_file is None:
        st.error("⚠️ Please upload a PDF resume first.")
        st.stop()

    # ── Read PDF bytes ─────────────────────────────────────────────────
    pdf_bytes = uploaded_file.read()

    # ── Stage 1: Extract text ──────────────────────────────────────────
    with st.spinner("📖 Extracting text from PDF…"):
        try:
            resume_text = extract_resume_text(pdf_bytes)
        except ValueError as e:
            st.error(str(e))
            st.stop()

    # ── Stage 2: AI analysis ───────────────────────────────────────────
    progress_bar = st.progress(0, text="🤖 Sending resume to AI…")
    for pct in range(0, 70, 5):
        time.sleep(0.06)
        progress_bar.progress(pct, text="🤖 AI is reading your resume…")

    try:
        with st.spinner("✨ Analyzing with Azure OpenAI GPT-4…"):
            result = analyze_resume(resume_text, job_role)
    except (EnvironmentError, RuntimeError) as e:
        progress_bar.empty()
        st.error(f"❌ Analysis failed: {e}")
        st.stop()

    for pct in range(70, 101, 5):
        time.sleep(0.04)
        progress_bar.progress(pct, text="📊 Building your report…")
    time.sleep(0.3)
    progress_bar.empty()

    st.success("✅ Analysis complete! Scroll down to see your results.")
    st.markdown("---")

    # ==================================================================
    #  RESULTS
    # ==================================================================

    # ── 1. Score overview ──────────────────────────────────────────────
    score        = result.get("score", 0)
    score_color  = get_score_color(score)
    score_label  = get_score_label(score)
    summary      = result.get("summary", "")
    breakdown    = result.get("score_breakdown", {})

    res_col1, res_col2 = st.columns([1, 2], gap="large")

    with res_col1:
        st.markdown(f"""
        <div class="score-container">
            <div class="score-ring" style="border: 6px solid {score_color};
                                           color: {score_color};">
                {score}
            </div>
            <div class="score-label" style="color:{score_color}">{score_label}</div>
            <div class="score-summary">{summary}</div>
        </div>
        """, unsafe_allow_html=True)

    with res_col2:
        st.markdown('<div class="section-header">📊 Score Breakdown</div>',
                    unsafe_allow_html=True)

        categories = {
            "🎨 Formatting":   breakdown.get("formatting",   0),
            "💡 Skills":       breakdown.get("skills",       0),
            "🏢 Experience":   breakdown.get("experience",   0),
            "🏆 Achievements": breakdown.get("achievements", 0),
            "🔑 Keywords":     breakdown.get("keywords",     0),
        }
        for label, val in categories.items():
            pct = int((val / 20) * 100)
            st.markdown(f"""
            <div class="prog-bar-wrap">
                <div class="prog-label"><span>{label}</span><span>{val}/20</span></div>
                <div class="prog-bar">
                    <div class="prog-fill" style="width:{pct}%"></div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── 2. Detected skills ─────────────────────────────────────────────
    skills = result.get("detected_skills", [])
    if skills:
        st.markdown('<div class="section-header">💡 Detected Skills</div>',
                    unsafe_allow_html=True)
        pills = "".join(
            f'<span class="skill-pill">{s}</span>' for s in skills
        )
        st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)

    # ── 3. Strengths ───────────────────────────────────────────────────
    strengths = result.get("strengths", [])
    if strengths:
        st.markdown('<div class="section-header">✅ Strengths</div>',
                    unsafe_allow_html=True)
        pills = "".join(
            f'<span class="skill-pill strength-pill">✓ {s}</span>' for s in strengths
        )
        st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── 4. Experience highlights ───────────────────────────────────────
    exp_list = result.get("experience_highlights", [])
    if exp_list:
        st.markdown('<div class="section-header">🏢 Experience Highlights</div>',
                    unsafe_allow_html=True)
        for exp in exp_list:
            st.markdown(f"""
            <div class="exp-card">
                <div class="exp-title">{exp.get("title","")}</div>
                <div class="exp-meta">
                    🏢 {exp.get("company","")} &nbsp;·&nbsp;
                    📅 {exp.get("duration","")}
                </div>
                <div class="exp-impact">🎯 {exp.get("impact","")}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── 5. Missing keywords ────────────────────────────────────────────
    missing = result.get("missing_keywords", [])
    if missing:
        st.markdown('<div class="section-header">🔑 Missing Keywords</div>',
                    unsafe_allow_html=True)
        st.caption("Add these to improve ATS matching and recruiter visibility.")
        pills = "".join(
            f'<span class="skill-pill missing-pill">+ {kw}</span>'
            for kw in missing
        )
        st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── 6. Improvement suggestions ─────────────────────────────────────
    suggestions = result.get("improvement_suggestions", [])
    if suggestions:
        st.markdown('<div class="section-header">🔧 Improvement Suggestions</div>',
                    unsafe_allow_html=True)

        # Group by priority for a tidy display
        for priority in ["High", "Medium", "Low"]:
            group = [s for s in suggestions if s.get("priority") == priority]
            if not group:
                continue

            color = get_priority_color(priority)
            with st.expander(
                f"{'🔴' if priority=='High' else '🟡' if priority=='Medium' else '🟢'}"
                f"  {priority} Priority  ({len(group)} items)",
                expanded=(priority == "High"),
            ):
                for sug in group:
                    st.markdown(f"""
                    <div class="suggestion-card">
                        <div class="icon">
                            {"🔴" if priority=="High" else "🟡" if priority=="Medium" else "🟢"}
                        </div>
                        <div class="content">
                            <div class="cat">{sug.get("category","")}</div>
                            <div class="text">{sug.get("suggestion","")}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── 7. Career recommendations ──────────────────────────────────────
    careers = result.get("career_recommendations", [])
    if careers:
        st.markdown('<div class="section-header">🚀 Career Recommendations</div>',
                    unsafe_allow_html=True)
        for career in careers:
            st.markdown(f"""
            <div class="career-card">
                <div class="role">
                    {career.get("role","")}
                    <span class="match-pct">
                        {career.get("match_percent", 0)}% match
                    </span>
                </div>
                <div class="reason">💬 {career.get("reason","")}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── 8. ATS tips ────────────────────────────────────────────────────
    ats_tips = result.get("ats_tips", [])
    if ats_tips:
        st.markdown('<div class="section-header">⚙️ ATS Optimization Tips</div>',
                    unsafe_allow_html=True)
        st.caption("Applicant Tracking Systems scan resumes before a human ever reads them.")
        for tip in ats_tips:
            st.markdown(f'<div class="ats-tip">💡 {tip}</div>',
                        unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;color:#8b949e;font-size:.85rem'>"
        "Analysis powered by Azure OpenAI GPT-4 · Results are AI-generated suggestions"
        "</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════
#  EMPTY STATE  (nothing uploaded yet)
# ══════════════════════════════════════════════════════════════════════════
elif uploaded_file is None:
    st.markdown("""
    <div style="text-align:center; padding:3rem; color:#8b949e">
        <div style="font-size:4rem; margin-bottom:1rem">📄</div>
        <h3 style="color:#e6edf3">Upload your resume to get started</h3>
        <p>Supports text-based PDFs up to 10 MB</p>
    </div>
    """, unsafe_allow_html=True)
