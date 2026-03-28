#!/usr/bin/env python3
"""
Main entry point for the Agentic AI Risk Auditor.
Coordinates the multi-agent workflow for risk assessment.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .config import settings
from agent.planner import TaskPlanner
from agent.executor import TaskExecutor
from agent.memory import AuditMemory
from agent.graph import AuditWorkflow
from rag.retriever import ComplianceRetriever
from models.llm import LLMClient
from eval.evaluator import AuditEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AuditRequest:
    """Audit request data structure."""
    system_description: str
    audit_type: str  # "compliance", "security", "ethical", "comprehensive"
    regulations: List[str]
    target_url: Optional[str] = None
    contract_address: Optional[str] = None
    document_paths: Optional[List[str]] = None
    custom_requirements: Optional[List[str]] = None


@dataclass
class AuditResult:
    """Audit result data structure."""
    audit_id: str
    timestamp: datetime
    request: AuditRequest
    risk_score: float
    findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    compliance_status: Dict[str, bool]
    executive_summary: str
    detailed_report: Dict[str, Any]


class AgenticAIRiskAuditor:
    """Main orchestrator for the AI risk audit system."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.planner = TaskPlanner(llm_client=self.llm_client)
        self.executor = TaskExecutor(llm_client=self.llm_client)
        self.memory = AuditMemory()
        self.workflow = AuditWorkflow(
            planner=self.planner,
            executor=self.executor,
            memory=self.memory
        )
        self.compliance_retriever = ComplianceRetriever()
        self.evaluator = AuditEvaluator()
        
    async def run_audit(self, request: AuditRequest) -> AuditResult:
        """
        Run a comprehensive AI risk audit.
        
        Args:
            request: Audit request with system details and requirements
            
        Returns:
            Complete audit result with findings and recommendations
        """
        logger.info(f"Starting audit for: {request.system_description}")
        
        # Generate audit ID
        audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Step 1: Plan the audit tasks
        logger.info("Planning audit tasks...")
        plan = await self.planner.plan_audit(request)
        
        # Step 2: Execute the audit workflow
        logger.info("Executing audit workflow...")
        execution_results = await self.workflow.run(plan)
        
        # Step 3: Retrieve relevant compliance information
        logger.info("Retrieving compliance information...")
        compliance_info = await self.compliance_retriever.retrieve_relevant(
            system_description=request.system_description,
            regulations=request.regulations,
            audit_type=request.audit_type
        )
        
        # Step 4: Analyze findings and generate recommendations
        logger.info("Analyzing findings and generating recommendations...")
        analysis = await self._analyze_findings(
            execution_results, 
            compliance_info, 
            request
        )
        
        # Step 5: Generate comprehensive report
        logger.info("Generating comprehensive report...")
        report = await self._generate_report(analysis, request)
        
        # Step 6: Calculate overall risk score
        risk_score = self._calculate_risk_score(analysis["findings"])
        
        # Create audit result
        result = AuditResult(
            audit_id=audit_id,
            timestamp=datetime.now(),
            request=request,
            risk_score=risk_score,
            findings=analysis["findings"],
            recommendations=analysis["recommendations"],
            compliance_status=analysis["compliance_status"],
            executive_summary=report["executive_summary"],
            detailed_report=report["detailed"]
        )
        
        # Save to memory
        self.memory.save_audit(result)
        
        logger.info(f"Audit completed: {audit_id}")
        return result
    
    async def _analyze_findings(
        self, 
        execution_results: Dict[str, Any],
        compliance_info: Dict[str, Any],
        request: AuditRequest
    ) -> Dict[str, Any]:
        """Analyze execution findings and generate recommendations."""
        
        # Combine findings from all tools
        all_findings = []
        for tool_name, tool_results in execution_results.items():
            if "findings" in tool_results:
                all_findings.extend(tool_results["findings"])
        
        # Check compliance against regulations
        compliance_status = {}
        for regulation in request.regulations:
            # Simple compliance check - in production, this would be more sophisticated
            regulation_findings = [
                f for f in all_findings 
                if regulation.lower() in f.get("tags", [])
            ]
            compliance_status[regulation] = len(regulation_findings) == 0
        
        # Generate recommendations based on findings
        recommendations = []
        for finding in all_findings:
            if finding.get("severity") in ["high", "critical"]:
                recommendation = {
                    "finding_id": finding.get("id"),
                    "title": f"Address {finding.get('title')}",
                    "description": finding.get("recommendation", "Review and fix the identified issue."),
                    "priority": "high",
                    "estimated_effort": "medium",
                    "resources": finding.get("resources", [])
                }
                recommendations.append(recommendation)
        
        return {
            "findings": all_findings,
            "compliance_status": compliance_status,
            "recommendations": recommendations,
            "compliance_info": compliance_info
        }
    
    async def _generate_report(
        self, 
        analysis: Dict[str, Any],
        request: AuditRequest
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        
        # Generate executive summary using LLM
        executive_prompt = f"""
        Generate an executive summary for an AI risk audit.
        
        System: {request.system_description}
        Audit Type: {request.audit_type}
        Regulations: {', '.join(request.regulations)}
        
        Findings: {len(analysis['findings'])} total findings
        Critical/High: {len([f for f in analysis['findings'] if f.get('severity') in ['critical', 'high']])}
        
        Compliance Status: {analysis['compliance_status']}
        
        Please provide a concise executive summary (3-4 paragraphs) highlighting:
        1. Overall risk assessment
        2. Key findings
        3. Compliance status
        4. Top recommendations
        """
        
        executive_summary = await self.llm_client.generate(
            prompt=executive_prompt,
            temperature=0.3
        )
        
        # Generate detailed report
        detailed_report = {
            "metadata": {
                "system": request.system_description,
                "audit_type": request.audit_type,
                "regulations": request.regulations,
                "timestamp": datetime.now().isoformat()
            },
            "findings_by_category": self._categorize_findings(analysis["findings"]),
            "compliance_analysis": analysis["compliance_status"],
            "recommendations": analysis["recommendations"],
            "risk_breakdown": self._calculate_risk_breakdown(analysis["findings"]),
            "tools_used": list(analysis.get("compliance_info", {}).get("tools_used", []))
        }
        
        return {
            "executive_summary": executive_summary,
            "detailed": detailed_report
        }
    
    def _categorize_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, List]:
        """Categorize findings by type."""
        categories = {
            "security": [],
            "privacy": [],
            "compliance": [],
            "ethical": [],
            "performance": [],
            "other": []
        }
        
        for finding in findings:
            category = finding.get("category", "other")
            if category in categories:
                categories[category].append(finding)
            else:
                categories["other"].append(finding)
        
        return categories
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score (0-100)."""
        if not findings:
            return 0.0
        
        severity_weights = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1
        }
        
        total_weight = 0
        for finding in findings:
            severity = finding.get("severity", "low")
            weight = severity_weights.get(severity, 1)
            total_weight += weight
        
        # Normalize to 0-100 scale
        max_possible = len(findings) * 10
        score = (total_weight / max_possible) * 100 if max_possible > 0 else 0
        
        return round(score, 2)
    
    def _calculate_risk_breakdown(self, findings: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate risk breakdown by category."""
        categories = self._categorize_findings(findings)
        breakdown = {}
        
        for category, category_findings in categories.items():
            if category_findings:
                category_score = self._calculate_risk_score(category_findings)
                breakdown[category] = category_score
        
        return breakdown


