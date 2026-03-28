#!/usr/bin/env python3
"""
FastAPI server for the Agentic AI Risk Auditor.
Provides REST API endpoints for running audits and managing results.
"""

import asyncio
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import logging

from .main import AgenticAIRiskAuditor, AuditRequest, AuditResult
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Risk Auditor API",
    description="API for automated AI risk assessment and compliance auditing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for audit results (in production, use a database)
audit_results: Dict[str, Dict[str, Any]] = {}
audit_queue: Dict[str, Dict[str, Any]] = {}


# Pydantic models for request/response
class AuditRequestModel(BaseModel):
    """Request model for audit API."""
    system_description: str = Field(..., description="Description of the AI system to audit")
    audit_type: str = Field(default="comprehensive", description="Type of audit (compliance, security, ethical, comprehensive)")
    regulations: List[str] = Field(default=["GDPR", "CCPA", "AI Act"], description="List of regulations to check against")
    target_url: Optional[str] = Field(None, description="URL of the system to audit")
    contract_address: Optional[str] = Field(None, description="Smart contract address to audit")
    document_paths: Optional[List[str]] = Field(None, description="Paths to documentation files")
    custom_requirements: Optional[List[str]] = Field(None, description="Custom requirements to check")
    
    class Config:
        schema_extra = {
            "example": {
                "system_description": "Customer service chatbot using GPT-4 with access to customer data",
                "audit_type": "comprehensive",
                "regulations": ["GDPR", "CCPA", "AI Act"],
                "custom_requirements": ["Data minimization", "Transparency", "User consent"]
            }
        }


class AuditResponseModel(BaseModel):
    """Response model for audit API."""
    audit_id: str = Field(..., description="Unique audit identifier")
    status: str = Field(..., description="Audit status (queued, running, completed, failed)")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="When the audit was created")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    result_url: Optional[str] = Field(None, description="URL to retrieve audit results")


class AuditResultModel(BaseModel):
    """Model for complete audit results."""
    audit_id: str = Field(..., description="Unique audit identifier")
    timestamp: datetime = Field(..., description="When the audit was completed")
    request: AuditRequestModel = Field(..., description="Original audit request")
    risk_score: float = Field(..., description="Overall risk score (0-100)")
    findings_count: int = Field(..., description="Number of findings")
    compliance_status: Dict[str, bool] = Field(..., description="Compliance status per regulation")
    executive_summary: str = Field(..., description="Executive summary")
    report_url: Optional[str] = Field(None, description="URL to download full report")


class AuditStatusModel(BaseModel):
    """Model for audit status."""
    audit_id: str = Field(..., description="Unique audit identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Current status message")
    created_at: datetime = Field(..., description="When the audit was created")
    updated_at: datetime = Field(..., description="Last status update")


# Dependency for auditor instance
def get_auditor():
    """Get auditor instance (singleton pattern)."""
    return AgenticAIRiskAuditor()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Agentic AI Risk Auditor API",
        "version": "1.0.0",
        "description": "API for automated AI risk assessment and compliance auditing",
        "endpoints": {
            "POST /audit": "Start a new audit",
            "GET /audit/{audit_id}": "Get audit results",
            "GET /audit/{audit_id}/status": "Get audit status",
            "GET /audits": "List all audits",
            "GET /audit/{audit_id}/report": "Download audit report",
            "POST /audit/batch": "Start multiple audits",
            "GET /health": "Health check"
        }
    }


@app.post("/audit", response_model=AuditResponseModel)
async def create_audit(
    request: AuditRequestModel,
    background_tasks: BackgroundTasks,
    auditor: AgenticAIRiskAuditor = Depends(get_auditor)
):
    """
    Start a new AI risk audit.
    
    This endpoint queues an audit for processing and returns immediately.
    Use the returned audit_id to check status and retrieve results.
    """
    # Generate unique audit ID
    audit_id = str(uuid.uuid4())
    
    # Convert to internal request model
    internal_request = AuditRequest(
        system_description=request.system_description,
        audit_type=request.audit_type,
        regulations=request.regulations,
        target_url=request.target_url,
        contract_address=request.contract_address,
        document_paths=request.document_paths,
        custom_requirements=request.custom_requirements
    )
    
    # Store in queue
    created_at = datetime.now()
    audit_queue[audit_id] = {
        "request": internal_request,
        "status": "queued",
        "created_at": created_at,
        "updated_at": created_at,
        "progress": 0,
        "message": "Audit queued for processing"
    }
    
    # Start background task
    background_tasks.add_task(
        process_audit,
        audit_id=audit_id,
        request=internal_request,
        auditor=auditor
    )
    
    # Estimate completion (simple heuristic: 2 minutes for comprehensive audit)
    estimated_completion = created_at.replace(second=created_at.second + 120)
    
    return AuditResponseModel(
        audit_id=audit_id,
        status="queued",
        message="Audit has been queued for processing",
        created_at=created_at,
        estimated_completion=estimated_completion,
        result_url=f"/audit/{audit_id}"
    )


