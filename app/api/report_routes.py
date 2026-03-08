"""
report_routes.py – Report generation and listing endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.services.report_service import generate_report, get_reports

router = APIRouter(prefix="/patient", tags=["Reports"])


@router.post("/{id}/report", status_code=201)
def create_report(id: int):
    """Generate a PDF report for a patient and return its path."""
    try:
        path = generate_report(id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")
    return {"patient_id": id, "file_path": path, "message": "Report generated successfully"}


@router.get("/{id}/reports")
def list_reports(id: int):
    """List all generated reports for a patient."""
    return {"patient_id": id, "reports": get_reports(id)}


@router.get("/{id}/report/download/{report_id}")
def download_report(id: int, report_id: int):
    """Stream-download a generated PDF."""
    from app.utils.db_utils import fetchone
    row = fetchone("SELECT * FROM reports WHERE id = ? AND patient_id = ?", (report_id, id))
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    path = row["file_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report file missing on disk")
    return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))
