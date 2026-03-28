# 🔍 Agentic AI Risk Auditor

**Multi-agent system for automated AI risk assessment and compliance auditing.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🎯 Overview

Agentic AI Risk Auditor is a comprehensive multi-agent system designed to automatically assess AI systems for privacy, security, ethics, and regulatory compliance risks. It combines LLM-powered analysis with specialized tools to provide detailed risk assessments and actionable recommendations.

## ✨ Features

### 🤖 **Multi-Agent Architecture**
- **Planner Agent**: Generates detailed audit plans based on target specifications
- **Executor Agent**: Coordinates tool execution and data collection
- **Analyzer Agent**: Processes results and generates risk assessments
- **Memory Agent**: Maintains context and learns from past audits

### 🛠️ **Specialized Tools**
- **Web Scraper**: Analyzes websites for privacy, security, and compliance indicators
- **Contract Analyzer**: Examines legal documents for AI-specific risks
- **RAG Retriever**: Semantic search across knowledge base of regulations and guidelines
- **Code Analyzer**: (Coming soon) Static analysis of AI/ML codebases

### 📊 **Comprehensive Analysis**
- **Privacy Assessment**: GDPR, CCPA, HIPAA compliance checking
- **Security Evaluation**: Vulnerability scanning and threat modeling
- **Ethics Review**: Bias detection, transparency assessment, fairness analysis
- **Compliance Verification**: Regulatory framework alignment

### 🎨 **User Interfaces**
- **Streamlit Web App**: Interactive dashboard for audit creation and visualization
- **REST API**: Programmatic access for integration with CI/CD pipelines
- **Command Line Interface**: (Coming soon) Batch processing and automation

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key (or Anthropic/Google API keys)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/CathySong/agentic-ai-risk-auditor.git
cd agentic-ai-risk-auditor

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```python
from agent.graph import RiskAuditGraph
from agent.planner import AuditPlanner
from agent.executor import AuditExecutor

# Initialize components
planner = AuditPlanner()
executor = AuditExecutor()
graph = RiskAuditGraph()

# Create audit plan
audit_params = {
    "audit_type": "Website",
    "target_name": "Example AI Service",
    "target_url": "https://example.com",
    "audit_scope": ["Privacy", "Security", "Compliance"]
}

plan = await planner.create_plan(audit_params)

# Execute audit
results = await executor.execute_plan(plan)

# Process results
final_report = await graph.process_results(results)
print(f"Risk Score: {final_report['overall_risk_score']:.2f}")
```

### Web Interface

```bash
# Launch Streamlit app
streamlit run ui/streamlit_app.py
```

Then open http://localhost:8501 in your browser.

## 📁 Project Structure

```
agentic-ai-risk-auditor/
├── agent/              # Multi-agent system
│   ├── graph.py       # LangGraph workflow
│   ├── planner.py     # Audit planning
│   ├── executor.py    # Task execution
│   ├── memory.py      # Context management
│   └── prompts.py     # LLM prompts
├── app/               # FastAPI application
│   ├── main.py       # Main app
│   ├── api.py        # REST endpoints
│   └── config.py     # Configuration
├── models/            # AI models
│   ├── llm.py        # LLM client
│   └── embeddings.py # Embedding models
├── tools/             # Specialized tools
│   ├── web_scraper.py
│   ├── contract_analyzer.py
│   └── (more tools)
├── rag/               # RAG system
│   └── retriever.py  # Document retrieval
├── ui/                # User interfaces
│   └── streamlit_app.py
├── tests/             # Test suite
├── outputs/           # Audit reports
├── scripts/           # Utility scripts
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key

# Model Selection
LLM_DEFAULT_PROVIDER=openai
LLM_OPENAI_MODEL=gpt-4-turbo-preview
LLM_ANTHROPIC_MODEL=claude-3-opus-20240229
LLM_GOOGLE_MODEL=gemini-pro

# Vector Database
CHROMA_DB_PATH=./chroma_db
VECTORDB_DEFAULT_COLLECTION=ai_risk_knowledge

# Tool Settings
WEB_SCRAPER_TIMEOUT=60
WEB_SCRAPER_MAX_PAGES=10
```

### Model Providers

The system supports multiple LLM providers:
- **OpenAI**: GPT-4, GPT-3.5
- **Anthropic**: Claude 3 series
- **Google**: Gemini Pro
- **Cohere**: (Coming soon)

## 📚 Knowledge Base

The system includes a built-in knowledge base with:
- **Legal Regulations**: GDPR, CCPA, HIPAA, EU AI Act
- **AI Guidelines**: IEEE, OECD, NIST AI frameworks
- **Security Standards**: ISO 27001, NIST CSF
- **Case Studies**: Real-world AI risk incidents
- **Best Practices**: Industry standards and recommendations

Add your own documents:
```python
from rag.retriever import RAGRetriever, DocumentType

retriever = RAGRetriever()
await retriever.add_documents([
    {
        "text": "Your document text here...",
        "metadata": {
            "source": "Your Source",
            "document_type": DocumentType.LEGAL_REGULATION.value
        }
    }
])
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_core_functionality.py

# Test coverage
pytest --cov=agentic_ai_risk_auditor tests/
```

## 📊 Example Audit Report

```json
{
  "audit_id": "audit_20240328_143022",
  "target_name": "Example AI Service",
  "overall_risk_score": 0.65,
  "risk_level": "HIGH",
  "findings": [
    {
      "title": "Missing Privacy Policy",
      "category": "privacy",
      "risk_level": "high",
      "description": "Website lacks a visible privacy policy.",
      "recommendations": ["Add comprehensive privacy policy", "Include data usage disclosures"]
    }
  ],
  "recommendations": [
    "Implement GDPR-compliant data processing",
    "Add AI transparency statement",
    "Conduct security penetration testing"
  ],
  "compliance_status": {
    "gdpr": "partial",
    "ccpa": "failed",
    "ai_ethics": "partial"
  }
}
```

## 🚀 Deployment

### Local Development
```bash
# Install in development mode
pip install -e .

# Run FastAPI server
uvicorn app.main:app --reload

# Run Streamlit app
streamlit run ui/streamlit_app.py
```

### Docker Deployment
```bash
# Build image
docker build -t agentic-ai-risk-auditor .

# Run container
docker run -p 8000:8000 -p 8501:8501 agentic-ai-risk-auditor
```

### Cloud Deployment
- **Vercel**: Deploy Streamlit app
- **Railway**: Deploy FastAPI backend
- **AWS/GCP**: Containerized deployment with Kubernetes

## 📈 Roadmap

### Phase 1: Core System (✅ Complete)
- [x] Multi-agent architecture
- [x] Basic tool implementations
- [x] Streamlit UI
- [x] REST API

### Phase 2: Enhanced Tools (🔄 In Progress)
- [ ] Code analysis for AI/ML systems
- [ ] API security testing
- [ ] Model card generation
- [ ] Bias detection algorithms

### Phase 3: Enterprise Features (📅 Planned)
- [ ] Team collaboration
- [ ] Audit scheduling
- [ ] Compliance reporting
- [ ] Integration with CI/CD

### Phase 4: Advanced AI (📅 Future)
- [ ] Autonomous audit optimization
- [ ] Predictive risk modeling
- [ ] Natural language explanations
- [ ] Cross-system correlation

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Uses [ChromaDB](https://www.trychroma.com/) for vector storage
- Inspired by [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- Thanks to the open-source AI safety community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/CathySong/agentic-ai-risk-auditor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CathySong/agentic-ai-risk-auditor/discussions)
- **Email**: cathy@example.com

---

**Made with ❤️ by Cathy Song | AI Safety & Compliance**

*"Building safer AI systems through automated risk assessment."*