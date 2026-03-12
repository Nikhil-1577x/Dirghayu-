/**
 * React hook for API data fetching and store hydration.
 */
import { useCallback, useEffect } from 'react';
import {
  listPatients,
  getDashboard,
  getMedications,
  getAlerts,
  getAdherence,
  getAppointments,
  getBiomarkers,
  type Patient,
  type DashboardResponse,
} from './endpoints';
import { usePatientStore } from '../store';
import { useMedicationStore } from '../store';
import { useAlertStore } from '../store';
import { useApiStore } from '../store';

// Map backend alert_type to frontend severity/category
function mapAlert(alert: { id: number; alert_type: string; message: string; timestamp: string }) {
  const type = alert.alert_type.toUpperCase();
  let severity: 'info' | 'warning' | 'critical' = 'info';
  let category: 'medication' | 'biomarker' | 'device' = 'medication';

  if (type.includes('MISSED') || type.includes('DRUG_HOLIDAY') || type.includes('RISK')) severity = 'critical';
  else if (type.includes('DOSE_REMINDER')) severity = 'warning';
  if (type.includes('DEVICE') || type.includes('CONNECT')) category = 'device';
  if (type.includes('BLOOD') || type.includes('BIOMARKER') || type.includes('GLUCOSE')) category = 'biomarker';

  return {
    id: String(alert.id),
    severity,
    category,
    title: alert.alert_type.replace(/_/g, ' '),
    description: alert.message,
    timestamp: alert.timestamp,
    read: false,
  };
}

// Map backend medication to frontend format
function mapMedication(m: { id: number; name: string; dose: string; schedule_time: string }) {
  const scheduleTime = m.schedule_time.includes(':')
    ? new Date(`2000-01-01T${m.schedule_time}`).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
    : m.schedule_time;
  return {
    id: String(m.id),
    name: m.name,
    dose: m.dose,
    frequency: 'As prescribed',
    scheduledTime: scheduleTime,
    status: 'pending' as const,
  };
}

function hydrateStoresFromDashboard(dash: DashboardResponse) {
  const { setPatient, setRiskScore } = usePatientStore.getState();
  const { setAlertsFromApi } = useAlertStore.getState();

  setPatient({
    name: dash.patient.name,
    caretakerName: 'Caregiver',
  });

  const risk = dash.risk_score;
    if (risk) {
      setRiskScore(Math.round(risk.score));
    }

  if (dash.recent_alerts?.length) {
    setAlertsFromApi(dash.recent_alerts.map(mapAlert));
  }
}

export function useApi() {
  const { patientId, setPatientId, setPatients, setLoading, setError } = useApiStore();
  const hydrateDashboard = useCallback(async (pid: number) => {
    setLoading(true);
    setError(null);
    try {
      const dash = await getDashboard(pid);
      hydrateStoresFromDashboard(dash);

      const [meds, alerts, adherence, appointments, biomarkers] = await Promise.all([
        getMedications(pid),
        getAlerts(pid),
        getAdherence(pid),
        getAppointments(pid),
        getBiomarkers(pid),
      ]);

      useMedicationStore.getState().setMedicationsFromApi(meds.map(mapMedication));
      useAlertStore.getState().setAlertsFromApi(
        (alerts.alerts ?? []).map((a: { id: number; alert_type: string; message: string; timestamp: string }) =>
          mapAlert({ ...a, id: a.id })
        )
      );
      useMedicationStore.getState().setAdherenceFromApi(adherence);
      const apts = (appointments as Array<{ id: number; doctor_name: string; appointment_time: string; notes?: string }>);
      useApiStore.getState().setAppointments(
        apts.map((a) => ({
          id: String(a.id),
          doctorName: a.doctor_name,
          specialization: 'General',
          date: a.appointment_time.split('T')[0],
          location: a.notes ?? '',
        }))
      );
      const typeMap: Record<string, string> = { systolic_bp: 'systolic', diastolic_bp: 'diastolic', fasting_glucose: 'glucose', blood_glucose: 'glucose' };
      const byDate: Record<string, Record<string, number>> = {};
      for (const b of biomarkers as Array<{ biomarker_type: string; value: number; timestamp: string }>) {
        const date = b.timestamp.split('T')[0];
        if (!byDate[date]) byDate[date] = {};
        const key = typeMap[b.biomarker_type] ?? b.biomarker_type.replace(/\s/g, '_').toLowerCase();
        byDate[date][key] = b.value;
      }
      const bioList = Object.entries(byDate).map(([date, rest]) => ({ date, ...rest })).sort((a, b) => a.date.localeCompare(b.date));
      useApiStore.getState().setBiomarkers(bioList as unknown as import('../store').Biomarker[]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPatients = useCallback(async () => {
    try {
      const patients = await listPatients();
      setPatients(patients as Patient[]);
      if (patients.length > 0 && !patientId) {
        setPatientId(patients[0].id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load patients');
    }
  }, [patientId, setPatientId, setPatients, setError]);

  useEffect(() => {
    loadPatients();
  }, []);

  useEffect(() => {
    if (patientId) {
      hydrateDashboard(patientId);
    }
  }, [patientId, hydrateDashboard]);

  return { patientId, hydrateDashboard, loadPatients };
}
