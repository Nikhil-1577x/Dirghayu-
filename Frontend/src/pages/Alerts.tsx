import { useState } from 'react';
import { AlertTriangle, Info, AlertCircle } from 'lucide-react';
import { useAlertStore } from '../store';

const severityConfig = {
    info: { icon: Info, color: '#38bdf8', bg: 'rgba(56,189,248,0.1)', border: 'rgba(56,189,248,0.25)', label: 'Info' },
    warning: { icon: AlertTriangle, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.25)', label: 'Warning' },
    critical: { icon: AlertCircle, color: '#ef4444', bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.35)', label: 'Critical' },
};

export default function Alerts() {
    const { alerts, markAllRead } = useAlertStore();
    const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');

    const filtered = alerts.filter(a => filter === 'all' || a.severity === filter);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24, paddingBottom: 40 }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 16 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 }}>System Alerts</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Review historical clinical and system notifications</p>
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                    <div style={{ display: 'flex', background: 'var(--bg-tertiary)', borderRadius: 8, padding: 4, border: '1px solid var(--border)' }}>
                        {(['all', 'critical', 'warning', 'info'] as const).map(f => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                style={{
                                    padding: '6px 12px',
                                    borderRadius: 6,
                                    fontSize: 12,
                                    fontWeight: 600,
                                    border: 'none',
                                    cursor: 'pointer',
                                    background: filter === f ? 'var(--accent-primary)' : 'transparent',
                                    color: filter === f ? 'white' : 'var(--text-muted)',
                                    transition: 'all 0.15s ease',
                                    textTransform: 'capitalize',
                                }}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                    <button className="btn btn-ghost" onClick={markAllRead}>Mark All Read</button>
                </div>
            </div>

            {/* List */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                {filtered.length === 0 ? (
                    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                        No alerts found for this filter.
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        {filtered.map((alert, i) => {
                            const cfg = severityConfig[alert.severity];
                            const Icon = cfg.icon;
                            const date = new Date(alert.timestamp).toLocaleString();
                            return (
                                <div
                                    key={alert.id}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: 16,
                                        padding: '20px 24px',
                                        borderBottom: i === filtered.length - 1 ? 'none' : '1px solid var(--border)',
                                        background: alert.read ? 'transparent' : 'rgba(255,255,255,0.02)',
                                        transition: 'background 0.2s ease',
                                    }}
                                >
                                    <div
                                        style={{
                                            width: 40,
                                            height: 40,
                                            background: cfg.bg,
                                            borderRadius: 10,
                                            flexShrink: 0,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                        }}
                                    >
                                        <Icon size={20} color={cfg.color} />
                                    </div>

                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                                            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>{alert.title}</h3>
                                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                                {date}
                                            </span>
                                        </div>

                                        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 12, maxWidth: 800 }}>
                                            {alert.description}
                                        </p>

                                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <span
                                                style={{
                                                    fontSize: 10,
                                                    fontWeight: 700,
                                                    color: cfg.color,
                                                    background: `${cfg.color}15`,
                                                    border: `1px solid ${cfg.color}30`,
                                                    padding: '2px 8px',
                                                    borderRadius: 20,
                                                    textTransform: 'uppercase',
                                                    letterSpacing: '0.05em'
                                                }}
                                            >
                                                {cfg.label}
                                            </span>
                                            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                                                Category: {alert.category}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
