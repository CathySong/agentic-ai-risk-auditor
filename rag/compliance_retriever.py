#!/usr/bin/env python3
"""
ComplianceRetriever compatibility class.
Provides the same interface as RAGRetriever for compliance-specific use.
"""

import logging
from typing import Dict, List, Any, Optional
from .retriever import RAGRetriever, DocumentType, SearchResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceRetriever(RAGRetriever):
    """
    Compliance-specific retriever.
    Inherits from RAGRetriever for compatibility.
    """
    
    def __init__(self, collection_name: str = "compliance_knowledge"):
        """Initialize compliance retriever with specific collection."""
        super().__init__(collection_name=collection_name)
        logger.info(f"ComplianceRetriever initialized with collection: {collection_name}")
    
    async def search_compliance(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search for compliance-related information.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        # Add compliance-specific context to query
        compliance_query = f"compliance regulation {query}"
        return await self.search(compliance_query, limit=limit)
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """Get compliance-specific statistics."""
        stats = self.get_collection_stats()
        stats["retriever_type"] = "compliance"
        stats["description"] = "Compliance knowledge base for regulations and standards"
        return stats


# For backward compatibility
def create_compliance_retriever() -> ComplianceRetriever:
    """Factory function for creating ComplianceRetriever."""
    return ComplianceRetriever()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        retriever = ComplianceRetriever()
        print(f"Compliance retriever created: {retriever}")
        
        # Test getting stats
        stats = retriever.get_compliance_stats()
        print(f"Stats: {stats}")
    
    asyncio.run(test())