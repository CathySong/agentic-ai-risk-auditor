#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) retriever for the Agentic AI Risk Auditor.
Provides semantic search and document retrieval capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from datetime import datetime

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np

from app.config import settings
from models.embeddings import EmbeddingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of documents in the knowledge base."""
    LEGAL_REGULATION = "legal_regulation"
    AI_GUIDELINE = "ai_guideline"
    SECURITY_STANDARD = "security_standard"
    CASE_STUDY = "case_study"
    RESEARCH_PAPER = "research_paper"
    COMPANY_POLICY = "company_policy"
    RISK_ASSESSMENT = "risk_assessment"
    GENERAL = "general"


@dataclass
class Document:
    """Represents a document in the knowledge base."""
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "metadata": self.metadata,
            "score": self.score,
            "embedding_dim": len(self.embedding) if self.embedding else 0
        }


@dataclass
class SearchResult:
    """Represents a search result."""
    query: str
    documents: List[Document]
    total_results: int
    search_time_ms: float
    search_params: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "documents": [doc.to_dict() for doc in self.documents],
            "total_results": self.total_results,
            "search_time_ms": self.search_time_ms,
            "search_params": self.search_params
        }


class RAGRetriever:
    """RAG retriever for semantic search and document retrieval."""
    
    def __init__(self, collection_name: Optional[str] = None):
        self.collection_name = collection_name or settings.vectordb.default_collection
        self.embedding_model = EmbeddingModel()
        self.chroma_client = None
        self.collection = None
        
        self._initialize_chroma()
        logger.info(f"RAG retriever initialized with collection: {self.collection_name}")
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=settings.vectordb.chroma_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "AI Risk Auditor Knowledge Base"}
            )
            
            logger.info(f"ChromaDB collection ready: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            # Fallback to in-memory storage
            self._use_in_memory_storage()
    
    def _use_in_memory_storage(self):
        """Fallback to in-memory storage."""
        logger.warning("Using in-memory storage (ChromaDB not available)")
        self.documents = {}  # id -> Document
        self.embeddings = {}  # id -> embedding
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add documents to the knowledge base.
        
        Args:
            documents: List of document dictionaries with 'text' and optional 'metadata'
            batch_size: Batch size for embedding generation
            
        Returns:
            Dictionary with addition results
        """
        if not documents:
            return {"added": 0, "errors": 0, "total": 0}
        
        logger.info(f"Adding {len(documents)} documents to knowledge base")
        
        batch_size = batch_size or settings.vectordb.embedding_batch_size
        
        try:
            # Prepare documents for addition
            texts = []
            metadatas = []
            ids = []
            
            for doc in documents:
                text = doc.get("text", "")
                if not text.strip():
                    continue
                
                # Generate document ID
                doc_id = self._generate_document_id(text, doc.get("metadata", {}))
                
                # Prepare metadata
                metadata = doc.get("metadata", {}).copy()
                metadata.update({
                    "added_at": datetime.now().isoformat(),
                    "text_length": len(text),
                    "document_type": metadata.get("document_type", DocumentType.GENERAL.value)
                })
                
                texts.append(text)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Generate embeddings
            embeddings = await self.embedding_model.embed(texts, batch_size=batch_size)
            
            # Add to vector store
            if self.collection:
                # ChromaDB addition
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                # In-memory storage
                for i, doc_id in enumerate(ids):
                    self.documents[doc_id] = Document(
                        id=doc_id,
                        text=texts[i],
                        metadata=metadatas[i],
                        embedding=embeddings[i]
                    )
                    self.embeddings[doc_id] = embeddings[i]
            
            logger.info(f"Successfully added {len(ids)} documents")
            return {
                "added": len(ids),
                "errors": len(documents) - len(ids),
                "total": len(ids)
            }
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return {"added": 0, "errors": len(documents), "total": 0}
    
    async def search(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> SearchResult:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            parameters: Search parameters
            
        Returns:
            SearchResult object
        """
        if parameters is None:
            parameters = {}
        
        start_time = asyncio.get_event_loop().time()
        
        logger.info(f"Searching knowledge base: '{query}'")
        
        try:
            # Generate query embedding
            query_embedding = await self.embedding_model.embed(query)
            
            # Prepare search parameters
            n_results = parameters.get("n_results", settings.vectordb.search_results_limit)
            where_filter = parameters.get("where_filter", {})
            where_document_filter = parameters.get("where_document_filter", {})
            
            # Perform search
            if self.collection:
                # ChromaDB search
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_filter,
                    where_document=where_document_filter,
                    include=["documents", "metadatas", "distances"]
                )
                
                # Process results
                documents = []
                if results["documents"] and results["documents"][0]:
                    for i, (doc_text, metadata, distance) in enumerate(
                        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
                    ):
                        # Convert distance to similarity score
                        similarity_score = 1.0 - distance
                        
                        document = Document(
                            id=results["ids"][0][i] if results["ids"] and results["ids"][0] else f"result_{i}",
                            text=doc_text,
                            metadata=metadata,
                            score=similarity_score
                        )
                        documents.append(document)
                
                total_results = len(documents)
                
            else:
                # In-memory search
                documents = await self._in_memory_search(
                    query_embedding, n_results, where_filter
                )
                total_results = len(documents)
            
            # Calculate search time
            search_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            result = SearchResult(
                query=query,
                documents=documents,
                total_results=total_results,
                search_time_ms=search_time_ms,
                search_params=parameters
            )
            
            logger.info(f"Search complete: {total_results} results in {search_time_ms:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            
            # Return empty result
            search_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            return SearchResult(
                query=query,
                documents=[],
                total_results=0,
                search_time_ms=search_time_ms,
                search_params=parameters
            )
    
    async def _in_memory_search(
        self,
        query_embedding: List[float],
        n_results: int,
        where_filter: Dict[str, Any]
    ) -> List[Document]:
        """Perform in-memory search."""
        if not self.documents:
            return []
        
        # Calculate similarities
        similarities = []
        for doc_id, doc_embedding in self.embeddings.items():
            document = self.documents[doc_id]
            
            # Apply filters
            if where_filter:
                if not self._apply_filter(document.metadata, where_filter):
                    continue
            
            # Calculate similarity
            similarity = self.embedding_model.similarity(query_embedding, doc_embedding)
            similarities.append((similarity, document))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top results
        top_results = similarities[:n_results]
        documents = []
        for similarity, document in top_results:
            document.score = similarity
            documents.append(document)
        
        return documents
    
    def _apply_filter(self, metadata: Dict[str, Any], where_filter: Dict[str, Any]) -> bool:
        """Apply filter to metadata."""
        for key, value in where_filter.items():
            if key not in metadata:
                return False
            
            metadata_value = metadata[key]
            
            # Handle different filter types
            if isinstance(value, dict):
                # Complex filter (e.g., {"$eq": "value"})
                for op, op_value in value.items():
                    if op == "$eq":
                        if metadata_value != op_value:
                            return False
                    elif op == "$ne":
                        if metadata_value == op_value:
                            return False
                    elif op == "$in":
                        if metadata_value not in op_value:
                            return False
                    elif op == "$nin":
                        if metadata_value in op_value:
                            return False
                    elif op == "$gt":
                        if not (isinstance(metadata_value, (int, float)) and metadata_value > op_value):
                            return False
                    elif op == "$gte":
                        if not (isinstance(metadata_value, (int, float)) and metadata_value >= op_value):
                            return False
                    elif op == "$lt":
                        if not (isinstance(metadata_value, (int, float)) and metadata_value < op_value):
                            return False
                    elif op == "$lte":
                        if not (isinstance(metadata_value, (int, float)) and metadata_value <= op_value):
                            return False
            else:
                # Simple equality filter
                if metadata_value != value:
                    return False
        
        return True
    
    async def search_with_reranking(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> SearchResult:
        """
        Search with reranking for better relevance.
        
        Args:
            query: Search query
            parameters: Search parameters
            
        Returns:
            SearchResult with reranked documents
        """
        if parameters is None:
            parameters = {}
        
        # First, get initial search results
        initial_results = await self.search(query, parameters)
        
        if not initial_results.documents:
            return initial_results
        
        # Rerank using cross-encoder or other method
        reranked_documents = await self._rerank_documents(query, initial_results.documents)
        
        # Update results with reranked documents
        initial_results.documents = reranked_documents
        return initial_results
    
    async def _rerank_documents(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Document]:
        """Rerank documents for better relevance."""
        # Simple reranking: boost documents with query terms
        query_terms = set(query.lower().split())
        
        for document in documents:
            text_terms = set(document.text.lower().split())
            term_overlap = len(query_terms.intersection(text_terms))
            
            # Boost score based on term overlap
            if term_overlap > 0:
                boost = min(term_overlap * 0.05, 0.2)  # Max 20% boost
                if document.score:
                    document.score += boost
        
        # Re-sort by updated score
        documents.sort(key=lambda x: x.score or 0, reverse=True)
        return documents
    
    async def retrieve_for_qa(
        self,
        question: str,
        context_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents for question answering.
        
        Args:
            question: Question to answer
            context_size: Maximum context size in tokens
            
        Returns:
            Dictionary with retrieved context
        """
        context_size = context_size or settings.vectordb.context_size_limit
        
        # Search for relevant documents
        search_params = {
            "n_results": 5,
            "where_filter": {"document_type": {"$in": [
                DocumentType.LEGAL_REGULATION.value,
                DocumentType.AI_GUIDELINE.value,
                DocumentType.CASE_STUDY.value
            ]}}
        }
        
        search_result = await self.search(question, search_params)
        
        # Build context from retrieved documents
        context_parts = []
        total_tokens = 0
        
        for document in search_result.documents:
            # Estimate tokens (rough approximation)
            doc_tokens = len(document.text.split())
            
            if total_tokens + doc_tokens > context_size:
                # Truncate if needed
                remaining_tokens = context_size - total_tokens
                if remaining_tokens > 100:  # Minimum useful context
                    truncated_text = " ".join(document.text.split()[:remaining_tokens])
                    context_parts.append(f"[Source: {document.metadata.get('source', 'Unknown')}]\n{truncated_text}")
                    total_tokens += remaining_tokens
                break
            
            context_parts.append(f"[Source: {document.metadata.get('source', 'Unknown')}]\n{document.text}")
            total_tokens += doc_tokens
        
        context = "\n\n".join(context_parts)
        
        return {
            "question": question,
            "context": context,
            "documents_used": len(context_parts),
            "total_tokens": total_tokens,
            "search_results": search_result.to_dict()
        }
    
    async def similarity_search(
        self,
        text: str,
        n_results: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Find documents similar to the given text.
        
        Args:
            text: Text to find similar documents for
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # Generate embedding for the text
        text_embedding = await self.embedding_model.embed(text)
        
        # Search for similar documents
        search_result = await self.search(text, {"n_results": n_results})
        
        # Return documents with scores
        return [(doc, doc.score or 0.0) for doc in search_result.documents]
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        if self.collection:
            try:
                # Get collection info
                collection_info = self.collection.get()
                
                # Count documents by type
                doc_types = {}
                for metadata in collection_info.get("metadatas", []):
                    doc_type = metadata.get("document_type", "unknown")
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
                return {
                    "collection_name": self.collection_name,
                    "total_documents": len(collection_info.get("ids", [])),
                    "document_types": doc_types,
                    "embedding_dimension": self.embedding_model.get_embedding_dimension(),
                    "storage_type": "chromadb"
                }
                
            except Exception as e:
                logger.error(f"Failed to get collection stats: {e}")
        
        # In-memory stats
        doc_types = {}
        for doc in self.documents.values():
            doc_type = doc.metadata.get("document_type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        return {
            "collection_name": self.collection_name,
            "total_documents": len(self.documents),
            "document_types": doc_types,
            "embedding_dimension": self.embedding_model.get_embedding_dimension(),
            "storage_type": "in_memory"
        }
    
    def delete_documents(
        self,
        document_ids: Optional[List[str]] = None,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Delete documents from the knowledge base.
        
        Args:
            document_ids: List of document IDs to delete
            where_filter: Filter for documents to delete
            
        Returns:
            Dictionary with deletion results
        """
        try:
            if self.collection:
                # ChromaDB deletion
                if document_ids:
                    self.collection.delete(ids=document_ids)
                    deleted_count = len(document_ids)
                elif where_filter:
                    # Note: ChromaDB's where deletion might not return count
                    self.collection.delete(where=where_filter)
                    deleted_count = "unknown (filter-based)"
                else:
                    return {"deleted": 0, "error": "No deletion criteria provided"}
            else:
                # In-memory deletion
                deleted_count = 0
                ids_to_delete = set(document_ids or [])
                
                if where_filter:
                    # Find documents matching filter
                    for doc_id, document in list(self.documents.items()):
                        if self._apply_filter(document.metadata, where_filter):
                            ids_to_delete.add(doc_id)
                
                # Delete documents
                for doc_id in ids_to_delete:
                    if doc_id in self.documents:
                        del self.documents[doc_id]
                        if doc_id in self.embeddings:
                            del self.embeddings[doc_id]
                        deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} documents")
            return {"deleted": deleted_count, "success": True}
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return {"deleted": 0, "error": str(e), "success": False}
    
    def reset_collection(self) -> Dict[str, Any]:
        """Reset the entire collection."""
        try:
            if self.collection:
                # Delete and recreate collection
                self.chroma_client.delete_collection(self.collection_name)
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "AI Risk Auditor Knowledge Base (reset)"}
                )
            else:
                # Clear in-memory storage
                self.documents.clear()
                self.embeddings.clear()
            
            logger.info(f"Collection {self.collection_name} reset")
            return {"reset": True, "collection": self.collection_name}
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return {"reset": False, "error": str(e)}
    
    def _generate_document_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique document ID."""
        # Create hash from text and metadata
        content = text + json.dumps(metadata, sort_keys=True)
        hash_obj = hashlib.md5(content.encode())
        return f"doc_{hash_obj.hexdigest()[:16]}"
    
    async def batch_search(
        self,
        queries: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform batch search for multiple queries.
        
        Args:
            queries: List of search queries
            parameters: Search parameters
            
        Returns:
            List of SearchResult objects
        """
        if parameters is None:
            parameters = {}
        
        tasks = [self.search(query, parameters) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch search failed for query {i}: {result}")
                processed_results.append(SearchResult(
                    query=queries[i],
                    documents=[],
                    total_results=0,
                    search_time_ms=0,
                    search_params=parameters
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def hybrid_search(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> SearchResult:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            parameters: Search parameters
            
        Returns:
            SearchResult with hybrid results
        """
        if parameters is None:
            parameters = {}
        
        # Get semantic search results
        semantic_params = parameters.copy()
        semantic_result = await self.search(query, semantic_params)
        
        # Get keyword search results (if supported)
        keyword_results = []
        if self.collection:
            try:
                # ChromaDB supports where_document for keyword search
                keyword_params = parameters.copy()
                keyword_params["where_document"] = {"$contains": query.split()[0]}  # First word
                
                keyword_result = await self.search(query, keyword_params)
                keyword_results = keyword_result.documents
            except Exception as e:
                logger.warning(f"Keyword search not supported: {e}")
        
        # Combine and deduplicate results
        all_documents = {}
        
        # Add semantic results
        for doc in semantic_result.documents:
            all_documents[doc.id] = doc
        
        # Add keyword results with adjusted scores
        for doc in keyword_results:
            if doc.id in all_documents:
                # Boost score for documents found by both methods
                existing_doc = all_documents[doc.id]
                if existing_doc.score:
                    existing_doc.score += 0.1  # 10% boost
            else:
                # Add new document with keyword bonus
                if doc.score:
                    doc.score += 0.05  # 5% bonus for keyword match
                all_documents[doc.id] = doc
        
        # Sort by score
        sorted_documents = sorted(
            all_documents.values(),
            key=lambda x: x.score or 0,
            reverse=True
        )
        
        # Limit results
        n_results = parameters.get("n_results", settings.vectordb.search_results_limit)
        final_documents = sorted_documents[:n_results]
        
        return SearchResult(
            query=query,
            documents=final_documents,
            total_results=len(final_documents),
            search_time_ms=semantic_result.search_time_ms,
            search_params=parameters
        )


# Example usage
if __name__ == "__main__":
    async def test_rag_retriever():
        # Initialize retriever
        retriever = RAGRetriever()
        
        # Sample documents
        sample_documents = [
            {
                "text": "The GDPR requires explicit consent for data processing and gives users the right to access and delete their data.",
                "metadata": {
                    "source": "EU Regulation",
                    "document_type": DocumentType.LEGAL_REGULATION.value,
                    "year": 2018,
                    "jurisdiction": "EU"
                }
            },
            {
                "text": "AI systems must be transparent, accountable, and fair. Algorithmic bias must be mitigated through regular testing.",
                "metadata": {
                    "source": "AI Ethics Guidelines",
                    "document_type": DocumentType.AI_GUIDELINE.value,
                    "organization": "IEEE",
                    "version": "2.0"
                }
            },
            {
                "text": "Data breaches must be reported within 72 hours under GDPR. Companies must implement appropriate security measures.",
                "metadata": {
                    "source": "Security Standard",
                    "document_type": DocumentType.SECURITY_STANDARD.value,
                    "regulation": "GDPR",
                    "article": "33"
                }
            }
        ]
        
        try:
            # Add documents
            add_result = await retriever.add_documents(sample_documents)
            print(f"Added documents: {add_result}")
            
            # Get collection stats
            stats = retriever.get_collection_stats()
            print(f"\nCollection stats: {stats}")
            
            # Search for documents
            query = "What are the data protection requirements for AI systems?"
            search_result = await retriever.search(query, {"n_results": 3})
            
            print(f"\nSearch query: '{query}'")
            print(f"Found {search_result.total_results} results in {search_result.search_time_ms:.1f}ms")
            
            for i, doc in enumerate(search_result.documents, 1):
                print(f"\nResult {i}:")
                print(f"  Score: {doc.score:.3f}")
                print(f"  Source: {doc.metadata.get('source', 'Unknown')}")
                print(f"  Type: {doc.metadata.get('document_type', 'Unknown')}")
                print(f"  Text: {doc.text[:100]}...")
            
            # Test QA retrieval
            qa_context = await retriever.retrieve_for_qa(
                "What are the GDPR requirements for data breaches?"
            )
            print(f"\nQA Context:")
            print(f"  Documents used: {qa_context['documents_used']}")
            print(f"  Total tokens: {qa_context['total_tokens']}")
            print(f"  Context preview: {qa_context['context'][:200]}...")
            
            # Test hybrid search
            hybrid_result = await retriever.hybrid_search("AI transparency requirements")
            print(f"\nHybrid search: {hybrid_result.total_results} results")
            
            # Test batch search
            queries = ["data protection", "AI ethics", "security standards"]
            batch_results = await retriever.batch_search(queries, {"n_results": 2})
            
            print(f"\nBatch search results:")
            for i, result in enumerate(batch_results):
                print(f"  Query '{queries[i]}': {result.total_results} results")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(test_rag_retriever())