#!/usr/bin/env python3
"""
Task planner for the Agentic AI Risk Auditor.
Responsible for breaking down audit requests into executable tasks.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

try:
    # LangChain 1.x imports
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    # Fallback for older versions
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from app.config import settings
from models.llm_main import create_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks that can be planned."""
    WEB_SCRAPING = "web_scraping"
    CONTRACT_ANALYSIS = "contract_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    SECURITY_ASSESSMENT = "security_assessment"
    ETHICAL_REVIEW = "ethical_review"
    SEARCH = "search"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"


class TaskPriority(Enum):
    """Priority levels for tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """Represents an individual task in the audit plan."""
    id: str
    type: TaskType
    description: str
    priority: TaskPriority
    dependencies: List[str]  # IDs of tasks that must complete first
    parameters: Dict[str, Any]
    expected_output: str
    timeout_seconds: int = 300
    retry_count: int = 2


@dataclass
class AuditPlan:
    """Complete audit plan with tasks and dependencies."""
    audit_id: str
    tasks: Dict[str, Task]  # task_id -> Task
    task_order: List[str]  # Execution order considering dependencies
    estimated_duration: int  # seconds
    required_tools: List[str]
    risk_areas: List[str]


class TaskPlanner:
    """Planner agent that breaks down audit requests into tasks."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or create_llm_client()
        self.planner_model = settings.agent.planner_model
        self.max_planning_steps = settings.agent.max_planning_steps
        
        # Define planning prompts
        self.system_prompt = """You are an expert AI risk auditor planner. Your job is to break down audit requests into specific, executable tasks.

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

Return a structured plan in JSON format."""
        
        self.human_prompt_template = """Audit Request:
System: {system_description}
Audit Type: {audit_type}
Regulations: {regulations}
Additional Info: {additional_info}

Please create a detailed audit plan with specific tasks."""

    async def plan_audit(self, audit_request: Any) -> AuditPlan:
        """
        Create an audit plan from an audit request.
        
        Args:
            audit_request: Audit request object from app.main
            
        Returns:
            AuditPlan with tasks and execution order
        """
        logger.info(f"Planning audit for: {audit_request.system_description}")
        
        # Prepare prompt
        additional_info = self._prepare_additional_info(audit_request)
        
        human_prompt = self.human_prompt_template.format(
            system_description=audit_request.system_description,
            audit_type=audit_request.audit_type,
            regulations=", ".join(audit_request.regulations),
            additional_info=additional_info
        )
        
        # Generate plan using LLM
        plan_json = await self._generate_plan_with_llm(human_prompt)
        
        # Parse and validate plan
        audit_plan = self._parse_plan(plan_json, audit_request)
        
        # Optimize task order
        audit_plan.task_order = self._optimize_task_order(audit_plan.tasks)
        
        # Calculate estimated duration
        audit_plan.estimated_duration = self._calculate_estimated_duration(audit_plan.tasks)
        
        logger.info(f"Audit plan created with {len(audit_plan.tasks)} tasks")
        return audit_plan
    
    def _prepare_additional_info(self, audit_request: Any) -> str:
        """Prepare additional information for the planning prompt."""
        info_parts = []
        
        if audit_request.target_url:
            info_parts.append(f"Target URL: {audit_request.target_url}")
        
        if audit_request.contract_address:
            info_parts.append(f"Contract Address: {audit_request.contract_address}")
        
        if audit_request.document_paths:
            info_parts.append(f"Documents: {len(audit_request.document_paths)} document(s)")
        
        if audit_request.custom_requirements:
            info_parts.append(f"Custom Requirements: {', '.join(audit_request.custom_requirements)}")
        
        return "\n".join(info_parts) if info_parts else "None"
    
    async def _generate_plan_with_llm(self, human_prompt: str) -> Dict[str, Any]:
        """Generate audit plan using LLM."""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        # Generate plan with LLM
        response = await self.llm_client.generate(
            messages=messages,
            model=self.planner_model,
            temperature=settings.agent.planner_temperature,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        try:
            # Parse JSON response
            plan_data = json.loads(response)
            return plan_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback to structured generation
            return await self._generate_structured_plan(human_prompt)
    
    async def _generate_structured_plan(self, human_prompt: str) -> Dict[str, Any]:
        """Fallback method for structured plan generation."""
        # This would use a more structured approach if JSON parsing fails
        # For now, return a basic plan structure
        return {
            "tasks": [
                {
                    "id": "task_1",
                    "type": "compliance_check",
                    "description": "Check compliance with specified regulations",
                    "priority": "high",
                    "dependencies": [],
                    "parameters": {},
                    "expected_output": "Compliance assessment report",
                    "timeout_seconds": 300
                },
                {
                    "id": "task_2", 
                    "type": "security_assessment",
                    "description": "Assess security vulnerabilities",
                    "priority": "high",
                    "dependencies": [],
                    "parameters": {},
                    "expected_output": "Security vulnerability report",
                    "timeout_seconds": 300
                },
                {
                    "id": "task_3",
                    "type": "report_generation",
                    "description": "Generate comprehensive audit report",
                    "priority": "medium",
                    "dependencies": ["task_1", "task_2"],
                    "parameters": {},
                    "expected_output": "Complete audit report",
                    "timeout_seconds": 600
                }
            ],
            "required_tools": ["compliance_retriever", "security_scanner", "report_generator"],
            "risk_areas": ["compliance", "security"]
        }
    
    def _parse_plan(self, plan_data: Dict[str, Any], audit_request: Any) -> AuditPlan:
        """Parse LLM-generated plan into AuditPlan object."""
        tasks = {}
        
        # Generate audit ID
        import uuid
        audit_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        # Parse tasks
        for task_data in plan_data.get("tasks", []):
            try:
                task = self._parse_task(task_data)
                tasks[task.id] = task
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid task data: {e}")
                continue
        
        # If no tasks were parsed, create default tasks
        if not tasks:
            tasks = self._create_default_tasks(audit_request)
        
        # Get required tools and risk areas
        required_tools = plan_data.get("required_tools", [])
        risk_areas = plan_data.get("risk_areas", [])
        
        return AuditPlan(
            audit_id=audit_id,
            tasks=tasks,
            task_order=[],  # Will be populated later
            estimated_duration=0,  # Will be calculated later
            required_tools=required_tools,
            risk_areas=risk_areas
        )
    
    def _parse_task(self, task_data: Dict[str, Any]) -> Task:
        """Parse individual task data."""
        task_id = task_data.get("id", f"task_{len(task_data)}")
        
        # Parse task type
        task_type_str = task_data.get("type", "").upper()
        try:
            task_type = TaskType(task_type_str.lower())
        except ValueError:
            logger.warning(f"Unknown task type: {task_type_str}, defaulting to compliance_check")
            task_type = TaskType.COMPLIANCE_CHECK
        
        # Parse priority
        priority_str = task_data.get("priority", "medium").upper()
        try:
            priority = TaskPriority(priority_str.lower())
        except ValueError:
            priority = TaskPriority.MEDIUM
        
        # Parse other fields
        description = task_data.get("description", "")
        dependencies = task_data.get("dependencies", [])
        parameters = task_data.get("parameters", {})
        expected_output = task_data.get("expected_output", "")
        timeout_seconds = task_data.get("timeout_seconds", 300)
        retry_count = task_data.get("retry_count", 2)
        
        return Task(
            id=task_id,
            type=task_type,
            description=description,
            priority=priority,
            dependencies=dependencies,
            parameters=parameters,
            expected_output=expected_output,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count
        )
    
    def _create_default_tasks(self, audit_request: Any) -> Dict[str, Task]:
        """Create default tasks if LLM planning fails."""
        tasks = {}
        
        # Task 1: Compliance check
        task1 = Task(
            id="task_1",
            type=TaskType.COMPLIANCE_CHECK,
            description=f"Check compliance with regulations: {', '.join(audit_request.regulations)}",
            priority=TaskPriority.HIGH,
            dependencies=[],
            parameters={"regulations": audit_request.regulations},
            expected_output="Compliance assessment report",
            timeout_seconds=300
        )
        tasks[task1.id] = task1
        
        # Task 2: Security assessment
        task2 = Task(
            id="task_2",
            type=TaskType.SECURITY_ASSESSMENT,
            description="Assess security vulnerabilities",
            priority=TaskPriority.HIGH,
            dependencies=[],
            parameters={},
            expected_output="Security vulnerability report",
            timeout_seconds=300
        )
        tasks[task2.id] = task2
        
        # Task 3: Report generation
        task3 = Task(
            id="task_3",
            type=TaskType.REPORT_GENERATION,
            description="Generate comprehensive audit report",
            priority=TaskPriority.MEDIUM,
            dependencies=["task_1", "task_2"],
            parameters={},
            expected_output="Complete audit report",
            timeout_seconds=600
        )
        tasks[task3.id] = task3
        
        # Add additional tasks based on audit request
        if audit_request.target_url:
            task4 = Task(
                id="task_4",
                type=TaskType.WEB_SCRAPING,
                description=f"Scrape and analyze website: {audit_request.target_url}",
                priority=TaskPriority.MEDIUM,
                dependencies=[],
                parameters={"url": audit_request.target_url},
                expected_output="Website analysis report",
                timeout_seconds=300
            )
            tasks[task4.id] = task4
        
        if audit_request.contract_address:
            task5 = Task(
                id="task_5",
                type=TaskType.CONTRACT_ANALYSIS,
                description=f"Analyze smart contract: {audit_request.contract_address}",
                priority=TaskPriority.HIGH,
                dependencies=[],
                parameters={"contract_address": audit_request.contract_address},
                expected_output="Smart contract security analysis",
                timeout_seconds=600
            )
            tasks[task5.id] = task5
        
        return tasks
    
    def _optimize_task_order(self, tasks: Dict[str, Task]) -> List[str]:
        """Optimize task execution order considering dependencies."""
        # Kahn's algorithm for topological sort
        task_order = []
        
        # Calculate in-degrees
        in_degree = {task_id: 0 for task_id in tasks}
        for task in tasks.values():
            for dep in task.dependencies:
                if dep in tasks:
                    in_degree[task.id] += 1
        
        # Initialize queue with tasks having no dependencies
        from collections import deque
        queue = deque([task_id for task_id, deg in in_degree.items() if deg == 0])
        
        while queue:
            task_id = queue.popleft()
            task_order.append(task_id)
            
            # Reduce in-degree of dependent tasks
            for dependent_task in tasks.values():
                if task_id in dependent_task.dependencies:
                    in_degree[dependent_task.id] -= 1
                    if in_degree[dependent_task.id] == 0:
                        queue.append(dependent_task.id)
        
        # Check for cycles
        if len(task_order) != len(tasks):
            logger.warning("Cycle detected in task dependencies, using priority-based ordering")
            # Fallback: sort by priority
            task_order = sorted(
                tasks.keys(),
                key=lambda tid: (
                    tasks[tid].priority.value,  # critical < high < medium < low
                    len(tasks[tid].dependencies)  # fewer dependencies first
                )
            )
        
        return task_order
    
    def _calculate_estimated_duration(self, tasks: Dict[str, Task]) -> int:
        """Calculate estimated total duration for all tasks."""
        total_duration = 0
        
        # Simple estimation: sum of task timeouts
        for task in tasks.values():
            total_duration += task.timeout_seconds
        
        # Add buffer for task coordination
        total_duration = int(total_duration * 1.2)
        
        return total_duration
    
    def validate_plan(self, audit_plan: AuditPlan) -> bool:
        """Validate that the audit plan is executable."""
        if not audit_plan.tasks:
            logger.error("Audit plan has no tasks")
            return False
        
        # Check that all dependencies exist
        for task in audit_plan.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in audit_plan.tasks:
                    logger.error(f"Task {task.id} depends on non-existent task {dep_id}")
                    return False
        
        # Check for circular dependencies
        visited = set()
        recursion_stack = set()
        
        def has_cycle(task_id):
            visited.add(task_id)
            recursion_stack.add(task_id)
            
            task = audit_plan.tasks[task_id]
            for dep_id in task.dependencies:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in recursion_stack:
                    return True
            
            recursion_stack.remove(task_id)
            return False
        
        for task_id in audit_plan.tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    logger.error("Circular dependency detected in audit plan")
                    return False
        
        return True
    
    async def refine_plan(self, audit_plan: AuditPlan, feedback: str) -> AuditPlan:
        """
        Refine audit plan based on feedback.
        
        Args:
            audit_plan: Original audit plan
            feedback: Feedback for refinement
            
        Returns:
            Refined audit plan
        """
        logger.info(f"Refining audit plan based on feedback: {feedback[:100]}...")
        
        # Prepare refinement prompt
        refinement_prompt = f"""Original Audit Plan:
{json.dumps(self._plan_to_dict(audit_plan), indent=2)}

Feedback: {feedback}

Please refine the audit plan based on this feedback. Consider:
1. Adding, removing, or modifying tasks
2. Adjusting priorities
3. Updating dependencies
4. Improving task descriptions and parameters

Return the refined plan in the same JSON format."""

        # Generate refined plan
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=refinement_prompt)
        ]
        
        response = await self.llm_client.generate(
            messages=messages,
            model=self.planner_model,
            temperature=settings.agent.planner_temperature,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        try:
            refined_data = json.loads(response)
            # Create a mock audit request for parsing
            from dataclasses import make_dataclass
            MockRequest = make_dataclass('MockRequest', [('system_description', str), ('audit_type', str), ('regulations', list)])
            mock_request = MockRequest(
                system_description="Refined plan",
                audit_type="comprehensive",
                regulations=[]
            )
            
            refined_plan = self._parse_plan(refined_data, mock_request)
            
            # Optimize and calculate duration
            refined_plan.task_order = self._optimize_task_order(refined_plan.tasks)
            refined_plan.estimated_duration = self._calculate_estimated_duration(refined_plan.tasks)
            
            logger.info(f"Plan refined: {len(refined_plan.tasks)} tasks")
            return refined_plan
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse refined plan: {e}")
            return audit_plan  # Return original plan if refinement fails
    
    def _plan_to_dict(self, audit_plan: AuditPlan) -> Dict[str, Any]:
        """Convert audit plan to dictionary for serialization."""
        return {
            "audit_id": audit_plan.audit_id,
            "tasks": [
                {
                    "id": task.id,
                    "type": task.type.value,
                    "description": task.description,
                    "priority": task.priority.value,
                    "dependencies": task.dependencies,
                    "parameters": task.parameters,
                    "expected_output": task.expected_output,
                    "timeout_seconds": task.timeout_seconds,
                    "retry_count": task.retry_count
                }
                for task in audit_plan.tasks.values()
            ],
            "task_order": audit_plan.task_order,
            "estimated_duration": audit_plan.estimated_duration,
            "required_tools": audit_plan.required_tools,
            "risk_areas": audit_plan.risk_areas
        }


# Example usage
if __name__ == "__main__":
    # Create a mock audit request for testing
    from dataclasses import make_dataclass
    
    MockRequest = make_dataclass('MockRequest', [
        ('system_description', str),
        ('audit_type', str),
        ('regulations', list),
        ('target_url', str),
        ('contract_address', str),
        ('document_paths', list),
        ('custom_requirements', list)
    ])
    
    mock_request = MockRequest(
        system_description="AI-powered customer service chatbot with access to personal data",
        audit_type="comprehensive",
        regulations=["GDPR", "CCPA", "AI Act"],
        target_url="https://example.com/chatbot",
        contract_address="0x742d35Cc6634C0532925a3b844Bc9e",
        document_paths=["privacy_policy.pdf", "terms_of_service.md"],
        custom_requirements=["Data minimization", "Transparency", "User consent"]
    )
    
    async def test_planner():
        planner = TaskPlanner()
        plan = await planner.plan_audit(mock_request)
        
        print(f"Audit Plan ID: {plan.audit_id}")
        print(f"Number of tasks: {len(plan.tasks)}")
        print(f"Estimated duration: {plan.estimated_duration} seconds")
        print(f"Required tools: {plan.required_tools}")
        print(f"Risk areas: {plan.risk_areas}")
        print("\nTask Order:")
        for i, task_id in enumerate(plan.task_order, 1):
            task = plan.tasks[task_id]
            print(f"{i}. {task.id}: {task.type.value} - {task.description[:50]}...")
        
        # Validate plan
        is_valid = planner.validate_plan(plan)
        print(f"\nPlan valid: {is_valid}")
    
    asyncio.run(test_planner())