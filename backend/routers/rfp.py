import json
import os
import uuid
import asyncio
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel

from config import settings
from services.rfp_creator import RFPCreator
from services.rfp_evaluator import RFPEvaluator

router = APIRouter(prefix="/api/rfp", tags=["rfp"])
rfp_creator = RFPCreator()
rfp_evaluator = RFPEvaluator()

RFP_STORAGE_DIR = os.path.join(settings.UPLOAD_DIR, "rfps")
EVAL_STORAGE_DIR = os.path.join(settings.UPLOAD_DIR, "evaluations")
os.makedirs(RFP_STORAGE_DIR, exist_ok=True)
os.makedirs(EVAL_STORAGE_DIR, exist_ok=True)


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


# ─── Evaluate Helpers ────────────────────────────────────────────────────────


def _save_evaluation(eval_id: str, data: dict):
    path = os.path.join(EVAL_STORAGE_DIR, f"{eval_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_evaluation(eval_id: str) -> dict:
    path = os.path.join(EVAL_STORAGE_DIR, f"{eval_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Evaluation '{eval_id}' not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def _run_evaluation(eval_id: str, rfp_text: str, vendor_responses: list, criteria: list):
    """Background task to run the AI evaluation."""
    eval_data = _load_evaluation(eval_id)
    try:
        eval_data["status"] = "processing"
        eval_data["progress"] = 10
        _save_evaluation(eval_id, eval_data)

        results = await rfp_evaluator.evaluate_responses(rfp_text, vendor_responses, criteria)

        eval_data["status"] = "completed"
        eval_data["progress"] = 100
        eval_data["results"] = results
        eval_data["proposals_evaluated"] = len(vendor_responses)
        _save_evaluation(eval_id, eval_data)
    except Exception as e:
        eval_data["status"] = "failed"
        eval_data["error"] = str(e)
        _save_evaluation(eval_id, eval_data)


# ─── EVALUATE Endpoints ──────────────────────────────────────────────────────


@router.post("/evaluate")
async def evaluate_rfp(
    background_tasks: BackgroundTasks,
    rfp_file: UploadFile = File(...),
    vendor_files: List[UploadFile] = File(...),
    vendor_names: str = Form(...),
    criteria: str = Form(...),
):
    eval_id = str(uuid.uuid4())

    # Parse vendor names and criteria from JSON strings
    try:
        names_list = json.loads(vendor_names)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="vendor_names must be valid JSON array")

    try:
        criteria_list = json.loads(criteria)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="criteria must be valid JSON array")

    if len(names_list) != len(vendor_files):
        raise HTTPException(
            status_code=400,
            detail=f"Number of vendor names ({len(names_list)}) must match vendor files ({len(vendor_files)})",
        )

    if len(vendor_files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 vendor responses required")

    # Extract text from RFP file
    rfp_bytes = await rfp_file.read()
    rfp_text = rfp_evaluator.extract_text(rfp_bytes, rfp_file.filename or "rfp.pdf")

    if not rfp_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from RFP file")

    # Extract text from vendor files
    vendor_responses = []
    for i, vf in enumerate(vendor_files):
        vf_bytes = await vf.read()
        vf_text = rfp_evaluator.extract_text(vf_bytes, vf.filename or f"vendor_{i}.pdf")
        vendor_responses.append({
            "vendor_name": names_list[i],
            "response_text": vf_text,
        })

    # Create initial evaluation record
    eval_data = {
        "eval_id": eval_id,
        "status": "queued",
        "progress": 0,
        "proposals_evaluated": 0,
        "vendor_names": names_list,
        "criteria": criteria_list,
        "results": None,
        "error": None,
    }
    _save_evaluation(eval_id, eval_data)

    # Run evaluation in background
    background_tasks.add_task(_run_evaluation, eval_id, rfp_text, vendor_responses, criteria_list)

    return {
        "eval_id": eval_id,
        "status": "queued",
        "proposals_count": len(vendor_responses),
        "message": "Evaluation started. Use the status endpoint to track progress.",
    }


@router.get("/evaluation/{eval_id}/status")
async def get_evaluation_status(eval_id: str):
    eval_data = _load_evaluation(eval_id)
    return {
        "eval_id": eval_id,
        "status": eval_data.get("status", "unknown"),
        "progress": eval_data.get("progress", 0),
        "proposals_evaluated": eval_data.get("proposals_evaluated", 0),
        "error": eval_data.get("error"),
        "message": (
            "Evaluation complete." if eval_data.get("status") == "completed"
            else "Evaluation in progress..." if eval_data.get("status") == "processing"
            else "Evaluation queued." if eval_data.get("status") == "queued"
            else f"Evaluation failed: {eval_data.get('error', 'Unknown error')}"
        ),
    }


@router.get("/evaluation/{eval_id}/results")
async def get_evaluation_results(eval_id: str):
    eval_data = _load_evaluation(eval_id)

    if eval_data.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation not yet completed. Current status: {eval_data.get('status')}",
        )

    return {
        "eval_id": eval_id,
        "status": "completed",
        "results": eval_data.get("results"),
    }


@router.get("/evaluation/{eval_id}/export/xlsx")
async def export_evaluation_xlsx(eval_id: str):
    eval_data = _load_evaluation(eval_id)

    if eval_data.get("status") != "completed" or not eval_data.get("results"):
        raise HTTPException(status_code=400, detail="Evaluation not completed yet")

    try:
        xlsx_bytes = rfp_evaluator.export_xlsx(eval_data["results"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XLSX generation failed: {str(e)}")

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="Evaluation_{eval_id[:8]}.xlsx"'},
    )


@router.get("/evaluation/{eval_id}/export/pdf")
async def export_evaluation_pdf(eval_id: str):
    eval_data = _load_evaluation(eval_id)

    if eval_data.get("status") != "completed" or not eval_data.get("results"):
        raise HTTPException(status_code=400, detail="Evaluation not completed yet")

    try:
        pdf_bytes = rfp_evaluator.export_pdf_report(eval_data["results"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Evaluation_{eval_id[:8]}.pdf"'},
    )
