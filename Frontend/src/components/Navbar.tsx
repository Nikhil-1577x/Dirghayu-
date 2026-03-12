import { Bell, Wifi, WifiOff, Loader2, User, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { usePatientStore } from '../store';
import { useAlertStore } from '../store';
import { useWSStore } from '../store';
import { useApiStore } from '../store';

export default function Navbar() {
  const { patientName, caretakerName } = usePatientStore();
  const { unreadCount } = useAlertStore();
  const { status: wsStatus } = useWSStore();
  const { patientId, patients, setPatientId, loading } = useApiStore();
  const [showPatientMenu, setShowPatientMenu] = useState(false);

  const wsConfig = {
    connected: {
      icon: Wifi,
      color: '#10b981',
      label: 'Live',
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.25)',
    },
    reconnecting: {
      icon: Loader2,
      color: '#f59e0b',
      label: 'Reconnecting',
      bg: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.25)',
    },
    disconnected: {
      icon: WifiOff,
      color: '#ef4444',
      label: 'Offline',
      bg: 'rgba(239, 68, 68, 0.1)',
      border: 'rgba(239, 68, 68, 0.25)',
    },
  }[wsStatus];

  const WsIcon = wsConfig.icon;

  return (
    <nav
      style={{
        height: 'var(--navbar-height)',
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--border)',
        boxShadow: '0 1px 0 rgba(0, 0, 0, 0.04)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      <div style={{ position: 'relative' }}>
        <button
          onClick={() => patients.length > 1 && setShowPatientMenu((v) => !v)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'none',
            border: 'none',
            cursor: patients.length > 1 ? 'pointer' : 'default',
            padding: 0,
          }}
        >
          <div>
            <div style={{ fontSize: 17, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1.2, textAlign: 'left' }}>
              {loading ? 'Loading...' : patientName}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2, textAlign: 'left' }}>
              Monitored by <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{caretakerName}</span>
            </div>
          </div>
          {patients.length > 1 && <ChevronDown size={18} color="var(--text-muted)" style={{ transform: showPatientMenu ? 'rotate(180deg)' : undefined, transition: 'transform 0.2s' }} />}
        </button>
        {showPatientMenu && patients.length > 1 && (
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              marginTop: 8,
              background: 'white',
              border: '1px solid var(--border)',
              borderRadius: 12,
              boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
              padding: 8,
              minWidth: 200,
              zIndex: 100,
            }}
          >
            {patients.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setPatientId(p.id);
                  setShowPatientMenu(false);
                }}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: 8,
                  border: 'none',
                  background: patientId === p.id ? 'var(--accent-muted)' : 'transparent',
                  color: patientId === p.id ? 'var(--accent-primary)' : 'var(--text-primary)',
                  fontSize: 14,
                  fontWeight: patientId === p.id ? 600 : 500,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                {p.name}
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 14px',
            borderRadius: 12,
            background: wsConfig.bg,
            border: `1px solid ${wsConfig.border}`,
          }}
        >
          <WsIcon
            size={14}
            color={wsConfig.color}
            style={wsStatus === 'reconnecting' ? { animation: 'spin 1s linear infinite' } : {}}
          />
          <span style={{ fontSize: 12, fontWeight: 600, color: wsConfig.color }}>{wsConfig.label}</span>
          {wsStatus === 'connected' && (
            <span
              style={{
                width: 6,
                height: 6,
                background: wsConfig.color,
                borderRadius: '50%',
                animation: 'dot-pulse 2s ease-in-out infinite',
              }}
            />
          )}
        </div>

        <Link to="/alerts" style={{ textDecoration: 'none' }}>
          <button
            style={{
              position: 'relative',
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border)',
              borderRadius: 12,
              padding: '10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
            }}
          >
            <Bell size={20} color="var(--text-secondary)" />
            {unreadCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  minWidth: 20,
                  height: 20,
                  padding: '0 6px',
                  background: '#ef4444',
                  color: 'white',
                  borderRadius: 10,
                  fontSize: 11,
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 2px 8px rgba(239, 68, 68, 0.4)',
                }}
              >
                {unreadCount}
              </span>
            )}
          </button>
        </Link>

        <div
          style={{
            width: 42,
            height: 42,
            background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(5, 150, 105, 0.3)',
          }}
        >
          <User size={20} color="white" strokeWidth={2.5} />
        </div>
      </div>
    </nav>
  );
}
