#!/usr/bin/env python3
"""
Simplified RiskAuditGraph without checkpoint dependencies.
Compatible with LangGraph 1.x.
"""

import logging
from typing import Dict, List, Any, Optional, TypedDict
from enum import Enum
import asyncio

# LangGraph 1.x imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from agent.planner import TaskPlanner, AuditPlan, Task
from agent.executor import TaskExecutor, ExecutionResult, ExecutionStatus
from agent.memory import AuditMemory
from agent.prompts import AuditPrompts
from models.llm_main import create_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditState(TypedDict):
    """State for the audit workflow."""
    input: str
    plan: Optional[AuditPlan]
    tasks: List[Task]
    current_task: Optional[Task]
    results: List[ExecutionResult]
    summary: Optional[str]
    recommendations: List[str]
    risk_level: Optional[str]
    metadata: Dict[str, Any]


class SimpleMemorySaver:
    """Simple in-memory checkpoint saver for compatibility."""
    
    def __init__(self):
        self.checkpoints = {}
    
    def get(self, config):
        """Get checkpoint for config."""
        key = str(config)
        return self.checkpoints.get(key)
    
    def put(self, config, checkpoint):
        """Save checkpoint for config."""
        key = str(config)
        self.checkpoints[key] = checkpoint


class RiskAuditGraph:
    """Main graph for orchestrating AI risk audits."""
    
    def __init__(self):
        self.llm_client = create_llm_client()
        self.planner = TaskPlanner(self.llm_client)
        self.executor = TaskExecutor(self.llm_client)
        self.memory = AuditMemory()
        self.prompts = AuditPrompts()
        
        # Build the graph
        self.graph = self._build_graph()
        self.compiled_graph = None
        
        logger.info("RiskAuditGraph initialized (simplified version)")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow without checkpointing."""
        graph = StateGraph(AuditState)
        
        # Add nodes
        graph.add_node("plan", self._plan_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("summarize", self._summarize_node)
        
        # Set entry point
        graph.set_entry_point("plan")
        
        # Add edges
        graph.add_edge("plan", "execute")
        graph.add_conditional_edges(
            "execute",
            self._should_continue,
            {
                "continue": "execute",
                "complete": "analyze"
            }
        )
        graph.add_edge("analyze", "summarize")
        graph.add_edge("summarize", END)
        
        return graph
    
    def _plan_node(self, state: AuditState) -> Dict[str, Any]:
        """Plan the audit tasks."""
        logger.info("Planning audit...")
        
        try:
            plan = self.planner.plan_audit(state["input"])
            return {
                "plan": plan,
                "tasks": plan.tasks,
                "current_task": plan.tasks[0] if plan.tasks else None,
                "results": []
            }
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            # Create a fallback plan
            return {
                "plan": AuditPlan(
                    objective=state["input"],
                    scope=["General AI risk assessment"],
                    tasks=[
                        Task(
                            id="task_1",
                            description="Analyze AI system risks",
                            tool="web_scraper",
                            parameters={"url": "https://example.com"},
                            dependencies=[]
                        )
                    ],
                    constraints=["Use available tools and data"]
                ),
                "tasks": [],
                "current_task": None,
                "results": []
            }
    
    def _execute_node(self, state: AuditState) -> Dict[str, Any]:
        """Execute the current task."""
        if not state["current_task"]:
            return {"current_task": None}
        
        logger.info(f"Executing task: {state['current_task'].id}")
        
        try:
            result = self.executor.execute_task(state["current_task"])
            
            # Update results
            results = state.get("results", [])
            results.append(result)
            
            # Get next task
            tasks = state.get("tasks", [])
            current_task_index = next(
                (i for i, t in enumerate(tasks) if t.id == state["current_task"].id),
                -1
            )
            
            next_task = None
            if current_task_index + 1 < len(tasks):
                next_task = tasks[current_task_index + 1]
            
            return {
                "results": results,
                "current_task": next_task
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            # Mark task as failed and move to next
            result = ExecutionResult(
                task_id=state["current_task"].id,
                status=ExecutionStatus.FAILED,
                output=f"Error: {str(e)}",
                metadata={"error": str(e)}
            )
            
            results = state.get("results", [])
            results.append(result)
            
            # Try to get next task
            tasks = state.get("tasks", [])
            current_task_index = next(
                (i for i, t in enumerate(tasks) if t.id == state["current_task"].id),
                -1
            )
            
            next_task = None
            if current_task_index + 1 < len(tasks):
                next_task = tasks[current_task_index + 1]
            
            return {
                "results": results,
                "current_task": next_task
            }
    
    def _should_continue(self, state: AuditState) -> str:
        """Determine if we should continue executing tasks."""
        if state["current_task"]:
            return "continue"
        return "complete"
    
    def _analyze_node(self, state: AuditState) -> Dict[str, Any]:
        """Analyze the audit results."""
        logger.info("Analyzing results...")
        
        try:
            # Simple analysis based on results
            results = state.get("results", [])
            successful = sum(1 for r in results if r.status == ExecutionStatus.COMPLETED)
            total = len(results)
            
            if total == 0:
                risk_level = "UNKNOWN"
                summary = "No tasks were executed successfully."
            else:
                success_rate = successful / total
                
                if success_rate >= 0.8:
                    risk_level = "LOW"
                elif success_rate >= 0.5:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"
                
                summary = f"Audit completed with {successful}/{total} successful tasks. Overall risk level: {risk_level}"
            
            # Generate recommendations
            recommendations = [
                "Implement regular security audits",
                "Establish data governance policies",
                "Monitor AI system performance",
                "Maintain compliance documentation"
            ]
            
            return {
                "summary": summary,
                "risk_level": risk_level,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "summary": f"Analysis failed: {str(e)}",
                "risk_level": "ERROR",
                "recommendations": ["Review audit process and retry"]
            }
    
    def _summarize_node(self, state: AuditState) -> Dict[str, Any]:
        """Create final summary."""
        logger.info("Creating final summary...")
        
        # Add metadata
        metadata = {
            "timestamp": "2026-03-28T11:00:00Z",
            "version": "1.0.0",
            "mock_mode": settings.llm.use_mock,
            "graph_version": "simple"
        }
        
        return {
            "metadata": metadata
        }
    
    def compile(self):
        """Compile the graph without checkpointing."""
        if not self.compiled_graph:
            # Simple compilation without checkpointing
            self.compiled_graph = self.graph.compile()
        
        return self.compiled_graph
    
    async def run_audit(self, input_text: str) -> Dict[str, Any]:
        """Run a complete audit workflow."""
        logger.info(f"Starting audit for: {input_text}")
        
        # Initialize state
        initial_state = AuditState(
            input=input_text,
            plan=None,
            tasks=[],
            current_task=None,
            results=[],
            summary=None,
            recommendations=[],
            risk_level=None,
            metadata={}
        )
        
        # Compile graph if needed
        if not self.compiled_graph:
            self.compile()
        
        # Run the graph
        try:
            # For async execution
            final_state = await self.compiled_graph.ainvoke(initial_state)
            
            # Format response
            return {
                "success": True,
                "input": input_text,
                "summary": final_state.get("summary", "No summary available"),
                "risk_level": final_state.get("risk_level", "UNKNOWN"),
                "recommendations": final_state.get("recommendations", []),
                "tasks_executed": len(final_state.get("results", [])),
                "tasks_successful": sum(1 for r in final_state.get("results", []) 
                                      if r.status == ExecutionStatus.COMPLETED),
                "metadata": final_state.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return {
                "success": False,
                "input": input_text,
                "error": str(e),
                "summary": f"Audit failed: {str(e)}",
                "risk_level": "ERROR",
                "recommendations": ["Review the input and try again"],
                "tasks_executed": 0,
                "tasks_successful": 0,
                "metadata": {"error": str(e)}
            }


# Factory function for compatibility
def create_risk_audit_graph():
    """Create a RiskAuditGraph instance."""
    return RiskAuditGraph()


# Example usage
if __name__ == "__main__":
    async def test():
        graph = RiskAuditGraph()
        result = await graph.run_audit(
            "Assess the AI risks for a healthcare chatbot system"
        )
        print(f"Audit result: {result}")
    
    asyncio.run(test())