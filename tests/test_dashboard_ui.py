from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_product_hierarchy_without_exceptions():
    app_path = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()

    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Overview",
        "Findings (6)",
        "Remediation",
    ]
    assert [metric.value for metric in app.metric] == [
        "72.0 / 100",
        "High",
        "2",
        "6",
    ]
