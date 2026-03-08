"""
drug_interaction_service.py – Drug interaction checker for Dirghayu (GAP 3).

Uses the drug_interactions SQLite table populated with 15 dangerous combinations
from CDSCO guidelines common in Indian NCD patients.

Severity levels:
  SEVERE   – triggers doctor WhatsApp alert immediately
  MODERATE – logged and returned to caller, no auto-alert
"""
import logging
from itertools import combinations

from app.utils.db_utils import execute, fetchall, rows_to_dicts
from app.utils.time_utils import utcnow_str

logger = logging.getLogger(__name__)

# ── 15 interactions from CDSCO guidelines ─────────────────────────────────
CDSCO_INTERACTIONS = [
    ("Metformin",          "Contrast dye",         "SEVERE",
     "Hold Metformin 48h before contrast imaging — risk of contrast-induced nephropathy and lactic acidosis."),
    ("Metformin",          "Alcohol",               "MODERATE",
     "Alcohol + Metformin increases lactic acidosis risk. Advise patient to avoid alcohol."),
    ("Amlodipine",         "Simvastatin",           "MODERATE",
     "Amlodipine increases Simvastatin plasma levels. Cap Simvastatin at 20mg/day to reduce myopathy risk."),
    ("Amlodipine",         "Grapefruit",            "MODERATE",
     "Grapefruit inhibits CYP3A4 increasing Amlodipine absorption and hypotension risk."),
    ("ACE Inhibitor",      "Potassium supplement",  "SEVERE",
     "ACE Inhibitor + Potassium supplement causes hyperkalemia. Monitor serum potassium closely."),
    ("ACE Inhibitor",      "NSAIDs",                "SEVERE",
     "ACE Inhibitor + NSAIDs (Ibuprofen/Diclofenac) — risk of acute kidney injury. Avoid combination."),
    ("ARB",                "ACE Inhibitor",         "SEVERE",
     "Dual RAAS blockade (ARB + ACE Inhibitor) is contraindicated — severe hypotension and renal failure risk."),
    ("Glipizide",          "Fluconazole",           "SEVERE",
     "Fluconazole inhibits CYP2C9 causing severe hypoglycemia with Glipizide. Avoid or monitor closely."),
    ("Glipizide",          "Alcohol",               "MODERATE",
     "Alcohol potentiates Glipizide hypoglycemia and causes flushing. Patient education required."),
    ("Insulin",            "Beta blockers",         "MODERATE",
     "Beta blockers mask tachycardia of hypoglycemia. Patient may not recognize low glucose. Monitor closely."),
    ("Insulin",            "Alcohol",               "SEVERE",
     "Alcohol causes unpredictable hypoglycemia with Insulin — potentially life-threatening. Avoid."),
    ("Atorvastatin",       "Clarithromycin",        "SEVERE",
     "Clarithromycin inhibits CYP3A4 causing major Atorvastatin accumulation — rhabdomyolysis risk."),
    ("Aspirin",            "Warfarin",              "SEVERE",
     "Aspirin + Warfarin substantially increases bleeding risk. Only combine under strict haematology supervision."),
    ("Thiazide diuretic",  "Lithium",               "SEVERE",
     "Thiazides reduce lithium renal clearance leading to lithium toxicity. Monitor lithium levels."),
    ("Spironolactone",     "ACE Inhibitor",         "MODERATE",
     "Spironolactone + ACE Inhibitor simultaneously elevate potassium — hyperkalemia risk. Monitor."),
]


def seed_drug_interactions() -> None:
    """
    Populate the drug_interactions table with CDSCO interactions.
    Idempotent — checks COUNT before inserting.
    """
    existing = fetchall("SELECT COUNT(*) AS n FROM drug_interactions")[0]["n"]
    if existing >= len(CDSCO_INTERACTIONS):
        logger.info("drug_interactions table already seeded (%d rows)", existing)
        return

    for drug_a, drug_b, severity, note in CDSCO_INTERACTIONS:
        execute(
            """INSERT INTO drug_interactions (drug_a, drug_b, severity, clinical_note)
               VALUES (?, ?, ?, ?)""",
            (drug_a, drug_b, severity, note),
        )
    logger.info("Seeded %d drug interactions into DB", len(CDSCO_INTERACTIONS))


def check_interactions(medication_names: list[str]) -> list[dict]:
    """
    Check every combination of medications against the drug_interactions table.
    Also checks each med against known food/substance flag names (Alcohol, Grapefruit, etc.).

    Returns list of dicts: {drug_a, drug_b, severity, clinical_note}
    """
    if not medication_names:
        return []

    rows = fetchall("SELECT * FROM drug_interactions")
    interactions_db = rows_to_dicts(rows)

    # Normalise comparison: lowercase strip
    def norm(s: str) -> str:
        return s.strip().lower()

    med_norms = {norm(m): m for m in medication_names}
    found: list[dict] = []
    seen: set[tuple] = set()

    for interaction in interactions_db:
        a = norm(interaction["drug_a"])
        b = norm(interaction["drug_b"])

        # Check if either substring matches — allows "ACE Inhibitor" to match "Lisinopril (ACE Inhibitor)"
        a_match = any(a in norm(m) or norm(m) in a for m in medication_names)
        b_match = any(b in norm(m) or norm(m) in b for m in medication_names)

        if a_match and b_match:
            key = (interaction["drug_a"], interaction["drug_b"])
            if key not in seen:
                seen.add(key)
                found.append({
                    "drug_a":        interaction["drug_a"],
                    "drug_b":        interaction["drug_b"],
                    "severity":      interaction["severity"],
                    "clinical_note": interaction["clinical_note"],
                })

    return found


def trigger_severe_alerts(patient_id: int, interactions: list[dict]) -> None:
    """
    For any SEVERE interaction found, send a doctor alert via the existing alert service.
    """
    from app.services.alert_service import send_whatsapp, _log_alert
    from app.utils.constants import AlertType
    from app.utils.db_utils import fetchone

    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if not patient or not patient["doctor_phone"]:
        return

    severe = [i for i in interactions if i["severity"] == "SEVERE"]
    if not severe:
        return

    lines = "\n".join(
        f"  ⚠️ {i['drug_a']} + {i['drug_b']}: {i['clinical_note']}"
        for i in severe
    )
    msg = (
        f"🚨 DRUG INTERACTION ALERT for {patient['name']}:\n"
        f"SEVERE interactions detected in current medication list:\n"
        f"{lines}\n"
        f"Immediate clinical review recommended."
    )
    sent = send_whatsapp(patient["doctor_phone"], msg)
    if sent:
        _log_alert(patient_id, AlertType.RISK_ESCALATION, msg, patient["doctor_phone"])
    logger.warning(
        "SEVERE drug interaction alert sent for patient %d: %d severe interactions",
        patient_id, len(severe),
    )
