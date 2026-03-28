#!/usr/bin/env python3
"""
Simple test to verify core functionality without installing all dependencies.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    modules_to_test = [
        ("app.config", "settings"),
        ("models.llm_main", "create_llm_client"),
        ("models.llm_mock", "MockLLMClient"),
        ("tools.web_scraper", "WebScraper"),
        ("tools.contract_analyzer", "ContractAnalyzer"),
        ("rag.retriever", "RAGRetriever"),
        ("agent.graph", "RiskAuditGraph"),
        ("agent.planner", "AuditPlanner"),
        ("agent.executor", "AuditExecutor"),
    ]
    
    for module_name, attr_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            if hasattr(module, attr_name):
                print(f"✅ {module_name}.{attr_name}")
            else:
                print(f"❌ {module_name}.{attr_name} (not found)")
        except ImportError as e:
            print(f"❌ {module_name}.{attr_name} (ImportError: {e})")
        except Exception as e:
            print(f"❌ {module_name}.{attr_name} (Error: {e})")

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from app.config import settings
        print(f"✅ Config loaded")
        print(f"   LLM mock mode: {settings.llm.use_mock}")
        print(f"   ChromaDB path: {settings.vectordb.chroma_db_path}")
        print(f"   Debug mode: {settings.debug}")
    except Exception as e:
        print(f"❌ Config error: {e}")

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
        
    except Exception as e:
        print(f"❌ Mock LLM error: {e}")

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
        
        for check_name, check_passed in checks:
            if check_passed:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                
    except Exception as e:
        print(f"❌ UI structure error: {e}")

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
        ("beautifulsoup4", "HTML parsing"),
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
    
    test_imports()
    test_config()
    test_mock_llm()
    test_ui_structure()
    check_dependencies()
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("\nNext steps:")
    print("1. Install missing dependencies: pip install -r requirements.txt")
    print("2. Run Streamlit UI: streamlit run ui/streamlit_app.py")
    print("3. Test with: python test_simple.py")
    print("=" * 60)

if __name__ == "__main__":
    main()