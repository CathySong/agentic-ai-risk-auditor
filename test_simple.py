#!/usr/bin/env python3
"""
Simple test to verify core functionality without installing all dependencies.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test lightweight imports without requiring optional agent deps."""
    print("Testing imports...")

    required_modules = [
        ("app.config", "settings"),
        ("models.llm_mock", "MockLLMClient"),
        ("tools.contract_analyzer", "ContractAnalyzer"),
    ]
    optional_modules = [
        ("models.llm_main", "create_llm_client"),
        ("tools.web_scraper", "WebScraper"),
        ("rag.retriever", "RAGRetriever"),
        ("agent.graph", "RiskAuditGraph"),
        ("agent.planner", "AuditPlanner"),
        ("agent.executor", "AuditExecutor"),
    ]

    failures = 0

    for module_name, attr_name in required_modules:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            if hasattr(module, attr_name):
                print(f"✅ {module_name}.{attr_name}")
            else:
                print(f"❌ {module_name}.{attr_name} (not found)")
                failures += 1
        except ImportError as e:
            print(f"❌ {module_name}.{attr_name} (ImportError: {e})")
            failures += 1
        except Exception as e:
            print(f"❌ {module_name}.{attr_name} (Error: {e})")
            failures += 1

    print("\nOptional full-stack imports:")
    for module_name, attr_name in optional_modules:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            print(f"✅ {module_name}.{attr_name}" if hasattr(module, attr_name) else f"⚠️  {module_name}.{attr_name} (not found)")
        except ImportError as e:
            print(f"⚠️  {module_name}.{attr_name} skipped ({e})")
        except Exception as e:
            print(f"⚠️  {module_name}.{attr_name} skipped ({e})")

    return failures

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from app.config import settings
        print(f"✅ Config loaded")
        print(f"   LLM mock mode: {settings.llm.use_mock}")
        print(f"   ChromaDB path: {settings.vectordb.chroma_db_path}")
        print(f"   Debug mode: {settings.debug}")
        return 0
    except Exception as e:
        print(f"❌ Config error: {e}")
        return 1

def test_mock_llm():
    """Test mock LLM functionality."""
    print("\nTesting mock LLM...")
    try:
        from models.llm_mock import MockLLMClient
        import asyncio
        
        async def test():
            client = MockLLMClient()
            response = await client.generate(
                prompt="What is AI risk assessment?",
                temperature=0.7,
                max_tokens=100
            )
            return response
        
        response = asyncio.run(test())
        print(f"✅ Mock LLM response: {response[:100]}...")
        
        # Test embedding
        async def test_embed():
            client = MockLLMClient()
            embedding = await client.generate_embedding("test text")
            return embedding
        
        embedding = asyncio.run(test_embed())
        print(f"✅ Mock embedding dimension: {len(embedding)}")
        
        return 0
    except Exception as e:
        print(f"❌ Mock LLM error: {e}")
        return 1

def test_ui_structure():
    """Test UI module structure."""
    print("\nTesting UI structure...")
    try:
        # Check if UI file exists and has basic structure
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "streamlit_app.py")
        with open(ui_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ("StreamlitApp class", "class StreamlitApp" in content),
            ("render_sidebar method", "def render_sidebar" in content),
            ("render_dashboard method", "def render_dashboard" in content),
            ("render_risk_audit method", "def render_risk_audit" in content),
            ("main function", "def main()" in content or "__name__ == \"__main__\"" in content),
        ]
        
        failures = 0
        for check_name, check_passed in checks:
            if check_passed:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                failures += 1
        return failures
                
    except Exception as e:
        print(f"❌ UI structure error: {e}")
        return 1

def check_dependencies():
    """Check required dependencies."""
    print("\nChecking dependencies...")
    
    dependencies = [
        ("streamlit", "UI framework"),
        ("plotly", "Visualization"),
        ("pandas", "Data processing"),
        ("pydantic", "Configuration"),
        ("aiohttp", "Async HTTP"),
        ("requests", "HTTP requests"),
        ("bs4", "HTML parsing"),
    ]
    
    for dep, description in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} ({description})")
        except ImportError:
            print(f"⚠️  {dep} ({description}) - not installed")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Agentic AI Risk Auditor - Simple Test")
    print("=" * 60)
    
    failures = 0
    failures += test_imports()
    failures += test_config()
    failures += test_mock_llm()
    failures += test_ui_structure()
    check_dependencies()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("\nNext steps:")
    print("1. Install missing dependencies: pip install -r requirements.txt")
    print("2. Run Streamlit UI: streamlit run ui/streamlit_app.py")
    print("3. Test with: python test_simple.py")
    print("=" * 60)
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
