#!/usr/bin/env python3
"""
Contract analyzer tool for the Agentic AI Risk Auditor.
Analyzes legal documents, contracts, and terms of service for risk assessment.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from models.llm import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContractType(Enum):
    """Types of contracts and legal documents."""
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    DATA_PROCESSING_AGREEMENT = "data_processing_agreement"
    SERVICE_LEVEL_AGREEMENT = "service_level_agreement"
    SOFTWARE_LICENSE = "software_license"
    AI_ETHICS_POLICY = "ai_ethics_policy"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk levels for contract clauses."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ContractClause:
    """Represents a contract clause with analysis."""
    text: str
    clause_type: str
    risk_level: RiskLevel
    risk_score: float
    issues: List[str]
    recommendations: List[str]
    legal_references: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "clause_type": self.clause_type,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "legal_references": self.legal_references
        }


@dataclass
class ContractAnalysis:
    """Complete analysis of a contract."""
    contract_type: ContractType
    document_length: int
    clauses_analyzed: int
    clauses: List[ContractClause]
    overall_risk_score: float
    compliance_status: Dict[str, bool]
    missing_clauses: List[str]
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contract_type": self.contract_type.value,
            "document_length": self.document_length,
            "clauses_analyzed": self.clauses_analyzed,
            "clauses": [clause.to_dict() for clause in self.clauses],
            "overall_risk_score": self.overall_risk_score,
            "compliance_status": self.compliance_status,
            "missing_clauses": self.missing_clauses,
            "summary": self.summary
        }


class ContractAnalyzer:
    """Analyzes contracts and legal documents for AI risk assessment."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        
        # Define risk patterns and keywords
        self.risk_patterns = {
            "data_collection": {
                "keywords": ["collect", "gather", "harvest", "store", "retain"],
                "risk_level": RiskLevel.MEDIUM,
                "issues": ["Excessive data collection", "Lack of purpose limitation"]
            },
            "data_sharing": {
                "keywords": ["share", "transfer", "disclose", "third party", "affiliate"],
                "risk_level": RiskLevel.HIGH,
                "issues": ["Unclear data sharing practices", "Lack of user consent"]
            },
            "ai_specific": {
                "keywords": ["artificial intelligence", "machine learning", "algorithm", "model", "training data"],
                "risk_level": RiskLevel.HIGH,
                "issues": ["AI bias risks", "Lack of transparency", "Training data concerns"]
            },
            "liability_limitation": {
                "keywords": ["limitation of liability", "disclaimer", "as is", "no warranty"],
                "risk_level": RiskLevel.MEDIUM,
                "issues": ["Overly broad liability limitations", "Unfair terms"]
            },
            "termination": {
                "keywords": ["terminate", "suspend", "cancel", "revoke"],
                "risk_level": RiskLevel.LOW,
                "issues": ["Unilateral termination rights", "Lack of notice"]
            },
            "governing_law": {
                "keywords": ["governing law", "jurisdiction", "venue", "arbitration"],
                "risk_level": RiskLevel.LOW,
                "issues": ["Unfavorable jurisdiction", "Mandatory arbitration"]
            }
        }
        
        # Compliance frameworks
        self.compliance_frameworks = {
            "gdpr": {
                "required_clauses": [
                    "data subject rights",
                    "lawful basis for processing",
                    "data protection officer",
                    "data breach notification",
                    "international data transfers"
                ],
                "description": "General Data Protection Regulation (EU)"
            },
            "ccpa": {
                "required_clauses": [
                    "right to know",
                    "right to delete",
                    "right to opt-out",
                    "do not sell my personal information"
                ],
                "description": "California Consumer Privacy Act"
            },
            "hipaa": {
                "required_clauses": [
                    "protected health information",
                    "business associate agreement",
                    "minimum necessary",
                    "security safeguards"
                ],
                "description": "Health Insurance Portability and Accountability Act"
            },
            "ai_ethics": {
                "required_clauses": [
                    "algorithmic transparency",
                    "bias mitigation",
                    "human oversight",
                    "accountability",
                    "fairness"
                ],
                "description": "AI Ethics Principles"
            }
        }
        
        logger.info("Contract analyzer initialized")
    
    async def analyze(
        self,
        contract_text: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ContractAnalysis:
        """
        Analyze a contract document.
        
        Args:
            contract_text: Text of the contract to analyze
            parameters: Additional analysis parameters
            
        Returns:
            ContractAnalysis object with complete analysis
        """
        if parameters is None:
            parameters = {}
        
        logger.info(f"Analyzing contract (length: {len(contract_text)} characters)")
        
        try:
            # Identify contract type
            contract_type = self._identify_contract_type(contract_text)
            
            # Extract clauses
            clauses = self._extract_clauses(contract_text)
            
            # Analyze each clause
            analyzed_clauses = []
            for clause_text in clauses:
                clause_analysis = await self._analyze_clause(clause_text, contract_type)
                analyzed_clauses.append(clause_analysis)
            
            # Check compliance
            compliance_status = self._check_compliance(contract_text)
            
            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(analyzed_clauses)
            
            # Identify missing clauses
            missing_clauses = self._identify_missing_clauses(contract_text, contract_type)
            
            # Generate summary
            summary = await self._generate_summary(analyzed_clauses, compliance_status, overall_risk)
            
            analysis = ContractAnalysis(
                contract_type=contract_type,
                document_length=len(contract_text),
                clauses_analyzed=len(analyzed_clauses),
                clauses=analyzed_clauses,
                overall_risk_score=overall_risk,
                compliance_status=compliance_status,
                missing_clauses=missing_clauses,
                summary=summary
            )
            
            logger.info(f"Contract analysis complete: {contract_type.value}, risk: {overall_risk:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Contract analysis failed: {e}")
            raise
    
    def _identify_contract_type(self, text: str) -> ContractType:
        """Identify the type of contract."""
        text_lower = text.lower()
        
        # Check for contract type indicators
        if "terms of service" in text_lower or "terms and conditions" in text_lower:
            return ContractType.TERMS_OF_SERVICE
        elif "privacy policy" in text_lower or "privacy notice" in text_lower:
            return ContractType.PRIVACY_POLICY
        elif "data processing agreement" in text_lower or "dpa" in text_lower:
            return ContractType.DATA_PROCESSING_AGREEMENT
        elif "service level agreement" in text_lower or "sla" in text_lower:
            return ContractType.SERVICE_LEVEL_AGREEMENT
        elif "software license" in text_lower or "end user license agreement" in text_lower:
            return ContractType.SOFTWARE_LICENSE
        elif "ai ethics" in text_lower or "responsible ai" in text_lower:
            return ContractType.AI_ETHICS_POLICY
        else:
            return ContractType.UNKNOWN
    
    def _extract_clauses(self, text: str) -> List[str]:
        """Extract individual clauses from contract text."""
        # Split by common clause separators
        separators = [
            r'\n\s*\d+\.\s+',  # Numbered clauses: "1. ", "2. "
            r'\n\s*[A-Z]\.\s+',  # Lettered clauses: "A. ", "B. "
            r'\n\s*ARTICLE\s+\d+',  # Articles: "ARTICLE 1", "ARTICLE 2"
            r'\n\s*SECTION\s+\d+',  # Sections: "SECTION 1", "SECTION 2"
            r'\n\s*Clause\s+\d+',  # Clauses: "Clause 1", "Clause 2"
        ]
        
        # Try each separator
        for separator in separators:
            clauses = re.split(separator, text)
            if len(clauses) > 1:
                # Remove empty clauses and trim
                clauses = [c.strip() for c in clauses if c.strip()]
                return clauses
        
        # If no separators found, split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    async def _analyze_clause(self, clause_text: str, contract_type: ContractType) -> ContractClause:
        """Analyze a single contract clause."""
        # Use LLM for detailed analysis
        analysis_prompt = f"""
        Analyze the following contract clause from a {contract_type.value} document:
        
        {clause_text}
        
        Please provide analysis in JSON format with these fields:
        1. clause_type: Type of clause (e.g., "data_collection", "liability", "termination")
        2. risk_level: Risk level ("low", "medium", "high", "critical")
        3. risk_score: Numeric risk score from 0.0 to 1.0
        4. issues: List of specific issues or concerns
        5. recommendations: List of recommendations for improvement
        6. legal_references: List of relevant laws or regulations
        
        Focus on AI-specific risks, data privacy, and compliance issues.
        """
        
        try:
            # Get LLM analysis
            response = await self.llm_client.generate(
                prompt=analysis_prompt,
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            analysis_data = json.loads(response)
            
            # Create clause object
            clause = ContractClause(
                text=clause_text[:500] + "..." if len(clause_text) > 500 else clause_text,
                clause_type=analysis_data.get("clause_type", "unknown"),
                risk_level=RiskLevel(analysis_data.get("risk_level", "low")),
                risk_score=float(analysis_data.get("risk_score", 0.0)),
                issues=analysis_data.get("issues", []),
                recommendations=analysis_data.get("recommendations", []),
                legal_references=analysis_data.get("legal_references", [])
            )
            
            return clause
            
        except Exception as e:
            logger.error(f"Clause analysis failed: {e}")
            
            # Fallback to rule-based analysis
            return self._rule_based_clause_analysis(clause_text, contract_type)
    
    def _rule_based_clause_analysis(self, clause_text: str, contract_type: ContractType) -> ContractClause:
        """Fallback rule-based clause analysis."""
        clause_text_lower = clause_text.lower()
        
        # Determine clause type and risk
        clause_type = "unknown"
        risk_level = RiskLevel.LOW
        risk_score = 0.0
        issues = []
        recommendations = []
        legal_references = []
        
        # Check against risk patterns
        for pattern_name, pattern_info in self.risk_patterns.items():
            for keyword in pattern_info["keywords"]:
                if keyword in clause_text_lower:
                    clause_type = pattern_name
                    risk_level = pattern_info["risk_level"]
                    risk_score = self._risk_level_to_score(risk_level)
                    issues.extend(pattern_info["issues"])
                    
                    # Add recommendations based on pattern
                    if pattern_name == "data_collection":
                        recommendations.append("Specify exact data types collected")
                        recommendations.append("Define purpose limitation")
                        legal_references.append("GDPR Article 5(1)(b)")
                    elif pattern_name == "data_sharing":
                        recommendations.append("Require explicit user consent")
                        recommendations.append("Specify third-party recipients")
                        legal_references.append("GDPR Article 44")
                    elif pattern_name == "ai_specific":
                        recommendations.append("Add AI transparency statement")
                        recommendations.append("Implement bias testing procedures")
                        legal_references.append("EU AI Act")
                    
                    break
        
        # Additional AI-specific checks
        if any(term in clause_text_lower for term in ["algorithm", "model", "training"]):
            if "transparency" not in clause_text_lower:
                issues.append("Lack of algorithmic transparency")
                recommendations.append("Add explainability requirements")
            
            if "bias" not in clause_text_lower and "fairness" not in clause_text_lower:
                issues.append("No mention of bias mitigation")
                recommendations.append("Include fairness assessment procedures")
        
        return ContractClause(
            text=clause_text[:500] + "..." if len(clause_text) > 500 else clause_text,
            clause_type=clause_type,
            risk_level=risk_level,
            risk_score=risk_score,
            issues=issues,
            recommendations=recommendations,
            legal_references=legal_references
        )
    
    def _check_compliance(self, text: str) -> Dict[str, bool]:
        """Check compliance with various frameworks."""
        text_lower = text.lower()
        compliance_status = {}
        
        for framework_name, framework_info in self.compliance_frameworks.items():
            # Check for required clauses
            missing_count = 0
            for required_clause in framework_info["required_clauses"]:
                if required_clause not in text_lower:
                    missing_count += 1
            
            # Determine compliance status
            if missing_count == 0:
                compliance_status[framework_name] = True
            elif missing_count <= len(framework_info["required_clauses"]) // 3:
                compliance_status[framework_name] = "partial"
            else:
                compliance_status[framework_name] = False
        
        return compliance_status
    
    def _calculate_overall_risk(self, clauses: List[ContractClause]) -> float:
        """Calculate overall risk score from clauses."""
        if not clauses:
            return 0.0
        
        # Weight clauses by risk level
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for clause in clauses:
            weight = self._risk_level_to_weight(clause.risk_level)
            total_weighted_score += clause.risk_score * weight
            total_weight += weight
        
        if total_weight > 0:
            return total_weighted_score / total_weight
        else:
            return 0.0
    
    def _identify_missing_clauses(self, text: str, contract_type: ContractType) -> List[str]:
        """Identify missing clauses based on contract type."""
        text_lower = text.lower()
        missing_clauses = []
        
        # Type-specific required clauses
        type_requirements = {
            ContractType.TERMS_OF_SERVICE: [
                "limitation of liability",
                "termination",
                "governing law",
                "dispute resolution"
            ],
            ContractType.PRIVACY_POLICY: [
                "data collection",
                "data usage",
                "data sharing",
                "user rights",
                "contact information"
            ],
            ContractType.DATA_PROCESSING_AGREEMENT: [
                "data protection",
                "security measures",
                "data breach notification",
                "subprocessing"
            ],
            ContractType.AI_ETHICS_POLICY: [
                "transparency",
                "fairness",
                "accountability",
                "human oversight"
            ]
        }
        
        # Check for missing clauses
        if contract_type in type_requirements:
            for required_clause in type_requirements[contract_type]:
                if required_clause not in text_lower:
                    missing_clauses.append(required_clause)
        
        return missing_clauses
    
    async def _generate_summary(
        self,
        clauses: List[ContractClause],
        compliance_status: Dict[str, bool],
        overall_risk: float
    ) -> str:
        """Generate summary of contract analysis."""
        # Count clauses by risk level
        risk_counts = {level.value: 0 for level in RiskLevel}
        for clause in clauses:
            risk_counts[clause.risk_level.value] += 1
        
        # Count compliance status
        compliant_frameworks = sum(1 for status in compliance_status.values() if status is True)
        total_frameworks = len(compliance_status)
        
        # Generate summary using LLM
        summary_prompt = f"""
        Generate a concise summary of contract analysis with these key points:
        
        1. Overall risk score: {overall_risk:.2f}/1.0
        2. Risk distribution: {risk_counts}
        3. Compliance status: {compliant_frameworks}/{total_frameworks} frameworks compliant
        4. Top concerns: {[c.issues[0] for c in clauses if c.issues][:3]}
        5. Key recommendations: {[c.recommendations[0] for c in clauses if c.recommendations][:3]}
        
        Keep summary under 200 words, focused on actionable insights.
        """
        
        try:
            summary = await self.llm_client.generate(
                prompt=summary_prompt,
                temperature=0.3,
                max_tokens=200
            )
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            
            # Fallback summary
            risk_level = "LOW"
            if overall_risk > 0.7:
                risk_level = "CRITICAL"
            elif overall_risk > 0.5:
                risk_level = "HIGH"
            elif overall_risk > 0.3:
                risk_level = "MEDIUM"
            
            return f"Contract analysis complete. Overall risk: {risk_level} ({overall_risk:.2f}/1.0). " \
                   f"Found {risk_counts['high'] + risk_counts['critical']} high-risk clauses. " \
                   f"Compliance: {compliant_frameworks}/{total_frameworks} frameworks."
    
    def _risk_level_to_score(self, risk_level: RiskLevel) -> float:
        """Convert risk level to numeric score."""
        mapping = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0
        }
        return mapping.get(risk_level, 0.0)
    
    def _risk_level_to_weight(self, risk_level: RiskLevel) -> float:
        """Convert risk level to weight for scoring."""
        mapping = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 2.0,
            RiskLevel.HIGH: 3.0,
            RiskLevel.CRITICAL: 4.0
        }
        return mapping.get(risk_level, 1.0)
    
    async def compare_contracts(
        self,
        contract1_text: str,
        contract2_text: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare two contracts for differences and risk assessment.
        
        Args:
            contract1_text: First contract text
            contract2_text: Second contract text
            parameters: Additional comparison parameters
            
        Returns:
            Comparison analysis
        """
        if parameters is None:
            parameters = {}
        
        logger.info("Comparing two contracts")
        
        try:
            # Analyze both contracts
            analysis1 = await self.analyze(contract1_text, parameters)
            analysis2 = await self.analyze(contract2_text, parameters)
            
            # Calculate differences
            risk_difference = abs(analysis1.overall_risk_score - analysis2.overall_risk_score)
            
            # Find unique clauses
            clauses1_texts = {c.text[:100] for c in analysis1.clauses}
            clauses2_texts = {c.text[:100] for c in analysis2.clauses}
            
            unique_to_1 = clauses1_texts - clauses2_texts
            unique_to_2 = clauses2_texts - clauses1_texts
            
            # Compare compliance
            compliance_comparison = {}
            all_frameworks = set(analysis1.compliance_status.keys()) | set(analysis2.compliance_status.keys())
            
            for framework in all_frameworks:
                status1 = analysis1.compliance_status.get(framework, False)
                status2 = analysis2.compliance_status.get(framework, False)
                
                if status1 != status2:
                    compliance_comparison[framework] = {
                        "contract1": status1,
                        "contract2": status2,
                        "difference": "different"
                    }
                else:
                    compliance_comparison[framework] = {
                        "contract1": status1,
                        "contract2": status2,
                        "difference": "same"
                    }
            
            # Generate comparison summary
            comparison_summary = await self._generate_comparison_summary(
                analysis1, analysis2, risk_difference, len(unique_to_1), len(unique_to_2)
            )
            
            result = {
                "contract1_analysis": analysis1.to_dict(),
                "contract2_analysis": analysis2.to_dict(),
                "comparison": {
                    "risk_difference": risk_difference,
                    "unique_clauses_contract1": len(unique_to_1),
                    "unique_clauses_contract2": len(unique_to_2),
                    "compliance_comparison": compliance_comparison,
                    "summary": comparison_summary
                },
                "recommendations": self._generate_comparison_recommendations(
                    analysis1, analysis2, risk_difference
                )
            }
            
            logger.info("Contract comparison complete")
            return result
            
        except Exception as e:
            logger.error(f"Contract comparison failed: {e}")
            raise
    
    async def _generate_comparison_summary(
        self,
        analysis1: ContractAnalysis,
        analysis2: ContractAnalysis,
        risk_difference: float,
        unique1_count: int,
        unique2_count: int
    ) -> str:
        """Generate comparison summary."""
        summary_prompt = f"""
        Compare two contract analyses:
        
        Contract 1:
        - Type: {analysis1.contract_type.value}
        - Risk: {analysis1.overall_risk_score:.2f}/1.0
        - Clauses: {analysis1.clauses_analyzed}
        
        Contract 2:
        - Type: {analysis2.contract_type.value}
        - Risk: {analysis2.overall_risk_score:.2f}/1.0
        - Clauses: {analysis2.clauses_analyzed}
        
        Comparison:
        - Risk difference: {risk_difference:.2f}
        - Unique clauses in Contract 1: {unique1_count}
        - Unique clauses in Contract 2: {unique2_count}
        
        Provide a concise comparison summary highlighting key differences and which contract is better.
        """
        
        try:
            summary = await self.llm_client.generate(
                prompt=summary_prompt,
                temperature=0.2,
                max_tokens=300
            )
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Comparison summary failed: {e}")
            
            # Determine which contract is better (lower risk)
            if analysis1.overall_risk_score < analysis2.overall_risk_score:
                better_contract = "Contract 1"
                risk_improvement = analysis2.overall_risk_score - analysis1.overall_risk_score
            else:
                better_contract = "Contract 2"
                risk_improvement = analysis1.overall_risk_score - analysis2.overall_risk_score
            
            return f"Comparison: {better_contract} has lower risk ({risk_improvement:.2f} improvement). " \
                   f"Found {unique1_count} unique clauses in Contract 1, {unique2_count} in Contract 2."
    
    def _generate_comparison_recommendations(
        self,
        analysis1: ContractAnalysis,
        analysis2: ContractAnalysis,
        risk_difference: float
    ) -> List[str]:
        """Generate recommendations based on comparison."""
        recommendations = []
        
        # Risk-based recommendations
        if risk_difference > 0.3:
            if analysis1.overall_risk_score < analysis2.overall_risk_score:
                recommendations.append("Consider adopting Contract 1's lower-risk clauses")
            else:
                recommendations.append("Consider adopting Contract 2's lower-risk clauses")
        
        # Compliance recommendations
        for framework, status1 in analysis1.compliance_status.items():
            status2 = analysis2.compliance_status.get(framework, False)
            
            if status1 is True and status2 is not True:
                recommendations.append(f"Add {framework.upper()} compliance clauses from Contract 1 to Contract 2")
            elif status2 is True and status1 is not True:
                recommendations.append(f"Add {framework.upper()} compliance clauses from Contract 2 to Contract 1")
        
        # Missing clauses recommendations
        if analysis1.missing_clauses:
            recommendations.append(f"Contract 1 missing: {', '.join(analysis1.missing_clauses[:3])}")
        if analysis2.missing_clauses:
            recommendations.append(f"Contract 2 missing: {', '.join(analysis2.missing_clauses[:3])}")
        
        return recommendations
    
    async def generate_contract_template(
        self,
        contract_type: ContractType,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a contract template with best practices.
        
        Args:
            contract_type: Type of contract to generate
            parameters: Template parameters
            
        Returns:
            Generated contract template
        """
        if parameters is None:
            parameters = {}
        
        logger.info(f"Generating {contract_type.value} template")
        
        # Define template prompts for different contract types
        template_prompts = {
            ContractType.TERMS_OF_SERVICE: """
            Generate a comprehensive Terms of Service template for an AI/ML service.
            
            Include these sections with AI-specific considerations:
            1. Acceptance of Terms
            2. Description of Service (mention AI/ML components)
            3. User Responsibilities
            4. Intellectual Property (address AI-generated content)
            5. Limitation of Liability (include AI-specific disclaimers)
            6. Data Usage and Privacy (reference AI training data)
            7. Termination
            8. Governing Law
            9. Dispute Resolution
            10. AI Ethics Statement
            
            Ensure compliance with GDPR, CCPA, and include AI transparency statements.
            Use clear, plain language.
            """,
            
            ContractType.PRIVACY_POLICY: """
            Generate a comprehensive Privacy Policy template for an AI/ML service.
            
            Include these sections with AI-specific considerations:
            1. Information We Collect (specify data used for AI training)
            2. How We Use Information (mention AI model improvement)
            3. Information Sharing (address third-party AI services)
            4. Data Security (AI-specific security measures)
            5. Your Rights (GDPR/CCPA compliance)
            6. AI Model Transparency
            7. Data Retention (for model training purposes)
            8. International Transfers
            9. Changes to Policy
            10. Contact Information
            
            Include specific sections about AI data usage, model transparency, and user consent for AI training.
            """,
            
            ContractType.AI_ETHICS_POLICY: """
            Generate a comprehensive AI Ethics Policy template.
            
            Include these principles and implementation guidelines:
            1. Transparency and Explainability
            2. Fairness and Bias Mitigation
            3. Privacy and Data Protection
            4. Accountability and Governance
            5. Safety and Reliability
            6. Human Oversight and Control
            7. Social and Environmental Responsibility
            
            For each principle, include:
            - Definition and importance
            - Implementation measures
            - Monitoring and evaluation
            - Reporting and remediation
            
            Make it actionable with specific procedures and checklists.
            """
        }
        
        prompt = template_prompts.get(contract_type, """
        Generate a comprehensive legal document template.
        Include standard clauses with clear, plain language.
        Ensure compliance with relevant regulations.
        """)
        
        try:
            template = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            logger.info(f"Template generated: {contract_type.value}")
            return template
            
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            raise


# Example usage
if __name__ == "__main__":
    async def test_contract_analyzer():
        # Initialize analyzer
        analyzer = ContractAnalyzer()
        
        # Sample contract text
        sample_contract = """
        TERMS OF SERVICE
        
        1. Acceptance of Terms
        By using our AI service, you agree to these terms.
        
        2. Data Collection
        We collect user data to improve our AI models. This includes usage patterns and feedback.
        
        3. Data Sharing
        We may share anonymized data with third-party AI research partners.
        
        4. Limitation of Liability
        We are not liable for any decisions made based on AI recommendations.
        
        5. AI Transparency
        Our AI models use machine learning algorithms. Specific details are proprietary.
        """
        
        try:
            # Analyze contract
            analysis = await analyzer.analyze(sample_contract)
            
            print(f"Contract type: {analysis.contract_type.value}")
            print(f"Overall risk: {analysis.overall_risk_score:.2f}")
            print(f"Clauses analyzed: {analysis.clauses_analyzed}")
            print(f"Compliance status: {analysis.compliance_status}")
            
            # Print high-risk clauses
            print("\nHigh-risk clauses:")
            for clause in analysis.clauses:
                if clause.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    print(f"  - {clause.clause_type}: {clause.risk_score:.2f}")
                    print(f"    Issues: {clause.issues}")
            
            # Generate template
            template = await analyzer.generate_contract_template(ContractType.AI_ETHICS_POLICY)
            print(f"\nGenerated template length: {len(template)} characters")
            print(f"First 200 chars: {template[:200]}...")
            
        except Exception as e:
            print(f"Error: {e}")
    
    import asyncio
    asyncio.run(test_contract_analyzer())