import streamlit as st
import json
import time
from auditor import WebsiteAuditor
from scoring import calculate_final_score, AUDIT_CRITERIA
from report import generate_report_html

st.set_page_config(
    page_title="AI/SEO Audit Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main-title {
        font-family: 'Space Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f1117;
        letter-spacing: -1px;
        margin-bottom: 0;
    }

    .subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-top: 4px;
        margin-bottom: 2rem;
    }

    .score-card {
        background: linear-gradient(135deg, #0f1117 0%, #1e2330 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        color: white;
        margin-bottom: 1.5rem;
    }

    .score-number {
        font-family: 'Space Mono', monospace;
        font-size: 4rem;
        font-weight: 700;
        line-height: 1;
    }

    .score-label {
        font-size: 0.85rem;
        opacity: 0.6;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.5rem;
    }

    .criteria-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        background: white;
    }

    .criteria-name {
        font-weight: 600;
        font-size: 0.95rem;
        color: #0f1117;
    }

    .criteria-score {
        font-family: 'Space Mono', monospace;
        font-weight: 700;
    }

    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .badge-high { background: #fee2e2; color: #991b1b; }
    .badge-medium { background: #fef3c7; color: #92400e; }
    .badge-low { background: #d1fae5; color: #065f46; }

    .finding-item {
        padding: 0.6rem 0.8rem;
        border-left: 3px solid #e5e7eb;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
        color: #374151;
        background: #f9fafb;
        border-radius: 0 8px 8px 0;
    }

    .finding-pass { border-left-color: #10b981; }
    .finding-fail { border-left-color: #ef4444; }
    .finding-warn { border-left-color: #f59e0b; }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
    }

    .info-box {
        background: #f0f4ff;
        border: 1px solid #c7d2fe;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        font-size: 0.875rem;
        color: #3730a3;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def render_score_badge(score: float) -> str:
    if score >= 80:
        colour = "#10b981"
        label = "Good"
    elif score >= 50:
        colour = "#f59e0b"
        label = "Needs Work"
    else:
        colour = "#ef4444"
        label = "Poor"
    return f'<span style="color:{colour}; font-weight:600;">{score:.0f}/100 — {label}</span>'


def render_priority_badge(priority: str) -> str:
    classes = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}
    cls = classes.get(priority, "badge-low")
    return f'<span class="badge {cls}">{priority} Priority</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    import os
    openai_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    st.markdown("---")

    st.markdown("### 🎯 Audit Scope")
    selected_criteria = {}
    for key, meta in AUDIT_CRITERIA.items():
        selected_criteria[key] = st.checkbox(
            f"{meta['icon']} {meta['label']}",
            value=True,
            help=f"Priority: {meta['priority']} | Weight: {meta['weight']}",
        )

    st.markdown("---")
    st.markdown("### 📖 Weight Guide")
    st.caption("Scores are weighted by priority:")
    for key, meta in AUDIT_CRITERIA.items():
        st.caption(f"**{meta['label']}** — weight {meta['weight']}x ({meta['priority']})")


# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🔍 AI/SEO Audit</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Automated website analysis powered by OpenAI</p>', unsafe_allow_html=True)

url_input = st.text_input(
    "Website URL",
    placeholder="https://example.com",
    label_visibility="collapsed",
)

col_btn, col_info = st.columns([1, 4])
with col_btn:
    run_audit = st.button("Run Audit →", type="primary", use_container_width=True)
with col_info:
    st.markdown(
        '<div class="info-box">Enter a full URL including <code>https://</code>. '
        "The audit fetches your page, analyses HTML, checks for structured data, "
        "ARIA usage, LLMs.txt, and more — then scores each category using GPT-4o.</div>",
        unsafe_allow_html=True,
    )

if run_audit:
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        st.stop()
    if not url_input:
        st.error("Please enter a URL to audit.")
        st.stop()

    active_criteria = [k for k, v in selected_criteria.items() if v]
    if not active_criteria:
        st.error("Please select at least one audit criterion.")
        st.stop()

    auditor = WebsiteAuditor(openai_key)

    with st.spinner("Fetching website..."):
        fetch_result = auditor.fetch_page(url_input)

    if not fetch_result["success"]:
        st.error(f"Could not fetch the URL: {fetch_result['error']}")
        st.stop()

    st.success(f"Fetched **{url_input}** — {fetch_result['size_kb']:.1f} KB, "
               f"status {fetch_result['status_code']}")

    results = {}
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, criterion_key in enumerate(active_criteria):
        meta = AUDIT_CRITERIA[criterion_key]
        status_text.text(f"Analysing: {meta['label']}...")
        result = auditor.analyse_criterion(
            criterion_key, fetch_result["html"], fetch_result["url"]
        )
        results[criterion_key] = result
        progress_bar.progress((i + 1) / len(active_criteria))
        time.sleep(0.1)

    status_text.empty()
    progress_bar.empty()

    final = calculate_final_score(results, active_criteria)

    # ── Results layout ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## Audit Results")

    col_score, col_meta = st.columns([1, 2])

    with col_score:
        grade_colour = (
            "#10b981" if final["weighted_score"] >= 80
            else "#f59e0b" if final["weighted_score"] >= 50
            else "#ef4444"
        )
        st.markdown(f"""
        <div class="score-card">
            <div class="score-number" style="color:{grade_colour};">{final['weighted_score']:.0f}</div>
            <div class="score-label">Overall Score / 100</div>
            <div style="margin-top:1rem; font-size:0.9rem; opacity:0.8;">
                Grade: <strong>{final['grade']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_meta:
        st.markdown(f"**URL Audited:** `{url_input}`")
        st.markdown(f"**Criteria Checked:** {len(active_criteria)}")
        st.markdown(f"**Raw Average:** {final['raw_average']:.1f}/100")
        st.markdown(f"**Weighted Score:** {final['weighted_score']:.1f}/100")

        passed = sum(1 for r in results.values() if r.get("score", 0) >= 70)
        st.markdown(f"**Passed (≥70):** {passed}/{len(active_criteria)} criteria")

    # ── Per-criterion breakdown ────────────────────────────────────────────────
    st.markdown("### Criteria Breakdown")

    for key, result in results.items():
        meta = AUDIT_CRITERIA[key]
        score = result.get("score", 0)
        with st.expander(
            f"{meta['icon']} {meta['label']} — {score:.0f}/100",
            expanded=(score < 70),
        ):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(
                    f"{render_priority_badge(meta['priority'])} "
                    f"&nbsp; Weight: **{meta['weight']}x**",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Summary:** {result.get('summary', 'No summary available.')}")
            with c2:
                st.metric("Score", f"{score:.0f}/100")

            findings = result.get("findings", [])
            if findings:
                st.markdown("**Findings:**")
                for f in findings:
                    status = f.get("status", "info")
                    icon = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
                    css_class = f"finding-{status}" if status in ("pass","fail","warn") else "finding-warn"
                    st.markdown(
                        f'<div class="finding-item {css_class}">{icon} {f["message"]}</div>',
                        unsafe_allow_html=True,
                    )

            recs = result.get("recommendations", [])
            if recs:
                st.markdown("**Recommendations:**")
                for r in recs:
                    st.markdown(f"- {r}")

    # ── Download report ────────────────────────────────────────────────────────
    st.markdown("---")
    report_html = generate_report_html(url_input, final, results, AUDIT_CRITERIA)
    st.download_button(
        label="⬇️ Download HTML Report",
        data=report_html,
        file_name="seo_audit_report.html",
        mime="text/html",
        type="secondary",
    )

    # Store in session for re-use
    st.session_state["last_results"] = results
    st.session_state["last_final"] = final
    st.session_state["last_url"] = url_input
