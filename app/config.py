#!/usr/bin/env python3
"""
Configuration settings for the Agentic AI Risk Auditor.
Uses Pydantic settings management with environment variable support.
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
from pydantic.tools import parse_obj_as
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseSettings):
    """Configuration for LLM providers."""
    
    # OpenAI
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_api_base: str = Field("https://api.openai.com/v1", env="OPENAI_API_BASE")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_embedding_model: str = Field("text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    openai_temperature: float = Field(0.1, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(4000, env="OPENAI_MAX_TOKENS")
    
    # Anthropic (optional)
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-opus-20240229", env="ANTHROPIC_MODEL")
    
    # Google (optional)
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    google_model: str = Field("gemini-pro", env="GOOGLE_MODEL")
    
    # Cohere (optional)
    cohere_api_key: Optional[str] = Field(None, env="COHERE_API_KEY")
    cohere_model: str = Field("command", env="COHERE_MODEL")
    
    # Default provider
    default_provider: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_"


class VectorDBConfig(BaseSettings):
    """Configuration for vector databases."""
    
    # Pinecone
    pinecone_api_key: Optional[str] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: str = Field("us-east-1", env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field("ai-risk-auditor", env="PINECONE_INDEX_NAME")
    
    # Qdrant
    qdrant_url: str = Field("http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    qdrant_collection_name: str = Field("ai_risk_auditor", env="QDRANT_COLLECTION_NAME")
    
    # Chroma (local)
    chroma_persist_directory: str = Field("./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Default vector store
    default_vector_store: str = Field("chroma", env="DEFAULT_VECTOR_STORE")
    
    # Embedding settings
    embedding_dimension: int = Field(1536, env="EMBEDDING_DIMENSION")  # OpenAI text-embedding-3-small
    embedding_batch_size: int = Field(100, env="EMBEDDING_BATCH_SIZE")
    
    class Config:
        env_file = ".env"
        env_prefix = "VECTORDB_"


class Web3Config(BaseSettings):
    """Configuration for Web3/blockchain tools."""
    
    # Infura
    infura_api_key: Optional[str] = Field(None, env="INFURA_API_KEY")
    infura_api_secret: Optional[str] = Field(None, env="INFURA_API_SECRET")
    
    # Alchemy
    alchemy_api_key: Optional[str] = Field(None, env="ALCHEMY_API_KEY")
    
    # Etherscan
    etherscan_api_key: Optional[str] = Field(None, env="ETHERSCAN_API_KEY")
    
    # Default Web3 provider
    default_web3_provider: str = Field("infura", env="DEFAULT_WEB3_PROVIDER")
    
    # Smart contract analysis
    slither_enabled: bool = Field(True, env="SLITHER_ENABLED")
    mythril_enabled: bool = Field(True, env="MYTHRIL_ENABLED")
    
    # Analysis timeout (seconds)
    contract_analysis_timeout: int = Field(300, env="CONTRACT_ANALYSIS_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_prefix = "WEB3_"


class ToolConfig(BaseSettings):
    """Configuration for external tools."""
    
    # Web scraping
    web_scraper_timeout: int = Field(30, env="WEB_SCRAPER_TIMEOUT")
    web_scraper_max_pages: int = Field(10, env="WEB_SCRAPER_MAX_PAGES")
    web_scraper_user_agent: str = Field(
        "Mozilla/5.0 (compatible; AgenticAIRiskAuditor/1.0; +https://github.com/yourusername/agentic-ai-risk-auditor)",
        env="WEB_SCRAPER_USER_AGENT"
    )
    
    # Search
    serpapi_api_key: Optional[str] = Field(None, env="SERPAPI_API_KEY")
    google_search_api_key: Optional[str] = Field(None, env="GOOGLE_SEARCH_API_KEY")
    google_search_cx: Optional[str] = Field(None, env="GOOGLE_SEARCH_CX")
    
    # Document parsing
    max_document_size_mb: int = Field(50, env="MAX_DOCUMENT_SIZE_MB")
    supported_document_formats: List[str] = Field(
        default_factory=lambda: [".pdf", ".docx", ".txt", ".md", ".html", ".json"],
        env="SUPPORTED_DOCUMENT_FORMATS"
    )
    
    # Rate limiting
    requests_per_minute: int = Field(60, env="REQUESTS_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_prefix = "TOOL_"
        
    @validator("supported_document_formats", pre=True)
    def parse_supported_formats(cls, v):
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v


class AgentConfig(BaseSettings):
    """Configuration for agent system."""
    
    # Planner agent
    planner_model: str = Field("gpt-4-turbo-preview", env="PLANNER_MODEL")
    planner_temperature: float = Field(0.2, env="PLANNER_TEMPERATURE")
    max_planning_steps: int = Field(10, env="MAX_PLANNING_STEPS")
    
    # Executor agent
    executor_model: str = Field("gpt-4-turbo-preview", env="EXECUTOR_MODEL")
    executor_temperature: float = Field(0.1, env="EXECUTOR_TEMPERATURE")
    max_execution_time: int = Field(600, env="MAX_EXECUTION_TIME")  # 10 minutes
    
    # Memory
    memory_window_size: int = Field(10, env="MEMORY_WINDOW_SIZE")
    memory_persistence: bool = Field(True, env="MEMORY_PERSISTENCE")
    memory_db_path: str = Field("./memory.db", env="MEMORY_DB_PATH")
    
    # Workflow
    max_parallel_tasks: int = Field(3, env="MAX_PARALLEL_TASKS")
    workflow_timeout: int = Field(1800, env="WORKFLOW_TIMEOUT")  # 30 minutes
    
    # Risk scoring
    risk_score_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "critical": 10.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 1.0
        },
        env="RISK_SCORE_WEIGHTS"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "AGENT_"
        
    @validator("risk_score_weights", pre=True)
    def parse_risk_weights(cls, v):
        if isinstance(v, str):
            # Parse string like "critical:10,high:7,medium:4,low:1"
            weights = {}
            for pair in v.split(","):
                key, value = pair.split(":")
                weights[key.strip()] = float(value.strip())
            return weights
        return v


class ComplianceConfig(BaseSettings):
    """Configuration for compliance checking."""
    
    # Regulations database
    regulations_db_path: str = Field("./rag/data/regulations", env="REGULATIONS_DB_PATH")
    policies_db_path: str = Field("./rag/data/policies", env="POLICIES_DB_PATH")
    
    # Default regulations to check
    default_regulations: List[str] = Field(
        default_factory=lambda: ["GDPR", "CCPA", "AI Act", "HIPAA", "PCI-DSS"],
        env="DEFAULT_REGULATIONS"
    )
    
    # RAG settings
    rag_top_k: int = Field(5, env="RAG_TOP_K")
    rag_similarity_threshold: float = Field(0.7, env="RAG_SIMILARITY_THRESHOLD")
    rag_chunk_size: int = Field(1000, env="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(200, env="RAG_CHUNK_OVERLAP")
    
    # Compliance scoring
    compliance_threshold: float = Field(0.8, env="COMPLIANCE_THRESHOLD")
    
    class Config:
        env_file = ".env"
        env_prefix = "COMPLIANCE_"
        
    @validator("default_regulations", pre=True)
    def parse_regulations(cls, v):
        if isinstance(v, str):
            return [reg.strip() for reg in v.split(",")]
        return v


class APIConfig(BaseSettings):
    """Configuration for API server."""
    
    # Server
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    debug: bool = Field(False, env="DEBUG")
    
    # CORS
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8501"],
        env="ALLOWED_ORIGINS"
    )
    
    # Authentication (optional)
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    require_api_key: bool = Field(False, env="REQUIRE_API_KEY")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_prefix = "API_"
        
    @validator("allowed_origins", pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class EvaluationConfig(BaseSettings):
    """Configuration for evaluation framework."""
    
    # Dataset
    eval_dataset_path: str = Field("./eval/dataset.json", env="EVAL_DATASET_PATH")
    eval_max_cases: int = Field(100, env="EVAL_MAX_CASES")
    
    # Metrics
    eval_metrics: List[str] = Field(
        default_factory=lambda: ["accuracy", "completeness", "response_time", "cost"],
        env="EVAL_METRICS"
    )
    
    # Execution
    eval_timeout_seconds: int = Field(30, env="EVAL_TIMEOUT_SECONDS")
    eval_parallel_tasks: int = Field(3, env="EVAL_PARALLEL_TASKS")
    
    # Output
    eval_output_dir: str = Field("./outputs/evaluation", env="EVAL_OUTPUT_DIR")
    
    class Config:
        env_file = ".env"
        env_prefix = "EVAL_"
        
    @validator("eval_metrics", pre=True)
    def parse_metrics(cls, v):
        if isinstance(v, str):
            return [metric.strip() for metric in v.split(",")]
        return v


class Settings(BaseSettings):
    """Main settings class combining all configurations."""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    secret_key: str = Field("your-secret-key-change-in-production", env="SECRET_KEY")
    
    # Database (optional)
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vectordb: VectorDBConfig = Field(default_factory=VectorDBConfig)
    web3: Web3Config = Field(default_factory=Web3Config)
    tool: ToolConfig = Field(default_factory=ToolConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() == "testing"


# Global settings instance
settings = Settings()

# Export for easy import
__all__ = ["settings"]