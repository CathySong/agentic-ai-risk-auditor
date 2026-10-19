"""Deployable public-surface AI risk audit service.

The MVP intentionally performs deterministic checks against one public website.
It produces the same report contract consumed by the Streamlit dashboard without
requiring provider API keys or the heavier multi-agent development stack.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


METHODOLOGY_VERSION = "1.0"
USER_AGENT = "AgenticAIRiskAuditor/1.0 (+https://github.com/CathySong/agentic-ai-risk-auditor)"


@dataclass
class Finding:
    id: str
    title: str
    category: str
    severity: str
    risk_points: int
    description: str
    evidence: str
    recommendation: str
    source: str


def _normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError("Enter a public website URL.")
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid HTTP or HTTPS URL.")
    return value


def _assert_public_host(url: str) -> None:
    """Reject local/private destinations before making a server-side request."""
    host = urlparse(url).hostname or ""
    if host.lower() in {"localhost", "localhost.localdomain"}:
        raise ValueError("Local and private network addresses cannot be audited.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
    except socket.gaierror as exc:
        raise ValueError("The website hostname could not be resolved.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%")[0])
        if not ip.is_global:
            raise ValueError("Local and private network addresses cannot be audited.")


def _finding(
    finding_id: str,
    title: str,
    category: str,
    severity: str,
    points: int,
    description: str,
    evidence: str,
    recommendation: str,
    source: str,
) -> Finding:
    return Finding(finding_id, title, category, severity, points, description, evidence, recommendation, source)


def _risk_level(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _category_scores(findings: List[Finding]) -> Dict[str, float]:
    maximums = {"security": 40, "privacy": 25, "transparency": 20, "compliance": 15}
    totals = {category: 0 for category in maximums}
    for finding in findings:
        if finding.category in totals:
            totals[finding.category] += finding.risk_points
    return {
        category: round(min(100, totals[category] / maximum * 100), 1)
        for category, maximum in maximums.items()
    }


def audit_public_website(
    target_name: str,
    target_url: str,
    system_description: str = "",
) -> Dict[str, Any]:
    """Audit observable public signals and return an AuditReport dictionary."""
    url = _normalize_url(target_url)
    _assert_public_host(url)
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=(5, 15),
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError(f"The website could not be read: {exc}") from exc

    if len(response.content) > 5_000_000:
        raise ValueError("The page is too large to audit safely.")
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise ValueError("The URL must return an HTML page.")

    final_url = response.url
    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.stripped_strings).lower()
    links = [urljoin(final_url, item.get("href", "")) for item in soup.find_all("a", href=True)]
    link_text = " ".join(item.get_text(" ", strip=True).lower() for item in soup.find_all("a"))
    headers = {key.lower(): value for key, value in response.headers.items()}
    findings: List[Finding] = []

    if urlparse(final_url).scheme != "https":
        findings.append(_finding("SEC-01", "Website is not protected by HTTPS", "security", "critical", 18, "Traffic can be intercepted or modified in transit.", final_url, "Redirect all traffic to HTTPS and enable HSTS.", final_url))
    if "strict-transport-security" not in headers:
        findings.append(_finding("SEC-02", "HSTS is not advertised", "security", "medium", 7, "Browsers are not instructed to enforce HTTPS on future visits.", "Strict-Transport-Security header not found.", "Add a Strict-Transport-Security header after confirming HTTPS coverage.", final_url))
    if "content-security-policy" not in headers:
        findings.append(_finding("SEC-03", "Content Security Policy is missing", "security", "high", 10, "The public page has less browser-side protection against injected content.", "Content-Security-Policy header not found.", "Deploy a tested Content-Security-Policy and monitor violations.", final_url))
    if "x-content-type-options" not in headers:
        findings.append(_finding("SEC-04", "MIME sniffing protection is missing", "security", "low", 5, "Browsers may infer content types instead of honoring declared types.", "X-Content-Type-Options header not found.", "Set X-Content-Type-Options: nosniff.", final_url))

    has_privacy = "privacy" in link_text or any("privacy" in link.lower() for link in links)
    if not has_privacy:
        findings.append(_finding("PRI-01", "No visible privacy notice", "privacy", "high", 15, "Visitors cannot easily find how personal data is collected, used, or retained.", "No privacy-labeled link was found on the audited page.", "Publish and prominently link a privacy notice covering data use, retention, vendors, and user rights.", final_url))
    if soup.find("form") and not any(term in text for term in ["consent", "privacy", "data use"]):
        findings.append(_finding("PRI-02", "Data collection form lacks nearby privacy context", "privacy", "medium", 10, "The page collects user input without an obvious explanation of data handling.", "A form was found without nearby consent or privacy language.", "Add concise data-use and consent language beside every collection form.", final_url))

    ai_terms = ["artificial intelligence", " ai ", "machine learning", "automated decision", "language model", "llm"]
    describes_ai = any(term in f" {text} " for term in ai_terms)
    if system_description.strip() and not describes_ai:
        findings.append(_finding("TRA-01", "AI use is not clearly disclosed", "transparency", "high", 12, "The submitted system is described as AI-enabled, but the public page does not clearly disclose AI use.", "No clear AI or automated-system disclosure was found in visible page text.", "Explain where AI is used, what it does, and where human review applies.", final_url))
    if describes_ai and not any(term in text for term in ["human review", "human oversight", "appeal", "contact us"]):
        findings.append(_finding("TRA-02", "Human oversight path is unclear", "transparency", "medium", 8, "Users may not know how to question or escalate an AI-assisted outcome.", "AI-related language was found without a clear human review or appeal path.", "Document a human escalation, review, or appeal channel.", final_url))

    has_terms = "terms" in link_text or any("terms" in link.lower() for link in links)
    if not has_terms:
        findings.append(_finding("COM-01", "Terms of use are not visible", "compliance", "medium", 8, "Public usage conditions and limitations are not easy to locate.", "No terms-labeled link was found on the audited page.", "Publish and link terms of use appropriate to the service and jurisdiction.", final_url))
    if not soup.html or not soup.html.get("lang"):
        findings.append(_finding("COM-02", "Page language is not declared", "compliance", "low", 3, "Assistive technology may have less context for pronunciation and interpretation.", "The HTML lang attribute is missing.", "Add the primary language to the root HTML element.", final_url))
    if not any(term in text for term in ["accessibility", "wcag"]):
        findings.append(_finding("COM-03", "Accessibility commitment is not visible", "compliance", "low", 4, "The audited page does not expose an accessibility statement or WCAG commitment.", "No accessibility or WCAG language was found.", "Publish an accessibility statement and provide a channel for reporting barriers.", final_url))

    risk_score = min(100, sum(item.risk_points for item in findings))
    categories = _category_scores(findings)
    ordered = sorted(findings, key=lambda item: item.risk_points, reverse=True)
    recommendations = [
        {
            "title": item.title,
            "priority": item.severity,
            "description": item.recommendation,
            "finding_id": item.id,
        }
        for item in ordered[:5]
    ]
    passed = 11 - len(findings)
    summary = (
        f"{target_name or urlparse(final_url).netloc} received a {risk_score}/100 public-surface risk score. "
        f"The audit identified {len(findings)} observable gaps and {max(0, passed)} checks without a finding. "
        "This automated review covers public website signals only and should be followed by an internal technical, legal, and governance review."
    )
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "1.0",
        "methodology_version": METHODOLOGY_VERSION,
        "id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "timestamp": now,
        "target_name": target_name.strip() or urlparse(final_url).netloc,
        "target_url": final_url,
        "audit_scope": "public website signals",
        "overall_risk_score": risk_score,
        "risk_scale": 100,
        "risk_level": _risk_level(risk_score),
        "category_scores": categories,
        "analysis": {key: {"risk_score": value} for key, value in categories.items()},
        "findings": [asdict(item) for item in ordered],
        "recommendations": recommendations,
        "executive_summary": summary,
        "summary": summary,
        "disclaimer": "Automated public-surface assessment only. Not legal advice, certification, or a penetration test.",
    }


def sample_report() -> Dict[str, Any]:
    """Return a stable demo report that renders without network or API keys."""
    findings = [
        Finding("PRI-01", "Sensitive prompts lack a documented retention limit", "privacy", "high", 18, "Conversation content may be retained longer than users expect.", "The sample policy describes collection but provides no deletion window.", "Define purpose-specific retention periods and automate deletion.", "Sample policy review"),
        Finding("SEC-01", "Prompt-injection controls are incomplete", "security", "high", 17, "Retrieved content can influence tool instructions without a trust boundary.", "Untrusted content is passed into the agent context without isolation metadata.", "Separate instructions from retrieved data and add tool authorization checks.", "Sample architecture review"),
        Finding("TRA-01", "Users are not told when content is AI-generated", "transparency", "medium", 12, "Users may treat generated guidance as verified human advice.", "No visible AI disclosure appears in the sample user flow.", "Add contextual disclosure and identify high-impact limitations.", "Sample UX review"),
        Finding("COM-01", "Human oversight evidence is incomplete", "compliance", "medium", 10, "Review ownership and escalation criteria are not documented.", "The sample governance record has no named reviewer or escalation SLA.", "Assign accountable owners and document review triggers.", "Sample governance review"),
        Finding("SEC-02", "Audit logging omits tool authorization decisions", "security", "medium", 9, "Investigators cannot reconstruct why a sensitive action was allowed.", "Tool calls are logged, but policy decisions are not.", "Log policy inputs, decision outcome, actor, and correlation ID.", "Sample logging review"),
        Finding("PRI-02", "Vendor data-use terms need verification", "privacy", "low", 6, "Third-party model handling may not match the stated privacy posture.", "The sample vendor register has no current DPA review date.", "Review DPAs and record training, retention, and region commitments.", "Sample vendor review"),
    ]
    categories = {"privacy": 72.0, "security": 76.0, "transparency": 55.0, "compliance": 61.0}
    return {
        "schema_version": "1.0",
        "methodology_version": METHODOLOGY_VERSION,
        "id": "audit_demo_001",
        "timestamp": "2026-10-19T12:00:00+00:00",
        "target_name": "Acme Support Copilot",
        "target_url": "https://example.com",
        "audit_scope": "sample comprehensive review",
        "overall_risk_score": 72,
        "risk_scale": 100,
        "risk_level": "high",
        "category_scores": categories,
        "analysis": {key: {"risk_score": value} for key, value in categories.items()},
        "findings": [asdict(item) for item in findings],
        "recommendations": [{"title": item.title, "priority": item.severity, "description": item.recommendation, "finding_id": item.id} for item in findings[:5]],
        "executive_summary": "The sample AI assistant scores 72/100, indicating high risk. The largest exposures are prompt-injection boundaries, data-retention governance, and incomplete audit evidence. Addressing the first three recommendations would materially reduce operational and compliance risk.",
        "summary": "Sample report for a customer-support AI assistant.",
        "disclaimer": "Sample data for product demonstration. Not legal advice, certification, or a penetration test.",
    }