@app.get("/audit/{audit_id}", response_model=AuditResultModel)
async def get_audit_result(audit_id: str):
    """
    Get audit results by ID.
    
    Returns the complete audit results if the audit is completed.
    """
    if audit_id not in audit_results:
        raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")
    
    result_data = audit_results[audit_id]
    result = result_data["result"]
    
    # Convert to response model
    request_model = AuditRequestModel(
        system_description=result.request.system_description,
        audit_type=result.request.audit_type,
        regulations=result.request.regulations,
        target_url=result.request.target_url,
        contract_address=result.request.contract_address,
        document_paths=result.request.document_paths,
        custom_requirements=result.request.custom_requirements
    )
    
    return AuditResultModel(
        audit_id=result.audit_id,
        timestamp=result.timestamp,
        request=request_model,
        risk_score=result.risk_score,
        findings_count=len(result.findings),
        compliance_status=result.compliance_status,
        executive_summary=result.executive_summary,
        report_url=f"/audit/{audit_id}/report"
    )


@app.get("/audit/{audit_id}/status", response_model=AuditStatusModel)
async def get_audit_status(audit_id: str):
    """
    Get current status of an audit.
    
    Returns progress information and current status message.
    """
    # Check if audit is in queue
    if audit_id in audit_queue:
        audit_data = audit_queue[audit_id]
        return AuditStatusModel(
            audit_id=audit_id,
            status=audit_data["status"],
            progress=audit_data["progress"],
            message=audit_data["message"],
            created_at=audit_data["created_at"],
            updated_at=audit_data["updated_at"]
        )
    
    # Check if audit is completed
    if audit_id in audit_results:
        result_data = audit_results[audit_id]
        return AuditStatusModel(
            audit_id=audit_id,
            status="completed",
            progress=100,
            message="Audit completed successfully",
            created_at=result_data["created_at"],
            updated_at=result_data["updated_at"]
        )
    
    raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")


