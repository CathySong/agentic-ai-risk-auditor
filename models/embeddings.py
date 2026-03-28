#!/usr/bin/env python3
"""
Embedding models for the Agentic AI Risk Auditor.
Provides unified interface for text embeddings.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from app.config import settings
from models.llm import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingModelType(Enum):
    """Types of embedding models."""
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    LOCAL = "local"


class EmbeddingModel:
    """Unified embedding model interface."""
    
    def __init__(
        self,
        model_type: Optional[EmbeddingModelType] = None,
        model_name: Optional[str] = None,
        device: Optional[str] = None
    ):
        self.model_type = model_type or EmbeddingModelType(settings.vectordb.default_vector_store)
        self.model_name = model_name or self._get_default_model_name()
        self.device = device or self._get_default_device()
        
        # Initialize model
        self.model = None
        self.llm_client = None
        self._initialize_model()
        
        logger.info(f"Embedding model initialized: {self.model_type.value}/{self.model_name}")
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        if self.model_type == EmbeddingModelType.OPENAI:
            # Use OpenAI API via LLM client
            self.llm_client = LLMClient()
            logger.info("Using OpenAI embeddings via API")
            
        elif self.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
            # Load local sentence transformer model
            try:
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )
                logger.info(f"SentenceTransformer model loaded: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model: {e}")
                # Fall back to OpenAI
                self.model_type = EmbeddingModelType.OPENAI
                self.llm_client = LLMClient()
                logger.info("Falling back to OpenAI embeddings")
                
        elif self.model_type == EmbeddingModelType.LOCAL:
            # For custom local models
            # This would be extended for specific local models
            logger.warning("Local embedding model type requires custom implementation")
            # Fall back to sentence transformers
            self.model_type = EmbeddingModelType.SENTENCE_TRANSFORMERS
            self._initialize_model()
    
    def _get_default_model_name(self) -> str:
        """Get default model name for current type."""
        if self.model_type == EmbeddingModelType.OPENAI:
            return settings.llm.openai_embedding_model
        elif self.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
            return "all-MiniLM-L6-v2"  # Good default for semantic search
        elif self.model_type == EmbeddingModelType.LOCAL:
            return "local-model"
        else:
            return "all-MiniLM-L6-v2"
    
    def _get_default_device(self) -> str:
        """Get default device for local models."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    async def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: Optional[int] = None,
        normalize: bool = True,
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for processing
            normalize: Whether to normalize embeddings
            **kwargs: Additional model-specific parameters
            
        Returns:
            Single embedding or list of embeddings
        """
        # Handle single text
        single_text = isinstance(texts, str)
        if single_text:
            texts = [texts]
        
        if not texts:
            return [] if not single_text else []
        
        # Generate embeddings based on model type
        if self.model_type == EmbeddingModelType.OPENAI:
            embeddings = await self._embed_openai(texts, **kwargs)
        elif self.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
            embeddings = await self._embed_sentence_transformers(texts, batch_size, **kwargs)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        # Normalize if requested
        if normalize:
            embeddings = self._normalize_embeddings(embeddings)
        
        # Return single embedding for single text
        if single_text and embeddings:
            return embeddings[0]
        
        return embeddings
    
    async def _embed_openai(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        if not self.llm_client:
            raise ValueError("LLM client not initialized for OpenAI embeddings")
        
        try:
            # Use batch embedding if available
            embeddings = await self.llm_client.batch_embed(
                texts=texts,
                model=self.model_name
            )
            
            # Handle any exceptions in batch
            valid_embeddings = []
            for i, emb in enumerate(embeddings):
                if isinstance(emb, Exception):
                    logger.error(f"Failed to embed text {i}: {emb}")
                    # Create zero vector as fallback
                    zero_emb = [0.0] * settings.vectordb.embedding_dimension
                    valid_embeddings.append(zero_emb)
                else:
                    valid_embeddings.append(emb)
            
            return valid_embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            # Return zero vectors as fallback
            zero_emb = [0.0] * settings.vectordb.embedding_dimension
            return [zero_emb] * len(texts)
    
    async def _embed_sentence_transformers(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        **kwargs
    ) -> List[List[float]]:
        """Generate embeddings using SentenceTransformers."""
        if not self.model:
            raise ValueError("SentenceTransformer model not initialized")
        
        batch_size = batch_size or settings.vectordb.embedding_batch_size
        
        try:
            # Convert to numpy array for processing
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                **kwargs
            )
            
            # Convert to list of lists
            embeddings_list = embeddings.tolist()
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"SentenceTransformer embedding failed: {e}")
            # Return zero vectors as fallback
            zero_emb = [0.0] * self.model.get_sentence_embedding_dimension()
            return [zero_emb] * len(texts)
    
    def _normalize_embeddings(self, embeddings: List[List[float]]) -> List[List[float]]:
        """Normalize embeddings to unit length."""
        normalized = []
        
        for emb in embeddings:
            emb_array = np.array(emb)
            norm = np.linalg.norm(emb_array)
            
            if norm > 0:
                normalized_emb = (emb_array / norm).tolist()
            else:
                normalized_emb = emb  # Keep as is if zero vector
            
            normalized.append(normalized_emb)
        
        return normalized
    
    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
        metric: str = "cosine"
    ) -> float:
        """
        Calculate similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            metric: Similarity metric ('cosine', 'dot', 'euclidean')
            
        Returns:
            Similarity score
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        if metric == "cosine":
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 > 0 and norm2 > 0:
                return dot_product / (norm1 * norm2)
            else:
                return 0.0
                
        elif metric == "dot":
            # Dot product
            return float(np.dot(vec1, vec2))
            
        elif metric == "euclidean":
            # Euclidean distance (converted to similarity)
            distance = np.linalg.norm(vec1 - vec2)
            return 1.0 / (1.0 + distance)  # Convert to similarity
            
        else:
            raise ValueError(f"Unsupported similarity metric: {metric}")
    
    def batch_similarity(
        self,
        query_embedding: List[float],
        document_embeddings: List[List[float]],
        metric: str = "cosine",
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate similarity between query and multiple documents.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of document embeddings
            metric: Similarity metric
            top_k: Return only top K results
            
        Returns:
            List of similarity results with indices and scores
        """
        results = []
        
        for i, doc_emb in enumerate(document_embeddings):
            score = self.similarity(query_embedding, doc_emb, metric)
            results.append({
                "index": i,
                "score": score,
                "embedding": doc_emb
            })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top K if specified
        if top_k is not None:
            results = results[:top_k]
        
        return results
    
    async def embed_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "text",
        batch_size: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Embed a list of documents.
        
        Args:
            documents: List of documents (dictionaries)
            text_field: Field containing text to embed
            batch_size: Batch size for embedding
            **kwargs: Additional embedding parameters
            
        Returns:
            List of documents with embeddings added
        """
        # Extract texts
        texts = [doc.get(text_field, "") for doc in documents]
        
        # Generate embeddings
        embeddings = await self.embed(texts, batch_size=batch_size, **kwargs)
        
        # Add embeddings to documents
        embedded_docs = []
        for i, (doc, emb) in enumerate(zip(documents, embeddings)):
            embedded_doc = doc.copy()
            embedded_doc["embedding"] = emb
            embedded_doc["embedding_dimension"] = len(emb)
            embedded_docs.append(embedded_doc)
        
        return embedded_docs
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self.model_type == EmbeddingModelType.OPENAI:
            return settings.vectordb.embedding_dimension
        elif self.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS and self.model:
            return self.model.get_sentence_embedding_dimension()
        else:
            return 384  # Default for MiniLM models
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_type": self.model_type.value,
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dimension": self.get_embedding_dimension(),
            "normalized": True,
            "supports_batch": True
        }
    
    def save_model(self, path: str):
        """Save the model to disk (for local models)."""
        if self.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS and self.model:
            self.model.save(path)
            logger.info(f"Model saved to {path}")
        else:
            logger.warning("Model saving only supported for local SentenceTransformer models")
    
    def load_model(self, path: str):
        """Load a model from disk (for local models)."""
        if self.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(path, device=self.device)
                self.model_name = path
                logger.info(f"Model loaded from {path}")
            except Exception as e:
                logger.error(f"Failed to load model from {path}: {e}")
        else:
            logger.warning("Model loading only supported for local SentenceTransformer models")


