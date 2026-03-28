#!/usr/bin/env python3
"""
Prompt templates for the Agentic AI Risk Auditor.
Contains all prompt templates used by the agent system.
"""

from typing import Dict, List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class AuditPrompts:
    """Collection of prompt templates for audit tasks."""
    
    # System prompts
    PLANNER_SYSTEM_PROMPT = """You are an expert AI risk auditor planner. Your job is to break down audit requests into specific, executable tasks.

Available task types:
1. web_scraping - Scrape website content for analysis
2. contract_analysis - Analyze smart contracts for security issues
3. document_analysis - Parse and analyze documentation
4. compliance_check - Check against regulations and standards
5. security_assessment - Assess security vulnerabilities
6. ethical_review - Review ethical implications
7. search - Search for relevant information online
8. data_analysis - Analyze data and metrics
9. report_generation - Generate audit reports

Available tools:
- web_scraper: For web_scraping tasks
- contract_analyzer: For contract_analysis tasks  
- doc_parser: For document_analysis tasks
- compliance_retriever: For compliance_check tasks
- security_scanner: For security_assessment tasks
- ethical_framework: For ethical_review tasks
- search_engine: For search tasks
- data_analyzer: For data_analysis tasks
- report_generator: For report_generation tasks

Consider:
- Task dependencies (some tasks need others to complete first)
- Priority based on risk and importance
- Time estimates for each task
- Required tools and resources
- Expected outputs for each task

Return a structured plan in JSON format with the following structure:
{
  "tasks": [
    {
      "id": "task_1",
      "type": "compliance_check",
      "description": "Check compliance with GDPR",
      "priority": "high",
      "dependencies": [],
      "parameters": {"regulations": ["GDPR"]},
      "expected_output": "GDPR compliance assessment",
      "timeout_seconds": 300,
      "retry_count": 2
    }
  ],
  "required_tools": ["compliance_retriever"],
  "risk_areas": ["compliance", "privacy"]
}"""
    
    EXECUTOR_SYSTEM_PROMPT = """You are an expert AI risk auditor executor. Your job is to execute audit tasks using the available tools.

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

Always validate tool outputs and handle errors gracefully.

Return results in structured JSON format appropriate for the task type."""
    
    ANALYZER_SYSTEM_PROMPT = """You are an expert AI risk analyst. Your job is to analyze findings and generate insights.

You will receive:
1. Raw findings from various tools
2. Context about the system being audited
3. Relevant regulations and standards

Your tasks:
1. Categorize findings by type (security, privacy, compliance, ethical, etc.)
2. Assess severity and impact
3. Identify patterns and root causes
4. Generate actionable recommendations
5. Calculate overall risk scores

Consider:
- Business impact and regulatory requirements
- Technical feasibility of recommendations
- Cost-benefit analysis
- Industry best practices

Return structured analysis in JSON format."""
    
    # Task-specific prompts
    @staticmethod
    def get_web_scraping_prompt(url: str, task_description: str, scraped_content: str) -> str:
        """Prompt for analyzing scraped website content."""
        return f"""Analyze the scraped website content for AI risk assessment.

Website URL: {url}
Task Description: {task_description}

Scraped Content Summary:
{scraped_content}

Please analyze for:
1. Privacy and data collection practices
2. Security vulnerabilities
3. Compliance with regulations
4. Ethical considerations
5. Transparency and user communication

Return a structured analysis in JSON format with:
- privacy_analysis: Analysis of privacy practices
- security_analysis: Analysis of security aspects
- compliance_analysis: Compliance status with common regulations
- ethical_analysis: Ethical considerations
- findings: List of specific findings with severity
- recommendations: List of recommendations

Example format:
{{
  "privacy_analysis": {{...}},
  "security_analysis": {{...}},
  "compliance_analysis": {{...}},
  "ethical_analysis": {{...}},
  "findings": [
    {{
      "id": "finding_1",
      "title": "Missing privacy policy",
      "description": "Website does not have a visible privacy policy",
      "severity": "high",
      "category": "privacy",
      "evidence": "Scraped content shows no privacy policy link"
    }}
  ],
  "recommendations": [
    {{
      "description": "Add a clear privacy policy page",
      "priority": "high",
      "effort": "low"
    }}
  ]
}}"""
    
    @staticmethod
    def get_contract_analysis_prompt(contract_address: str, contract_code: str, analysis_results: Dict) -> str:
        """Prompt for analyzing smart contracts."""
        return f"""Analyze smart contract for security and compliance risks.

Contract Address: {contract_address}
Contract Code Provided: {'Yes' if contract_code else 'No'}

Analysis Results:
{analysis_results}

Please provide comprehensive analysis covering:
1. Security vulnerabilities (reentrancy, overflow, access control, etc.)
2. Compliance with blockchain standards (ERC-20, ERC-721, etc.)
3. Economic risks (tokenomics, fee structures)
4. Governance and upgrade risks
5. Regulatory compliance (AML, KYC considerations)

Return structured analysis in JSON format with:
- security_assessment: Detailed security analysis
- compliance_assessment: Compliance with standards and regulations
- risk_analysis: Risk assessment with scores
- findings: List of specific security findings
- recommendations: Security improvement recommendations

Include severity ratings (critical, high, medium, low) for all findings."""
    
    @staticmethod
    def get_compliance_check_prompt(system_description: str, regulation: str, compliance_info: Dict) -> str:
        """Prompt for compliance checking."""
        return f"""Check compliance with {regulation} for the following AI system:

System Description: {system_description}

Relevant {regulation} Requirements:
{compliance_info.get('summary', 'No requirements found')}

Please analyze:
1. Which requirements apply to this system
2. Current compliance status for each requirement
3. Gaps and violations
4. Recommendations for compliance
5. Risk level and justification

Return a structured compliance analysis in JSON format with:
- applicable_requirements: List of requirements that apply
- compliance_status: Status for each requirement (compliant, partially_compliant, non_compliant)
- gaps: Detailed description of compliance gaps
- risk_assessment: Overall risk assessment
- recommendations: Specific recommendations for compliance
- evidence: Evidence supporting the analysis

For each requirement, provide:
- requirement_id: Identifier if available
- description: Requirement description
- status: Compliance status
- evidence: Supporting evidence
- risk_level: Associated risk level"""
    
    @staticmethod
    def get_security_assessment_prompt(system_description: str, security_data: Dict) -> str:
        """Prompt for security assessment."""
        return f"""Perform security assessment for AI system:

System: {system_description}

Available Data:
{security_data}

Please assess:
1. Data security and encryption
2. Access controls and authentication
3. API security and rate limiting
4. Vulnerability to common attacks (SQL injection, XSS, etc.)
5. Compliance with security standards (OWASP, NIST, ISO 27001)
6. Incident response and monitoring
7. Third-party dependency risks

Return a structured security assessment in JSON format with:
- security_controls: Analysis of existing security controls
- vulnerabilities: Identified vulnerabilities with CVSS scores if applicable
- threat_model: Threat modeling analysis
- risk_assessment: Overall risk assessment
- recommendations: Security improvement recommendations
- compliance_status: Compliance with security standards

Use standard security terminology and reference known vulnerabilities (CVE IDs if applicable)."""
    
    @staticmethod
    def get_ethical_review_prompt(system_description: str, ethical_frameworks: List[str]) -> str:
        """Prompt for ethical review."""
        frameworks_text = ", ".join(ethical_frameworks) if ethical_frameworks else "Standard ethical frameworks"
        
        return f"""Perform ethical review for AI system:

System: {system_description}
Ethical Frameworks: {frameworks_text}

Consider ethical dimensions:
1. Fairness and bias mitigation
2. Transparency and explainability
3. Privacy and data ethics
4. Accountability and responsibility
5. Social impact and unintended consequences
6. Environmental impact
7. Human rights considerations

Return a structured ethical review in JSON format with:
- fairness_analysis: Analysis of fairness and bias
- transparency_analysis: Analysis of transparency and explainability
- privacy_analysis: Privacy and data ethics assessment
- accountability_analysis: Accountability mechanisms
- social_impact: Social impact assessment
- ethical_risks: List of ethical risks with severity
- recommendations: Ethical improvement recommendations
- framework_compliance: Compliance with specified ethical frameworks

Reference specific ethical principles and provide concrete examples."""
    
    @staticmethod
    def get_report_generation_prompt(audit_data: Dict, findings: List[Dict], context: Dict) -> str:
        """Prompt for report generation."""
        return f"""Generate comprehensive audit report based on the following data:

Audit Context:
{context}

Audit Data Summary:
{audit_data}

Findings ({len(findings)} total):
{findings[:10]}  # Show first 10 findings

Please generate a professional audit report including:
1. Executive Summary (1-2 paragraphs)
2. Methodology and Scope
3. Detailed Findings (categorized by type and severity)
4. Risk Assessment (overall and by category)
5. Recommendations (prioritized by impact and effort)
6. Compliance Status
7. Appendices (if needed)

Return the report in JSON format with:
- executive_summary: Concise summary for leadership
- methodology: Audit approach and scope
- findings_by_category: Findings organized by category
- risk_assessment: Detailed risk assessment
- recommendations: Prioritized recommendations
- compliance_summary: Compliance status summary
- next_steps: Suggested follow-up actions

Make the report actionable, specific, and tailored to the target audience (technical team, management, regulators)."""
    
    @staticmethod
    def get_finding_analysis_prompt(findings: List[Dict], context: Dict) -> str:
        """Prompt for analyzing and synthesizing findings."""
        return f"""Analyze and synthesize audit findings.

Audit Context:
{context}

Findings to Analyze ({len(findings)} findings):
{findings}

Please:
1. Categorize findings by type (security, privacy, compliance, etc.)
2. Assess overall severity and impact
3. Identify patterns and root causes
4. Prioritize findings by risk level
5. Generate consolidated recommendations
6. Calculate overall risk scores

Return analysis in JSON format with:
- categorization: Findings organized by category
- severity_analysis: Severity distribution and analysis
- pattern_analysis: Identified patterns and root causes
- prioritization: Prioritized list of findings
- consolidated_recommendations: Consolidated recommendations
- risk_scores: Overall and category risk scores
- insights: Key insights and observations

Focus on actionable insights that can drive improvement."""
    
    @staticmethod
    def get_risk_scoring_prompt(findings: List[Dict], context: Dict) -> str:
        """Prompt for calculating risk scores."""
        return f"""Calculate risk scores based on audit findings.

System Context:
{context}

Findings ({len(findings)} findings):
{findings}

Please calculate:
1. Overall risk score (0-100)
2. Risk scores by category (security, privacy, compliance, etc.)
3. Severity distribution
4. Impact assessment
5. Likelihood assessment

Use a consistent scoring methodology:
- Critical findings: 10 points each
- High findings: 7 points each  
- Medium findings: 4 points each
- Low findings: 1 point each

Consider:
- Business impact
- Regulatory implications
- Technical complexity
- User impact

Return risk assessment in JSON format with:
- overall_risk_score: Overall score (0-100)
- category_scores: Scores by category
- severity_distribution: Count of findings by severity
- impact_assessment: Business impact assessment
- likelihood_assessment: Likelihood of issues occurring
- risk_level: Overall risk level (low, medium, high, critical)
- justification: Justification for scores and levels

Provide clear justification for all scores and assessments."""
    
    # Template prompts for dynamic generation
    @staticmethod
    def create_custom_prompt(task_type: str, parameters: Dict) -> str:
        """Create custom prompt based on task type and parameters."""
        prompt_templates = {
            "data_analysis": """Analyze data for {system_description}.

Data Characteristics: {data_characteristics}
Analysis Goals: {analysis_goals}

Please analyze for:
1. Data quality issues
2. Statistical patterns and anomalies
3. Correlation with risk factors
4. Predictive insights
5. Data visualization recommendations

Return structured analysis in JSON format.""",
            
            "search_analysis": """Analyze search results for {query}.

Search Results: {search_results}
Analysis Context: {context}

Please analyze:
1. Relevance to audit objectives
2. Credibility of sources
3. Key insights and information
4. Gaps in information
5. Additional search recommendations

Return structured analysis in JSON format.""",
            
            "document_analysis": """Analyze document for AI risk assessment.

Document: {document_name}
Document Type: {document_type}
Content Summary: {content_summary}

Please analyze for:
1. Policy compliance and gaps
2. Risk disclosures and limitations
3. Technical specifications and requirements
4. Legal and regulatory references
5. Implementation guidance

Return structured analysis in JSON format."""
        }
        
        template = prompt_templates.get(task_type, """Analyze {task_description}.

Parameters: {parameters}

Please provide comprehensive analysis in JSON format.""")
        
        # Format template with parameters
        formatted_params = {k: str(v) for k, v in parameters.items()}
        return template.format(**formatted_params)
    
    # Chain prompts for multi-step analysis
    @staticmethod
    def get_analysis_chain_prompts() -> List[Dict[str, str]]:
        """Get prompts for multi-step analysis chain."""
        return [
            {
                "step": "initial_analysis",
                "prompt": """Perform initial analysis of the provided data.

Data: {data}

Identify:
1. Key issues and concerns
2. Data quality assessment
3. Initial risk indicators
4. Areas requiring deeper analysis

Return initial analysis in JSON format."""
            },
            {
                "step": "detailed_analysis", 
                "prompt": """Based on the initial analysis, perform detailed analysis.

Initial Analysis: {initial_analysis}
Original Data: {data}

Conduct detailed analysis of:
1. Root cause analysis for identified issues
2. Impact assessment
3. Pattern recognition
4. Comparative analysis with standards

Return detailed analysis in JSON format."""
            },
            {
                "step": "synthesis",
                "prompt": """Synthesize findings from detailed analysis.

Detailed Analysis: {detailed_analysis}
Initial Analysis: {initial_analysis}

Synthesize:
1. Consolidated findings and insights
2. Prioritized recommendations
3. Risk assessment summary
4. Executive summary

Return synthesis in JSON format."""
            }
        ]


# Example usage
if __name__ == "__main__":
    prompts = AuditPrompts()
    
    # Test web scraping prompt
    web_prompt = prompts.get_web_scraping_prompt(
        url="https://example.com",
        task_description="Analyze website for privacy compliance",
        scraped_content="Website collects user data through forms and cookies..."
    )
    print(f"Web scraping prompt length: {len(web_prompt)} characters")
    
    # Test compliance prompt
    compliance_prompt = prompts.get_compliance_check_prompt(
        system_description="AI chatbot processing customer data",
        regulation="GDPR",
        compliance_info={"summary": "GDPR requires explicit consent, data minimization, and right to erasure."}
    )
    print(f"Compliance prompt length: {len(compliance_prompt)} characters")
    
    # Test custom prompt
    custom_prompt = prompts.create_custom_prompt(
        task_type="data_analysis",
        parameters={
            "system_description": "Medical device data pipeline",
            "data_characteristics": "Time-series patient data, 1M records",
            "analysis_goals": "Identify adherence patterns and risk factors"
        }
    )
    print(f"Custom prompt length: {len(custom_prompt)} characters")