/**
 * API endpoint functions - maps to backend routes.
 */
import { api } from './client';

// ─── Types (backend-compatible) ──────────────────────────────────────────────

export interface Patient {
  id: number;
  name: string;
  age: number;
  gender: string;
  phone: string;
  family_phone?: string;
  doctor_phone?: string;
  created_at: string;
}

export interface Medication {
  id: number;
  patient_id: number;
  name: string;
  dose: string;
  schedule_time: string;
}

export interface Appointment {
  id: number;
  patient_id: number;
  appointment_time: string;
  doctor_name: string;
  notes?: string;
}

export interface DashboardResponse {
  patient: Patient;
  latest_biomarkers: Record<string, { value: number; timestamp: string; slope?: number; trend?: string }>;
  risk_score: { score: number; risk_level: string } | null;
  weekly_adherence: { taken: number; late: number; missed: number; total: number; weekly_score: number };
  daily_adherence: { taken: number; late: number; missed: number; total: number; daily_score: number };
  recent_alerts: Array<{ id: number; alert_type: string; message: string; timestamp: string }>;
}

export interface AdherenceResponse {
  patient_id: number;
  daily_adherence: { taken: number; late: number; missed: number; total: number; daily_score: number };
  weekly_score: number;
  weekly_adherence: { taken: number; late: number; missed: number; total: number; weekly_score: number };
  missed_doses: Array<{ id: number; medication_id: number; timestamp: string; status: string }>;
}

export interface BiomarkerReading {
  id: number;
  patient_id: number;
  biomarker_type: string;
  value: number;
  timestamp: string;
  slope?: number;
  trend?: string;
}

export interface ReportInfo {
  id: number;
  patient_id: number;
  file_path: string;
  created_at: string;
}

// ─── Patient ─────────────────────────────────────────────────────────────────

export async function listPatients(): Promise<Patient[]> {
  return api.get<Patient[]>('/patient/');
}

export async function getPatient(id: number): Promise<Patient> {
  return api.get<Patient>(`/patient/${id}`);
}

export async function getDashboard(patientId: number): Promise<DashboardResponse> {
  return api.get<DashboardResponse>(`/patient/${patientId}/dashboard`);
}

export async function createPatient(data: {
  name: string;
  age: number;
  gender: string;
  phone: string;
  family_phone?: string;
  doctor_phone?: string;
}): Promise<Patient> {
  return api.post<Patient>('/patient/', data);
}

// ─── Medications ─────────────────────────────────────────────────────────────

export async function getMedications(patientId: number): Promise<Medication[]> {
  return api.get<Medication[]>(`/patient/${patientId}/medications`);
}

export async function addMedication(
  patientId: number,
  data: { name: string; dose: string; schedule_time: string }
): Promise<{ id: number; name: string; dose: string; schedule_time: string }> {
  return api.post(`/patient/${patientId}/medication`, data);
}

// ─── Alerts ──────────────────────────────────────────────────────────────────

export async function getAlerts(patientId: number): Promise<{
  patient_id: number;
  alerts: Array<{ id: number; alert_type: string; message: string; sent_to: string; timestamp: string }>;
}> {
  return api.get(`/patient/${patientId}/alerts`);
}

// ─── Adherence ───────────────────────────────────────────────────────────────

export async function getAdherence(patientId: number): Promise<AdherenceResponse> {
  return api.get(`/patient/${patientId}/adherence`);
}

// ─── Biomarkers ──────────────────────────────────────────────────────────────

export async function getBiomarkers(patientId: number): Promise<BiomarkerReading[]> {
  return api.get(`/patient/${patientId}/biomarkers`);
}

export async function uploadBiomarkerOcr(
  patientId: number,
  file: File
): Promise<{ added: number; records: Array<Record<string, unknown>> }> {
  // Backend expects multipart form with file param - use raw fetch for FormData
  const base = import.meta.env.VITE_API_URL ?? '';
  const url = `${base}/patient/${patientId}/biomarkers/ocr`;
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(url, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function getBiomarkerNarrative(patientId: number): Promise<{ narrative: string }> {
  return api.get(`/patient/${patientId}/biomarkers/narrative`);
}

// ─── Appointments ────────────────────────────────────────────────────────────

export async function getAppointments(patientId: number): Promise<Appointment[]> {
  return api.get<Appointment[]>(`/patient/${patientId}/appointments`);
}

export async function addAppointment(
  patientId: number,
  data: { appointment_time: string; doctor_name: string; notes?: string }
): Promise<{ id: number } & typeof data> {
  return api.post(`/patient/${patientId}/appointment`, data);
}

// ─── Reports ─────────────────────────────────────────────────────────────────

export async function generateReport(patientId: number): Promise<{
  patient_id: number;
  file_path: string;
  message: string;
}> {
  return api.post(`/patient/${patientId}/report`);
}

export async function listReports(patientId: number): Promise<{
  patient_id: number;
  reports: ReportInfo[];
}> {
  return api.get(`/patient/${patientId}/reports`);
}

export function getReportDownloadUrl(patientId: number, reportId: number): string {
  const base = import.meta.env.VITE_API_URL ?? '';
  return `${base}/patient/${patientId}/report/download/${reportId}`;
}

// ─── Risk ────────────────────────────────────────────────────────────────────

export async function getRiskScore(patientId: number): Promise<{
  patient_id: number;
  score: number;
  risk_level: string;
  timestamp?: string;
}> {
  return api.get(`/patient/${patientId}/risk`);
}

// ─── Health ──────────────────────────────────────────────────────────────────

export async function healthCheck(): Promise<{ status: string; service: string }> {
  return api.get('/');
}
