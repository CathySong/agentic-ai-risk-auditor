#!/usr/bin/env python3
"""
Fix imports in the project to use the new LLM client structure.
"""

import os
import re

def fix_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace imports
    replacements = [
        # Replace LLMClient imports
        (r'from models\.llm import LLMClient', 'from models.llm_main import create_llm_client'),
        (r'from models\.llm import LLMClient, LLMProvider', 'from models.llm_main import create_llm_client, LLMProvider'),
        
        # Update LLMClient instantiation
        (r'LLMClient\(', 'create_llm_client('),
        (r'LLMClient\(\)', 'create_llm_client()'),
    ]
    
    original_content = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        print(f"Fixed: {filepath}")
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    
    return False

def main():
    """Main function to fix all Python files."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    files_to_fix = [
        "agent/planner.py",
        "agent/executor.py",
        "agent/graph.py",
        "agent/memory.py",
        "tools/contract_analyzer.py",
        "rag/retriever.py",
        "models/embeddings.py",
        "ui/streamlit_app.py",
        "tests/test_core_functionality.py",
    ]
    
    fixed_count = 0
    for rel_path in files_to_fix:
        filepath = os.path.join(project_root, rel_path)
        if os.path.exists(filepath):
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"Warning: File not found: {filepath}")
    
    print(f"\nFixed {fixed_count} files")
    
    # Also update requirements.txt to be more realistic
    requirements_path = os.path.join(project_root, "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, 'w') as f:
            f.write("""# Core dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0

# AI/ML dependencies (optional - for real API usage)
openai>=1.0.0
anthropic>=0.7.0
google-generativeai>=0.3.0
langchain>=0.0.340
langchain-openai>=0.0.2
langchain-community>=0.0.10
langgraph>=0.0.10
chromadb>=0.4.18
sentence-transformers>=2.2.2

# Web scraping
beautifulsoup4>=4.12.0
requests>=2.31.0
playwright>=1.40.0
aiohttp>=3.9.0

# UI
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0

# Utilities
tenacity>=8.2.0
numpy>=1.24.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
""")
        print("Updated requirements.txt")

if __name__ == "__main__":
    main()