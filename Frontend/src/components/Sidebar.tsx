import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Pill, FileText, Bell, Calendar, Activity, Shield } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/medications', icon: Pill, label: 'Medications' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/appointments', icon: Calendar, label: 'Appointments' },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside
      style={{
        width: 'var(--sidebar-width)',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        boxShadow: '2px 0 20px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ padding: '28px 24px 24px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div
            style={{
              width: 44,
              height: 44,
              background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
              borderRadius: 14,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(5, 150, 105, 0.35)',
            }}
          >
            <Activity size={24} color="white" strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 20, color: 'var(--text-primary)', letterSpacing: '-0.03em', lineHeight: 1.2 }}>
              Dirghayu
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.06em', marginTop: 1 }}>
              HEALTH MONITOR
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: '24px 20px 10px' }}>
        <span className="section-title">Menu</span>
      </div>

      <nav style={{ flex: 1, padding: '0 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {navItems.map(({ to, icon: Icon, label }) => {
          const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
          return (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                padding: '12px 16px',
                borderRadius: 12,
                textDecoration: 'none',
                fontSize: 14,
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                background: isActive ? 'var(--accent-muted)' : 'transparent',
                border: '1px solid transparent',
                transition: 'all 0.2s ease',
              }}
            >
              <Icon
                size={20}
                color={isActive ? 'var(--accent-primary)' : 'var(--text-muted)'}
                strokeWidth={isActive ? 2.5 : 2}
              />
              {label}
            </NavLink>
          );
        })}
      </nav>

      <div
        style={{
          padding: '20px 24px',
          margin: '0 12px 20px',
          borderRadius: 14,
          background: 'linear-gradient(135deg, rgba(5, 150, 105, 0.08) 0%, rgba(5, 150, 105, 0.04) 100%)',
          border: '1px solid var(--accent-border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <Shield size={18} color="var(--accent-primary)" strokeWidth={2} />
          <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>Secure Connection</span>
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
          End-to-end encrypted · HIPAA compliant
        </div>
      </div>
    </aside>
  );
}
