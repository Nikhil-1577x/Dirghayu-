// Zustand stores for Dirghayu

import { create } from 'zustand';

// ─── Types ───────────────────────────────────────────────────────────────────

export type MedicineStatus = 'taken' | 'pending' | 'missed';

export interface Medication {
    id: string;
    name: string;
    dose: string;
    frequency: string;
    scheduledTime: string;
    status: MedicineStatus;
}

export interface Biomarker {
    date: string;
    systolic?: number;
    diastolic?: number;
    heartRate?: number;
    glucose?: number;
    cholesterol?: number;
}

export interface Alert {
    id: string;
    severity: 'info' | 'warning' | 'critical';
    category: 'medication' | 'biomarker' | 'device';
    title: string;
    description: string;
    timestamp: string;
    read: boolean;
}

export interface ActivityEvent {
    id: string;
    type: 'dose_taken' | 'reminder_sent' | 'biomarker_uploaded' | 'device_connected' | 'alert_generated';
    description: string;
    timestamp: string;
}

export interface Appointment {
    id: string;
    doctorName: string;
    specialization: string;
    date: string;
    location: string;
}

export interface AdherenceDay {
    date: string;
    status: 'taken' | 'late' | 'missed' | 'no-data';
}

// ─── Patient Store ────────────────────────────────────────────────────────────

interface PatientState {
    patientName: string;
    caretakerName: string;
    riskScore: number;
    riskCategory: 'low' | 'moderate' | 'high';
    overallMedicineStatus: MedicineStatus;
    lastDoseTime: string | null;
    nextDoseTime: string | null;
    nextMedicineName: string | null;
    setPatient: (data: { name: string; caretakerName?: string }) => void;
    setRiskScore: (score: number) => void;
    setMedicineStatus: (status: MedicineStatus, lastDose?: string, nextDose?: string, nextMed?: string) => void;
}

export const usePatientStore = create<PatientState>((set) => ({
    patientName: 'Ramesh Sharma',
    caretakerName: 'Priya',
    riskScore: 27,
    riskCategory: 'high',
    overallMedicineStatus: 'taken',
    lastDoseTime: '8:32 AM',
    nextDoseTime: '1:00 PM',
    nextMedicineName: 'Aspirin',
    setPatient: (data) =>
        set({
            patientName: data.name,
            caretakerName: data.caretakerName ?? 'Caregiver',
        }),
    setRiskScore: (score) => {
        const category = score < 10 ? 'low' : score < 20 ? 'moderate' : 'high';
        set({ riskScore: score, riskCategory: category as 'low' | 'moderate' | 'high' });
    },
    setMedicineStatus: (status, lastDose, nextDose, nextMed) =>
        set({ overallMedicineStatus: status, lastDoseTime: lastDose || null, nextDoseTime: nextDose || null, nextMedicineName: nextMed || null }),
}));

// ─── Medication Store ─────────────────────────────────────────────────────────

interface MedicationState {
    todaysMedications: Medication[];
    allMedications: Medication[];
    adherenceData: AdherenceDay[];
    markAsTaken: (id: string) => void;
    addMedication: (med: Omit<Medication, 'id'>) => void;
    setMedicationsFromApi: (meds: Medication[]) => void;
    setAdherenceFromApi: (adherence: { daily_adherence?: unknown; weekly_adherence?: unknown }) => void;
}

