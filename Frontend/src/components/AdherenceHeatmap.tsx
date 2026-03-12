import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useMedicationStore } from '../store';
import { Calendar } from 'lucide-react';

const STATUS_COLORS = {
  taken: '#10b981',
  late: '#f59e0b',
  missed: '#ef4444',
  'no-data': '#e2e8f0',
};

export default function AdherenceHeatmap() {
  const { adherenceData } = useMedicationStore();
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !adherenceData.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const cellSize = 14;
    const gap = 3;
    const step = cellSize + gap;
    const marginLeft = 32;
    const marginTop = 28;

    const weekdayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const dayLabels = [1, 3, 5];
    dayLabels.forEach((d) => {
      svg
        .append('text')
        .attr('x', 10)
        .attr('y', marginTop + d * step + cellSize / 2 + 4)
        .text(weekdayLabels[d])
        .attr('fill', '#64748b')
        .attr('font-size', 10)
        .attr('font-family', "'Plus Jakarta Sans', sans-serif");
    });

    let monthLabeled = new Set<string>();
    adherenceData.forEach((item) => {
      const date = new Date(item.date);
      const dayOfWeek = date.getDay();
      const diffDays = Math.round((date.getTime() - new Date(adherenceData[0].date).getTime()) / 86400000);
      const weekNum = Math.floor(diffDays / 7);
      const x = weekNum * step + marginLeft;
      const y = dayOfWeek * step + marginTop;

      if (date.getDate() <= 7) {
        const monthKey = `${date.getFullYear()}-${date.getMonth()}`;
        if (!monthLabeled.has(monthKey)) {
          monthLabeled.add(monthKey);
          svg
            .append('text')
            .attr('x', x + cellSize / 2)
            .attr('y', marginTop - 8)
            .text(date.toLocaleString('default', { month: 'short' }))
            .attr('fill', '#64748b')
            .attr('font-size', 10)
            .attr('text-anchor', 'middle')
            .attr('font-family', "'Plus Jakarta Sans', sans-serif");
        }
      }

      const color = STATUS_COLORS[item.status];

      svg
        .append('rect')
        .attr('x', x)
        .attr('y', y)
        .attr('width', cellSize)
        .attr('height', cellSize)
        .attr('rx', 4)
        .attr('ry', 4)
        .attr('fill', color)
        .attr('opacity', item.status === 'no-data' ? 0.6 : 1)
        .style('cursor', item.status !== 'no-data' ? 'pointer' : 'default')
        .style('transition', 'opacity 0.15s ease')
        .on('mouseover', function (event) {
          if (item.status === 'no-data') return;
          d3.select(this).attr('opacity', 0.85);

          const tooltip = tooltipRef.current;
          if (!tooltip) return;
          tooltip.style.display = 'block';
          tooltip.style.left = `${event.offsetX + 14}px`;
          tooltip.style.top = `${event.offsetY - 44}px`;

          const statusText = {
            taken: '✓ Taken on time',
            late: '⏰ Taken late',
            missed: '✗ Missed',
            'no-data': 'No data',
          }[item.status];

          tooltip.innerHTML = `
            <div style="font-weight:700;color:${color};margin-bottom:4px;font-size:12px">${statusText}</div>
            <div style="color:#64748b;font-size:11px">${item.date}</div>
          `;
        })
        .on('mouseout', function () {
          d3.select(this).attr('opacity', item.status === 'no-data' ? 0.6 : 1);
          if (tooltipRef.current) tooltipRef.current.style.display = 'none';
        });
    });

    const weeks = 53;
    const days = 7;
    const width = weeks * step + marginLeft;
    const height = days * step + marginTop + 20;
    svg.attr('width', width).attr('height', height);
  }, [adherenceData]);

  return (
    <div className="card" style={{ position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 16 }}>
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
            <Calendar size={22} color="var(--accent-primary)" strokeWidth={2} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Medication Adherence</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>365-day history</div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <div key={status} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-muted)' }}>
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 4,
                  background: color,
                  opacity: status === 'no-data' ? 0.6 : 1,
                }}
              />
              <span>{status === 'no-data' ? 'No data' : status.charAt(0).toUpperCase() + status.slice(1)}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <svg ref={svgRef} />
      </div>

      <div
        ref={tooltipRef}
        style={{
          display: 'none',
          position: 'absolute',
          background: '#ffffff',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '10px 14px',
          fontSize: 12,
          pointerEvents: 'none',
          zIndex: 20,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12)',
          whiteSpace: 'nowrap',
        }}
      />
    </div>
  );
}
