"""
biomarker_routes.py – Biomarker endpoints.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
import shutil, tempfile, os

from app.models.biomarker import BiomarkerCreate, BiomarkerOut
from app.services.biomarker_service import add_biomarker, get_biomarkers, ingest_from_image, get_narrative

router = APIRouter(prefix="/patient", tags=["Biomarkers"])


@router.get("/{id}/biomarkers")
def get_patient_biomarkers(id: int):
    """Return all biomarker readings for a patient."""
    return get_biomarkers(id)


@router.post("/{id}/biomarkers", status_code=201)
def add_patient_biomarker(id: int, data: BiomarkerCreate):
    return add_biomarker(id, data.biomarker_type, data.value, data.timestamp)


@router.post("/{id}/biomarkers/ocr", status_code=201)
async def ocr_biomarker_upload(id: int, file: UploadFile = File(...)):
    """
    Upload an image file; OCR pipeline extracts biomarker values.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        records = ingest_from_image(id, tmp_path)
    finally:
        os.unlink(tmp_path)
    return {"added": len(records), "records": records}


@router.get("/{id}/biomarkers/narrative")
def patient_narrative(id: int):
    """Return AI-generated narrative from biomarkers."""
    return {"patient_id": id, "narrative": get_narrative(id)}
