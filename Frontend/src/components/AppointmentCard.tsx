import { Calendar, MapPin, Clock, FileText } from 'lucide-react';
import { useApiStore } from '../store';

function daysUntil(dateStr: string): number {
  const today = new Date();
  const target = new Date(dateStr + 'T00:00:00');
  return Math.ceil((target.getTime() - today.getTime()) / 86400000);
}

export default function AppointmentCard() {
  const { appointments } = useApiStore();
  const next = appointments[0];
  if (!next) return null;
  const days = daysUntil(next.date);
  const dateFormatted = new Date(next.date + 'T00:00:00').toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

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
          <Calendar size={22} color="var(--accent-primary)" strokeWidth={2} />
        </div>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Next Appointment</div>
      </div>

      <div
        style={{
          background: 'linear-gradient(135deg, rgba(5, 150, 105, 0.06) 0%, rgba(5, 150, 105, 0.02) 100%)',
          border: '1px solid var(--accent-border)',
          borderRadius: 14,
          padding: '20px',
          marginBottom: 18,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6, letterSpacing: '-0.02em' }}>
              {next.doctorName}
            </div>
            <div style={{ fontSize: 13, color: 'var(--accent-primary)', fontWeight: 600, marginBottom: 12 }}>
              {next.specialization}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)', marginBottom: 6 }}>
              <Clock size={14} />
              {dateFormatted}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)' }}>
              <MapPin size={14} />
              {next.location}
            </div>
          </div>
          <div
            style={{
              background: 'var(--accent-muted)',
              border: '1px solid var(--accent-border)',
              borderRadius: 14,
              padding: '12px 18px',
              textAlign: 'center',
              minWidth: 72,
              flexShrink: 0,
            }}
          >
            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent-primary)', lineHeight: 1.1 }}>{days}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>days</div>
          </div>
        </div>
      </div>

      {appointments[1] && (
        <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 18 }}>
          <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>Also upcoming</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              {appointments[1].doctorName} · {appointments[1].specialization}
            </span>
            <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>in {daysUntil(appointments[1].date)} days</span>
          </div>
        </div>
      )}

      <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', gap: 10 }}>
        <FileText size={16} strokeWidth={2} />
        Generate PDF Summary Report
      </button>
    </div>
  );
}
