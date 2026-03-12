import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { generateBiomarkerData, useApiStore } from '../store';
import { Activity } from 'lucide-react';

const PERIODS = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
];

const METRICS = [
  { key: 'systolic', name: 'Systolic BP', color: '#3b82f6', unit: 'mmHg', threshold: 130 },
  { key: 'diastolic', name: 'Diastolic BP', color: '#8b5cf6', unit: 'mmHg', threshold: 90 },
  { key: 'heartRate', name: 'Heart Rate', color: '#10b981', unit: 'bpm', threshold: 100 },
  { key: 'glucose', name: 'Glucose', color: '#f59e0b', unit: 'mg/dL', threshold: 140 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid var(--border)',
        borderRadius: 12,
        padding: '12px 16px',
        fontSize: 13,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12)',
      }}
    >
      <div style={{ fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color, display: 'flex', gap: 12, justifyContent: 'space-between', marginBottom: 4 }}>
          <span>{p.name}</span>
          <span style={{ fontWeight: 700 }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function BiomarkerChart() {
  const [period, setPeriod] = useState(30);
  const [activeMetrics, setActiveMetrics] = useState(['systolic', 'heartRate']);
  const apiBiomarkers = useApiStore((s) => s.biomarkers);

  const data = apiBiomarkers.length >= period
    ? apiBiomarkers.slice(-period)
    : generateBiomarkerData(period);
  const displayData = data.map((d) => ({
    ...d,
    date: period <= 7 ? d.date.slice(5) : d.date.slice(5),
  }));

  const thresholds = METRICS.filter((m) => activeMetrics.includes(m.key));

  const toggleMetric = (key: string) => {
    setActiveMetrics((prev) => (prev.includes(key) ? (prev.length > 1 ? prev.filter((k) => k !== key) : prev) : [...prev, key]));
  };

  return (
    <div className="card">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 20,
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
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
            <Activity size={22} color="var(--accent-primary)" strokeWidth={2} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Biomarker Timeline</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Clinical trends over time</div>
          </div>
        </div>

        <div style={{ display: 'flex', background: 'var(--bg-tertiary)', borderRadius: 10, padding: 4, border: '1px solid var(--border)' }}>
          {PERIODS.map(({ label, days }) => (
            <button
              key={label}
              onClick={() => setPeriod(days)}
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: period === days ? 'var(--accent-primary)' : 'transparent',
                color: period === days ? 'white' : 'var(--text-muted)',
                transition: 'all 0.2s ease',
                fontFamily: 'inherit',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {METRICS.map(({ key, name, color }) => (
          <button
            key={key}
            onClick={() => toggleMetric(key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 14px',
              borderRadius: 9999,
              border: `1px solid ${activeMetrics.includes(key) ? `${color}60` : 'var(--border)'}`,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              background: activeMetrics.includes(key) ? `${color}15` : 'transparent',
              color: activeMetrics.includes(key) ? color : 'var(--text-muted)',
              transition: 'all 0.2s ease',
              fontFamily: 'inherit',
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: activeMetrics.includes(key) ? color : 'var(--text-muted)',
              }}
            />
            {name}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={displayData} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
          <CartesianGrid stroke="rgba(0, 0, 0, 0.06)" strokeDasharray="4 4" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: 'var(--text-muted)', fontFamily: "'Plus Jakarta Sans', sans-serif" }}
            axisLine={false}
            tickLine={false}
            interval={Math.floor(data.length / 6)}
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--text-muted)', fontFamily: "'Plus Jakarta Sans', sans-serif" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {thresholds.map(
            ({ key, threshold, color, name }) =>
              activeMetrics.includes(key) && (
                <ReferenceLine
                  key={`ref-${key}`}
                  y={threshold}
                  stroke={color}
                  strokeDasharray="6 4"
                  strokeWidth={1.2}
                  strokeOpacity={0.5}
                  label={{ value: `${name} limit`, fill: color, fontSize: 10, position: 'insideBottomRight' }}
                />
              )
          )}
          {METRICS.filter((m) => activeMetrics.includes(m.key)).map(({ key, name, color }) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              name={name}
              stroke={color}
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0, fill: color }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