async def run_audit(
    system_description: str,
    audit_type: str = "comprehensive",
    regulations: List[str] = None,
    **kwargs
) -> AuditResult:
    """
    Convenience function to run an audit.
    
    Args:
        system_description: Description of the AI system to audit
        audit_type: Type of audit ("compliance", "security", "ethical", "comprehensive")
        regulations: List of regulations to check against
        **kwargs: Additional parameters for AuditRequest
        
    Returns:
        AuditResult object
    """
    if regulations is None:
        regulations = ["GDPR", "CCPA", "AI Act"]
    
    request = AuditRequest(
        system_description=system_description,
        audit_type=audit_type,
        regulations=regulations,
        **kwargs
    )
    
    auditor = AgenticAIRiskAuditor()
    return await auditor.run_audit(request)


if __name__ == "__main__":
    # Example usage
    async def main():
        # Example audit request
        request = AuditRequest(
            system_description="Customer service chatbot using GPT-4 with access to customer data",
            audit_type="comprehensive",
            regulations=["GDPR", "CCPA", "AI Act"],
            custom_requirements=["Data minimization", "Transparency", "User consent"]
        )
        
        auditor = AgenticAIRiskAuditor()
        result = await auditor.run_audit(request)
        
        print(f"Audit ID: {result.audit_id}")
        print(f"Risk Score: {result.risk_score}/100")
        print(f"Findings: {len(result.findings)}")
        print(f"\nExecutive Summary:\n{result.executive_summary}")
    
    asyncio.run(main())