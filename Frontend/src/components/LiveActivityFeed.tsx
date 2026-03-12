import { useEffect } from 'react';
import { Zap, Bell, Heart, Wifi, CheckCircle2 } from 'lucide-react';
import { useAlertStore, useWSStore } from '../store';

const eventConfig = {
  dose_taken: { icon: CheckCircle2, color: '#10b981', bg: 'rgba(16, 185, 129, 0.08)' },
  reminder_sent: { icon: Bell, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.08)' },
  biomarker_uploaded: { icon: Heart, color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.08)' },
  device_connected: { icon: Wifi, color: '#10b981', bg: 'rgba(16, 185, 129, 0.08)' },
  alert_generated: { icon: Zap, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.08)' },
};

function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'Just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function LiveActivityFeed() {
  const { activityFeed, addActivity } = useAlertStore();
  const { status: wsStatus } = useWSStore();

  useEffect(() => {
    if (wsStatus !== 'connected') return;
    const events = [
      { type: 'biomarker_uploaded' as const, description: 'Heart rate reading uploaded: 74 bpm' },
      { type: 'reminder_sent' as const, description: 'WhatsApp reminder dispatched for afternoon dose' },
      { type: 'device_connected' as const, description: 'Smart monitoring device synced' },
    ];
    let idx = 0;
    const interval = setInterval(() => {
      addActivity({ ...events[idx % events.length], timestamp: new Date().toISOString() });
      idx++;
    }, 18000);
    return () => clearInterval(interval);
  }, [wsStatus, addActivity]);

  return (
    <div className="card" style={{ height: 'fit-content', maxHeight: 440, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18, flexShrink: 0 }}>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div
            style={{
              width: 10,
              height: 10,
              background: wsStatus === 'connected' ? '#10b981' : '#f59e0b',
              borderRadius: '50%',
              boxShadow: wsStatus === 'connected' ? '0 0 10px rgba(16, 185, 129, 0.5)' : 'none',
            }}
          />
          {wsStatus === 'connected' && (
            <div
              style={{
                position: 'absolute',
                width: 20,
                height: 20,
                background: 'rgba(16, 185, 129, 0.15)',
                borderRadius: '50%',
                animation: 'pulse-ring 2s ease-in-out infinite',
              }}
            />
          )}
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Live Activity</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Real-time event stream</div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, overflowY: 'auto', flex: 1 }}>
        {activityFeed.slice(0, 10).map((event, i) => {
          const cfg = eventConfig[event.type];
          const Icon = cfg.icon;

          return (
            <div
              key={event.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                padding: '12px 14px',
                borderRadius: 12,
                background: i === 0 ? cfg.bg : 'var(--bg-tertiary)',
                border: i === 0 ? `1px solid ${cfg.color}25` : '1px solid var(--border)',
                transition: 'all 0.2s ease',
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: `${cfg.color}15`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <Icon size={18} color={cfg.color} strokeWidth={2} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.5 }}>{event.description}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{timeAgo(event.timestamp)}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
