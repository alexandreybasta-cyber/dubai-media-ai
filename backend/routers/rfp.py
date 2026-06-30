import uuid
from typing import Optional, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/rfp", tags=["rfp"])


class RFPCreateRequest(BaseModel):
    title: str
    project_description: str
    sections: Optional[List[str]] = None
    tone: str = "professional"
    language: str = "en"


class RegenerateSectionRequest(BaseModel):
    rfp_id: str
    section_name: str
    instructions: Optional[str] = None


class RFPEvaluateRequest(BaseModel):
    rfp_document_url: Optional[str] = None
    criteria: Optional[List[str]] = None
    proposals: List[str] = []


@router.post("/create")
async def create_rfp(request: RFPCreateRequest):
    rfp_id = str(uuid.uuid4())
    return {
        "rfp_id": rfp_id,
        "title": request.title,
        "status": "completed",
        "sections": [
            {
                "name": "Executive Summary",
                "content": (
                    f"This Request for Proposal outlines the requirements for {request.title}. "
                    "The selected vendor will deliver a comprehensive solution aligned with "
                    "Dubai Media Incorporated's strategic vision for digital transformation."
                ),
            },
            {
                "name": "Project Overview",
                "content": request.project_description,
            },
            {
                "name": "Scope of Work",
                "content": (
                    "The vendor shall provide end-to-end implementation including: "
                    "system design, development, testing, deployment, training, and "
                    "12-month post-launch support."
                ),
            },
            {
                "name": "Technical Requirements",
                "content": (
                    "The proposed solution must support cloud-native architecture, "
                    "high availability (99.9% uptime SLA), and integration with "
                    "existing media asset management systems."
                ),
            },
            {
                "name": "Evaluation Criteria",
                "content": (
                    "Proposals will be evaluated on: Technical capability (30%), "
                    "Cost effectiveness (25%), Timeline (20%), Team experience (15%), "
                    "and Innovation (10%)."
                ),
            },
            {
                "name": "Submission Guidelines",
                "content": (
                    "All proposals must be submitted electronically by the deadline. "
                    "Proposals should not exceed 50 pages excluding appendices."
                ),
            },
        ],
    }


@router.post("/regenerate-section")
async def regenerate_section(request: RegenerateSectionRequest):
    return {
        "rfp_id": request.rfp_id,
        "section_name": request.section_name,
        "content": (
            f"[Regenerated] Updated content for '{request.section_name}' section "
            f"based on instructions: {request.instructions or 'default regeneration'}. "
            "This section has been refined to better align with project requirements "
            "and industry best practices."
        ),
        "status": "completed",
    }


@router.get("/{rfp_id}/export/docx")
async def export_rfp_docx(rfp_id: str):
    return {
        "rfp_id": rfp_id,
        "format": "docx",
        "download_url": f"/uploads/rfp/{rfp_id}/document.docx",
        "status": "ready",
        "message": "DOCX export generated successfully.",
    }


@router.get("/{rfp_id}/export/pdf")
async def export_rfp_pdf(rfp_id: str):
    return {
        "rfp_id": rfp_id,
        "format": "pdf",
        "download_url": f"/uploads/rfp/{rfp_id}/document.pdf",
        "status": "ready",
        "message": "PDF export generated successfully.",
    }


@router.post("/evaluate")
async def evaluate_rfp(request: RFPEvaluateRequest):
    eval_id = str(uuid.uuid4())
    return {
        "eval_id": eval_id,
        "status": "processing",
        "proposals_count": len(request.proposals),
        "message": "Evaluation started. Use the status endpoint to track progress.",
    }


@router.get("/evaluation/{eval_id}/status")
async def get_evaluation_status(eval_id: str):
    return {
        "eval_id": eval_id,
        "status": "completed",
        "progress": 100,
        "proposals_evaluated": 3,
        "message": "All proposals have been evaluated.",
    }


@router.get("/evaluation/{eval_id}/results")
async def get_evaluation_results(eval_id: str):
    return {
        "eval_id": eval_id,
        "status": "completed",
        "rankings": [
            {
                "rank": 1,
                "proposal_name": "Vendor A - TechSolutions Inc.",
                "overall_score": 87.5,
                "scores": {
                    "technical_capability": 90,
                    "cost_effectiveness": 82,
                    "timeline": 88,
                    "team_experience": 85,
                    "innovation": 92,
                },
                "recommendation": "Strongly Recommended",
                "summary": "Comprehensive solution with strong AI capabilities and proven media industry track record.",
            },
            {
                "rank": 2,
                "proposal_name": "Vendor B - MediaTech Global",
                "overall_score": 79.2,
                "scores": {
                    "technical_capability": 78,
                    "cost_effectiveness": 88,
                    "timeline": 75,
                    "team_experience": 80,
                    "innovation": 70,
                },
                "recommendation": "Recommended with Reservations",
                "summary": "Cost-effective proposal but limited innovation in AI-driven features.",
            },
            {
                "rank": 3,
                "proposal_name": "Vendor C - Digital Dynamics",
                "overall_score": 72.0,
                "scores": {
                    "technical_capability": 70,
                    "cost_effectiveness": 75,
                    "timeline": 80,
                    "team_experience": 65,
                    "innovation": 68,
                },
                "recommendation": "Not Recommended",
                "summary": "Lacks depth in media-specific AI capabilities.",
            },
        ],
    }


@router.get("/evaluation/{eval_id}/export/xlsx")
async def export_evaluation_xlsx(eval_id: str):
    return {
        "eval_id": eval_id,
        "format": "xlsx",
        "download_url": f"/uploads/evaluation/{eval_id}/results.xlsx",
        "status": "ready",
        "message": "Excel export generated successfully.",
    }


@router.get("/evaluation/{eval_id}/export/pdf")
async def export_evaluation_pdf(eval_id: str):
    return {
        "eval_id": eval_id,
        "format": "pdf",
        "download_url": f"/uploads/evaluation/{eval_id}/report.pdf",
        "status": "ready",
        "message": "PDF evaluation report generated successfully.",
    }
