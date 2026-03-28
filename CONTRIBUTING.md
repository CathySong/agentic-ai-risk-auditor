# Contributing to Agentic AI Risk Auditor

Thank you for your interest in contributing to the Agentic AI Risk Auditor! This document provides guidelines and instructions for contributing.

## 🎯 Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Git
- Basic understanding of AI risk assessment concepts

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/CathySong/agentic-ai-risk-auditor.git
   cd agentic-ai-risk-auditor
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 📝 Contribution Workflow

### 1. Find an Issue
- Check the [Issues](https://github.com/CathySong/agentic-ai-risk-auditor/issues) page
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to let others know you're working on it

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Your Changes
- Follow the existing code style
- Write clear commit messages
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_core_functionality.py

# Check code style
flake8 agentic_ai_risk_auditor/
```

### 5. Commit Your Changes
```bash
git add .
git commit -m "feat: Add new feature description"
# or
git commit -m "fix: Resolve issue #123"
```

### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## 🏗️ Project Structure

```
agentic-ai-risk-auditor/
├── agent/          # Multi-agent system
├── app/           # FastAPI application
├── models/        # AI models
├── tools/         # Specialized tools
├── rag/          # RAG system
├── ui/           # User interfaces
├── tests/        # Test suite
└── docs/         # Documentation
```

## 📚 Coding Standards

### Python Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where possible
- Maximum line length: 100 characters
- Use descriptive variable names

### Documentation
- Add docstrings to all functions and classes
- Update README.md for significant changes
- Include examples in docstrings

### Testing
- Write unit tests for new functionality
- Aim for >80% test coverage
- Use descriptive test names
- Test both success and failure cases

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

Example:
```
feat: Add web scraper tool for website analysis
fix: Resolve memory leak in audit executor
docs: Update installation instructions
```

## 🧪 Testing Guidelines

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentic_ai_risk_auditor tests/

# Run specific test
pytest tests/test_web_scraper.py -v

# Run tests matching pattern
pytest -k "test_llm" -v
```

### Writing Tests
```python
import pytest
from agentic_ai_risk_auditor.tools.web_scraper import WebScraper

class TestWebScraper:
    """Test suite for WebScraper tool."""
    
    @pytest.mark.asyncio
    async def test_scrape_basic_website(self):
        """Test scraping a basic website."""
        async with WebScraper() as scraper:
            result = await scraper.scrape("https://example.com")
            assert result["metadata"]["success"] is True
            assert "analysis" in result
```

## 🔧 Adding New Tools

1. Create a new file in `tools/` directory
2. Implement the tool interface
3. Add to `agent/executor.py` if needed
4. Write comprehensive tests
5. Update documentation

Example tool structure:
```python
class NewTool:
    """Description of the new tool."""
    
    def __init__(self):
        self.initialized = True
    
    async def analyze(self, target, parameters=None):
        """Main analysis method."""
        # Implementation here
        return {
            "analysis": {},
            "findings": [],
            "risk_score": 0.0
        }
```

## 📖 Documentation

### Updating Documentation
- Update README.md for major changes
- Add docstrings to new functions/classes
- Create new markdown files in `docs/` if needed
- Include examples and usage instructions

### Building Documentation
```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## 🐛 Reporting Bugs

1. Check if the bug already exists in [Issues](https://github.com/CathySong/agentic-ai-risk-auditor/issues)
2. Create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages or screenshots

## 💡 Feature Requests

1. Check if the feature already exists or is planned
2. Create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Proposed implementation (if known)
   - Any relevant references or examples

## 🏆 Recognition

Contributors will be:
- Listed in the README.md
- Acknowledged in release notes
- Invited to join the project's discussions

## ❓ Questions?

- Open a [Discussion](https://github.com/CathySong/agentic-ai-risk-auditor/discussions)
- Comment on relevant issues
- Email: cathy@example.com

Thank you for contributing to making AI systems safer! 🚀