# Example usage
if __name__ == "__main__":
    async def test_embeddings():
        # Initialize embedding model
        embedder = EmbeddingModel()
        
        # Test single embedding
        text = "AI risk assessment involves evaluating potential harms from AI systems."
        
        try:
            embedding = await embedder.embed(text)
            print(f"Single embedding dimension: {len(embedding)}")
            print(f"Embedding sample: {embedding[:5]}...")
            
            # Test batch embeddings
            texts = [
                "Data privacy is crucial for AI systems.",
                "Security vulnerabilities can compromise AI models.",
                "Ethical considerations include fairness and transparency."
            ]
            
            embeddings = await embedder.embed(texts, batch_size=2)
            print(f"\nBatch embeddings: {len(embeddings)}")
            print(f"Each dimension: {len(embeddings[0])}")
            
            # Test similarity
            sim_score = embedder.similarity(embeddings[0], embeddings[1])
            print(f"\nSimilarity between first two texts: {sim_score:.4f}")
            
            # Test batch similarity
            query = "AI security and privacy"
            query_embedding = await embedder.embed(query)
            
            similarities = embedder.batch_similarity(
                query_embedding,
                embeddings,
                top_k=2
            )
            
            print(f"\nTop similarities for query '{query}':")
            for sim in similarities:
                print(f"  Score {sim['score']:.4f} for text {sim['index']}")
            
            # Test document embedding
            documents = [
                {"id": 1, "text": "GDPR compliance requires data protection."},
                {"id": 2, "text": "AI systems must be transparent and explainable."},
                {"id": 3, "text": "Security testing is essential for AI deployment."}
            ]
            
            embedded_docs = await embedder.embed_documents(documents)
            print(f"\nEmbedded {len(embedded_docs)} documents")
            print(f"First document keys: {list(embedded_docs[0].keys())}")
            
            # Get model info
            info = embedder.get_model_info()
            print(f"\nModel info: {info}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(test_embeddings())