#!/usr/bin/env python3
"""
LangGraph workflow for the Agentic AI Risk Auditor.
Defines the agent workflow using LangGraph for state management and orchestration.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from enum import Enum
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from agent.planner import TaskPlanner, AuditPlan, Task
from agent.executor import TaskExecutor, ExecutionResult, ExecutionStatus
from agent.memory import AuditMemory
from agent.prompts import AuditPrompts
from models.llm import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditState(TypedDict):
    """State definition for the audit workflow."""
    # Input
    audit_request: Dict[str, Any]
    system_description: str
    audit_type: str
    regulations: List[str]
    
    # Planning
    audit_plan: Optional[AuditPlan]
    planning_complete: bool
    
    # Execution
    tasks: Dict[str, Task]
    task_order: List[str]
    execution_results: Dict[str, ExecutionResult]
    completed_tasks: List[str]
    failed_tasks: List[str]
    
    # Analysis
    findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    compliance_status: Dict[str, bool]
    risk_score: float
    
    # Context
    context: Dict[str, Any]
    memory_items: List[Dict[str, Any]]
    
    # Workflow control
    current_step: str
    error: Optional[str]
    should_continue: bool


class AuditWorkflow:
    """Main workflow orchestrator using LangGraph."""
    
    def __init__(
        self,
        planner: Optional[TaskPlanner] = None,
        executor: Optional[TaskExecutor] = None,
        memory: Optional[AuditMemory] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.planner = planner or TaskPlanner()
        self.executor = executor or TaskExecutor()
        self.memory = memory or AuditMemory()
        self.llm_client = llm_client or LLMClient()
        
        # Initialize workflow graph
        self.graph = self._create_workflow_graph()
        self.checkpointer = MemorySaver()
        
        # Compile graph
        self.app = self.graph.compile(checkpointer=self.checkpointer)
        
        logger.info("Audit workflow initialized")
    
    def _create_workflow_graph(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(AuditState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_workflow)
        workflow.add_node("plan_audit", self._plan_audit)
        workflow.add_node("validate_plan", self._validate_plan)
        workflow.add_node("execute_tasks", self._execute_tasks)
        workflow.add_node("analyze_results", self._analyze_results)
        workflow.add_node("generate_report", self._generate_report)
        workflow.add_node("handle_error", self._handle_error)
        workflow.add_node("finalize", self._finalize_workflow)
        
        # Add edges
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "plan_audit")
        workflow.add_edge("plan_audit", "validate_plan")
        
        # Conditional edge from validate_plan
        workflow.add_conditional_edges(
            "validate_plan",
            self._should_execute_tasks,
            {
                "execute": "execute_tasks",
                "replan": "plan_audit",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("execute_tasks", "analyze_results")
        workflow.add_edge("analyze_results", "generate_report")
        workflow.add_edge("generate_report", "finalize")
        
        # Error handling edges
        workflow.add_edge("handle_error", "finalize")
        
        # Add fallback edges for robustness
        workflow.add_edge("plan_audit", "handle_error")  # If planning fails
        workflow.add_edge("execute_tasks", "handle_error")  # If execution fails
        workflow.add_edge("analyze_results", "handle_error")  # If analysis fails
        workflow.add_edge("generate_report", "handle_error")  # If report generation fails
        
        return workflow
    
    async def _initialize_workflow(self, state: AuditState) -> Dict[str, Any]:
        """Initialize the audit workflow."""
        logger.info("Initializing audit workflow")
        
        # Extract from audit request
        audit_request = state["audit_request"]
        
        return {
            "system_description": audit_request.get("system_description", ""),
            "audit_type": audit_request.get("audit_type", "comprehensive"),
            "regulations": audit_request.get("regulations", []),
            "context": {
                "initialized_at": asyncio.get_event_loop().time(),
                "request_id": audit_request.get("audit_id", "unknown"),
                "workflow_version": "1.0"
            },
            "current_step": "initialize",
            "should_continue": True,
            "error": None
        }
    
    async def _plan_audit(self, state: AuditState) -> Dict[str, Any]:
        """Plan the audit tasks."""
        logger.info("Planning audit tasks")
        
        try:
            # Create audit request object for planner
            from app.main import AuditRequest
            from dataclasses import make_dataclass
            
            # Create a proper audit request
            audit_request = AuditRequest(
                system_description=state["system_description"],
                audit_type=state["audit_type"],
                regulations=state["regulations"],
                target_url=state["audit_request"].get("target_url"),
                contract_address=state["audit_request"].get("contract_address"),
                document_paths=state["audit_request"].get("document_paths"),
                custom_requirements=state["audit_request"].get("custom_requirements")
            )
            
            # Generate plan
            audit_plan = await self.planner.plan_audit(audit_request)
            
            # Validate plan
            is_valid = self.planner.validate_plan(audit_plan)
            
            if not is_valid:
                logger.warning("Generated plan is invalid, will attempt replanning")
                return {
                    "audit_plan": None,
                    "planning_complete": False,
                    "current_step": "plan_audit",
                    "error": "Generated audit plan is invalid",
                    "should_continue": True  # Will trigger replanning
                }
            
            # Store tasks and order
            tasks = audit_plan.tasks
            task_order = audit_plan.task_order
            
            # Store in memory
            for task in tasks.values():
                self.memory.store_memory_item(
                    content=f"Task planned: {task.description}",
                    metadata={
                        "task_id": task.id,
                        "type": task.type.value,
                        "priority": task.priority.value,
                        "audit_type": state["audit_type"]
                    },
                    importance=0.7 if task.priority.value in ["critical", "high"] else 0.3
                )
            
            logger.info(f"Audit plan created with {len(tasks)} tasks")
            
            return {
                "audit_plan": audit_plan,
                "tasks": tasks,
                "task_order": task_order,
                "planning_complete": True,
                "current_step": "plan_audit",
                "error": None,
                "should_continue": True
            }
            
        except Exception as e:
            logger.error(f"Failed to plan audit: {e}")
            return {
                "audit_plan": None,
                "planning_complete": False,
                "current_step": "plan_audit",
                "error": str(e),
                "should_continue": False  # Will trigger error handling
            }
    
    async def _validate_plan(self, state: AuditState) -> Dict[str, Any]:
        """Validate the audit plan."""
        logger.info("Validating audit plan")
        
        audit_plan = state.get("audit_plan")
        
        if not audit_plan:
            return {
                "current_step": "validate_plan",
                "error": "No audit plan to validate",
                "should_continue": False
            }
        
        # Check if plan has tasks
        if not audit_plan.tasks:
            return {
                "current_step": "validate_plan",
                "error": "Audit plan has no tasks",
                "should_continue": False
            }
        
        # Validate task dependencies
        for task in audit_plan.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in audit_plan.tasks:
                    return {
                        "current_step": "validate_plan",
                        "error": f"Task {task.id} depends on non-existent task {dep_id}",
                        "should_continue": False
                    }
        
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
                    return {
                        "current_step": "validate_plan",
                        "error": "Circular dependency detected in audit plan",
                        "should_continue": False
                    }
        
        # Check estimated duration
        if audit_plan.estimated_duration > settings.agent.workflow_timeout:
            logger.warning(f"Plan estimated duration ({audit_plan.estimated_duration}s) exceeds workflow timeout ({settings.agent.workflow_timeout}s)")
            # Continue anyway, but log warning
        
        logger.info("Audit plan validation passed")
        
        return {
            "current_step": "validate_plan",
            "error": None,
            "should_continue": True
        }
    
    def _should_execute_tasks(self, state: AuditState) -> str:
        """Determine whether to execute tasks or handle error/replan."""
        if state.get("error"):
            return "error"
        
        if not state.get("planning_complete", False):
            return "replan"
        
        if not state.get("audit_plan"):
            return "replan"
        
        return "execute"
    
    async def _execute_tasks(self, state: AuditState) -> Dict[str, Any]:
        """Execute audit tasks."""
        logger.info("Executing audit tasks")
        
        try:
            tasks = state["tasks"]
            task_order = state["task_order"]
            
            if not tasks or not task_order:
                return {
                    "current_step": "execute_tasks",
                    "error": "No tasks to execute",
                    "should_continue": False
                }
            
            # Prepare tasks for execution based on dependencies
            executable_tasks = []
            completed_tasks = state.get("completed_tasks", [])
            failed_tasks = state.get("failed_tasks", [])
            
            for task_id in task_order:
                if task_id in completed_tasks or task_id in failed_tasks:
                    continue
                
                task = tasks[task_id]
                
                # Check if dependencies are met
                dependencies_met = all(dep_id in completed_tasks for dep_id in task.dependencies)
                
                if dependencies_met:
                    executable_tasks.append(task)
                else:
                    logger.debug(f"Task {task_id} waiting for dependencies: {task.dependencies}")
            
            if not executable_tasks:
                # All tasks are either completed, failed, or waiting for dependencies
                # Check if we're stuck
                remaining_tasks = [
                    task_id for task_id in task_order 
                    if task_id not in completed_tasks and task_id not in failed_tasks
                ]
                
                if remaining_tasks:
                    # Some tasks are still pending
                    logger.info(f"Waiting for {len(remaining_tasks)} tasks to become executable")
                    return {
                        "current_step": "execute_tasks",
                        "should_continue": True
                    }
                else:
                    # All tasks processed
                    logger.info("All tasks processed")
                    return {
                        "current_step": "execute_tasks",
                        "should_continue": True
                    }
            
            # Execute tasks in parallel (with limits)
            execution_results = state.get("execution_results", {})
            
            # Group tasks by priority for execution
            critical_tasks = [t for t in executable_tasks if t.priority.value in ["critical", "high"]]
            other_tasks = [t for t in executable_tasks if t.priority.value in ["medium", "low"]]
            
            # Execute critical tasks first
            tasks_to_execute = critical_tasks + other_tasks
            tasks_to_execute = tasks_to_execute[:settings.agent.max_parallel_tasks]
            
            logger.info(f"Executing {len(tasks_to_execute)} tasks (max parallel: {settings.agent.max_parallel_tasks})")
            
            # Execute tasks
            new_results = await self.executor.execute_tasks_parallel(
                tasks_to_execute,
                max_parallel=settings.agent.max_parallel_tasks
            )
            
            # Update execution results
            execution_results.update(new_results)
            
            # Update completed and failed tasks
            for task_id, result in new_results.items():
                if result.status == ExecutionStatus.COMPLETED:
                    completed_tasks.append(task_id)
                    
                    # Store in memory
                    self.memory.store_memory_item(
                        content=f"Task completed: {tasks[task_id].description}",
                        metadata={
                            "task_id": task_id,
                            "execution_time": result.execution_time,
                            "status": "completed",
                            "output_keys": list(result.output.keys()) if result.output else []
                        },
                        importance=0.6
                    )
                    
                elif result.status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]:
                    failed_tasks.append(task_id)
                    
                    # Store in memory
                    self.memory.store_memory_item(
                        content=f"Task failed: {tasks[task_id].description}",
                        metadata={
                            "task_id": task_id,
                            "error": result.error,
                            "status": result.status.value,
                            "retry_count": result.retry_count
                        },
                        importance=0.8  # High importance for failures
                    )
                    
                    # Check if we should retry
                    task = tasks[task_id]
                    if result.retry_count < task.retry_count:
                        logger.info(f"Task {task_id} will be retried (attempt {result.retry_count + 1}/{task.retry_count})")
                        # Remove from failed tasks so it can be retried
                        failed_tasks.remove(task_id)
            
            # Update context with execution progress
            context = state.get("context", {})
            context["execution_progress"] = {
                "total_tasks": len(tasks),
                "completed": len(completed_tasks),
                "failed": len(failed_tasks),
                "pending": len(tasks) - len(completed_tasks) - len(failed_tasks)
            }
            
            logger.info(f"Execution progress: {len(completed_tasks)} completed, {len(failed_tasks)} failed")
            
            return {
                "execution_results": execution_results,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "context": context,
                "current_step": "execute_tasks",
                "should_continue": True
            }
            
        except Exception as e:
            logger.error(f"Failed to execute tasks: {e}")
            return {
                "current_step": "execute_tasks",
                "error": str(e),
                "should_continue": False
            }
    
    async def _analyze_results(self, state: AuditState) -> Dict[str, Any]:
        """Analyze execution results and generate findings."""
        logger.info("Analyzing execution results")
        
        try:
            execution_results = state.get("execution_results", {})
            tasks = state.get("tasks", {})
            
            if not execution_results:
                return {
                    "current_step": "analyze_results",
                    "error": "No execution results to analyze",
                    "should_continue": False
                }
            
            # Collect all findings from execution results
            all_findings = []
            all_recommendations = []
            
            for task_id, result in execution_results.items():
                if result.status == ExecutionStatus.COMPLETED and result.output:
                    # Extract findings from task output
                    if "findings" in result.output:
                        findings = result.output["findings"]
                        if isinstance(findings, list):
                            for finding in findings:
                                if isinstance(finding, dict):
                                    finding["task_id"] = task_id
                                    finding["task_type"] = tasks[task_id].type.value if task_id in tasks else "unknown"
                                    all_findings.append(finding)
                    
                    # Extract recommendations
                    if "recommendations" in result.output:
                        recommendations = result.output["recommendations"]
                        if isinstance(recommendations, list):
                            all_recommendations.extend(recommendations)
            
            # Analyze findings using LLM
            if all_findings:
                analysis_prompt = AuditPrompts.get_finding_analysis_prompt(
                    findings=all_findings,
                    context={
                        "system_description": state["system_description"],
                        "audit_type": state["audit_type"],
                        "regulations": state["regulations"]
                    }
                )
                
                analysis = await self.llm_client.generate(
                    prompt=analysis_prompt,
                    model=settings.agent.executor_model,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                
                try:
                    analysis_data = json.loads(analysis)
                    
                    # Extract categorized findings and recommendations
                    categorized_findings = analysis_data.get("categorization", {})
                    consolidated_recommendations = analysis_data.get("consolidated_recommendations", [])
                    
                    # Calculate risk score
                    risk_score = analysis_data.get("risk_scores", {}).get("overall_risk_score", 50.0)
                    
                    # Update compliance status
                    compliance_status = {}
                    for regulation in state["regulations"]:
                        # Simple compliance check based on findings
                        regulation_findings = [
                            f for f in all_findings 
                            if regulation.lower() in str(f).lower()
                        ]
                        compliance_status[regulation] = len(regulation_findings) == 0
                    
                    # Store in memory
                    self.memory.store_memory_item(
                        content=f"Analysis completed for {state['system_description']}",
                        metadata={
                            "findings_count": len(all_findings),
                            "recommendations_count": len(consolidated_recommendations),
                            "risk_score": risk_score,
                            "audit_type": state["audit_type"]
                        },
                        importance=0.9
                    )
                    
                    logger.info(f"Analysis completed: {len(all_findings)} findings, risk score: {risk_score}")
                    
                    return {
                        "findings": all_findings,
                        "recommendations": consolidated_recommendations,
                        "compliance_status": compliance_status,
                        "risk_score": risk_score,
                        "current_step": "analyze_results",
                        "should_continue": True
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse analysis JSON: {e}")
                    # Fallback to basic analysis
                    return {
                        "findings": all_findings,
                        "recommendations": all_recommendations,
                        "compliance_status": {},
                        "risk_score": 50.0,  # Default score
                        "current_step": "analyze_results",
                        "error": f"Analysis parsing failed: {e}",
                        "should_continue": True  # Continue despite error
                    }
            
            else:
                # No findings to analyze
                logger.info("No findings to analyze")
                return {
                    "findings": [],
                    "recommendations": [],
                    "compliance_status": {},
                    "risk_score": 0.0,
                    "current_step": "analyze_results",
                    "should_continue": True
                }
            
        except Exception as e:
            logger.error(f"Failed to analyze results: {e}")
            return {
                "current_step": "analyze_results",
                "error": str(e),
                "should_continue": False
            }
    
    async def _generate_report(self, state: AuditState) -> Dict[str, Any]:
        """Generate final audit report."""
        logger.info("Generating audit report")
        
        try:
            # Prepare report data
            report_data = {
                "system_description": state["system_description"],
                "audit_type": state["audit_type"],
                "regulations": state["regulations"],
                "findings": state.get("findings", []),
                "recommendations": state.get("recommendations", []),
                "compliance_status": state.get("compliance_status", {}),
                "risk_score": state.get("risk_score", 0.0),
                "execution_summary": {
                    "total_tasks": len(state.get("tasks", {})),
                    "completed_tasks": len(state.get("completed_tasks", [])),
                    "failed_tasks": len(state.get("failed_tasks", []))
                }
            }
            
            # Generate report using LLM
            report_prompt = AuditPrompts.get_report_generation_prompt(
                audit_data=report_data,
                findings=state.get("findings", []),
                context=state.get("context", {})
            )
            
            report = await self.llm_client.generate(
                prompt=report_prompt,
                model=settings.agent.executor_model,
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            try:
                report_data = json.loads(report)
                
                # Store report in memory
                self.memory.store_memory_item(
                    content=f"Audit report generated for {state['system_description']}",
                    metadata={
                        "report_sections": list(report_data.keys()),
                        "risk_score": state.get("risk_score", 0.0),
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=1.0  # Highest importance for reports
                )
                
                logger.info("Audit report generated successfully")
                
                return {
                    "current_step": "generate_report",
                    "report": report_data,
                    "should_continue": True
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse report JSON: {e}")
                # Create basic report structure
                basic_report = {
                    "executive_summary": f"Audit completed for {state['system_description']}",
                    "findings_summary": f"{len(state.get('findings', []))} findings identified",
                    "risk_score": state.get("risk_score", 0.0),
                    "recommendations": state.get("recommendations", []),
                    "error": "Report generation failed, using basic structure"
                }
                
                return {
                    "current_step": "generate_report",
                    "report": basic_report,
                    "error": f"Report parsing failed: {e}",
                    "should_continue": True  # Continue despite error
                }
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                "current_step": "generate_report",
                "error": str(e),
                "should_continue": False
            }
    
    async def _handle_error(self, state: AuditState) -> Dict[str, Any]:
        """Handle errors in the workflow."""
        error = state.get("error", "Unknown error")
        current_step = state.get("current_step", "unknown")
        
        logger.error(f"Workflow error at step {current_step}: {error}")
        
        # Store error in memory
        self.memory.store_memory_item(
            content=f"Workflow error at {current_step}: {error}",
            metadata={
                "step": current_step,
                "error": error,
                "timestamp": asyncio.get_event_loop().time()
            },
            importance=0.9  # High importance for errors
        )
        
        # Create error report
        error_report = {
            "status": "failed",
            "error_step": current_step,
            "error_message": error,
            "partial_results": {
                "completed_tasks": state.get("completed_tasks", []),
                "failed_tasks": state.get("failed_tasks", []),
                "findings": state.get("findings", []),
                "risk_score": state.get("risk_score", 0.0)
            },
            "recommendation": "Review the error and consider re-running the audit with adjusted parameters"
        }
        
        return {
            "current_step": "handle_error",
            "report": error_report,
            "should_continue": False  # Stop workflow
        }
    
    async def _finalize_workflow(self, state: AuditState) -> Dict[str, Any]:
        """Finalize the audit workflow."""
        logger.info("Finalizing audit workflow")
        
        # Determine if workflow was successful
        has_error = state.get("error") is not None or state.get("current_step") == "handle_error"
        
        if has_error:
            final_report = state.get("report", {"status": "failed", "error": "Unknown error"})
            status = "failed"
        else:
            final_report = state.get("report", {"status": "completed", "summary": "Audit completed"})
            status = "completed"
        
        # Update context
        context = state.get("context", {})
        context["workflow_completed"] = True
        context["completion_status"] = status
        context["completion_time"] = asyncio.get_event_loop().time()
        
        # Store final state in memory
        self.memory.store_memory_item(
            content=f"Audit workflow {status} for {state['system_description']}",
            metadata={
                "status": status,
                "risk_score": state.get("risk_score", 0.0),
                "findings_count": len(state.get("findings", [])),
                "total_tasks": len(state.get("tasks", {})),
                "completed_tasks": len(state.get("completed_tasks", [])),
                "workflow_duration": context.get("completion_time", 0) - context.get("initialized_at", 0)
            },
            importance=0.8
        )
        
        logger.info(f"Audit workflow {status}")
        
        return {
            "current_step": "finalize",
            "status": status,
            "final_report": final_report,
            "context": context,
            "should_continue": False  # Workflow ends here
        }
    
    async def run(self, audit_plan: AuditPlan, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the audit workflow.
        
        Args:
            audit_plan: The audit plan to execute
            config: Additional configuration
            
        Returns:
            Final workflow state
        """
        logger.info(f"Starting audit workflow for plan: {audit_plan.audit_id}")
        
        # Prepare initial state
        initial_state = AuditState(
            audit_request={
                "system_description": "AI system under audit",
                "audit_type": "comprehensive",
                "regulations": ["GDPR", "CCPA"],
                "audit_id": audit_plan.audit_id
            },
            system_description="AI system under audit",
            audit_type="comprehensive",
            regulations=["GDPR", "CCPA"],
            audit_plan=audit_plan,
            planning_complete=True,
            tasks=audit_plan.tasks,
            task_order=audit_plan.task_order,
            execution_results={},
            completed_tasks=[],
            failed_tasks=[],
            findings=[],
            recommendations=[],
            compliance_status={},
            risk_score=0.0,
            context={
                "plan_id": audit_plan.audit_id,
                "initialized_at": asyncio.get_event_loop().time(),
                "config": config or {}
            },
            memory_items=[],
            current_step="initialize",
            error=None,
            should_continue=True
        )
        
        # Run workflow
        try:
            final_state = await self.app.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": audit_plan.audit_id}}
            )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Create error state
            error_state = {
                "status": "failed",
                "error": str(e),
                "final_report": {
                    "status": "failed",
                    "error": str(e),
                    "recommendation": "Workflow execution failed, check logs for details"
                },
                "context": {
                    "error_time": asyncio.get_event_loop().time(),
                    "error_type": type(e).__name__
                }
            }
            
            return error_state


