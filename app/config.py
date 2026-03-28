#!/usr/bin/env python3
"""
Fixed configuration for the Agentic AI Risk Auditor.
Compatible with Pydantic 2.x and pydantic-settings.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseSettings):
    """Configuration for LLM providers."""
    
    # Mock mode for testing (no API keys needed)
    use_mock: bool = Field(True, alias="LLM_USE_MOCK")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    openai_api_base: str = Field("https://api.openai.com/v1", alias="OPENAI_API_BASE")
    openai_model: str = Field("gpt-3.5-turbo", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field("text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    openai_temperature: float = Field(0.1, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(2000, alias="OPENAI_MAX_TOKENS")
    
    # Anthropic (optional)
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-haiku-20240307", alias="ANTHROPIC_MODEL")
    
    # Google (optional)
    google_api_key: Optional[str] = Field(None, alias="GOOGLE_API_KEY")
    google_model: str = Field("gemini-pro", alias="GOOGLE_MODEL")
    
    # Default provider
    default_provider: str = Field("openai", alias="DEFAULT_LLM_PROVIDER")
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_"
        extra = "ignore"


class VectorDBConfig(BaseSettings):
    """Configuration for vector databases."""
    
    # ChromaDB
    chroma_db_path: str = Field("./chroma_db", alias="CHROMA_DB_PATH")
    default_collection: str = Field("ai_risk_knowledge", alias="DEFAULT_COLLECTION")
    
    # Embedding settings
    embedding_dimension: int = Field(1536, alias="EMBEDDING_DIMENSION")
    embedding_batch_size: int = Field(32, alias="EMBEDDING_BATCH_SIZE")
    
    # Search settings
    search_results_limit: int = Field(10, alias="SEARCH_RESULTS_LIMIT")
    context_size_limit: int = Field(4000, alias="CONTEXT_SIZE_LIMIT")
    
    class Config:
        env_file = ".env"
        env_prefix = "VECTORDB_"
        extra = "ignore"


class ToolConfig(BaseSettings):
    """Configuration for tools."""
    
    # Web scraping
    web_scraper_timeout: int = Field(60, alias="WEB_SCRAPER_TIMEOUT")
    web_scraper_max_pages: int = Field(10, alias="WEB_SCRAPER_MAX_PAGES")
    web_scraper_user_agent: str = Field(
        "Mozilla/5.0 (compatible; AgenticAIRiskAuditor/1.0)",
        alias="WEB_SCRAPER_USER_AGENT"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "TOOL_"
        extra = "ignore"


class ServerConfig(BaseSettings):
    """Configuration for server."""
    
    host: str = Field("0.0.0.0", alias="SERVER_HOST")
    port: int = Field(8000, alias="SERVER_PORT")
    reload: bool = Field(True, alias="SERVER_RELOAD")
    
    class Config:
        env_file = ".env"
        env_prefix = "SERVER_"
        extra = "ignore"


class Settings(BaseSettings):
    """Main settings class."""
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vectordb: VectorDBConfig = Field(default_factory=VectorDBConfig)
    tool: ToolConfig = Field(default_factory=ToolConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    # General settings
    debug: bool = Field(True, alias="DEBUG")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Create global settings instance
settings = Settings()