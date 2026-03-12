import { usePatientStore } from '../store';
import { TrendingUp } from 'lucide-react';

export default function RiskScoreGauge() {
  const { riskScore, riskCategory } = usePatientStore();

  const SIZE = 200;
  const STROKE = 14;
  const R = (SIZE - STROKE) / 2;
  const CENTER = SIZE / 2;
  const ARC_START_DEG = 135;
  const ARC_END_DEG = 405;
  const TOTAL_ARC = 270;

  const getColor = () => {
    if (riskScore < 10) return '#10b981';
    if (riskScore < 20) return '#f59e0b';
    return '#ef4444';
  };

  const polar = (deg: number) => {
    const rad = ((deg - 90) * Math.PI) / 180;
    return { x: CENTER + R * Math.cos(rad), y: CENTER + R * Math.sin(rad) };
  };

  const arcPath = (startDeg: number, endDeg: number) => {
    const s = polar(startDeg);
    const e = polar(endDeg);
    const large = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${R} ${R} 0 ${large} 1 ${e.x} ${e.y}`;
  };

  const fillAngle = ARC_START_DEG + (riskScore / 100) * TOTAL_ARC;
  const color = getColor();

  const categoryLabel = { low: 'Low Risk', moderate: 'Moderate Risk', high: 'High Risk' }[riskCategory];
  const categoryColor = { low: '#10b981', moderate: '#f59e0b', high: '#ef4444' }[riskCategory];

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Cardiovascular Risk</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>QRISK3 Score</div>
        </div>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <TrendingUp size={18} color="var(--text-muted)" />
        </div>
      </div>

      <svg width={SIZE} height={SIZE} style={{ overflow: 'visible' }}>
        {/* Neutral track only - no colored zone overlay */}
        <path
          d={arcPath(ARC_START_DEG, ARC_END_DEG)}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={STROKE}
          strokeLinecap="round"
        />

        {/* Filled progress */}
        <path
          d={arcPath(ARC_START_DEG, fillAngle)}
          fill="none"
          stroke={color}
          strokeWidth={STROKE}
          strokeLinecap="round"
          style={{ transition: 'all 0.8s cubic-bezier(0.16, 1, 0.3, 1)', filter: `drop-shadow(0 0 6px ${color}50)` }}
        />

        <text x={CENTER} y={CENTER - 12} textAnchor="middle" fill="var(--text-primary)" fontSize={40} fontWeight={800} fontFamily="'Plus Jakarta Sans', sans-serif">
          {riskScore}%
        </text>
        <text x={CENTER} y={CENTER + 16} textAnchor="middle" fill={categoryColor} fontSize={12} fontWeight={700} fontFamily="'Plus Jakarta Sans', sans-serif" letterSpacing="0.05em">
          {categoryLabel.toUpperCase()}
        </text>
      </svg>

      <div style={{ display: 'flex', gap: 20, fontSize: 12 }}>
        {[
          { label: 'Low', color: '#10b981' },
          { label: 'Moderate', color: '#f59e0b' },
          { label: 'High', color: '#ef4444' },
        ].map(({ label, color: c }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
