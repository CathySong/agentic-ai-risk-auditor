#!/usr/bin/env python3
"""
Document parser for various file formats.
Simplified version for compatibility.
"""

import logging
from typing import Dict, List, Any, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentParser:
    """Simple document parser for text extraction."""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.md', '.html', '.json']
    
    async def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with parsed content and metadata
        """
        logger.info(f"Parsing document: {file_path}")
        
        try:
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {ext}",
                    "content": "",
                    "metadata": {}
                }
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic metadata
            metadata = {
                "file_path": file_path,
                "file_size": len(content),
                "file_extension": ext,
                "line_count": len(content.splitlines()),
                "word_count": len(content.split())
            }
            
            return {
                "success": True,
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Document parsing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "metadata": {}
            }
    
    async def parse_text(self, text: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse text content directly.
        
        Args:
            text: Text content to parse
            metadata: Optional metadata
            
        Returns:
            Dictionary with parsed content
        """
        logger.info("Parsing text content")
        
        try:
            metadata = metadata or {}
            metadata.update({
                "content_type": "text",
                "text_length": len(text),
                "line_count": len(text.splitlines()),
                "word_count": len(text.split())
            })
            
            return {
                "success": True,
                "content": text,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Text parsing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "metadata": {}
            }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return self.supported_formats.copy()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        parser = DocumentParser()
        
        # Test text parsing
        result = await parser.parse_text("This is a test document for AI risk assessment.")
        print(f"Text parsing result: {result}")
        
        # Test supported formats
        formats = parser.get_supported_formats()
        print(f"Supported formats: {formats}")
    
    asyncio.run(test())