"""Focused tests for the audit dashboard's 0-100 risk scale."""

import ast
from pathlib import Path
from typing import Any

import pytest

from app import audit_service


def load_score_helpers():
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helpers = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"normalize_risk_score", "risk_label"}
    ]
    namespace = {"Any": Any}
    exec(compile(ast.Module(body=helpers, type_ignores=[]), "<score_helpers>", "exec"), namespace)
    return namespace["normalize_risk_score"], namespace["risk_label"]


def test_risk_score_normalizes_legacy_and_current_values():
    normalize, _ = load_score_helpers()
    assert normalize(0.72) == 72.0
    assert normalize(72) == 72.0
    assert normalize(130) == 100.0
    assert normalize(-10) == 0.0
    assert normalize("not-a-score") == 0.0


def test_risk_labels_cover_the_full_scale():
    _, label = load_score_helpers()
    assert label(0)[0] == "Low"
    assert label(30)[0] == "Medium"
    assert label(70)[0] == "High"
    assert label(85)[0] == "Critical"


def test_sample_report_uses_stable_100_point_contract():
    report = audit_service.sample_report()
    assert report["risk_scale"] == 100
    assert report["overall_risk_score"] == 72
    assert report["risk_level"] == "high"
    assert report["schema_version"] == "1.0"
    assert report["category_scores"]
    assert report["findings"]
    assert report["recommendations"]
    assert all(finding["risk_scenario"] for finding in report["findings"])
    assert all(finding["business_impact"] for finding in report["findings"])
    assert all(finding["likelihood"] for finding in report["findings"])
    assert all(finding["impact"] for finding in report["findings"])
    assert all(finding["remediation_effort"] for finding in report["findings"])


def test_private_hosts_are_rejected(monkeypatch):
    monkeypatch.setattr(
        audit_service.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("127.0.0.1", 0))],
    )
    with pytest.raises(ValueError, match="private network"):
        audit_service.audit_public_website("Local", "http://internal.example")
