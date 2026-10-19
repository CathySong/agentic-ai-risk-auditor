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
import plotly.graph_objects as go
import streamlit as st

from app.audit_service import audit_public_website, sample_report


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
        return "Critical", "#dc2626"
    if score >= 70:
        return "High", "#ea580c"
    if score >= 30:
        return "Medium", "#ca8a04"
    return "Low", "#16a34a"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem}
        [data-testid="stHeader"] {background: rgba(255,255,255,.78); backdrop-filter: blur(14px)}
        .hero {padding:2.2rem 2.4rem;border-radius:24px;background:linear-gradient(135deg,#07111f,#132846);color:white;margin-bottom:1.4rem;box-shadow:0 18px 50px rgba(15,23,42,.16)}
        .hero .kicker {font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;color:#7dd3fc;font-weight:700}
        .hero h1 {font-size:clamp(2.2rem,5vw,4.5rem);line-height:1;margin:.5rem 0 1rem;letter-spacing:-.04em}
        .hero p {max-width:760px;color:#cbd5e1;font-size:1.08rem;line-height:1.65;margin:0}
        .report-label {font-size:.76rem;letter-spacing:.11em;text-transform:uppercase;color:#64748b;font-weight:700;margin-top:1.8rem}
        .summary {border:1px solid #e2e8f0;border-left:5px solid #2563eb;border-radius:14px;padding:1rem 1.15rem;background:#f8fafc;margin:.5rem 0 1.2rem;line-height:1.65}
        .finding {border:1px solid #e2e8f0;border-radius:14px;padding:1rem 1.1rem;margin:.7rem 0;background:white}
        .finding-title {font-weight:750;color:#0f172a}
        .finding-meta {font-size:.78rem;color:#64748b;margin-top:.2rem;text-transform:uppercase;letter-spacing:.04em}
        .disclaimer {font-size:.8rem;color:#64748b;border-top:1px solid #e2e8f0;padding-top:1rem;margin-top:2rem}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(report: Dict[str, Any]) -> None:
    score = normalize_risk_score(report.get("overall_risk_score", report.get("risk_score", 0)))
    level, color = risk_label(score)
    findings = report.get("findings", []) or []
    recommendations = report.get("recommendations", []) or []
    high_count = sum(1 for item in findings if str(item.get("severity", item.get("risk_level", ""))).lower() in {"high", "critical"})

    st.markdown('<div class="report-label">Audit report dashboard</div>', unsafe_allow_html=True)
    st.subheader(report.get("target_name", "Audit result"))
    cols = st.columns(4)
    cols[0].metric("Total Risk Score", f"{score:.1f} / 100")
    cols[1].metric("Risk Level", level)
    cols[2].metric("High / Critical", high_count)
    cols[3].metric("Findings", len(findings))

    summary = report.get("executive_summary", report.get("summary", "No summary available."))
    safe_summary = html.escape(str(summary)).replace("\n", "<br>")
    st.markdown(f'<div class="summary"><strong>Executive summary</strong><br>{safe_summary}</div>', unsafe_allow_html=True)

    gauge_col, severity_col = st.columns([1.2, 1])
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": " / 100", "font": {"size": 38}},
        title={"text": f"{level} risk"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30], "color": "#dcfce7"},
                {"range": [30, 70], "color": "#fef9c3"},
                {"range": [70, 85], "color": "#ffedd5"},
                {"range": [85, 100], "color": "#fee2e2"},
            ],
            "threshold": {"line": {"color": color, "width": 4}, "thickness": .75, "value": score},
        },
    ))
    gauge.update_layout(height=320, margin=dict(l=20, r=20, t=55, b=20))
    with gauge_col:
        st.plotly_chart(gauge, use_container_width=True)

    severity_names = ["Critical", "High", "Medium", "Low"]
    severity_values = [sum(1 for item in findings if str(item.get("severity", item.get("risk_level", "low"))).capitalize() == name) for name in severity_names]
    with severity_col:
        if sum(severity_values):
            chart = px.pie(
                names=severity_names,
                values=severity_values,
                hole=.62,
                color=severity_names,
                color_discrete_map={"Critical": "#dc2626", "High": "#ea580c", "Medium": "#ca8a04", "Low": "#16a34a"},
                title="Findings by severity",
            )
            chart.update_layout(height=320, margin=dict(l=20, r=20, t=55, b=20))
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.success("No risk findings were generated.")

    category_scores = report.get("category_scores") or {
        key: normalize_risk_score(value.get("risk_score", 0))
        for key, value in (report.get("analysis", {}) or {}).items()
        if isinstance(value, dict)
    }
    if category_scores:
        data = pd.DataFrame({"Category": [key.title() for key in category_scores], "Risk Score": [normalize_risk_score(value) for value in category_scores.values()]})
        category_chart = px.bar(data, x="Risk Score", y="Category", orientation="h", color="Risk Score", color_continuous_scale="RdYlGn_r", range_color=[0, 100], title="Risk score by category")
        category_chart.update_xaxes(range=[0, 100], title="Risk Score (0-100)")
        category_chart.update_layout(height=max(300, len(data) * 70), coloraxis_showscale=False)
        st.plotly_chart(category_chart, use_container_width=True)

    st.subheader("Prioritized findings")
    if findings:
        for index, finding in enumerate(findings, 1):
            title = html.escape(str(finding.get("title", f"Finding {index}")))
            severity = html.escape(str(finding.get("severity", finding.get("risk_level", "unknown"))).upper())
            category = html.escape(str(finding.get("category", "other")).upper())
            points = finding.get("risk_points")
            points_text = f" · +{points} RISK POINTS" if points is not None else ""
            st.markdown(f'<div class="finding"><div class="finding-title">{index}. {title}</div><div class="finding-meta">{severity} · {category}{points_text}</div></div>', unsafe_allow_html=True)
            with st.expander("Evidence and remediation", expanded=index <= 2):
                st.write(finding.get("description", "No description available."))
                st.markdown(f"**Evidence:** {finding.get('evidence', 'Not provided.')}")
                st.markdown(f"**Recommended action:** {finding.get('recommendation', 'Review the finding and define an owner.')}")
    else:
        st.success("No observable gaps were found in this automated public-surface review.")

    st.subheader("Remediation plan")
    for index, item in enumerate(recommendations, 1):
        if isinstance(item, dict):
            st.markdown(f"{index}. **{item.get('title', 'Recommendation')}** - {item.get('description', '')}")
        else:
            st.markdown(f"{index}. {item}")

    json_payload = json.dumps(report, indent=2, default=str)
    findings_csv = pd.DataFrame(findings).to_csv(index=False) if findings else ""
    export_a, export_b = st.columns(2)
    export_a.download_button("Download full report (JSON)", json_payload, file_name=f"{report.get('id', 'audit')}.json", mime="application/json", use_container_width=True)
    export_b.download_button("Download findings (CSV)", findings_csv, file_name=f"{report.get('id', 'audit')}_findings.csv", mime="text/csv", disabled=not findings, use_container_width=True)
    st.markdown(f'<div class="disclaimer">Methodology v{html.escape(str(report.get("methodology_version", "1.0")))} · {html.escape(str(report.get("disclaimer", "Automated assessment only.")))}</div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="AI Risk Auditor", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")
    inject_styles()
    st.markdown(
        """
        <section class="hero">
          <div class="kicker">Agentic AI Risk Auditor</div>
          <h1>Turn AI risk into<br>a decision-ready score.</h1>
          <p>Review public security, privacy, transparency, and compliance signals. Get a prioritized 0-100 risk report with evidence and remediation steps.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.form("audit_form"):
        st.subheader("Run a public-surface audit")
        col_a, col_b = st.columns(2)
        target_name = col_a.text_input("Product or system name", placeholder="Acme Support Copilot")
        target_url = col_b.text_input("Public website", placeholder="https://example.com")
        description = st.text_area("How does the system use AI?", placeholder="Customer-support assistant that retrieves account data and drafts responses.", height=90)
        submitted = st.form_submit_button("Run risk audit", type="primary", use_container_width=True)

    demo_col, note_col = st.columns([1, 3])
    if demo_col.button("View sample report", use_container_width=True):
        st.session_state.audit_report = sample_report()
    note_col.caption("The MVP checks observable public signals. It does not access private systems or perform penetration testing.")

    if submitted:
        if not target_name.strip() or not target_url.strip():
            st.error("Enter both a product name and a public website.")
        else:
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
