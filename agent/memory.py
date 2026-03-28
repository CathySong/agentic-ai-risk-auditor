#!/usr/bin/env python3
"""
Memory system for the Agentic AI Risk Auditor.
Manages context, state, and persistence for the agent system.
"""

import json
import logging
import pickle
import sqlite3
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import hashlib

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Represents an item in memory."""
    id: str
    content: Any
    metadata: Dict[str, Any]
    timestamp: float
    importance: float  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: float = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AuditMemoryRecord:
    """Record of an audit in memory."""
    audit_id: str
    request: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: datetime
    context: Dict[str, Any] = None
    findings: List[Dict[str, Any]] = None
    recommendations: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.findings is None:
            self.findings = []
        if self.recommendations is None:
            self.recommendations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "audit_id": self.audit_id,
            "request": self.request,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "findings": self.findings,
            "recommendations": self.recommendations
        }


class AuditMemory:
    """Memory system for audit context and state management."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.agent.memory_db_path
        self.memory_window = settings.agent.memory_window_size
        self.persistence = settings.agent.memory_persistence
        
        # In-memory storage
        self.short_term_memory: Dict[str, MemoryItem] = {}
        self.audit_memory: Dict[str, AuditMemoryRecord] = {}
        self.context_memory: Dict[str, Any] = {}
        
        # Initialize database if persistence is enabled
        if self.persistence:
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for persistence."""
        try:
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create tables
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_memory (
                    audit_id TEXT PRIMARY KEY,
                    request TEXT,
                    result TEXT,
                    timestamp TEXT,
                    context TEXT,
                    findings TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata TEXT,
                    timestamp REAL,
                    importance REAL,
                    access_count INTEGER,
                    last_accessed REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS context_memory (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info(f"Memory database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory database: {e}")
            self.persistence = False
    
    def save_audit(self, audit_result: Any):
        """
        Save an audit result to memory.
        
        Args:
            audit_result: AuditResult object from app.main
        """
        try:
            # Convert audit result to record
            record = AuditMemoryRecord(
                audit_id=audit_result.audit_id,
                request=asdict(audit_result.request),
                result={
                    "risk_score": audit_result.risk_score,
                    "findings": audit_result.findings,
                    "recommendations": audit_result.recommendations,
                    "compliance_status": audit_result.compliance_status,
                    "executive_summary": audit_result.executive_summary
                },
                timestamp=audit_result.timestamp,
                context={
                    "system_description": audit_result.request.system_description,
                    "audit_type": audit_result.request.audit_type,
                    "regulations": audit_result.request.regulations
                },
                findings=audit_result.findings,
                recommendations=audit_result.recommendations
            )
            
            # Save to in-memory storage
            self.audit_memory[audit_result.audit_id] = record
            
            # Save to database if persistence is enabled
            if self.persistence:
                self._save_audit_to_db(record)
            
            # Update context memory with learnings
            self._update_context_from_audit(record)
            
            logger.info(f"Audit saved to memory: {audit_result.audit_id}")
            
        except Exception as e:
            logger.error(f"Failed to save audit to memory: {e}")
    
    def _save_audit_to_db(self, record: AuditMemoryRecord):
        """Save audit record to database."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO audit_memory 
                (audit_id, request, result, timestamp, context, findings, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.audit_id,
                json.dumps(record.request),
                json.dumps(record.result),
                record.timestamp.isoformat(),
                json.dumps(record.context),
                json.dumps(record.findings),
                json.dumps(record.recommendations)
            ))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save audit to database: {e}")
    
    def _update_context_from_audit(self, record: AuditMemoryRecord):
        """Update context memory with learnings from audit."""
        # Extract key learnings from findings
        for finding in record.findings:
            if finding.get("severity") in ["high", "critical"]:
                key = f"finding_{finding.get('category', 'general')}_{finding.get('title', '').lower().replace(' ', '_')}"
                self.context_memory[key] = {
                    "finding": finding,
                    "audit_id": record.audit_id,
                    "timestamp": record.timestamp.isoformat()
                }
        
        # Update common patterns
        system_type = record.context.get("system_description", "").lower()
        if "chatbot" in system_type:
            self.context_memory["system_type_chatbot"] = {
                "common_issues": ["data_privacy", "transparency", "user_consent"],
                "last_audited": record.timestamp.isoformat(),
                "audit_count": self._get_audit_count_by_type("chatbot") + 1
            }
        
        # Save context to database if persistence is enabled
        if self.persistence:
            self._save_context_to_db()
    
    def _save_context_to_db(self):
        """Save context memory to database."""
        try:
            for key, value in self.context_memory.items():
                self.cursor.execute('''
                    INSERT OR REPLACE INTO context_memory 
                    (key, value, timestamp)
                    VALUES (?, ?, ?)
                ''', (
                    key,
                    json.dumps(value),
                    time.time()
                ))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save context to database: {e}")
    
    def get_audit(self, audit_id: str) -> Optional[AuditMemoryRecord]:
        """Get audit record by ID."""
        # Try in-memory first
        if audit_id in self.audit_memory:
            return self.audit_memory[audit_id]
        
        # Try database if persistence is enabled
        if self.persistence:
            return self._get_audit_from_db(audit_id)
        
        return None
    
    def _get_audit_from_db(self, audit_id: str) -> Optional[AuditMemoryRecord]:
        """Get audit record from database."""
        try:
            self.cursor.execute(
                "SELECT request, result, timestamp, context, findings, recommendations FROM audit_memory WHERE audit_id = ?",
                (audit_id,)
            )
            
            row = self.cursor.fetchone()
            if row:
                request, result, timestamp, context, findings, recommendations = row
                
                return AuditMemoryRecord(
                    audit_id=audit_id,
                    request=json.loads(request),
                    result=json.loads(result),
                    timestamp=datetime.fromisoformat(timestamp),
                    context=json.loads(context),
                    findings=json.loads(findings),
                    recommendations=json.loads(recommendations)
                )
            
        except Exception as e:
            logger.error(f"Failed to get audit from database: {e}")
        
        return None
    
    def get_recent_audits(self, limit: int = 10) -> List[AuditMemoryRecord]:
        """Get most recent audits."""
        audits = list(self.audit_memory.values())
        
        # Sort by timestamp (newest first)
        audits.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Get from database if needed
        if self.persistence and len(audits) < limit:
            db_audits = self._get_recent_audits_from_db(limit - len(audits))
            audits.extend(db_audits)
        
        return audits[:limit]
    
    def _get_recent_audits_from_db(self, limit: int) -> List[AuditMemoryRecord]:
        """Get recent audits from database."""
        try:
            self.cursor.execute(
                "SELECT audit_id, request, result, timestamp, context, findings, recommendations FROM audit_memory ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            
            audits = []
            for row in self.cursor.fetchall():
                audit_id, request, result, timestamp, context, findings, recommendations = row
                
                audits.append(AuditMemoryRecord(
                    audit_id=audit_id,
                    request=json.loads(request),
                    result=json.loads(result),
                    timestamp=datetime.fromisoformat(timestamp),
                    context=json.loads(context),
                    findings=json.loads(findings),
                    recommendations=json.loads(recommendations)
                ))
            
            return audits
            
        except Exception as e:
            logger.error(f"Failed to get recent audits from database: {e}")
            return []
    
    def get_similar_audits(self, system_description: str, limit: int = 5) -> List[AuditMemoryRecord]:
        """Get audits similar to the given system description."""
        # Simple keyword-based similarity for now
        # In production, this would use embeddings and vector search
        
        keywords = set(system_description.lower().split())
        similar_audits = []
        
        for audit in self.audit_memory.values():
            audit_text = f"{audit.context.get('system_description', '')} {audit.context.get('audit_type', '')}".lower()
            audit_keywords = set(audit_text.split())
            
            # Calculate Jaccard similarity
            intersection = len(keywords.intersection(audit_keywords))
            union = len(keywords.union(audit_keywords))
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.3:  # Threshold for similarity
                similar_audits.append((similarity, audit))
        
        # Sort by similarity
        similar_audits.sort(key=lambda x: x[0], reverse=True)
        
        return [audit for _, audit in similar_audits[:limit]]
    
    def store_memory_item(self, content: Any, metadata: Dict[str, Any] = None, importance: float = 0.5):
        """
        Store an item in short-term memory.
        
        Args:
            content: The content to store
            metadata: Additional metadata
            importance: Importance score (0.0 to 1.0)
        """
        if metadata is None:
            metadata = {}
        
        # Generate ID
        content_hash = hashlib.md5(str(content).encode()).hexdigest()
        memory_id = f"memory_{content_hash[:8]}_{int(time.time())}"
        
        # Create memory item
        item = MemoryItem(
            id=memory_id,
            content=content,
            metadata=metadata,
            timestamp=time.time(),
            importance=importance
        )
        
        # Store in memory
        self.short_term_memory[memory_id] = item
        
        # Store in database if persistence is enabled
        if self.persistence:
            self._store_memory_item_to_db(item)
        
        # Manage memory window
        self._manage_memory_window()
        
        return memory_id
    
    def _store_memory_item_to_db(self, item: MemoryItem):
        """Store memory item to database."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO memory_items 
                (id, content, metadata, timestamp, importance, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.id,
                json.dumps(item.content),
                json.dumps(item.metadata),
                item.timestamp,
                item.importance,
                item.access_count,
                item.last_accessed
            ))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to store memory item to database: {e}")
    
    def retrieve_memory(self, query: str = None, limit: int = None) -> List[MemoryItem]:
        """
        Retrieve memory items.
        
        Args:
            query: Optional query to filter items
            limit: Maximum number of items to return
            
        Returns:
            List of memory items
        """
        if limit is None:
            limit = self.memory_window
        
        items = list(self.short_term_memory.values())
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            filtered_items = []
            for item in items:
                content_str = str(item.content).lower()
                metadata_str = str(item.metadata).lower()
                if query_lower in content_str or query_lower in metadata_str:
                    filtered_items.append(item)
            items = filtered_items
        
        # Sort by importance and recency
        items.sort(key=lambda x: (
            x.importance * 0.7 +  # Importance weight
            (x.access_count / 10) * 0.2 +  # Access count weight
            ((time.time() - x.timestamp) / 3600) * -0.1  # Recency weight (negative because newer is better)
        ), reverse=True)
        
        # Update access counts
        for item in items[:limit]:
            item.access_count += 1
            item.last_accessed = time.time()
        
        return items[:limit]
    
    def get_context(self, key: str = None) -> Any:
        """
        Get context value.
        
        Args:
            key: Context key, or None for all context
            
        Returns:
            Context value or entire context dictionary
        """
        if key is None:
            return self.context_memory
        
        return self.context_memory.get(key)
    
    def update_context(self, key: str, value: Any):
        """
        Update context value.
        
        Args:
            key: Context key
            value: New value
        """
        self.context_memory[key] = {
            "value": value,
            "timestamp": time.time(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save to database if persistence is enabled
        if self.persistence:
            self._save_context_to_db()
    
    def clear_context(self):
        """Clear all context memory."""
        self.context_memory.clear()
        
        if self.persistence:
            try:
                self.cursor.execute("DELETE FROM context_memory")
                self.conn.commit()
            except Exception as e:
                logger.error(f"Failed to clear context from database: {e}")
    
    def _manage_memory_window(self):
        """Manage memory window size."""
        if len(self.short_term_memory) > self.memory_window * 2:
            # Remove least important items
            items = list(self.short_term_memory.values())
            items.sort(key=lambda x: (
                x.importance,
                x.access_count,
                x.last_accessed
            ))
            
            # Keep only the most important items
            items_to_keep = items[-self.memory_window:]
            self.short_term_memory = {item.id: item for item in items_to_keep}
            
            logger.info(f"Memory window managed: kept {len(self.short_term_memory)} items")
    
    def _get_audit_count_by_type(self, system_type: str) -> int:
        """Get count of audits by system type."""
        count = 0
        for audit in self.audit_memory.values():
            if system_type in audit.context.get("system_description", "").lower():
                count += 1
        return count
    
    def save_to_file(self, filepath: str):
        """Save memory to file."""
        try:
            data = {
                "short_term_memory": {k: v.to_dict() for k, v in self.short_term_memory.items()},
                "audit_memory": {k: v.to_dict() for k, v in self.audit_memory.items()},
                "context_memory": self.context_memory,
                "timestamp": time.time()
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Memory saved to file: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save memory to file: {e}")
    
    def load_from_file(self, filepath: str):
        """Load memory from file."""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            # Load short-term memory
            self.short_term_memory = {
                k: MemoryItem.from_dict(v) 
                for k, v in data.get("short_term_memory", {}).items()
            }
            
            # Load audit memory
            self.audit_memory = {}
            for k, v in data.get("audit_memory", {}).items():
                try:
                    record = AuditMemoryRecord(
                        audit_id=k,
                        request=v["request"],
                        result=v["result"],
                        timestamp=datetime.fromisoformat(v["timestamp"]),
                        context=v.get("context", {}),
                        findings=v.get("findings", []),
                        recommendations=v.get("recommendations", [])
                    )
                    self.audit_memory[k] = record
                except Exception as e:
                    logger.warning(f"Failed to load audit memory {k}: {e}")
            
            # Load context memory
            self.context_memory = data.get("context_memory", {})
            
            logger.info(f"Memory loaded from file: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load memory from file: {e}")
    
    def close(self):
        """Close database connections."""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Memory database connection closed")


# Example usage
if __name__ == "__main__":
    # Create memory system
    memory = AuditMemory()
    
    # Test storing and retrieving memory items
    memory_id = memory.store_memory_item(
        content="GDPR requires explicit consent for data processing",
        metadata={"source": "regulation", "topic": "privacy"},
        importance=0.8
    )
    
    print(f"Stored memory item: {memory_id}")
    
    # Test retrieving memory
    items = memory.retrieve_memory(query="GDPR", limit=5)
    print(f"Retrieved {len(items)} memory items")
    
    # Test context management
    memory.update_context("current_audit", {
        "system": "chatbot",
        "status": "in_progress",
        "start_time": datetime.now().isoformat()
    })
    
    context = memory.get_context("current_audit")
    print(f"Current context: {context}")
    
    # Test audit memory
    test_audit = AuditMemoryRecord(
        audit_id="test_audit_001",
        request={
            "system_description": "Customer service chatbot",
            "audit_type": "compliance",
            "regulations": ["GDPR", "CCPA"]
        },
        result={
            "risk_score": 65.5,
            "findings": [
                {"title": "Missing consent mechanism", "severity": "high"}
            ],
            "recommendations": [
                {"description": "Add explicit consent checkbox", "priority": "high"}
            ]
        },
        timestamp=datetime.now()
    )
    
    memory.audit_memory[test_audit.audit_id] = test_audit
    
    # Get similar audits
    similar = memory.get_similar_audits("AI chatbot for customer support", limit=3)
    print(f"Found {len(similar)} similar audits")
    
    # Clean up
    memory.close()
