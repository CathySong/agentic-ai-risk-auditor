#!/usr/bin/env python3
"""
Simple search engine for compatibility.
"""

import logging
from typing import Dict, List, Any, Optional
import json
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEngine:
    """Simple search engine for compatibility."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.info("SearchEngine initialized (simple version)")
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for information related to the query."""
        logger.info(f"Searching for: {query}")
        
        # Simple mock implementation
        await asyncio.sleep(0.5)  # Simulate network delay
        
        mock_results = [
            {
                "title": f"AI Risk Assessment Guidelines for {query}",
                "url": "https://example.com/ai-risk-guidelines",
                "snippet": "Comprehensive guidelines for assessing AI risks including privacy, security, and compliance considerations.",
                "relevance": 0.95,
                "source": "example.com"
            },
            {
                "title": f"Best Practices for {query} Security",
                "url": "https://example.com/security-best-practices",
                "snippet": "Security best practices including threat modeling, vulnerability assessment, and incident response.",
                "relevance": 0.88,
                "source": "example.com"
            },
            {
                "title": f"Compliance Requirements for {query}",
                "url": "https://example.com/compliance-requirements",
                "snippet": "Overview of GDPR, CCPA, HIPAA and other compliance requirements for AI systems.",
                "relevance": 0.82,
                "source": "example.com"
            },
            {
                "title": f"Ethical Considerations in {query}",
                "url": "https://example.com/ethical-considerations",
                "snippet": "Discussion of ethical considerations including bias, fairness, transparency and accountability.",
                "relevance": 0.75,
                "source": "example.com"
            }
        ]
        
        return mock_results[:limit]
    
    async def search_multiple(self, queries: List[str], limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Search for multiple queries."""
        tasks = {query: self.search(query, limit) for query in queries}
        results = {}
        for query, task in tasks.items():
            results[query] = await task
        return results
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            "engine": "mock-search",
            "version": "1.0.0",
            "total_searches": 0,
            "mock_mode": True,
            "capabilities": ["web_search", "document_search"]
        }


# Example usage
if __name__ == "__main__":
    async def test():
        engine = SearchEngine()
        results = await engine.search("AI risk assessment", limit=3)
        print(f"Search results: {json.dumps(results, indent=2)}")
    
    asyncio.run(test())