#!/usr/bin/env python3
"""
LLM client for the Agentic AI Risk Auditor.
Provides unified interface for multiple LLM providers.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from openai import AsyncOpenAI
import anthropic
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"


class LLMClient:
    """Unified LLM client supporting multiple providers."""
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or LLMProvider(settings.llm.default_provider)
        
        # Initialize clients based on configuration
        self.clients = {}
        self._initialize_clients()
        
        logger.info(f"LLM client initialized with provider: {self.provider.value}")
    
    def _initialize_clients(self):
        """Initialize LLM clients based on configuration."""
        # OpenAI client
        if settings.llm.openai_api_key:
            self.clients[LLMProvider.OPENAI] = AsyncOpenAI(
                api_key=settings.llm.openai_api_key,
                base_url=settings.llm.openai_api_base
            )
            logger.info("OpenAI client initialized")
        
        # Anthropic client
        if settings.llm.anthropic_api_key:
            self.clients[LLMProvider.ANTHROPIC] = anthropic.AsyncAnthropic(
                api_key=settings.llm.anthropic_api_key
            )
            logger.info("Anthropic client initialized")
        
        # Google client
        if settings.llm.google_api_key:
            genai.configure(api_key=settings.llm.google_api_key)
            self.clients[LLMProvider.GOOGLE] = genai
            logger.info("Google client initialized")
        
        # Cohere client (would be implemented similarly)
        # if settings.llm.cohere_api_key:
        #     self.clients[LLMProvider.COHERE] = ...
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Generate text using the configured LLM provider.
        
        Args:
            prompt: Text prompt (alternative to messages)
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name (overrides default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Response format specification
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Generated text
        """
        # Use default values if not provided
        model = model or self._get_default_model()
        temperature = temperature or settings.llm.openai_temperature
        max_tokens = max_tokens or settings.llm.openai_max_tokens
        
        # Prepare messages
        if prompt and not messages:
            messages = [{"role": "user", "content": prompt}]
        elif not messages:
            raise ValueError("Either prompt or messages must be provided")
        
        try:
            # Call appropriate provider
            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    **kwargs
                )
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            elif self.provider == LLMProvider.GOOGLE:
                return await self._generate_google(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            
            # Try fallback provider if available
            if self.provider != LLMProvider.OPENAI and LLMProvider.OPENAI in self.clients:
                logger.info("Falling back to OpenAI")
                self.provider = LLMProvider.OPENAI
                return await self.generate(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    **kwargs
                )
            
            raise
    
    async def _generate_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate using OpenAI API."""
        if LLMProvider.OPENAI not in self.clients:
            raise ValueError("OpenAI client not initialized")
        
        client = self.clients[LLMProvider.OPENAI]
        
        # Prepare API parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        if response_format:
            params["response_format"] = response_format
        
        try:
            response = await client.chat.completions.create(**params)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Generate using Anthropic API."""
        if LLMProvider.ANTHROPIC not in self.clients:
            raise ValueError("Anthropic client not initialized")
        
        client = self.clients[LLMProvider.ANTHROPIC]
        
        # Convert messages to Anthropic format
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        try:
            response = await client.messages.create(
                model=model,
                system=system_message,
                messages=anthropic_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def _generate_google(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Generate using Google Gemini API."""
        if LLMProvider.GOOGLE not in self.clients:
            raise ValueError("Google client not initialized")
        
        # Configure model
        genai_model = genai.GenerativeModel(model)
        
        # Convert messages to Google format
        google_messages = []
        for msg in messages:
            google_messages.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            })
        
        try:
            # Note: Google's async API might be different
            # This is a simplified synchronous version
            response = genai_model.generate_content(
                contents=google_messages,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    **kwargs
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise
    
    async def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            model: Embedding model name
            
        Returns:
            Embedding vector
        """
        model = model or settings.llm.openai_embedding_model
        
        if self.provider == LLMProvider.OPENAI:
            return await self._generate_openai_embedding(text, model)
        else:
            # For other providers, fall back to OpenAI for embeddings
            if LLMProvider.OPENAI in self.clients:
                return await self._generate_openai_embedding(text, model)
            else:
                raise ValueError("Embedding generation not supported for current provider")
    
    async def _generate_openai_embedding(self, text: str, model: str) -> List[float]:
        """Generate embedding using OpenAI."""
        if LLMProvider.OPENAI not in self.clients:
            raise ValueError("OpenAI client not initialized")
        
        client = self.clients[LLMProvider.OPENAI]
        
        try:
            response = await client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    def _get_default_model(self) -> str:
        """Get default model for current provider."""
        if self.provider == LLMProvider.OPENAI:
            return settings.llm.openai_model
        elif self.provider == LLMProvider.ANTHROPIC:
            return settings.llm.anthropic_model
        elif self.provider == LLMProvider.GOOGLE:
            return settings.llm.google_model
        elif self.provider == LLMProvider.COHERE:
            return settings.llm.cohere_model
        else:
            return settings.llm.openai_model  # Fallback
    
    async def batch_generate(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[str]:
        """
        Generate text for multiple prompts in batch.
        
        Args:
            prompts: List of text prompts
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated texts
        """
        tasks = [self.generate(prompt=prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def batch_embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            model: Embedding model name
            
        Returns:
            List of embedding vectors
        """
        tasks = [self.generate_embedding(text, model) for text in texts]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def switch_provider(self, provider: LLMProvider):
        """
        Switch to a different LLM provider.
        
        Args:
            provider: New provider to use
        """
        if provider not in self.clients:
            raise ValueError(f"Provider {provider.value} not initialized")
        
        self.provider = provider
        logger.info(f"Switched to provider: {provider.value}")
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers."""
        return list(self.clients.keys())
    
    def get_model_info(self, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """
        Get information about available models.
        
        Args:
            provider: Provider to get models for (default: current provider)
            
        Returns:
            Dictionary with model information
        """
        provider = provider or self.provider
        
        model_info = {
            "provider": provider.value,
            "available": provider in self.clients
        }
        
        if provider == LLMProvider.OPENAI:
            model_info.update({
                "default_model": settings.llm.openai_model,
                "embedding_model": settings.llm.openai_embedding_model,
                "max_tokens": settings.llm.openai_max_tokens,
                "temperature_range": (0.0, 2.0)
            })
        elif provider == LLMProvider.ANTHROPIC:
            model_info.update({
                "default_model": settings.llm.anthropic_model,
                "max_tokens": 4096,  # Typical for Claude
                "temperature_range": (0.0, 1.0)
            })
        elif provider == LLMProvider.GOOGLE:
            model_info.update({
                "default_model": settings.llm.google_model,
                "max_tokens": 8192,  # Typical for Gemini
                "temperature_range": (0.0, 1.0)
            })
        
        return model_info


# Example usage
if __name__ == "__main__":
    async def test_llm_client():
        # Initialize client
        client = LLMClient()
        
        # Test generation
        prompt = "What are the key considerations for AI risk assessment?"
        
        try:
            response = await client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            print(f"Generated response ({len(response)} characters):")
            print(response[:200] + "...")
            
            # Test embedding
            embedding = await client.generate_embedding(prompt)
            print(f"\nEmbedding dimension: {len(embedding)}")
            print(f"Embedding sample: {embedding[:5]}...")
            
            # Test batch generation
            prompts = [
                "What is AI safety?",
                "Explain data privacy in AI systems"
            ]
            
            batch_responses = await client.batch_generate(prompts, max_tokens=200)
            print(f"\nBatch responses: {len(batch_responses)}")
            
            # Get model info
            info = client.get_model_info()
            print(f"\nModel info: {info}")
            
            # List available providers
            providers = client.get_available_providers()
            print(f"Available providers: {[p.value for p in providers]}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(test_llm_client())