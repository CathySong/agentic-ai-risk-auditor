# Agentic AI Risk Auditor

Prototype multi-agent system for auditing AI products, websites, and policy documents for privacy, security, compliance, and ethics risks.

The project is designed as a portfolio-quality demonstration of agent orchestration: a planner breaks an audit into tasks, tool executors gather evidence, analyzers map findings to risk categories, and a final report summarizes risk level and recommendations.

## What It Demonstrates

- Multi-agent workflow design for audit planning and execution
- Mock-first LLM architecture for local testing without API keys
- Website, document, and contract-analysis tool interfaces
- RAG-oriented compliance knowledge retrieval
- FastAPI and Streamlit entry points
- Environment-based provider configuration
- CI smoke test for import/config sanity

## Current Status

This is an engineering prototype, not a production compliance system. It is suitable for demonstrating architecture, testing agent workflows, and exploring how AI risk assessments can be structured. Real compliance use would require legal review, stronger source verification, and validated benchmark datasets.

## Architecture

```text
agent/          Planner, executor, graph, memory, prompts
app/            FastAPI application and configuration
models/         Mock and provider-backed LLM clients
rag/            Compliance retrieval layer
tools/          Web, document, search, and contract tools
ui/             Streamlit dashboard
tests/          Core functionality checks
```

## Quick Start

```bash
git clone https://github.com/CathySong/agentic-ai-risk-auditor.git
cd agentic-ai-risk-auditor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_minimal.txt
cp .env.example .env
python test_simple.py
```

The default `.env.example` uses mock LLM mode, so the smoke test can run without external API keys.

## Running the Interfaces

Streamlit UI:

```bash
streamlit run ui/streamlit_app.py
```

FastAPI server:

```bash
uvicorn app.main:app --reload
```

## Configuration

Copy `.env.example` to `.env` and add provider keys only when needed.

```env
LLM_USE_MOCK=true
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
```

The repository intentionally does not track `.env`.

## Testing

```bash
python test_simple.py
```

For deeper tests, install the full dependency set and run:

```bash
pip install -r requirements.txt
python -m pytest tests/
```

## Roadmap

- Add deterministic fixture-based tests for each tool
- Add a sample audit report under `examples/`
- Split optional LLM/vector dependencies into extras
- Add benchmark prompts and expected risk-classification outputs
- Improve source citation and evidence traceability in generated reports

## Responsible Use

This tool can surface possible risks, but it does not replace professional legal, security, privacy, or compliance review.
