#!/usr/bin/env python3
"""
Task executor for the Agentic AI Risk Auditor.
Responsible for executing tasks using appropriate tools.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from app.config import settings
from models.llm import LLMClient
from agent.planner import Task, TaskType, TaskPriority
from tools.web_scraper import WebScraper
from tools.contract_analyzer import ContractAnalyzer
from tools.doc_parser import DocumentParser
from tools.search import SearchEngine
from rag.retriever import ComplianceRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status for tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


@dataclass
class ExecutionResult:
    """Result of task execution."""
    task_id: str
    status: ExecutionStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0  # seconds
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolExecution:
    """Represents a tool execution."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    execution_time: float


class TaskExecutor:
    """Executor agent that runs tasks using appropriate tools."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.executor_model = settings.agent.executor_model
        self.max_execution_time = settings.agent.max_execution_time
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Tool mapping from task types
        self.task_tool_mapping = {
            TaskType.WEB_SCRAPING: ["web_scraper"],
            TaskType.CONTRACT_ANALYSIS: ["contract_analyzer"],
            TaskType.DOCUMENT_ANALYSIS: ["doc_parser"],
            TaskType.COMPLIANCE_CHECK: ["compliance_retriever", "search_engine"],
            TaskType.SECURITY_ASSESSMENT: ["security_scanner", "contract_analyzer"],
            TaskType.ETHICAL_REVIEW: ["ethical_framework"],
            TaskType.SEARCH: ["search_engine"],
            TaskType.DATA_ANALYSIS: ["data_analyzer"],
            TaskType.REPORT_GENERATION: ["report_generator"]
        }
        
        # Execution prompts
        self.system_prompt = """You are an expert AI risk auditor executor. Your job is to execute audit tasks using the available tools.

Available tools:
1. web_scraper: Scrape website content for analysis
2. contract_analyzer: Analyze smart contracts for security issues
3. doc_parser: Parse and analyze documentation
4. compliance_retriever: Check against regulations and standards
5. security_scanner: Assess security vulnerabilities
6. ethical_framework: Review ethical implications
7. search_engine: Search for relevant information online
8. data_analyzer: Analyze data and metrics
9. report_generator: Generate audit reports

For each task:
1. Understand the task requirements
2. Select appropriate tools
3. Execute tools with correct parameters
4. Analyze and synthesize results
5. Return structured output

