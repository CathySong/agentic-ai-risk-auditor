#!/usr/bin/env python3
"""
Main LLM client factory for the Agentic AI Risk Auditor.
Automatically selects between real API client and mock client based on configuration.
"""

import logging
from typing import Optional
from enum import Enum

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MOCK = "mock"


def create_llm_client(provider: Optional[LLMProvider] = None):
    """
    Create appropriate LLM client based on configuration.
    
    Args:
        provider: Preferred LLM provider
        
    Returns:
        LLM client instance (real or mock)
    """
    # Use mock mode if configured or no API keys available
    use_mock = settings.llm.use_mock
    
    if use_mock:
        logger.info("Using mock LLM client (no API keys required)")
        from models.llm_mock import MockLLMClient
        return MockLLMClient(provider or LLMProvider.MOCK)
    else:
        # Check if we have any API keys
        has_api_keys = (
            settings.llm.openai_api_key or
            settings.llm.anthropic_api_key or
            settings.llm.google_api_key
        )
        
        if not has_api_keys:
            logger.warning("No API keys found, falling back to mock mode")
            from models.llm_mock import MockLLMClient
            return MockLLMClient(provider or LLMProvider.MOCK)
        
        # Use real API client
        logger.info("Using real LLM client with API keys")
        from models.llm import LLMClient
        return LLMClient(provider)


# Convenience function for common use case
async def generate_text(prompt: str, **kwargs) -> str:
    """Generate text using the configured LLM client."""
    client = create_llm_client()
    return await client.generate(prompt=prompt, **kwargs)


async def generate_embedding(text: str, **kwargs) -> list:
    """Generate embedding using the configured LLM client."""
    client = create_llm_client()
    return await client.generate_embedding(text, **kwargs)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        client = create_llm_client()
        
        # Test generation
        response = await client.generate(
            prompt="What is AI risk assessment?",
            temperature=0.7,
            max_tokens=200
        )
        print(f"Response: {response}")
        
        # Test embedding
        embedding = await client.generate_embedding("test text")
        print(f"Embedding dimension: {len(embedding)}")
    
    asyncio.run(test())