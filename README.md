# Agentic AI Risk Auditor

Multi-agent audit toolkit for evaluating AI systems across privacy, security, compliance, and operational risk.

This project demonstrates how to turn an ambiguous AI governance problem into a structured workflow: plan the audit, collect evidence, retrieve relevant guidance, score risk, and produce decision-ready findings.

## Why It Matters

AI teams need repeatable ways to evaluate systems before and after release. This repo is a practical prototype for that workflow: it combines agent orchestration, retrieval, web/document analysis, and risk scoring into a tool that can be used from an API or web UI.

## Capabilities

- Multi-agent planning and execution for AI risk reviews
- RAG-based retrieval over compliance and best-practice material
- Website, document, and contract analysis hooks
- Risk scoring with structured findings and recommendations
- FastAPI service and Streamlit interface
- Mock-mode configuration for local demos without provider keys

## Architecture

```text
agentic-ai-risk-auditor/
├── agent/      # Planner, executor, graph, memory, prompts
├── app/        # FastAPI application and configuration
├── models/     # LLM and embedding clients
├── rag/        # Compliance retrieval layer
├── tools/      # Web, document, and contract analyzers
├── ui/         # Streamlit app
└── tests/      # Core functionality checks
```

## Quick Start

```bash
git clone https://github.com/CathySong/agentic-ai-risk-auditor.git
cd agentic-ai-risk-auditor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Run the API:

```bash
uvicorn app.api:app --reload
```

Run the Streamlit UI:

```bash
streamlit run ui/streamlit_app.py
```

Run tests:

```bash
python -m pytest tests/
```

## Example Use Case

```python
from app.main import AgenticAIRiskAuditor, AuditRequest

auditor = AgenticAIRiskAuditor()

request = AuditRequest(
    system_description="Customer-support AI assistant for regulated workflows",
    audit_type="comprehensive",
    regulations=["NIST AI RMF", "GDPR"],
    target_url="https://example.com",
)

result = await auditor.run_audit(request)
print(result.risk_score)
```

## What This Shows

For Staff Data Scientist and AI Engineer roles, this project highlights:

- decomposing fuzzy business risk into measurable evaluation steps;
- designing agent workflows with clear responsibilities;
- combining retrieval, scoring, and reporting into a usable system;
- building prototype surfaces that can become production services;
- documenting assumptions so outputs can be reviewed and improved.

## Notes

This is a portfolio-grade prototype, not legal advice or a replacement for a formal compliance review. It is designed to show system design, evaluation thinking, and practical AI engineering patterns.
