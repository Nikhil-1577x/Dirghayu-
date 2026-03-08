"""
patient_routes.py – Patient CRUD + dashboard endpoint.
"""
from fastapi import APIRouter, HTTPException
from app.models.patient import PatientCreate, PatientOut
from app.utils.db_utils import execute, fetchone, fetchall, rows_to_dicts, row_to_dict

router = APIRouter(prefix="/patient", tags=["Patients"])


@router.post("/", response_model=PatientOut, status_code=201)
def create_patient(data: PatientCreate):
    row_id = execute(
        "INSERT INTO patients (name, age, gender, phone, family_phone, doctor_phone) VALUES (?,?,?,?,?,?)",
        (data.name, data.age, data.gender, data.phone, data.family_phone, data.doctor_phone),
    )
    row = fetchone("SELECT * FROM patients WHERE id = ?", (row_id,))
    return dict(row)


@router.get("/", response_model=list[PatientOut])
def list_patients():
    return rows_to_dicts(fetchall("SELECT * FROM patients ORDER BY id"))


@router.get("/{id}", response_model=PatientOut)
def get_patient(id: int):
    row = fetchone("SELECT * FROM patients WHERE id = ?", (id,))
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dict(row)


@router.get("/{id}/dashboard")
def patient_dashboard(id: int):
    """
    Returns: patient info, latest biomarkers, risk score, adherence %, recent alerts.
    """
    from app.services.adherence_engine import get_weekly_adherence, get_daily_adherence
    from app.services.biomarker_service import get_latest_biomarkers
    from app.services.risk_service import get_latest_risk
    from app.services.alert_service import get_alert_history

    patient = fetchone("SELECT * FROM patients WHERE id = ?", (id,))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "patient": dict(patient),
        "latest_biomarkers": get_latest_biomarkers(id),
        "risk_score": get_latest_risk(id),
        "weekly_adherence": get_weekly_adherence(id),
        "daily_adherence": get_daily_adherence(id),
        "recent_alerts": get_alert_history(id)[:10],
    }


@router.post("/{id}/medication", status_code=201)
def add_medication(id: int, data: dict):
    from app.models.medication import MedicationCreate
    med = MedicationCreate(patient_id=id, **data)
    row_id = execute(
        "INSERT INTO medications (patient_id, name, dose, schedule_time) VALUES (?,?,?,?)",
        (id, med.name, med.dose, med.schedule_time),
    )
    return {"id": row_id, "patient_id": id, "name": med.name, "dose": med.dose, "schedule_time": med.schedule_time}


@router.get("/{id}/medications")
def get_medications(id: int):
    return rows_to_dicts(fetchall("SELECT * FROM medications WHERE patient_id = ?", (id,)))


@router.post("/{id}/appointment", status_code=201)
def add_appointment(id: int, data: dict):
    from app.models.appointment import AppointmentCreate
    appt = AppointmentCreate(patient_id=id, **data)
    row_id = execute(
        "INSERT INTO appointments (patient_id, appointment_time, doctor_name, notes) VALUES (?,?,?,?)",
        (id, appt.appointment_time, appt.doctor_name, appt.notes),
    )
    return {"id": row_id, **appt.dict()}


@router.get("/{id}/appointments")
def get_appointments(id: int):
    return rows_to_dicts(fetchall("SELECT * FROM appointments WHERE patient_id = ? ORDER BY appointment_time", (id,)))
