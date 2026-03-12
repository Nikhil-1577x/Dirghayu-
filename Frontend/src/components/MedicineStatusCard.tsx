import { Link } from 'react-router-dom';
import { CheckCircle2, Clock, AlertCircle, ChevronRight } from 'lucide-react';
import { usePatientStore } from '../store';

export default function MedicineStatusCard() {
  const { patientName, overallMedicineStatus, lastDoseTime, nextDoseTime, nextMedicineName } = usePatientStore();

  const config = {
    taken: {
      bg: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.03) 100%)',
      border: 'rgba(16, 185, 129, 0.25)',
      icon: CheckCircle2,
      iconColor: '#10b981',
      label: 'Medicine Taken Today',
      sublabel: 'Morning doses confirmed ✓',
      badgeBg: 'rgba(16, 185, 129, 0.15)',
      badgeColor: '#047857',
      badgeText: 'ON TRACK',
    },
    pending: {
      bg: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(245, 158, 11, 0.03) 100%)',
      border: 'rgba(245, 158, 11, 0.3)',
      icon: Clock,
      iconColor: '#f59e0b',
      label: 'Dose Pending',
      sublabel: `${nextMedicineName ? nextMedicineName + ' due soon' : 'Next dose approaching'}`,
      badgeBg: 'rgba(245, 158, 11, 0.15)',
      badgeColor: '#b45309',
      badgeText: 'PENDING',
    },
    missed: {
      bg: 'linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(239, 68, 68, 0.03) 100%)',
      border: 'rgba(239, 68, 68, 0.3)',
      icon: AlertCircle,
      iconColor: '#ef4444',
      label: 'Dose Missed',
      sublabel: 'Immediate attention required',
      badgeBg: 'rgba(239, 68, 68, 0.15)',
      badgeColor: '#dc2626',
      badgeText: 'MISSED',
    },
  }[overallMedicineStatus];

  const StatusIcon = config.icon;

  return (
    <div
      style={{
        background: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: 'var(--radius-xl)',
        padding: '32px 36px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 28,
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.04)',
      }}
    >
      <div style={{ flex: 1, zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
          <span
            style={{
              background: config.badgeBg,
              color: config.badgeColor,
              fontSize: 10,
              fontWeight: 800,
              letterSpacing: '0.1em',
              padding: '4px 12px',
              borderRadius: 9999,
              border: `1px solid ${config.iconColor}40`,
            }}
          >
            {config.badgeText}
          </span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Today · {patientName}</span>
        </div>
        <h2 style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.03em', marginBottom: 8, lineHeight: 1.2 }}>
          {config.label}
        </h2>
        <p style={{ fontSize: 15, color: 'var(--text-secondary)', marginBottom: 24, lineHeight: 1.5 }}>{config.sublabel}</p>

        <div style={{ display: 'flex', gap: 40, flexWrap: 'wrap' }}>
          {lastDoseTime && (
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Last Dose
              </div>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>{lastDoseTime}</div>
            </div>
          )}
          {nextDoseTime && (
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Next Dose
              </div>
              <div style={{ fontSize: 18, fontWeight: 700, color: config.iconColor }}>
                {nextDoseTime}
                {nextMedicineName && <span style={{ fontSize: 14, color: 'var(--text-secondary)', marginLeft: 8, fontWeight: 500 }}>{nextMedicineName}</span>}
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ zIndex: 1, flexShrink: 0 }}>
        <div
          style={{
            width: 100,
            height: 100,
            background: `${config.iconColor}18`,
            border: `2px solid ${config.iconColor}35`,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'absolute',
              width: 100,
              height: 100,
              border: `2px solid ${config.iconColor}25`,
              borderRadius: '50%',
              animation: 'pulse-ring 2.5s ease-in-out infinite',
            }}
          />
          <StatusIcon size={48} color={config.iconColor} strokeWidth={1.5} />
        </div>
      </div>

      <Link
        to="/medications"
        style={{
          position: 'absolute',
          bottom: 24,
          right: 28,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 13,
          color: 'var(--accent-primary)',
          textDecoration: 'none',
          fontWeight: 600,
          transition: 'gap 0.2s ease',
          zIndex: 1,
        }}
      >
        View Schedule <ChevronRight size={16} strokeWidth={2.5} />
      </Link>
    </div>
  );
}
