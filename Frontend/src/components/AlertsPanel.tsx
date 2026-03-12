import { Link } from 'react-router-dom';
import { AlertTriangle, Info, AlertCircle, Bell } from 'lucide-react';
import { useAlertStore } from '../store';

const severityConfig = {
  info: { icon: Info, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.08)', border: 'rgba(59, 130, 246, 0.2)', label: 'Info' },
  warning: { icon: AlertTriangle, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.08)', border: 'rgba(245, 158, 11, 0.2)', label: 'Warning' },
  critical: { icon: AlertCircle, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.08)', border: 'rgba(239, 68, 68, 0.2)', label: 'Critical' },
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

export default function AlertsPanel() {
  const { alerts } = useAlertStore();
  const sorted = [...alerts].sort((a, b) => {
    const order = { critical: 0, warning: 1, info: 2 };
    return order[a.severity] - order[b.severity];
  });
  const unreadCount = sorted.filter((a) => !a.read).length;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 12,
              background: 'var(--red-muted)',
              border: '1px solid var(--red-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Bell size={22} color="var(--red-primary)" strokeWidth={2} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Active Alerts</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{unreadCount} unread</div>
          </div>
        </div>
        <Link to="/alerts" style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-primary)', textDecoration: 'none' }}>
          View all
        </Link>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {sorted.slice(0, 5).map((alert, i) => {
          const cfg = severityConfig[alert.severity];
          const Icon = cfg.icon;
          return (
            <div
              key={alert.id}
              style={{
                display: 'flex',
                gap: 14,
                padding: '14px 16px',
                borderRadius: 12,
                background: alert.read ? 'var(--bg-tertiary)' : cfg.bg,
                border: `1px solid ${alert.read ? 'var(--border)' : cfg.border}`,
                animation: `fadeInUp ${0.15 + i * 0.06}s cubic-bezier(0.16, 1, 0.3, 1) forwards`,
                opacity: alert.read ? 0.85 : 1,
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: `${cfg.color}15`,
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon size={18} color={cfg.color} strokeWidth={2} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{alert.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.5 }}>{alert.description}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      color: cfg.color,
                      background: `${cfg.color}20`,
                      padding: '2px 8px',
                      borderRadius: 6,
                    }}
                  >
                    {cfg.label}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{timeAgo(alert.timestamp)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