Always validate tool outputs and handle errors gracefully."""
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize all available tools."""
        tools = {}
        
        try:
            tools["web_scraper"] = WebScraper()
            logger.info("WebScraper tool initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize WebScraper: {e}")
            tools["web_scraper"] = None
        
        try:
            tools["contract_analyzer"] = ContractAnalyzer()
            logger.info("ContractAnalyzer tool initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ContractAnalyzer: {e}")
            tools["contract_analyzer"] = None
        
        try:
            tools["doc_parser"] = DocumentParser()
            logger.info("DocumentParser tool initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize DocumentParser: {e}")
            tools["doc_parser"] = None
        
        try:
            tools["compliance_retriever"] = ComplianceRetriever()
            logger.info("ComplianceRetriever tool initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ComplianceRetriever: {e}")
            tools["compliance_retriever"] = None
        
        try:
            tools["search_engine"] = SearchEngine()
            logger.info("SearchEngine tool initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize SearchEngine: {e}")
            tools["search_engine"] = None
        
        # Placeholder tools (would be implemented in production)
        tools["security_scanner"] = None  # Would be SecurityScanner()
        tools["ethical_framework"] = None  # Would be EthicalFramework()
        tools["data_analyzer"] = None  # Would be DataAnalyzer()
        tools["report_generator"] = None  # Would be ReportGenerator()
        
        return tools
    
    async def execute_task(self, task: Task, context: Dict[str, Any] = None) -> ExecutionResult:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            context: Additional context from previous tasks
            
        Returns:
            ExecutionResult with status and output
        """
        logger.info(f"Executing task {task.id}: {task.type.value}")
        
        start_time = time.time()
        execution_id = str(uuid.uuid4())
        
        # Initialize result
        result = ExecutionResult(
            task_id=task.id,
            status=ExecutionStatus.RUNNING,
            output=None,
            metadata={
                "execution_id": execution_id,
                "task_type": task.type.value,
                "priority": task.priority.value,
                "start_time": start_time
            }
        )
        
        try:
            # Check timeout
            if task.timeout_seconds <= 0:
                raise ValueError(f"Invalid timeout: {task.timeout_seconds}")
            
            # Execute with timeout
            async with asyncio.timeout(task.timeout_seconds):
                # Get appropriate tools for this task type
                tool_names = self.task_tool_mapping.get(task.type, [])
                available_tools = []
                
                for tool_name in tool_names:
                    tool = self.tools.get(tool_name)
                    if tool is not None:
                        available_tools.append((tool_name, tool))
                    else:
                        logger.warning(f"Tool {tool_name} not available for task {task.id}")
                
                if not available_tools:
                    raise ValueError(f"No tools available for task type: {task.type.value}")
                
                # Execute task based on type
                if task.type == TaskType.WEB_SCRAPING:
                    output = await self._execute_web_scraping(task, available_tools, context)
                elif task.type == TaskType.CONTRACT_ANALYSIS:
                    output = await self._execute_contract_analysis(task, available_tools, context)
                elif task.type == TaskType.DOCUMENT_ANALYSIS:
                    output = await self._execute_document_analysis(task, available_tools, context)
                elif task.type == TaskType.COMPLIANCE_CHECK:
                    output = await self._execute_compliance_check(task, available_tools, context)
                elif task.type == TaskType.SECURITY_ASSESSMENT:
                    output = await self._execute_security_assessment(task, available_tools, context)
                elif task.type == TaskType.ETHICAL_REVIEW:
                    output = await self._execute_ethical_review(task, available_tools, context)
                elif task.type == TaskType.SEARCH:
                    output = await self._execute_search(task, available_tools, context)
                elif task.type == TaskType.DATA_ANALYSIS:
                    output = await self._execute_data_analysis(task, available_tools, context)
                elif task.type == TaskType.REPORT_GENERATION:
                    output = await self._execute_report_generation(task, available_tools, context)
                else:
                    raise ValueError(f"Unknown task type: {task.type.value}")
                
                # Update result
                result.status = ExecutionStatus.COMPLETED
                result.output = output
                result.execution_time = time.time() - start_time
                result.metadata["end_time"] = time.time()
                result.metadata["success"] = True
                
                logger.info(f"Task {task.id} completed in {result.execution_time:.2f}s")
                
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"Task timed out after {task.timeout_seconds} seconds"
            result.execution_time = time.time() - start_time
            result.metadata["end_time"] = time.time()
            result.metadata["timeout"] = True
            logger.error(f"Task {task.id} timed out")
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.execution_time = time.time() - start_time
            result.metadata["end_time"] = time.time()
            result.metadata["error_type"] = type(e).__name__
            logger.error(f"Task {task.id} failed: {e}")
        
        return result
    
    async def _execute_web_scraping(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute web scraping task."""
        web_scraper = None
        for tool_name, tool in tools:
            if tool_name == "web_scraper":
                web_scraper = tool
                break
        
        if not web_scraper:
            raise ValueError("Web scraper tool not available")
        
        # Extract URL from parameters or context
        url = task.parameters.get("url")
        if not url and context and "target_url" in context:
            url = context["target_url"]
        
        if not url:
            raise ValueError("No URL provided for web scraping")
        
        # Execute scraping
        scraped_data = await web_scraper.scrape(url, task.parameters)
        
        # Analyze content for risks
        analysis_prompt = f"""Analyze the scraped website content for AI risk assessment.

Website URL: {url}
Task Description: {task.description}

Scraped Content Summary:
{scraped_data.get('summary', 'No summary available')}

Please analyze for:
1. Privacy and data collection practices
2. Security vulnerabilities
3. Compliance with regulations
4. Ethical considerations
5. Transparency and user communication

Return a structured analysis in JSON format."""
        
        analysis = await self.llm_client.generate(
            prompt=analysis_prompt,
            model=self.executor_model,
            temperature=settings.agent.executor_temperature,
            response_format={"type": "json_object"}
        )
        
        return {
            "url": url,
            "scraped_data": scraped_data,
            "analysis": json.loads(analysis),
            "findings": self._extract_findings_from_analysis(analysis, "web_scraping")
        }
    
    async def _execute_contract_analysis(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute smart contract analysis task."""
        contract_analyzer = None
        for tool_name, tool in tools:
            if tool_name == "contract_analyzer":
                contract_analyzer = tool
                break
        
        if not contract_analyzer:
            raise ValueError("Contract analyzer tool not available")
        
        # Extract contract address or code
        contract_address = task.parameters.get("contract_address")
        contract_code = task.parameters.get("contract_code")
        
        if not contract_address and not contract_code:
            if context and "contract_address" in context:
                contract_address = context["contract_address"]
            else:
                raise ValueError("No contract address or code provided")
        
        # Analyze contract
        if contract_address:
            analysis = await contract_analyzer.analyze_by_address(contract_address, task.parameters)
        else:
            analysis = await contract_analyzer.analyze_by_code(contract_code, task.parameters)
        
        return {
            "contract_address": contract_address,
            "contract_code_provided": bool(contract_code),
            "analysis": analysis,
            "findings": self._extract_findings_from_analysis(analysis, "contract_analysis"),
            "security_score": analysis.get("security_score", 0),
            "risk_level": analysis.get("risk_level", "unknown")
        }
    
    async def _execute_document_analysis(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute document analysis task."""
        doc_parser = None
        for tool_name, tool in tools:
            if tool_name == "doc_parser":
                doc_parser = tool
                break
        
        if not doc_parser:
            raise ValueError("Document parser tool not available")
        
        # Extract document paths
        document_paths = task.parameters.get("document_paths", [])
        if not document_paths and context and "document_paths" in context:
            document_paths = context["document_paths"]
        
        if not document_paths:
            raise ValueError("No document paths provided")
        
        # Parse and analyze documents
        all_analysis = []
        all_findings = []
        
        for doc_path in document_paths:
            try:
                parsed_content = await doc_parser.parse(doc_path, task.parameters)
                
                # Analyze document content
                analysis_prompt = f"""Analyze document for AI risk assessment.

Document: {doc_path}
Task Description: {task.description}

Document Content Summary:
{parsed_content.get('summary', 'No summary available')}

Please analyze for:
1. Privacy policies and data handling
2. Security requirements and practices
3. Compliance statements
4. Ethical guidelines
5. Risk disclosures

Return a structured analysis in JSON format."""
                
                analysis = await self.llm_client.generate(
                    prompt=analysis_prompt,
                    model=self.executor_model,
                    temperature=settings.agent.executor_temperature,
                    response_format={"type": "json_object"}
                )
                
                analysis_data = json.loads(analysis)
                all_analysis.append({
                    "document": doc_path,
                    "analysis": analysis_data
                })
                
                findings = self._extract_findings_from_analysis(analysis, "document_analysis")
                for finding in findings:
                    finding["document"] = doc_path
                all_findings.extend(findings)
                
            except Exception as e:
                logger.error(f"Failed to analyze document {doc_path}: {e}")
                all_analysis.append({
                    "document": doc_path,
                    "error": str(e),
                    "analysis": None
                })
        
        return {
            "documents_analyzed": len(document_paths),
            "analysis": all_analysis,
            "findings": all_findings
        }
    
    async def _execute_compliance_check(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute compliance check task."""
        compliance_retriever = None
        search_engine = None
        
        for tool_name, tool in tools:
            if tool_name == "compliance_retriever":
                compliance_retriever = tool
            elif tool_name == "search_engine":
                search_engine = tool
        
        if not compliance_retriever:
            raise ValueError("Compliance retriever tool not available")
        
        # Extract regulations to check
        regulations = task.parameters.get("regulations", [])
        if not regulations and context and "regulations" in context:
            regulations = context["regulations"]
        
        if not regulations:
            regulations = settings.compliance.default_regulations
        
        # Get system description
        system_description = task.parameters.get("system_description")
        if not system_description and context and "system_description" in context:
            system_description = context["system_description"]
        
        if not system_description:
            system_description = "AI system under audit"
        
        # Check compliance
        compliance_results = []
        all_findings = []
        
        for regulation in regulations:
            try:
                # Retrieve relevant compliance information
                compliance_info = await compliance_retriever.retrieve_relevant(
                    query=f"{regulation} compliance requirements for {system_description}",
                    top_k=settings.compliance.rag_top_k
                )
                
                # Analyze compliance
                analysis_prompt = f"""Check compliance with {regulation} for the following AI system:

System Description: {system_description}

Relevant {regulation} Requirements:
{compliance_info.get('summary', 'No requirements found')}

Task Description: {task.description}

Please analyze:
1. Which requirements apply to this system
2. Current compliance status for each requirement
3. Gaps and violations
4. Recommendations for compliance

Return a structured compliance analysis in JSON format."""
                
                analysis = await self.llm_client.generate(
                    prompt=analysis_prompt,
                    model=self.executor_model,
                    temperature=settings.agent.executor_temperature,
                    response_format={"type": "json_object"}
                )
                
                analysis_data = json.loads(analysis)
                compliance_results.append({
                    "regulation": regulation,
                    "analysis": analysis_data,
                    "compliance_info": compliance_info
                })
                
                findings = self._extract_findings_from_analysis(analysis, "compliance_check")
                for finding in findings:
                    finding["regulation"] = regulation
                all_findings.extend(findings)
                
            except Exception as e:
                logger.error(f"Failed to check compliance with {regulation}: {e}")
                compliance_results.append({
                    "regulation": regulation,
                    "error": str(e),
                    "analysis": None
                })
        
        return {
            "regulations_checked": len(regulations),
            "compliance_results": compliance_results,
            "findings": all_findings,
            "overall_compliance_score": self._calculate_compliance_score(compliance_results)
        }
    
    async def _execute_security_assessment(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute security assessment task."""
        # This would use security_scanner and contract_analyzer tools
        # For now, create a placeholder implementation
        system_description = task.parameters.get("system_description")
        if not system_description and context and "system_description" in context:
            system_description = context["system_description"]
        
        analysis_prompt = f"""Perform security assessment for AI system:

System: {system_description}
Task Description: {task.description}

Please assess:
1. Data security and encryption
2. Access controls and authentication
3. API security and rate limiting
4. Vulnerability to common attacks (SQL injection, XSS, etc.)
5. Compliance with security standards (OWASP, NIST, ISO 27001)

Return a structured security assessment in JSON format."""
        
        analysis = await self.llm_client.generate(
            prompt=analysis_prompt,
            model=self.executor_model,
            temperature=settings.agent.executor_temperature,
            response_format={"type": "json_object"}
        )
        
        return {
            "security_assessment": json.loads(analysis),
            "findings": self._extract_findings_from_analysis(analysis, "security_assessment"),
            "recommendations": self._extract_recommendations_from_analysis(analysis)
        }
    
    async def _execute_ethical_review(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute ethical review task."""
        system_description = task.parameters.get("system_description")
        if not system_description and context and "system_description" in context:
            system_description = context["system_description"]
        
        analysis_prompt = f"""Perform ethical review for AI system:

System: {system_description}
Task Description: {task.description}

Consider ethical frameworks:
1. Fairness and bias mitigation
2. Transparency and explainability
3. Privacy and data ethics
4. Accountability and responsibility
5. Social impact and unintended consequences

Return a structured ethical review in JSON format."""
        
        analysis = await self.llm_client.generate(
            prompt=analysis_prompt,
            model=self.executor_model,
            temperature=settings.agent.executor_temperature,
            response_format={"type": "json_object"}
        )
        
        return {
            "ethical_review": json.loads(analysis),
            "findings": self._extract_findings_from_analysis(analysis, "ethical_review"),
            "ethical_risks": self._extract_ethical_risks_from_analysis(analysis)
        }
    
    async def _execute_search(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute search task."""
        search_engine = None
        for tool_name, tool in tools:
            if tool_name == "search_engine":
                search_engine = tool
                break
        
        if not search_engine:
            # Fallback to LLM-based search simulation
            query = task.parameters.get("query", task.description)
            
            search_prompt = f"""Simulate search results for query: {query}

Task Description: {task.description}

Please provide simulated search results that would be relevant for AI risk assessment.
Include sources, summaries, and relevance scores.

Return structured search results in JSON format."""
            
            results = await self.llm_client.generate(
                prompt=search_prompt,
                model=self.executor_model,
                temperature=settings.agent.executor_temperature,
                response_format={"type": "json_object"}
            )
            
            return {
                "query": query,
                "results": json.loads(results),
                "source": "llm_simulation"
            }
        
        # Use actual search engine if available
        query = task.parameters.get("query", task.description)
        search_results = await search_engine.search(query, task.parameters)
        
        return {
            "query": query,
            "results": search_results,
            "source": "search_engine"
        }
    
    async def _execute_data_analysis(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute data analysis task."""
        # This would use data_analyzer tool
        # For now, create a placeholder implementation
        data_description = task.parameters.get("data_description", "System data for analysis")
        
        analysis_prompt = f"""Perform data analysis for AI risk assessment:

Data Description: {data_description}
Task Description: {task.description}

Analyze for:
1. Data quality issues
2. Statistical patterns and anomalies
3. Correlation with risk factors
4. Predictive insights
5. Data visualization recommendations

Return structured data analysis in JSON format."""
        
        analysis = await self.llm_client.generate(
            prompt=analysis_prompt,
            model=self.executor_model,
            temperature=settings.agent.executor_temperature,
            response_format={"type": "json_object"}
        )
        
        return {
            "data_analysis": json.loads(analysis),
            "findings": self._extract_findings_from_analysis(analysis, "data_analysis"),
            "metrics": self._extract_metrics_from_analysis(analysis)
        }
    
    async def _execute_report_generation(
        self, 
        task: Task, 
        tools: List[Tuple[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute report generation task."""
        # This would use report_generator tool
        # For now, create a placeholder implementation
        
        # Collect inputs from context
        inputs = {
            "task_description": task.description,
            "parameters": task.parameters,
            "context_summary": self._summarize_context(context) if context else "No context available"
        }
        
        report_prompt = f"""Generate comprehensive audit report:

Task: {task.description}
Parameters: {json.dumps(task.parameters, indent=2)}
Context Summary: {inputs['context_summary']}

Generate a professional audit report including:
1. Executive summary
2. Methodology
3. Findings and analysis
4. Risk assessment
5. Recommendations
6. Appendices

Return structured report in JSON format."""
        
        report = await self.llm_client.generate(
            prompt=report_prompt,
            model=self.executor_model,
            temperature=settings.agent.executor_temperature,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        return {
            "report": json.loads(report),
            "inputs": inputs,
            "generated_at": time.time()
        }
    
    def _extract_findings_from_analysis(self, analysis: str, source: str) -> List[Dict[str, Any]]:
        """Extract findings from analysis text."""
        try:
            analysis_data = json.loads(analysis)
            findings = []
            
            # Try to extract findings from common structures
            if isinstance(analysis_data, dict):
                # Look for findings key
                if "findings" in analysis_data and isinstance(analysis_data["findings"], list):
                    for finding in analysis_data["findings"]:
                        if isinstance(finding, dict):
                            finding["source"] = source
                            findings.append(finding)
                
                # Look for issues key
                elif "issues" in analysis_data and isinstance(analysis_data["issues"], list):
                    for issue in analysis_data["issues"]:
                        if isinstance(issue, dict):
                            issue["source"] = source
                            issue["type"] = issue.get("type", "issue")
                            findings.append(issue)
                
                # Look for risks key
                elif "risks" in analysis_data and isinstance(analysis_data["risks"], list):
                    for risk in analysis_data["risks"]:
                        if isinstance(risk, dict):
                            risk["source"] = source
                            risk["type"] = "risk"
                            findings.append(risk)
            
            # If no structured findings found, create a summary finding
            if not findings:
                findings.append({
                    "id": f"finding_{int(time.time())}_{source}",
                    "title": f"Analysis from {source}",
                    "description": f"Analysis completed for {source}",
                    "severity": "medium",
                    "category": source,
                    "source": source,
                    "timestamp": time.time()
                })
            
            return findings
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to extract findings from analysis: {e}")
            # Return a basic finding
            return [{
                "id": f"finding_{int(time.time())}_{source}",
                "title": f"Analysis from {source}",
                "description": f"Raw analysis: {analysis[:200]}...",
                "severity": "medium",
                "category": source,
                "source": source,
                "timestamp": time.time(),
                "raw_analysis": analysis[:500]  # Store truncated raw analysis
            }]
    
    def _extract_recommendations_from_analysis(self, analysis: str) -> List[Dict[str, Any]]:
        """Extract recommendations from analysis text."""
        try:
            analysis_data = json.loads(analysis)
            recommendations = []
            
            if isinstance(analysis_data, dict):
                if "recommendations" in analysis_data and isinstance(analysis_data["recommendations"], list):
                    for rec in analysis_data["recommendations"]:
                        if isinstance(rec, dict):
                            recommendations.append(rec)
                        elif isinstance(rec, str):
                            recommendations.append({
                                "description": rec,
                                "priority": "medium"
                            })
            
            return recommendations
            
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
    
    def _extract_ethical_risks_from_analysis(self, analysis: str) -> List[Dict[str, Any]]:
        """Extract ethical risks from analysis text."""
        try:
            analysis_data = json.loads(analysis)
            risks = []
            
            if isinstance(analysis_data, dict):
                if "ethical_risks" in analysis_data and isinstance(analysis_data["ethical_risks"], list):
                    risks.extend(analysis_data["ethical_risks"])
                elif "risks" in analysis_data and isinstance(analysis_data["risks"], list):
                    risks.extend(analysis_data["risks"])
            
            return risks
            
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
    
    def _extract_metrics_from_analysis(self, analysis: str) -> Dict[str, Any]:
        """Extract metrics from analysis text."""
        try:
            analysis_data = json.loads(analysis)
            metrics = {}
            
            if isinstance(analysis_data, dict):
                # Look for common metric keys
                for key in ["metrics", "statistics", "scores", "measurements"]:
                    if key in analysis_data and isinstance(analysis_data[key], dict):
                        metrics.update(analysis_data[key])
            
            return metrics
            
        except (json.JSONDecodeError, KeyError, TypeError):
            return {}
    
    def _calculate_compliance_score(self, compliance_results: List[Dict[str, Any]]) -> float:
        """Calculate overall compliance score from results."""
        if not compliance_results:
            return 0.0
        
        total_score = 0
        valid_results = 0
        
        for result in compliance_results:
            if result.get("analysis"):
                # Try to extract score from analysis
                analysis = result["analysis"]
                if isinstance(analysis, dict):
                    score = analysis.get("compliance_score")
                    if isinstance(score, (int, float)):
                        total_score += score
                        valid_results += 1
                    elif "status" in analysis:
                        # Convert status to score
                        status = analysis["status"]
                        if status == "compliant":
                            total_score += 100
                        elif status == "partially_compliant":
                            total_score += 50
                        elif status == "non_compliant":
                            total_score += 0
                        else:
                            total_score += 50  # Default
                        valid_results += 1
        
        return total_score / valid_results if valid_results > 0 else 0.0
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Summarize context for report generation."""
        if not context:
            return "No context available"
        
        summary_parts = []
        
        if "system_description" in context:
            summary_parts.append(f"System: {context['system_description'][:100]}...")
        
        if "regulations" in context:
            summary_parts.append(f"Regulations: {', '.join(context['regulations'])}")
        
        if "audit_type" in context:
            summary_parts.append(f"Audit Type: {context['audit_type']}")
        
        if "findings_summary" in context:
            summary_parts.append(f"Findings: {context['findings_summary']}")
        
        return "\n".join(summary_parts)
    
    async def execute_tasks_parallel(
        self, 
        tasks: List[Task], 
        max_parallel: int = None
    ) -> Dict[str, ExecutionResult]:
        """
        Execute multiple tasks in parallel.
        
        Args:
            tasks: List of tasks to execute
            max_parallel: Maximum number of parallel executions
            
        Returns:
            Dictionary of task_id -> ExecutionResult
        """
        if max_parallel is None:
            max_parallel = settings.agent.max_parallel_tasks
        
        logger.info(f"Executing {len(tasks)} tasks in parallel (max {max_parallel})")
        
        # Create semaphore for limiting parallel executions
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def execute_with_semaphore(task: Task) -> Tuple[str, ExecutionResult]:
            async with semaphore:
                result = await self.execute_task(task)
                return task.id, result
        
        # Execute all tasks
        tasks_with_semaphore = [execute_with_semaphore(task) for task in tasks]
        results = await asyncio.gather(*tasks_with_semaphore, return_exceptions=True)
        
        # Process results
        execution_results = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task execution failed with exception: {result}")
                continue
            
            task_id, exec_result = result
            execution_results[task_id] = exec_result
        
        return execution_results


# Example usage
if __name__ == "__main__":
    # Create a test task
    from agent.planner import Task, TaskType, TaskPriority
    
    test_task = Task(
        id="test_task_1",
        type=TaskType.COMPLIANCE_CHECK,
        description="Check GDPR compliance for customer data processing",
        priority=TaskPriority.HIGH,
        dependencies=[],
        parameters={
            "regulations": ["GDPR"],
            "system_description": "AI-powered customer service chatbot"
        },
        expected_output="GDPR compliance assessment report",
        timeout_seconds=300
    )
    
    async def test_executor():
        executor = TaskExecutor()
        result = await executor.execute_task(test_task)
        
        print(f"Task ID: {result.task_id}")
        print(f"Status: {result.status.value}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        
        if result.status == ExecutionStatus.COMPLETED:
            print(f"Output keys: {list(result.output.keys())}")
            if "findings" in result.output:
                print(f"Findings: {len(result.output['findings'])}")
        elif result.error:
            print(f"Error: {result.error}")
    
    asyncio.run(test_executor())