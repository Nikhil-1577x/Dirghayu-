import { useState } from 'react';
import { Pill, Plus, Calendar, CheckSquare } from 'lucide-react';
import { useMedicationStore } from '../store';
import { useApiStore } from '../store';
import { addMedication as addMedicationApi } from '../api/endpoints';

export default function Medications() {
  const { allMedications, addMedication, setMedicationsFromApi } = useMedicationStore();
  const { patientId } = useApiStore();
  const [showAdd, setShowAdd] = useState(false);
  const [newMed, setNewMed] = useState({ name: '', dose: '', frequency: '', scheduledTime: '' });
  const [adding, setAdding] = useState(false);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMed.name || !newMed.dose || !newMed.scheduledTime) return;
    if (patientId) {
      setAdding(true);
      try {
        const res = await addMedicationApi(patientId, {
          name: newMed.name,
          dose: newMed.dose,
          schedule_time: newMed.scheduledTime,
        });
        const meds = [
          ...allMedications,
          { id: String(res.id), name: res.name, dose: res.dose, frequency: newMed.frequency || 'As prescribed', scheduledTime: newMed.scheduledTime, status: 'pending' as const },
        ];
        setMedicationsFromApi(meds);
        setShowAdd(false);
        setNewMed({ name: '', dose: '', frequency: '', scheduledTime: '' });
      } catch (err) {
        console.error('Failed to add medication:', err);
      } finally {
        setAdding(false);
      }
    } else {
      addMedication({ ...newMed, status: 'pending' });
      setShowAdd(false);
      setNewMed({ name: '', dose: '', frequency: '', scheduledTime: '' });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28, paddingBottom: 48 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 20 }}>
        <div className="page-header">
          <h1>Medication Schedule</h1>
          <p>Manage current prescriptions and daily schedule</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(!showAdd)}>
          <Plus size={18} strokeWidth={2} />
          {showAdd ? 'Cancel' : 'Add Medication'}
        </button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <div className="card animate-fadeInUp" style={{ padding: 28, border: '1px solid var(--accent-border)', background: 'linear-gradient(135deg, rgba(5, 150, 105, 0.06), transparent)' }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <Pill size={20} color="var(--accent-primary)" />
            New Prescription
          </h3>
          <form onSubmit={handleAdd} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>Medicine Name</label>
              <input
                type="text"
                value={newMed.name}
                onChange={(e) => setNewMed({ ...newMed, name: e.target.value })}
                placeholder="e.g. Aspirin"
                className="input"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>Dose</label>
              <input
                type="text"
                value={newMed.dose}
                onChange={(e) => setNewMed({ ...newMed, dose: e.target.value })}
                placeholder="e.g. 75mg"
                className="input"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>Frequency</label>
              <select
                value={newMed.frequency}
                onChange={(e) => setNewMed({ ...newMed, frequency: e.target.value })}
                className="input"
              >
                <option value="">Select...</option>
                <option value="Once daily">Once daily</option>
                <option value="Twice daily">Twice daily</option>
                <option value="As needed">As needed</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>Scheduled Time</label>
              <input
                type="text"
                value={newMed.scheduledTime}
                onChange={(e) => setNewMed({ ...newMed, scheduledTime: e.target.value })}
                placeholder="e.g. 8:00 AM"
                className="input"
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', gridColumn: '1 / -1' }}>
              <button type="submit" className="btn btn-primary" disabled={adding}>
                {adding ? 'Saving...' : 'Save Medication'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
              <th style={{ padding: '18px 24px', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Medicine</th>
              <th style={{ padding: '18px 24px', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Dose</th>
              <th style={{ padding: '18px 24px', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Frequency</th>
              <th style={{ padding: '18px 24px', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Schedule</th>
            </tr>
          </thead>
          <tbody>
            {allMedications.map((med, i) => (
              <tr key={med.id} style={{ borderBottom: i === allMedications.length - 1 ? 'none' : '1px solid var(--border)' }}>
                <td style={{ padding: '18px 24px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div style={{ width: 40, height: 40, borderRadius: 12, background: 'var(--accent-muted)', border: '1px solid var(--accent-border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Pill size={18} color="var(--accent-primary)" strokeWidth={2} />
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>{med.name}</div>
                  </div>
                </td>
                <td style={{ padding: '18px 24px', color: 'var(--text-secondary)', fontSize: 14 }}>{med.dose}</td>
                <td style={{ padding: '18px 24px', color: 'var(--text-secondary)', fontSize: 14 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <CheckSquare size={16} color="var(--text-muted)" />
                    {med.frequency}
                  </span>
                </td>
                <td style={{ padding: '18px 24px', color: 'var(--text-secondary)', fontSize: 14 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Calendar size={16} color="var(--text-muted)" />
                    {med.scheduledTime}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