export const useMedicationStore = create<MedicationState>((set) => ({
    todaysMedications: [
        { id: '1', name: 'Metformin 500mg', dose: '500mg', frequency: 'Twice daily', scheduledTime: '8:00 AM', status: 'taken' },
        { id: '2', name: 'Aspirin 75mg', dose: '75mg', frequency: 'Once daily', scheduledTime: '1:00 PM', status: 'pending' },
        { id: '3', name: 'Atorvastatin 10mg', dose: '10mg', frequency: 'Once daily', scheduledTime: '8:00 PM', status: 'pending' },
        { id: '4', name: 'Amlodipine 5mg', dose: '5mg', frequency: 'Once daily', scheduledTime: '8:00 AM', status: 'taken' },
    ],
    allMedications: [
        { id: '1', name: 'Metformin 500mg', dose: '500mg', frequency: 'Twice daily', scheduledTime: '8:00 AM, 8:00 PM', status: 'taken' },
        { id: '2', name: 'Aspirin 75mg', dose: '75mg', frequency: 'Once daily', scheduledTime: '1:00 PM', status: 'pending' },
        { id: '3', name: 'Atorvastatin 10mg', dose: '10mg', frequency: 'Once daily', scheduledTime: '8:00 PM', status: 'pending' },
        { id: '4', name: 'Amlodipine 5mg', dose: '5mg', frequency: 'Once daily', scheduledTime: '8:00 AM', status: 'taken' },
        { id: '5', name: 'Metoprolol 25mg', dose: '25mg', frequency: 'Twice daily', scheduledTime: '9:00 AM, 9:00 PM', status: 'taken' },
    ],
    adherenceData: generateAdheranceData(),
    markAsTaken: (id) =>
        set((s) => ({
            todaysMedications: s.todaysMedications.map((m) =>
                m.id === id ? { ...m, status: 'taken' } : m
            ),
        })),
    addMedication: (med) =>
        set((s) => ({
            allMedications: [
                ...s.allMedications,
                { ...med, id: String(Date.now()) },
            ],
        })),
    setMedicationsFromApi: (meds) =>
        set({
            allMedications: meds,
            todaysMedications: meds.slice(0, 5),
        }),
    setAdherenceFromApi: () => {
        /* Adherence heatmap uses mock data - backend doesn't have per-day history yet */
    },
}));

function generateAdheranceData(): AdherenceDay[] {
    const data: AdherenceDay[] = [];
    const today = new Date(2026, 2, 9); // March 9, 2026
    const statuses: AdherenceDay['status'][] = ['taken', 'taken', 'taken', 'late', 'taken', 'missed', 'no-data'];
    for (let i = 364; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(today.getDate() - i);
        const rand = statuses[Math.floor(Math.random() * statuses.length)];
        data.push({
            date: d.toISOString().split('T')[0],
            status: i === 0 ? 'taken' : rand,
        });
    }
    return data;
}

// ─── Alert Store ──────────────────────────────────────────────────────────────

interface AlertState {
    alerts: Alert[];
    activityFeed: ActivityEvent[];
    unreadCount: number;
    addAlert: (alert: Omit<Alert, 'id' | 'read'>) => void;
    addActivity: (event: Omit<ActivityEvent, 'id'>) => void;
    markAllRead: () => void;
    setAlertsFromApi: (alerts: Alert[]) => void;
}

const MOCK_ALERTS: Alert[] = [
    {
        id: '1',
        severity: 'warning',
        category: 'medication',
        title: 'Afternoon Dose Pending',
        description: 'Aspirin 75mg scheduled at 1:00 PM has not been confirmed.',
        timestamp: new Date().toISOString(),
        read: false,
    },
    {
        id: '2',
        severity: 'info',
        category: 'biomarker',
        title: 'Blood Pressure Slightly Elevated',
        description: 'Latest reading: 138/88 mmHg. This is within acceptable bounds but worth monitoring.',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        read: false,
    },
    {
        id: '3',
        severity: 'info',
        category: 'device',
        title: 'Device Reconnected',
        description: 'Smart pill dispenser reconnected successfully at 9:15 AM.',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        read: true,
    },
];

const MOCK_FEED: ActivityEvent[] = [
    { id: '1', type: 'dose_taken', description: 'Metformin 500mg dose confirmed', timestamp: new Date(Date.now() - 600000).toISOString() },
    { id: '2', type: 'biomarker_uploaded', description: 'Blood pressure reading uploaded: 138/88', timestamp: new Date(Date.now() - 3600000).toISOString() },
    { id: '3', type: 'reminder_sent', description: 'WhatsApp reminder sent for afternoon dose', timestamp: new Date(Date.now() - 7200000).toISOString() },
    { id: '4', type: 'device_connected', description: 'Smart pill dispenser device connected', timestamp: new Date(Date.now() - 10800000).toISOString() },
    { id: '5', type: 'dose_taken', description: 'Amlodipine 5mg morning dose confirmed', timestamp: new Date(Date.now() - 14400000).toISOString() },
];

