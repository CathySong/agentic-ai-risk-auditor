#!/usr/bin/env python3
"""
Test core functionality of the Agentic AI Risk Auditor.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from agent.graph import RiskAuditGraph
from agent.planner import AuditPlanner
from agent.executor import AuditExecutor
from tools.web_scraper import WebScraper
from tools.contract_analyzer import ContractAnalyzer, ContractType
from rag.retriever import RAGRetriever, DocumentType
from models.llm import LLMClient
from models.embeddings import EmbeddingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoreFunctionalityTests:
    """Test suite for core functionality."""
    
    def __init__(self):
        self.test_results = {}
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Agentic AI Risk Auditor Core Functionality Tests")
        print("=" * 60)
        
        # Test 1: Configuration
        await self.test_configuration()
        
        # Test 2: LLM Models
        await self.test_llm_models()
        
        # Test 3: Embedding Models
        await self.test_embedding_models()
        
        # Test 4: RAG Retriever
        await self.test_rag_retriever()
        
        # Test 5: Web Scraper
        await self.test_web_scraper()
        
        # Test 6: Contract Analyzer
        await self.test_contract_analyzer()
        
        # Test 7: Audit Planner
        await self.test_audit_planner()
        
        # Test 8: Audit Executor
        await self.test_audit_executor()
        
        # Test 9: Risk Audit Graph
        await self.test_risk_audit_graph()
        
        # Print summary
        self.print_summary()
    
    async def test_configuration(self):
        """Test configuration loading."""
        print("\n📋 Test 1: Configuration")
        try:
            # Check that settings are loaded
            assert hasattr(settings, 'llm'), "LLM settings missing"
            assert hasattr(settings, 'vectordb'), "VectorDB settings missing"
            assert hasattr(settings, 'tool'), "Tool settings missing"
            
            # Check required settings
            assert settings.llm.default_provider, "Default LLM provider not set"
            assert settings.vectordb.chroma_db_path, "ChromaDB path not set"
            
            self.test_results["configuration"] = {
                "status": "PASS",
                "details": {
                    "llm_provider": settings.llm.default_provider,
                    "chroma_path": settings.vectordb.chroma_db_path,
                    "search_limit": settings.vectordb.search_results_limit
                }
            }
            print("✅ Configuration test passed")
            
        except Exception as e:
            self.test_results["configuration"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Configuration test failed: {e}")
    
    async def test_llm_models(self):
        """Test LLM model functionality."""
        print("\n🤖 Test 2: LLM Models")
        try:
            # Initialize LLM client
            llm_client = LLMClient()
            
            # Test basic generation
            test_prompt = "What is AI risk assessment in one sentence?"
            response = await llm_client.generate(
                prompt=test_prompt,
                temperature=0.1,
                max_tokens=50
            )
            
            assert response, "LLM response is empty"
            assert len(response) > 10, "LLM response too short"
            
            # Test batch generation
            prompts = ["Test prompt 1", "Test prompt 2"]
            batch_responses = await llm_client.batch_generate(
                prompts=prompts,
                max_tokens=20
            )
            
            assert len(batch_responses) == 2, "Batch generation failed"
            
            # Test model info
            model_info = llm_client.get_model_info()
            assert "provider" in model_info, "Model info missing provider"
            
            self.test_results["llm_models"] = {
                "status": "PASS",
                "details": {
                    "provider": model_info.get("provider"),
                    "response_length": len(response),
                    "batch_success": len(batch_responses)
                }
            }
            print("✅ LLM models test passed")
            
        except Exception as e:
            self.test_results["llm_models"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ LLM models test failed: {e}")
    
    async def test_embedding_models(self):
        """Test embedding model functionality."""
        print("\n🔢 Test 3: Embedding Models")
        try:
            # Initialize embedding model
            embedder = EmbeddingModel()
            
            # Test single embedding
            text = "AI risk assessment involves evaluating potential harms."
            embedding = await embedder.embed(text)
            
            assert embedding, "Embedding is empty"
            assert isinstance(embedding, list), "Embedding is not a list"
            assert len(embedding) > 0, "Embedding has zero dimensions"
            
            # Test batch embeddings
            texts = ["Text 1 for embedding", "Text 2 for embedding"]
            embeddings = await embedder.embed(texts, batch_size=2)
            
            assert len(embeddings) == 2, "Batch embedding failed"
            assert len(embeddings[0]) == len(embeddings[1]), "Embedding dimensions mismatch"
            
            # Test similarity
            similarity = embedder.similarity(embeddings[0], embeddings[1])
            assert 0 <= similarity <= 1, "Similarity score out of range"
            
            # Test model info
            model_info = embedder.get_model_info()
            assert "embedding_dimension" in model_info, "Model info missing dimension"
            
            self.test_results["embedding_models"] = {
                "status": "PASS",
                "details": {
                    "embedding_dim": len(embedding),
                    "similarity_score": similarity,
                    "model_type": model_info.get("model_type")
                }
            }
            print("✅ Embedding models test passed")
            
        except Exception as e:
            self.test_results["embedding_models"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Embedding models test failed: {e}")
    
    async def test_rag_retriever(self):
        """Test RAG retriever functionality."""
        print("\n📚 Test 4: RAG Retriever")
        try:
            # Initialize retriever
            retriever = RAGRetriever("test_collection")
            
            # Add test documents
            test_documents = [
                {
                    "text": "GDPR requires data protection by design and by default.",
                    "metadata": {
                        "source": "GDPR Article 25",
                        "document_type": DocumentType.LEGAL_REGULATION.value,
                        "test": True
                    }
                },
                {
                    "text": "AI systems must be transparent and explainable to users.",
                    "metadata": {
                        "source": "AI Ethics Guidelines",
                        "document_type": DocumentType.AI_GUIDELINE.value,
                        "test": True
                    }
                }
            ]
            
            add_result = await retriever.add_documents(test_documents)
            assert add_result["added"] > 0, "Failed to add documents"
            
            # Test search
            search_result = await retriever.search("data protection requirements")
            assert search_result.total_results > 0, "Search returned no results"
            assert search_result.documents, "Search documents list is empty"
            
            # Test QA retrieval
            qa_context = await retriever.retrieve_for_qa("What does GDPR require?")
            assert qa_context["documents_used"] > 0, "QA retrieval failed"
            assert qa_context["context"], "QA context is empty"
            
            # Test collection stats
            stats = retriever.get_collection_stats()
            assert stats["total_documents"] > 0, "Collection stats incorrect"
            
            # Clean up
            retriever.reset_collection()
            
            self.test_results["rag_retriever"] = {
                "status": "PASS",
                "details": {
                    "documents_added": add_result["added"],
                    "search_results": search_result.total_results,
                    "qa_documents": qa_context["documents_used"]
                }
            }
            print("✅ RAG retriever test passed")
            
        except Exception as e:
            self.test_results["rag_retriever"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ RAG retriever test failed: {e}")
    
    async def test_web_scraper(self):
        """Test web scraper functionality."""
        print("\n🌐 Test 5: Web Scraper")
        try:
            # Initialize scraper
            async with WebScraper() as scraper:
                # Test with a simple, reliable test URL
                test_url = "https://httpbin.org/html"
                
                # Scrape the test page
                result = await scraper.scrape(test_url, {"use_playwright": False})
                
                assert result["url"] == test_url, "URL mismatch"
                assert result["metadata"]["success"], "Scraping failed"
                assert "content" in result, "Content missing"
                assert "analysis" in result, "Analysis missing"
                
                # Check analysis components
                analysis = result["analysis"]
                assert "privacy_indicators" in analysis, "Privacy analysis missing"
                assert "security_indicators" in analysis, "Security analysis missing"
                assert "risk_score" in analysis, "Risk score missing"
                
                self.test_results["web_scraper"] = {
                    "status": "PASS",
                    "details": {
                        "url": result["url"],
                        "success": result["metadata"]["success"],
                        "risk_score": analysis.get("risk_score", 0)
                    }
                }
                print("✅ Web scraper test passed")
                
        except Exception as e:
            self.test_results["web_scraper"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Web scraper test failed: {e}")
    
    async def test_contract_analyzer(self):
        """Test contract analyzer functionality."""
        print("\n📝 Test 6: Contract Analyzer")
        try:
            # Initialize analyzer
            analyzer = ContractAnalyzer()
            
            # Test contract
            test_contract = """
            PRIVACY POLICY
            
            1. Data Collection
            We collect user data to improve our services.
            
            2. Data Usage
            Data may be used for AI model training.
            
            3. User Rights
            Users can request data deletion.
            """
            
            # Analyze contract
            analysis = await analyzer.analyze(test_contract)
            
            assert analysis.contract_type, "Contract type not identified"
            assert analysis.clauses_analyzed > 0, "No clauses analyzed"
            assert 0 <= analysis.overall_risk_score <= 1, "Risk score out of range"
            assert analysis.compliance_status, "Compliance status missing"
            
            # Test template generation
            template = await analyzer.generate_contract_template(ContractType.AI_ETHICS_POLICY)
            assert template, "Template generation failed"
            assert len(template) > 100, "Template too short"
            
            self.test_results["contract_analyzer"] = {
                "status": "PASS",
                "details": {
                    "contract_type": analysis.contract_type.value,
                    "clauses_analyzed": analysis.clauses_analyzed,
                    "risk_score": analysis.overall_risk_score,
                    "template_length": len(template)
                }
            }
            print("✅ Contract analyzer test passed")
            
        except Exception as e:
            self.test_results["contract_analyzer"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Contract analyzer test failed: {e}")
    
    async def test_audit_planner(self):
        """Test audit planner functionality."""
        print("\n📋 Test 7: Audit Planner")
        try:
            # Initialize planner
            planner = AuditPlanner()
            
            # Test audit parameters
            audit_params = {
                "audit_type": "Website",
                "target_name": "Test Website",
                "target_url": "https://example.com",
                "audit_scope": ["Privacy", "Security"],
                "priority": "Medium"
            }
            
            # Create audit plan
            plan = await planner.create_plan(audit_params)
            
            assert plan, "Plan creation failed"
            assert "steps" in plan, "Plan missing steps"
            assert len(plan["steps"]) > 0, "Plan has no steps"
            assert "resources" in plan, "Plan missing resources"
            assert "timeline" in plan, "Plan missing timeline"
            
            # Validate plan structure
            for step in plan["steps"]:
                assert "action" in step, "Step missing action"
                assert "tool" in step, "Step missing tool"
                assert "parameters" in step, "Step missing parameters"
            
            self.test_results["audit_planner"] = {
                "status": "PASS",
                "details": {
                    "steps_count": len(plan["steps"]),
                    "estimated_duration": plan.get("timeline", {}).get("estimated_duration", "unknown"),
                    "resources_count": len(plan.get("resources", []))
                }
            }
            print("✅ Audit planner test passed")
            
        except Exception as e:
            self.test_results["audit_planner"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Audit planner test failed: {e}")
    
    async def test_audit_executor(self):
        """Test audit executor functionality."""
        print("\n⚡ Test 8: Audit Executor")
        try:
            # Initialize executor
            executor = AuditExecutor()
            
            # Create a simple test plan
            test_plan = {
                "steps": [
                    {
                        "action": "analyze_text",
                        "tool": "llm",
                        "parameters": {
                            "text": "Test AI system for risk assessment.",
                            "analysis_type": "initial_assessment"
                        }
                    }
                ],
                "resources": ["llm_client"],
                "timeline": {
                    "estimated_duration": "5 minutes"
                }
            }
            
            # Execute plan
            results = await executor.execute_plan(test_plan)
            
            assert results, "Execution failed"
            assert "steps_executed" in results, "Results missing steps_executed"
            assert "findings" in results, "Results missing findings"
            assert "execution_time" in results, "Results missing execution_time"
            
            # Check that steps were executed
            assert results["steps_executed"] > 0, "No steps were executed"
            
            self.test_results["audit_executor"] = {
                "status": "PASS",
                "details": {
                    "steps_executed": results["steps_executed"],
                    "findings_count": len(results.get("findings", [])),
                    "execution_time": results.get("execution_time", 0)
                }
            }
            print("✅ Audit executor test passed")
            
        except Exception as e:
            self.test_results["audit_executor"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Audit executor test failed: {e}")
    
    async def test_risk_audit_graph(self):
        """Test risk audit graph functionality."""
        print("\n🔄 Test 9: Risk Audit Graph")
        try:
            # Initialize graph
            graph = RiskAuditGraph()
            
            # Create test results
            test_results = {
                "findings": [
                    {
                        "title": "Test finding",
                        "description": "This is a test finding.",
                        "risk_level": "medium",
                        "category": "privacy",
                        "source": "test"
                    }
                ],
                "analysis": {
                    "privacy": {"risk_score": 0.5},
                    "security": {"risk_score": 0.3}
                },
                "raw_data": {"test": "data"}
            }
            
            # Process results through graph
            processed_results = await graph.process_results(test_results)
            
            assert processed_results, "Graph processing failed"
            assert "overall_risk_score" in processed_results, "Missing overall risk score"
            assert "findings" in processed_results, "Missing findings"
            assert "recommendations" in processed_results, "Missing recommendations"
            assert "summary" in processed_results, "Missing summary"
            
            # Validate risk score
            risk_score = processed_results["overall_risk_score"]
            assert 0 <= risk_score <= 1, f"Invalid risk score: {risk_score}"
            
            # Validate findings were preserved
            assert len(processed_results["findings"]) >= len(test_results["findings"]), "Findings lost"
            
            self.test_results["risk_audit_graph"] = {
                "status": "PASS",
                "details": {
                    "overall_risk_score": risk_score,
                    "findings_count": len(processed_results["findings"]),
                    "recommendations_count": len(processed_results.get("recommendations", [])),
                    "has_summary": bool(processed_results.get("summary"))
                }
            }
            print("✅ Risk audit graph test passed")
            
        except Exception as e:
            self.test_results["risk_audit_graph"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Risk audit graph test failed: {e}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            status = result["status"]
            if status == "PASS":
                passed += 1
                print(f"✅ {test_name}: PASS")
                if "details" in result:
                    for key, value in result["details"].items():
                        print(f"   - {key}: {value}")
            else:
                failed += 1
                print(f"❌ {test_name}: FAIL")
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        print("=" * 60)
        
        if failed == 0:
            print("\n🎉 All tests passed! Agentic AI Risk Auditor is ready.")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Please check the errors above.")


async def main():
    """Main test runner."""
    tester = CoreFunctionalityTests()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())