@app.get("/audits")
async def list_audits(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all audits with optional filtering by status.
    
    Returns paginated list of audit summaries.
    """
    all_audits = []
    
    # Add queued/running audits
    for audit_id, audit_data in audit_queue.items():
        all_audits.append({
            "audit_id": audit_id,
            "status": audit_data["status"],
            "created_at": audit_data["created_at"],
            "system_description": audit_data["request"].system_description[:100] + "...",
            "audit_type": audit_data["request"].audit_type
        })
    
    # Add completed audits
    for audit_id, result_data in audit_results.items():
        result = result_data["result"]
        all_audits.append({
            "audit_id": audit_id,
            "status": "completed",
            "created_at": result_data["created_at"],
            "system_description": result.request.system_description[:100] + "...",
            "audit_type": result.request.audit_type,
            "risk_score": result.risk_score,
            "findings_count": len(result.findings)
        })
    
    # Filter by status if specified
    if status:
        all_audits = [a for a in all_audits if a["status"] == status]
    
    # Sort by creation date (newest first)
    all_audits.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Paginate
    paginated = all_audits[offset:offset + limit]
    
    return {
        "total": len(all_audits),
        "limit": limit,
        "offset": offset,
        "audits": paginated
    }


@app.get("/audit/{audit_id}/report")
async def download_audit_report(audit_id: str):
    """
    Download audit report as JSON file.
    
    Returns a JSON file with the complete audit report.
    """
    if audit_id not in audit_results:
        raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")
    
    result_data = audit_results[audit_id]
    result = result_data["result"]
    
    # Create report dictionary
    report = {
        "audit_id": result.audit_id,
        "timestamp": result.timestamp.isoformat(),
        "request": {
            "system_description": result.request.system_description,
            "audit_type": result.request.audit_type,
            "regulations": result.request.regulations,
            "target_url": result.request.target_url,
            "contract_address": result.request.contract_address,
            "custom_requirements": result.request.custom_requirements
        },
        "risk_score": result.risk_score,
        "findings": result.findings,
        "recommendations": result.recommendations,
        "compliance_status": result.compliance_status,
        "executive_summary": result.executive_summary,
        "detailed_report": result.detailed_report
    }
    
    # In a real implementation, you would save this to a file
    # For now, we'll return it as JSON response
    return JSONResponse(
        content=report,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=audit_report_{audit_id}.json"
        }
    )


@app.post("/audit/batch")
async def create_batch_audit(
    requests: List[AuditRequestModel],
    background_tasks: BackgroundTasks,
    auditor: AgenticAIRiskAuditor = Depends(get_auditor)
):
    """
    Start multiple audits in batch.
    
    Returns a list of audit IDs for tracking.
    """
    audit_ids = []
    
    for request in requests:
        audit_id = str(uuid.uuid4())
        
        # Convert to internal request model
        internal_request = AuditRequest(
            system_description=request.system_description,
            audit_type=request.audit_type,
            regulations=request.regulations,
            target_url=request.target_url,
            contract_address=request.contract_address,
            document_paths=request.document_paths,
            custom_requirements=request.custom_requirements
        )
        
        # Store in queue
        created_at = datetime.now()
        audit_queue[audit_id] = {
            "request": internal_request,
            "status": "queued",
            "created_at": created_at,
            "updated_at": created_at,
            "progress": 0,
            "message": "Audit queued for batch processing"
        }
        
        # Start background task
        background_tasks.add_task(
            process_audit,
            audit_id=audit_id,
            request=internal_request,
            auditor=auditor
        )
        
        audit_ids.append(audit_id)
    
    return {
        "message": f"Started {len(audit_ids)} audits in batch",
        "audit_ids": audit_ids,
        "status_url": "/audits"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "queue_size": len(audit_queue),
        "completed_audits": len(audit_results)
    }


@app.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    # Calculate some basic metrics
    total_audits = len(audit_queue) + len(audit_results)
    
    if audit_results:
        avg_risk_score = sum(r["result"].risk_score for r in audit_results.values()) / len(audit_results)
        total_findings = sum(len(r["result"].findings) for r in audit_results.values())
    else:
        avg_risk_score = 0
        total_findings = 0
    
    return {
        "total_audits": total_audits,
        "queued_audits": len(audit_queue),
        "completed_audits": len(audit_results),
        "average_risk_score": round(avg_risk_score, 2),
        "total_findings": total_findings,
        "timestamp": datetime.now().isoformat()
    }


async def process_audit(
    audit_id: str,
    request: AuditRequest,
    auditor: AgenticAIRiskAuditor
):
    """
    Background task to process an audit.
    
    This function runs asynchronously and updates the audit status.
    """
    try:
        # Update status to running
        audit_queue[audit_id].update({
            "status": "running",
            "progress": 10,
            "message": "Planning audit tasks...",
            "updated_at": datetime.now()
        })
        
        # Run the audit
        result = await auditor.run_audit(request)
        
        # Store result
        audit_results[audit_id] = {
            "result": result,
            "created_at": audit_queue[audit_id]["created_at"],
            "updated_at": datetime.now()
        }
        
        # Remove from queue
        del audit_queue[audit_id]
        
        logger.info(f"Audit {audit_id} completed successfully")
        
    except Exception as e:
        # Update status to failed
        audit_queue[audit_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Audit failed: {str(e)}",
            "updated_at": datetime.now()
        })
        
        logger.error(f"Audit {audit_id} failed: {e}")
        
        # Optionally, move to results with error status
        audit_results[audit_id] = {
            "error": str(e),
            "created_at": audit_queue[audit_id]["created_at"],
            "updated_at": datetime.now()
        }
        
        # Remove from queue
        del audit_queue[audit_id]


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )