import { Calendar as CalendarIcon, MapPin, Clock, FileText, UserPlus, Phone, Video } from 'lucide-react';
import { useApiStore } from '../store';

function daysUntil(dateStr: string): number {
  const today = new Date(2026, 2, 9);
  const target = new Date(dateStr + 'T00:00:00');
  return Math.ceil((target.getTime() - today.getTime()) / 86400000);
}

export default function Appointments() {
  const { appointments } = useApiStore();
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28, paddingBottom: 48 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 14,
              background: 'var(--accent-muted)',
              border: '1px solid var(--accent-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CalendarIcon size={24} color="var(--accent-primary)" strokeWidth={2} />
          </div>
          <div className="page-header">
            <h1>Appointments</h1>
            <p>Schedule and manage doctor visits</p>
          </div>
        </div>
        <button className="btn btn-primary">
          <UserPlus size={18} strokeWidth={2} />
          New Appointment
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 28 }}>
        {/* Upcoming List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Scheduled Visits</h3>

          {appointments.map((apt, i) => {
            const days = daysUntil(apt.date);
            const isNext = i === 0;
            const dateFormatted = new Date(apt.date + 'T00:00:00').toLocaleDateString('en-IN', {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            });

            return (
              <div
                key={apt.id}
                className="card"
                style={{
                  padding: 26,
                  border: isNext ? '1px solid var(--accent-border)' : '1px solid var(--border)',
                  background: isNext ? 'linear-gradient(135deg, rgba(5, 150, 105, 0.06), rgba(5, 150, 105, 0.02))' : 'var(--bg-card)',
                  boxShadow: isNext ? '0 2px 12px rgba(5, 150, 105, 0.12)' : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 22, gap: 20 }}>
                  <div style={{ display: 'flex', gap: 18 }}>
                    <div
                      style={{
                        width: 52,
                        height: 52,
                        borderRadius: 14,
                        background: isNext ? 'var(--accent-muted)' : 'var(--bg-secondary)',
                        border: isNext ? '1px solid var(--accent-border)' : '1px solid var(--border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      <CalendarIcon size={26} color={isNext ? 'var(--accent-primary)' : 'var(--text-muted)'} strokeWidth={2} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: 19, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4, letterSpacing: '-0.02em' }}>{apt.doctorName}</h4>
                      <div style={{ fontSize: 14, color: 'var(--accent-primary)', fontWeight: 600, marginBottom: 12 }}>{apt.specialization}</div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 14, color: 'var(--text-secondary)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <Clock size={16} color="var(--text-muted)" />
                          {dateFormatted} at 10:30 AM
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <MapPin size={16} color="var(--text-muted)" />
                          {apt.location}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div
                    style={{
                      background: isNext ? 'var(--accent-muted)' : 'var(--bg-secondary)',
                      border: isNext ? '1px solid var(--accent-border)' : '1px solid var(--border)',
                      borderRadius: 14,
                      padding: '12px 18px',
                      textAlign: 'center',
                      minWidth: 72,
                      flexShrink: 0,
                    }}
                  >
                    <div style={{ fontSize: 26, fontWeight: 800, color: isNext ? 'var(--accent-primary)' : 'var(--text-primary)', lineHeight: 1.1 }}>{days}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>days</div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 12, paddingTop: 18, borderTop: '1px solid var(--border)' }}>
                  <button className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
                    <FileText size={16} strokeWidth={2} />
                    Generate Report
                  </button>
                  <button className="btn btn-ghost" style={{ flex: 1, justifyContent: 'center' }}>
                    <Video size={16} strokeWidth={2} />
                    Join Virtual
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Calendar Side Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>March 2026</h3>
          <div
            className="card"
            style={{
              padding: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 320,
              color: 'var(--text-muted)',
              border: '1px dashed var(--border)',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  margin: '0 auto 20px',
                  borderRadius: 16,
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <CalendarIcon size={32} color="var(--text-muted)" style={{ opacity: 0.5 }} strokeWidth={1.5} />
              </div>
              <p style={{ fontSize: 14, maxWidth: 240, lineHeight: 1.6 }}>
                Interactive calendar view. Select dates to view or schedule appointments.
              </p>
            </div>
          </div>

          <div className="card" style={{ padding: 24 }}>
            <h4 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>Quick Contacts</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {appointments.map((apt) => (
                <div
                  key={apt.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '12px 0',
                    borderBottom: '1px solid var(--border)',
                  }}
                >
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{apt.doctorName}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{apt.specialization}</div>
                  </div>
                  <button
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 12,
                      background: 'var(--accent-muted)',
                      border: '1px solid var(--accent-border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      color: 'var(--accent-primary)',
                    }}
                  >
                    <Phone size={18} strokeWidth={2} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
