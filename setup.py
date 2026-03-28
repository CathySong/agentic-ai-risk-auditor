from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentic-ai-risk-auditor",
    version="1.0.0",
    author="Cathy Song",
    author_email="cathy@example.com",
    description="Multi-agent system for automated AI risk assessment and compliance auditing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CathySong/agentic-ai-risk-auditor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "web": [
            "streamlit>=1.28.0",
            "plotly>=5.17.0",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-risk-auditor=app.main:main",
            "ai-risk-cli=scripts.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "agentic_ai_risk_auditor": [
            "*.md",
            "*.txt",
            "*.json",
        ],
    },
)