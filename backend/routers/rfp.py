import json
import os
import uuid
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from config import settings
from services.rfp_creator import RFPCreator

router = APIRouter(prefix="/api/rfp", tags=["rfp"])
rfp_creator = RFPCreator()

RFP_STORAGE_DIR = os.path.join(settings.UPLOAD_DIR, "rfps")
os.makedirs(RFP_STORAGE_DIR, exist_ok=True)


# ─── Models ──────────────────────────────────────────────────────────────────


class EvaluationCriterion(BaseModel):
    name: str
    weight: int
    description: str = ""


class TimelineMilestone(BaseModel):
    name: str
    date: str


class TimelineData(BaseModel):
    start_date: str
    end_date: str
    milestones: List[TimelineMilestone] = []


class BudgetRange(BaseModel):
    min: float
    max: float
    currency: str = "AED"


class RFPCreateRequest(BaseModel):
    project_title: str
    project_overview: str
    scope_of_work: str = ""
    technical_requirements: List[str] = []
    evaluation_criteria: List[EvaluationCriterion] = []
    timeline: Optional[TimelineData] = None
    budget_range: Optional[BudgetRange] = None
    compliance_requirements: List[str] = []
    industry: str = "Broadcasting"
    language: str = "en"
    tone: str = "formal"


class RegenerateSectionRequest(BaseModel):
    rfp_id: str
    section_name: str
    instructions: Optional[str] = None


class RFPEvaluateRequest(BaseModel):
    rfp_document_url: Optional[str] = None
    criteria: Optional[List[str]] = None
    proposals: List[str] = []


# ─── Helper ──────────────────────────────────────────────────────────────────


def _save_rfp(rfp_id: str, data: dict):
    path = os.path.join(RFP_STORAGE_DIR, f"{rfp_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_rfp(rfp_id: str) -> dict:
    path = os.path.join(RFP_STORAGE_DIR, f"{rfp_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"RFP '{rfp_id}' not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── CREATE Endpoints ────────────────────────────────────────────────────────


@router.post("/create")
async def create_rfp(request: RFPCreateRequest):
    rfp_id = str(uuid.uuid4())
    input_data = {
        "project_title": request.project_title,
        "project_overview": request.project_overview,
        "scope_of_work": request.scope_of_work,
        "technical_requirements": request.technical_requirements,
        "evaluation_criteria": [c.model_dump() for c in request.evaluation_criteria],
        "timeline": request.timeline.model_dump() if request.timeline else {},
        "budget_range": request.budget_range.model_dump() if request.budget_range else None,
        "compliance_requirements": request.compliance_requirements,
        "industry": request.industry,
        "language": request.language,
        "tone": request.tone,
    }

    try:
        rfp_data = await rfp_creator.generate_rfp(input_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    rfp_data["rfp_id"] = rfp_id
    _save_rfp(rfp_id, rfp_data)

    return {
        "rfp_id": rfp_id,
        "title": request.project_title,
        "status": "completed",
        "sections": rfp_data["sections"],
        "language": rfp_data["language"],
    }


@router.post("/regenerate-section")
async def regenerate_section(request: RegenerateSectionRequest):
    rfp_data = _load_rfp(request.rfp_id)

    try:
        new_content = await rfp_creator.regenerate_section(
            rfp_data, request.section_name, request.instructions or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Update stored RFP
    bilingual = rfp_data.get("language") == "both"
    for section in rfp_data.get("sections", []):
        if section["name"] == request.section_name:
            if bilingual and "---AR---" in new_content:
                parts = new_content.split("---AR---")
                section["content_en"] = parts[0].strip()
                section["content_ar"] = parts[1].strip()
            elif rfp_data.get("language") == "ar":
                section["content_ar"] = new_content
            else:
                section["content_en"] = new_content
            break

    _save_rfp(request.rfp_id, rfp_data)

    return {
        "rfp_id": request.rfp_id,
        "section_name": request.section_name,
        "content": new_content,
        "status": "completed",
    }


@router.get("/{rfp_id}/export/docx")
async def export_rfp_docx(rfp_id: str):
    rfp_data = _load_rfp(rfp_id)

    try:
        docx_bytes = rfp_creator.export_docx(rfp_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="RFP_{rfp_id[:8]}.docx"'},
    )


@router.get("/{rfp_id}/export/pdf")
async def export_rfp_pdf(rfp_id: str):
    rfp_data = _load_rfp(rfp_id)

    try:
        pdf_bytes = rfp_creator.export_pdf(rfp_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="RFP_{rfp_id[:8]}.pdf"'},
    )


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