export const useAlertStore = create<AlertState>((set) => ({
    alerts: MOCK_ALERTS,
    activityFeed: MOCK_FEED,
    unreadCount: MOCK_ALERTS.filter((a) => !a.read).length,
    addAlert: (alert) =>
        set((s) => {
            const newAlert = { ...alert, id: String(Date.now()), read: false };
            return { alerts: [newAlert, ...s.alerts], unreadCount: s.unreadCount + 1 };
        }),
    addActivity: (event) =>
        set((s) => ({
            activityFeed: [{ ...event, id: String(Date.now()) }, ...s.activityFeed].slice(0, 50),
        })),
    markAllRead: () => set((s) => ({ alerts: s.alerts.map((a) => ({ ...a, read: true })), unreadCount: 0 })),
    setAlertsFromApi: (alerts) =>
        set({
            alerts,
            unreadCount: alerts.filter((a) => !a.read).length,
        }),
}));

// ─── WebSocket Store ──────────────────────────────────────────────────────────

type WSStatus = 'connected' | 'reconnecting' | 'disconnected';

interface WSState {
    status: WSStatus;
    setStatus: (s: WSStatus) => void;
}

export const useWSStore = create<WSState>((set) => ({
    status: 'connected',
    setStatus: (status) => set({ status }),
}));

// ─── Mock Biomarker Data ──────────────────────────────────────────────────────

export function generateBiomarkerData(days: number): Biomarker[] {
    const data: Biomarker[] = [];
    const today = new Date(2026, 2, 9);
    for (let i = days - 1; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(today.getDate() - i);
        data.push({
            date: d.toISOString().split('T')[0],
            systolic: 125 + Math.round((Math.random() - 0.5) * 30),
            diastolic: 82 + Math.round((Math.random() - 0.5) * 14),
            heartRate: 72 + Math.round((Math.random() - 0.5) * 18),
            glucose: 110 + Math.round((Math.random() - 0.5) * 40),
            cholesterol: 205 + Math.round((Math.random() - 0.5) * 30),
        });
    }
    return data;
}

// Default mock appointments when API has none
export const MOCK_APPOINTMENTS: Appointment[] = [
    {
        id: '1',
        doctorName: 'Dr. Ananya Sharma',
        specialization: 'Cardiology',
        date: '2026-03-14',
        location: 'Apollo Hospital, Delhi',
    },
    {
        id: '2',
        doctorName: 'Dr. Rajesh Patel',
        specialization: 'Endocrinology',
        date: '2026-03-28',
        location: 'Fortis Healthcare, Delhi',
    },
];

// ─── API Store (patient selection, loading, appointments from backend) ─────────

interface ApiState {
    patientId: number | null;
    patients: Array<{ id: number; name: string }>;
    appointments: Appointment[];
    biomarkers: Biomarker[];
    loading: boolean;
    error: string | null;
    setPatientId: (id: number | null) => void;
    setPatients: (p: Array<{ id: number; name: string }>) => void;
    setAppointments: (a: Appointment[]) => void;
    setBiomarkers: (b: Biomarker[]) => void;
    setLoading: (v: boolean) => void;
    setError: (e: string | null) => void;
}

export const useApiStore = create<ApiState>((set) => ({
    patientId: null,
    patients: [],
    appointments: MOCK_APPOINTMENTS,
    biomarkers: [],
    loading: false,
    error: null,
    setPatientId: (id) => set({ patientId: id }),
    setPatients: (p) => set({ patients: p }),
    setAppointments: (a) => set({ appointments: a.length ? a : MOCK_APPOINTMENTS }),
    setBiomarkers: (b) => set({ biomarkers: b }),
    setLoading: (v) => set({ loading: v }),
    setError: (e) => set({ error: e }),
}));