# Example usage
if __name__ == "__main__":
    async def test_workflow():
        # Create a simple test plan
        from agent.planner import AuditPlan, Task, TaskType, TaskPriority
        
        test_tasks = {
            "task_1": Task(
                id="task_1",
                type=TaskType.COMPLIANCE_CHECK,
                description="Check GDPR compliance",
                priority=TaskPriority.HIGH,
                dependencies=[],
                parameters={"regulations": ["GDPR"]},
                expected_output="GDPR compliance assessment",
                timeout_seconds=300
            ),
            "task_2": Task(
                id="task_2",
                type=TaskType.SECURITY_ASSESSMENT,
                description="Basic security assessment",
                priority=TaskPriority.MEDIUM,
                dependencies=[],
                parameters={},
                expected_output="Security assessment report",
                timeout_seconds=300
            )
        }
        
        test_plan = AuditPlan(
            audit_id="test_plan_001",
            tasks=test_tasks,
            task_order=["task_1", "task_2"],
            estimated_duration=600,
            required_tools=["compliance_retriever", "security_scanner"],
            risk_areas=["compliance", "security"]
        )
        
        # Create and run workflow
        workflow = AuditWorkflow()
        result = await workflow.run(test_plan)
        
        print(f"Workflow status: {result.get('status', 'unknown')}")
        print(f"Final step: {result.get('current_step', 'unknown')}")
        
        if "final_report" in result:
            report = result["final_report"]
            print(f"Report status: {report.get('status', 'unknown')}")
            if "error" in report:
                print(f"Error: {report['error']}")
        
        # Clean up
        if hasattr(workflow.memory, 'close'):
            workflow.memory.close()
    
    asyncio.run(test_workflow())