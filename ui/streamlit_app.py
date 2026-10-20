#!/usr/bin/env python3
"""Streamlit product MVP for the Agentic AI Risk Auditor."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.audit_service import audit_public_website, sample_report


SYSTEM_TYPES = {
    "Select a system type": "",
    "Portfolio / brochure website": "",
    "SaaS or e-commerce website (no AI)": "",
    "AI chatbot or copilot": "AI chatbot or copilot that generates user-facing responses.",
    "AI agent or automated workflow": "AI agent that uses tools or automates a multi-step workflow.",
    "AI search, recommendation, or ranking": "AI system that searches, recommends, scores, or ranks results.",
    "AI content generation tool": "AI system that generates text, images, audio, video, or code.",
    "High-impact automated decision system": "AI system that supports or makes decisions affecting people.",
    "Other AI-enabled product": "AI-enabled product or service.",
}


def normalize_risk_score(value: Any) -> float:
    try:
        score = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    if 0 <= score <= 1:
        score *= 100
    return round(max(0.0, min(100.0, score)), 1)


def risk_label(score: float) -> tuple[str, str]:
    if score >= 85:
        return "Critical", "#cf1322"
    if score >= 70:
        return "High", "#d4380d"
    if score >= 30:
        return "Medium", "#d48806"
    return "Low", "#389e0d"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp{background:#f5f7fa}.block-container{max-width:1240px;padding-top:1.25rem;padding-bottom:4rem}
        [data-testid="stHeader"]{background:rgba(245,247,250,.86);backdrop-filter:blur(14px)}
        [data-testid="stForm"],[data-testid="stMetric"],[data-testid="stPlotlyChart"]{background:#fff;border:1px solid #f0f0f0;border-radius:10px;box-shadow:0 1px 2px rgba(0,0,0,.03)}
        [data-testid="stForm"]{padding:1rem 1.25rem 1.25rem}[data-testid="stMetric"]{padding:1rem 1.1rem}
        [data-testid="stMetricLabel"]{color:#667085}[data-testid="stMetricValue"]{font-weight:650;letter-spacing:-.02em}
        [data-testid="stPlotlyChart"]{padding:.35rem}
        .hero{display:flex;justify-content:space-between;align-items:center;gap:2rem;padding:1.15rem 1.35rem;border-radius:10px;background:#fff;border:1px solid #f0f0f0;margin-bottom:1rem;box-shadow:0 1px 2px rgba(0,0,0,.03)}
        .hero .kicker{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#1677ff;font-weight:700}
        .hero h1{font-size:1.65rem;line-height:1.25;margin:.18rem 0 .35rem;letter-spacing:-.025em;color:#1f1f1f}.hero p{color:#667085;font-size:.92rem;line-height:1.5;margin:0}
        .hero-badge{white-space:nowrap;background:#e6f4ff;color:#0958d9;border:1px solid #91caff;border-radius:999px;padding:.42rem .75rem;font-size:.78rem;font-weight:650}
        .report-identity{display:flex;justify-content:space-between;align-items:center;gap:1.5rem;margin:1.5rem 0 1rem;padding:1.25rem 1.4rem;background:#fff;border:1px solid #d9d9d9;border-left:5px solid #1677ff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.04)}
        .identity-eyebrow{font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;color:#1677ff;font-weight:750;margin-bottom:.28rem}.identity-name{font-size:1.55rem;line-height:1.25;font-weight:700;color:#141414;letter-spacing:-.025em}.identity-url{font-size:.84rem;color:#667085;margin-top:.3rem}.identity-meta{text-align:right;color:#8c8c8c;font-size:.76rem;line-height:1.55;white-space:nowrap}.identity-risk{display:inline-block;margin-top:.4rem;padding:.2rem .55rem;border-radius:99px;font-weight:750}
        .summary{border:1px solid #bae0ff;border-radius:10px;padding:1rem 1.15rem;background:#e6f4ff;margin:.5rem 0 1rem;line-height:1.6;color:#1f1f1f}
        .score-panel{height:100%;min-height:170px;border-radius:10px;padding:1.15rem 1.25rem;color:#fff}.risk-low{background:linear-gradient(135deg,#52c41a,#237804);box-shadow:0 6px 20px rgba(82,196,26,.22)}.risk-medium{background:linear-gradient(135deg,#fadb14,#d48806);box-shadow:0 6px 20px rgba(250,173,20,.22);color:#3d2b00}.risk-high{background:linear-gradient(135deg,#fa8c16,#d4380d);box-shadow:0 6px 20px rgba(250,140,22,.22)}.risk-critical{background:linear-gradient(135deg,#ff4d4f,#a8071a);box-shadow:0 6px 20px rgba(255,77,79,.22)}
        .score-panel .label{font-size:.8rem;opacity:.8}.score-panel .number{font-size:3rem;line-height:1.1;font-weight:700;margin:.55rem 0 .25rem;letter-spacing:-.05em}.score-panel .level{display:inline-block;border-radius:999px;padding:.24rem .58rem;background:rgba(255,255,255,.16);font-size:.75rem;font-weight:650}
        .category-card{background:#fff;border:1px solid #f0f0f0;border-radius:10px;padding:1rem 1.1rem;margin-bottom:.65rem}.category-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:.45rem;font-size:.87rem}.category-name{font-weight:600;color:#262626}.category-value{color:#595959;font-variant-numeric:tabular-nums}
        .progress-track{height:7px;border-radius:99px;background:#f0f0f0;overflow:hidden}.progress-fill{height:100%;border-radius:99px}
        .finding{border:1px solid #f0f0f0;border-radius:10px;padding:1rem 1.1rem;margin:.65rem 0;background:white;box-shadow:0 1px 2px rgba(0,0,0,.025)}.finding-title{font-weight:650;color:#262626}.finding-meta{font-size:.75rem;color:#8c8c8c;margin-top:.25rem;text-transform:uppercase;letter-spacing:.035em}
        .severity{display:inline-block;padding:.15rem .48rem;border-radius:999px;font-weight:700;margin-right:.35rem}.severity-critical{background:#fff1f0;color:#cf1322}.severity-high{background:#fff2e8;color:#d4380d}.severity-medium{background:#fffbe6;color:#d48806}.severity-low{background:#f6ffed;color:#389e0d}
        .disclaimer{font-size:.8rem;color:#64748b;border-top:1px solid #e2e8f0;padding-top:1rem;margin-top:2rem}
        .report-section{display:flex;align-items:center;gap:.9rem;margin:2.35rem 0 1rem;padding:1rem 1.05rem;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.025)}.section-overview{background:#e6f4ff;border:1px solid #91caff}.section-findings{background:#fff7e6;border:1px solid #ffd591}.section-remediation{background:#f6ffed;border:1px solid #b7eb8f}.section-export{background:#f9f0ff;border:1px solid #d3adf7}
        .section-index{display:flex;align-items:center;justify-content:center;flex:0 0 34px;height:34px;border-radius:9px;color:#fff;font-size:.76rem;font-weight:750;letter-spacing:.03em}.section-overview .section-index{background:#1677ff}.section-findings .section-index{background:#fa8c16}.section-remediation .section-index{background:#52c41a}.section-export .section-index{background:#722ed1}.report-section-title{font-size:1.28rem;line-height:1.25;font-weight:700;color:#141414;letter-spacing:-.015em}.report-section-copy{font-size:.82rem;color:#595959;margin-top:.2rem}
        @media(max-width:700px){.hero,.report-identity{align-items:flex-start;flex-direction:column}.hero-badge{white-space:normal}.identity-meta{text-align:left}.block-container{padding-left:.8rem;padding-right:.8rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(report: Dict[str, Any]) -> None:
    score = normalize_risk_score(report.get("overall_risk_score", report.get("risk_score", 0)))
    level, _ = risk_label(score)
    findings = report.get("findings", []) or []
    recommendations = report.get("recommendations", []) or []
    high_count = sum(1 for item in findings if str(item.get("severity", item.get("risk_level", ""))).lower() in {"high", "critical"})
    target_name = html.escape(str(report.get("target_name", "Audit result")))
    target_url = html.escape(str(report.get("target_url", "")))
    st.markdown(
        f'<div class="report-identity"><div><div class="identity-eyebrow">Audit report</div><div class="identity-name">{target_name}</div><div class="identity-url">{target_url}</div></div><div class="identity-meta">PUBLIC SURFACE AUDIT<br>Methodology v{html.escape(str(report.get("methodology_version", "1.0")))}<br><span class="identity-risk risk-{level.lower()}">{level.upper()} RISK</span></div></div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    cols[0].metric("Risk Exposure Score", f"{score:.1f} / 100", help="Higher means more observable risk. This is not a safety percentage or certification.")
    cols[1].metric("Risk Level", level)
    cols[2].metric("High / Critical", high_count)
    cols[3].metric("Findings", len(findings))

    category_scores = report.get("category_scores") or {
        key: normalize_risk_score(value.get("risk_score", 0))
        for key, value in (report.get("analysis", {}) or {}).items()
        if isinstance(value, dict)
    }
    st.markdown('<div class="report-section section-overview"><div class="section-index">01</div><div><div class="report-section-title">Overview</div><div class="report-section-copy">At-a-glance risk posture and category distribution</div></div></div>', unsafe_allow_html=True)
    summary = report.get("executive_summary", report.get("summary", "No summary available."))
    safe_summary = html.escape(str(summary)).replace("\n", "<br>")
    st.markdown(f'<div class="summary"><strong>Executive summary</strong><br>{safe_summary}</div>', unsafe_allow_html=True)
    score_col, category_col, severity_col = st.columns([.8, 1.35, 1.15])
    with score_col:
        st.markdown(f'<div class="score-panel risk-{level.lower()}"><div class="label">RISK EXPOSURE SCORE</div><div class="number">{score:.0f}<span style="font-size:1rem;opacity:.7"> / 100</span></div><span class="level">{level} risk</span><div style="font-size:.72rem;opacity:.78;margin-top:.75rem;line-height:1.4">Higher means more observable risk — not a safety percentage.</div></div>', unsafe_allow_html=True)
    with category_col:
        for name, value in category_scores.items():
            category_score = normalize_risk_score(value)
            _, bar_color = risk_label(category_score)
            st.markdown(f'<div class="category-card"><div class="category-row"><span class="category-name">{html.escape(str(name).title())}</span><span class="category-value">{category_score:.1f} / 100</span></div><div class="progress-track"><div class="progress-fill" style="width:{category_score}%;background:{bar_color}"></div></div></div>', unsafe_allow_html=True)
    severity_names = ["Critical", "High", "Medium", "Low"]
    severity_values = [sum(1 for item in findings if str(item.get("severity", item.get("risk_level", "low"))).capitalize() == name) for name in severity_names]
    with severity_col:
        if sum(severity_values):
            chart = px.pie(names=severity_names, values=severity_values, hole=.7, color=severity_names, color_discrete_map={"Critical":"#cf1322","High":"#d4380d","Medium":"#d48806","Low":"#389e0d"})
            chart.update_traces(textposition="inside", textinfo="value")
            chart.update_layout(height=245, margin=dict(l=8, r=8, t=22, b=8), showlegend=True, legend=dict(orientation="h", y=-.1), annotations=[dict(text="Severity", x=.5, y=.5, font_size=13, showarrow=False)])
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
        else:
            st.success("No risk findings were generated.")

    st.markdown(f'<div class="report-section section-findings"><div class="section-index">02</div><div><div class="report-section-title">Findings <span style="color:#8c8c8c;font-weight:500">({len(findings)})</span></div><div class="report-section-copy">Prioritized evidence and recommended corrective action</div></div></div>', unsafe_allow_html=True)
    if findings:
        for index, finding in enumerate(findings, 1):
            title = html.escape(str(finding.get("title", f"Finding {index}")))
            severity_raw = str(finding.get("severity", finding.get("risk_level", "unknown"))).lower()
            severity = html.escape(severity_raw.upper())
            category = html.escape(str(finding.get("category", "other")).upper())
            points = finding.get("risk_points")
            points_text = f" · +{points} RISK POINTS" if points is not None else ""
            severity_class = severity_raw if severity_raw in {"critical", "high", "medium", "low"} else "low"
            st.markdown(f'<div class="finding"><div class="finding-title"><span class="severity severity-{severity_class}">{severity}</span>{index}. {title}</div><div class="finding-meta">{category}{points_text}</div></div>', unsafe_allow_html=True)
            with st.expander("Why this matters and how to fix it", expanded=index == 1):
                st.markdown(f"**Evidence**  \n{finding.get('evidence', 'Not provided.')}")
                st.markdown(f"**Risk scenario**  \n{finding.get('risk_scenario', finding.get('description', 'Not provided.'))}")
                st.markdown(f"**Business impact if left unresolved**  \n{finding.get('business_impact', finding.get('description', 'Not provided.'))}")
                likelihood = str(finding.get("likelihood", "possible")).title()
                impact = str(finding.get("impact", "moderate")).title()
                effort = str(finding.get("remediation_effort", "review")).title()
                st.markdown(f"**Risk rationale:** Likelihood `{likelihood}` × Impact `{impact}`  \n**Estimated remediation effort:** `{effort}`")
                st.markdown(f"**Recommended action**  \n{finding.get('recommendation', 'Review the finding and define an owner.')}")
    else:
        st.success("No observable gaps were found in this automated public-surface review.")

    st.markdown('<div class="report-section section-remediation"><div class="section-index">03</div><div><div class="report-section-title">Remediation plan</div><div class="report-section-copy">Actions ordered by risk priority</div></div></div>', unsafe_allow_html=True)
    if recommendations:
        for index, item in enumerate(recommendations, 1):
            if isinstance(item, dict):
                priority = html.escape(str(item.get("priority", "review")).upper())
                st.markdown(f"**{index}. {item.get('title', 'Recommendation')}**  ·  `{priority}`")
                st.write(item.get("description", ""))
                st.divider()
            else:
                st.markdown(f"{index}. {item}")
    else:
        st.info("No remediation actions are currently required.")

    st.markdown('<div class="report-section section-export"><div class="section-index">04</div><div><div class="report-section-title">Export report</div><div class="report-section-copy">Download the complete result or findings data</div></div></div>', unsafe_allow_html=True)

    json_payload = json.dumps(report, indent=2, default=str)
    findings_csv = pd.DataFrame(findings).to_csv(index=False) if findings else ""
    export_a, export_b = st.columns(2)
    export_a.download_button("Download full report (JSON)", json_payload, file_name=f"{report.get('id', 'audit')}.json", mime="application/json", use_container_width=True)
    export_b.download_button("Download findings (CSV)", findings_csv, file_name=f"{report.get('id', 'audit')}_findings.csv", mime="text/csv", disabled=not findings, use_container_width=True)
    st.markdown(f'<div class="disclaimer">Public Surface Audit · Methodology v{html.escape(str(report.get("methodology_version", "1.0")))} · {html.escape(str(report.get("disclaimer", "Automated assessment only.")))}</div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="AI Risk Auditor", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")
    inject_styles()
    st.markdown(
        """
        <section class="hero"><div><div class="kicker">Agentic AI Risk Auditor</div><h1>AI Risk Overview</h1><p>Public security, privacy, transparency, and compliance signals in one decision-ready report.</p></div><div class="hero-badge">Public Surface Audit · 0–100 risk</div></section>
        """,
        unsafe_allow_html=True,
    )
    with st.form("audit_form"):
        st.markdown("#### Run a public-surface audit")
        col_a, col_b = st.columns(2)
        target_name = col_a.text_input("Product or system name", placeholder="Acme Support Copilot")
        target_url = col_b.text_input("Public website", placeholder="https://example.com")
        system_type = st.selectbox(
            "System type",
            options=list(SYSTEM_TYPES),
            help="This sets the audit scope so a portfolio is not judged like an AI decision system.",
        )
        additional_context = st.text_input(
            "Additional context (optional)",
            placeholder="Example: Uses customer account data to draft support replies.",
        )
        submitted = st.form_submit_button("Run risk audit", type="primary", use_container_width=True)
    demo_col, note_col = st.columns([1, 3])
    if demo_col.button("View sample report", use_container_width=True):
        st.session_state.audit_report = sample_report()
    note_col.caption("This MVP checks observable public signals. It does not access private systems or perform penetration testing.")
    if submitted:
        if not target_name.strip() or not target_url.strip() or system_type == "Select a system type":
            st.error("Enter a product name and public website, then select a system type.")
        else:
            base_description = SYSTEM_TYPES[system_type]
            description = " ".join(part for part in [base_description, additional_context.strip()] if part).strip() if base_description else ""
            with st.spinner("Reading the public page and calculating risk…"):
                try:
                    st.session_state.audit_report = audit_public_website(target_name, target_url, description)
                except ValueError as exc:
                    st.error(str(exc))
    if "audit_report" not in st.session_state:
        st.session_state.audit_report = sample_report()
    render_dashboard(st.session_state.audit_report)


if __name__ == "__main__":
    main()
