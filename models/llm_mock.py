#!/usr/bin/env python3
"""
Mock LLM client for testing without API keys.
"""

import asyncio
import logging
import random
import json
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MOCK = "mock"


class MockLLMClient:
    """Mock LLM client for testing without API keys."""
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or LLMProvider.MOCK
        
        # Mock responses database
        self.mock_responses = {
            "ai_risk_assessment": [
                "AI risk assessment involves evaluating potential harms from AI systems, including privacy violations, security vulnerabilities, and ethical concerns.",
                "Key considerations for AI risk assessment include data privacy, algorithmic bias, transparency, accountability, and compliance with regulations like GDPR and CCPA.",
                "A comprehensive AI risk assessment should cover technical security, data governance, model fairness, and organizational accountability frameworks."
            ],
            "data_protection": [
                "GDPR requires explicit consent for data processing and gives users rights to access, rectify, and delete their personal data.",
                "Data protection measures should include encryption, access controls, data minimization, and regular security audits.",
                "Privacy by design and by default are key principles for compliant data processing systems."
            ],
            "security": [
                "AI systems must be secured against adversarial attacks, data poisoning, and model extraction.",
                "Security best practices include input validation, output sanitization, rate limiting, and continuous monitoring.",
                "Regular security testing and penetration testing are essential for maintaining AI system security."
            ],
            "compliance": [
                "Compliance with AI regulations requires transparency, human oversight, and risk management procedures.",
                "Organizations should establish AI governance frameworks with clear accountability and audit trails.",
                "Regular compliance audits and impact assessments help ensure ongoing regulatory adherence."
            ]
        }
        
        logger.info(f"Mock LLM client initialized with provider: {self.provider.value}")
    
    async def generate(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        max_tokens: Optional[int] = 500,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Generate mock text response.
        
        Args:
            prompt: Text prompt (alternative to messages)
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name (ignored in mock)
            temperature: Sampling temperature (affects response variation)
            max_tokens: Maximum tokens to generate
            response_format: Response format specification
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        # Get the text to analyze
        text = ""
        if prompt:
            text = prompt
        elif messages:
            # Extract the last user message
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    text = msg.get("content", "")
                    break
        
        logger.info(f"Mock LLM generating response for: {text[:100]}...")
        
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Determine response category based on prompt
        category = self._categorize_prompt(text)
        
        # Get mock response
        responses = self.mock_responses.get(category, self.mock_responses["ai_risk_assessment"])
        response = random.choice(responses)
        
        # Add some variation based on temperature
        if temperature and temperature > 0.5:
            variations = [
                f"Based on the query '{text[:50]}...', {response.lower()}",
                f"In response to your question: {response}",
                f"Analysis: {response} Additional considerations may apply based on specific context.",
                f"{response} This is a mock response for testing purposes."
            ]
            response = random.choice(variations)
        
        # Truncate if max_tokens is specified (rough approximation)
        if max_tokens:
            words = response.split()
            if len(words) > max_tokens // 3:  # Rough approximation: 3 chars per word
                response = " ".join(words[:max_tokens // 3]) + "..."
        
        # Format JSON if requested
        if response_format and response_format.get("type") == "json_object":
            response = json.dumps({
                "analysis": response,
                "category": category,
                "confidence": random.uniform(0.7, 0.95),
                "timestamp": datetime.now().isoformat(),
                "mock": True
            })
        
        return response
    
    async def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate mock embedding for text.
        
        Args:
            text: Text to embed
            model: Embedding model name
            
        Returns:
            Mock embedding vector
        """
        logger.info(f"Mock embedding for: {text[:50]}...")
        
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Generate deterministic but varied embedding based on text
        seed = hash(text) % 10000
        random.seed(seed)
        
        # Create mock embedding vector
        dimension = settings.vectordb.embedding_dimension
        embedding = [random.uniform(-1, 1) for _ in range(dimension)]
        
        # Normalize
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _categorize_prompt(self, text: str) -> str:
        """Categorize prompt to select appropriate mock response."""
        text_lower = text.lower()
        
        categories = {
            "data_protection": ["privacy", "gdpr", "ccpa", "data protection", "personal data"],
            "security": ["security", "vulnerability", "attack", "threat", "malware"],
            "compliance": ["compliance", "regulation", "legal", "law", "standard"],
            "ai_risk_assessment": ["ai", "artificial intelligence", "machine learning", "risk", "assessment"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "ai_risk_assessment"
    
    async def batch_generate(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[str]:
        """
        Generate mock text for multiple prompts in batch.
        
        Args:
            prompts: List of text prompts
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated texts
        """
        tasks = [self.generate(prompt=prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    async def batch_embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate mock embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            model: Embedding model name
            
        Returns:
            List of embedding vectors
        """
        tasks = [self.generate_embedding(text, model) for text in texts]
        return await asyncio.gather(*tasks)
    
    def get_model_info(self, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """
        Get information about available models.
        
        Args:
            provider: Provider to get models for (default: current provider)
            
        Returns:
            Dictionary with model information
        """
        return {
            "provider": self.provider.value,
            "available": True,
            "mock": True,
            "capabilities": ["text_generation", "embeddings"],
            "limitations": ["mock_data_only", "no_real_api_calls"]
        }


# Factory function to create appropriate client
def create_llm_client(provider: Optional[LLMProvider] = None):
    """Create LLM client based on configuration."""
    if settings.llm.use_mock:
        logger.info("Using mock LLM client (no API keys required)")
        return MockLLMClient(provider or LLMProvider.MOCK)
    else:
        # Import the real client only when needed
        from models.llm import LLMClient as RealLLMClient
        return RealLLMClient(provider)


# Example usage
if __name__ == "__main__":
    async def test_mock_llm():
        client = MockLLMClient()
        
        # Test generation
        prompt = "What are the key considerations for AI risk assessment?"
        response = await client.generate(prompt=prompt, temperature=0.7)
        print(f"Response: {response}")
        
        # Test embedding
        embedding = await client.generate_embedding("test text")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"Embedding sample: {embedding[:5]}")
        
        # Test batch operations
        prompts = ["test 1", "test 2"]
        responses = await client.batch_generate(prompts)
        print(f"Batch responses: {responses}")
    
    asyncio.run(test_mock_llm())