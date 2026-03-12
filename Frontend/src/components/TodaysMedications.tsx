import { format } from 'date-fns';
import { CheckCircle2, Clock, AlertCircle, Pill } from 'lucide-react';
import { useMedicationStore } from '../store';

const statusConfig = {
  taken: { icon: CheckCircle2, color: '#10b981', label: 'Taken', bg: 'rgba(16, 185, 129, 0.08)' },
  pending: { icon: Clock, color: '#f59e0b', label: 'Pending', bg: 'rgba(245, 158, 11, 0.08)' },
  missed: { icon: AlertCircle, color: '#ef4444', label: 'Missed', bg: 'rgba(239, 68, 68, 0.08)' },
};

export default function TodaysMedications() {
  const { todaysMedications, markAsTaken } = useMedicationStore();
  const takenCount = todaysMedications.filter((m) => m.status === 'taken').length;

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 12,
            background: 'var(--accent-muted)',
            border: '1px solid var(--accent-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Pill size={22} color="var(--accent-primary)" strokeWidth={2} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Today's Medications</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{format(new Date(), 'EEEE, MMMM d, yyyy')}</div>
        </div>
        <span
          style={{
            background: 'var(--accent-muted)',
            color: 'var(--accent-primary)',
            fontSize: 12,
            fontWeight: 700,
            padding: '6px 14px',
            borderRadius: 9999,
            border: '1px solid var(--accent-border)',
          }}
        >
          {takenCount}/{todaysMedications.length}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {todaysMedications.map((med, i) => {
          const cfg = statusConfig[med.status];
          const Icon = cfg.icon;
          return (
            <div
              key={med.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '14px 16px',
                borderRadius: 12,
                background: cfg.bg,
                border: `1px solid ${cfg.color}25`,
                animation: `fadeInUp ${0.15 + i * 0.05}s cubic-bezier(0.16, 1, 0.3, 1) forwards`,
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: `${cfg.color}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <Icon size={20} color={cfg.color} strokeWidth={2} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{med.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  {med.scheduledTime} · {med.dose}
                </div>
              </div>
              <span
                style={{
                  background: `${cfg.color}15`,
                  color: cfg.color,
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '4px 12px',
                  borderRadius: 9999,
                  border: `1px solid ${cfg.color}30`,
                }}
              >
                {cfg.label}
              </span>
              {med.status === 'pending' && (
                <button onClick={() => markAsTaken(med.id)} className="btn btn-primary" style={{ padding: '8px 16px', fontSize: 12 }}>
                  Mark Taken
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
