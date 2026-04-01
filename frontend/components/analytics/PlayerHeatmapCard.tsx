"use client";

import { useState, useMemo } from "react";

interface HeatmapData {
  grid_size: number;
  cells: number[][];
  max_value: number;
}

interface PlayerHeatmaps {
  all_events?: HeatmapData;
  passes?: HeatmapData;
  shots?: HeatmapData;
}

interface PlayerHeatmapCardProps {
  heatmaps: PlayerHeatmaps | null;
}

type Mode = "all_events" | "passes" | "shots";

const MODE_LABEL: Record<Mode, string> = {
  all_events: "Все действия",
  passes: "Передачи",
  shots: "Удары",
};

// Насыщенная палитра: зелёный → жёлтый → оранжевый → красный
const HEAT_STOPS: { t: number; r: number; g: number; b: number; a: number }[] = [
  { t: 0, r: 34, g: 197, b: 94, a: 0.45 },     // насыщенный зелёный
  { t: 0.35, r: 250, g: 204, b: 21, a: 0.7 },  // яркий жёлтый
  { t: 0.65, r: 249, g: 115, b: 22, a: 0.85 }, // насыщенный оранжевый
  { t: 1, r: 220, g: 38, b: 38, a: 0.95 },     // насыщенный красный
];

function heatColor(t: number): string {
  if (t <= 0) return `rgba(${HEAT_STOPS[0].r},${HEAT_STOPS[0].g},${HEAT_STOPS[0].b},${HEAT_STOPS[0].a})`;
  if (t >= 1) return `rgba(${HEAT_STOPS[HEAT_STOPS.length - 1].r},${HEAT_STOPS[HEAT_STOPS.length - 1].g},${HEAT_STOPS[HEAT_STOPS.length - 1].b},${HEAT_STOPS[HEAT_STOPS.length - 1].a})`;
  let i = 0;
  while (i < HEAT_STOPS.length - 1 && HEAT_STOPS[i + 1].t <= t) i++;
  const a = HEAT_STOPS[i];
  const b = HEAT_STOPS[i + 1];
  const s = (t - a.t) / (b.t - a.t);
  const r = Math.round(a.r + (b.r - a.r) * s);
  const g = Math.round(a.g + (b.g - a.g) * s);
  const bl = Math.round(a.b + (b.b - a.b) * s);
  const alpha = a.a + (b.a - a.a) * s;
  return `rgba(${r},${g},${bl},${alpha})`;
}

export function PlayerHeatmapCard({ heatmaps }: PlayerHeatmapCardProps) {
  if (!heatmaps) return null;

  const availableModes = (["all_events", "passes", "shots"] as Mode[]).filter(
    (m) => heatmaps[m]
  );
  if (availableModes.length === 0) return null;

  const [initialMode] = availableModes;
  const [mode, setMode] = useState<Mode>(initialMode);

  const data = heatmaps[mode];
  if (!data) return null;

  const { grid_size, cells, max_value } = data;
  const safeMax = max_value || 1;

  // Smooth heat layer: SVG with blurred circles so no hard edges
  const circles = useMemo(() => {
    const list: { row: number; col: number; value: number; intensity: number }[] = [];
    cells.forEach((row, rowIdx) =>
      row.forEach((value, colIdx) => {
        if (value <= 0) return;
        list.push({
          row: rowIdx,
          col: colIdx,
          value,
          intensity: value / safeMax,
        });
      })
    );
    return list;
  }, [cells, safeMax]);

  const cellW = 100 / grid_size;
  const cellH = 100 / grid_size;
  const radius = Math.max(cellW, cellH) * 0.85;

  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm space-y-4 animate-fade-in-up">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">
            Тепловая карта действий
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Интенсивность по координатам событий в матче
          </p>
        </div>
        <div className="inline-flex items-center rounded-full bg-slate-100 p-1 text-xs">
          {(["all_events", "passes", "shots"] as Mode[]).map((m) => {
            if (!heatmaps[m]) return null;
            return (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`px-3 py-1.5 rounded-full transition-all duration-300 text-xs font-medium ${
                  mode === m
                    ? "bg-white shadow-sm text-slate-900"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {MODE_LABEL[m]}
              </button>
            );
          })}
        </div>
      </div>

      {/* Направление атаки (вверх = ворота соперника) */}
      <div className="flex justify-center">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <span>Направление атаки</span>
          <svg className="w-4 h-4 text-slate-400" fill="currentColor" viewBox="0 0 24 24" aria-hidden style={{ transform: "rotate(-90deg)" }}>
            <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" />
          </svg>
        </div>
      </div>

      {/* Pitch container: aspect ratio, rounded, no cut-off */}
      <div className="relative w-full overflow-hidden rounded-xl bg-[#2d5016] shadow-inner">
        <div
          className="relative w-full"
          style={{ paddingBottom: `${(68 / 105) * 100}%` }}
        >
          <div className="absolute inset-0 flex items-center justify-center p-[6%]">
            {/* Inner pitch (padding = no cut-off edges) */}
            <div className="relative w-full h-full rounded-lg overflow-hidden bg-[#3a6b1f]">
              {/* Smooth heatmap layer via SVG + blur (key = re-animate on mode change) */}
              <svg
                key={mode}
                className="absolute inset-0 w-full h-full text-transparent"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
              >
                <defs>
                  <filter id="heatmap-blur" x="-30%" y="-30%" width="160%" height="160%">
                    <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" />
                  </filter>
                  <linearGradient id="pitch-grass" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#4a7c23" />
                    <stop offset="100%" stopColor="#2d5016" />
                  </linearGradient>
                </defs>
                {/* Subtle grass gradient */}
                <rect width="100" height="100" fill="url(#pitch-grass)" opacity="0.4" />
                {/* Heat circles — smooth, no hard edges */}
                <g filter="url(#heatmap-blur)">
                  {circles.map(({ row, col, intensity }, idx) => {
                    const x = (col + 0.5) * cellW;
                    const y = (row + 0.5) * cellH;
                    const fill = heatColor(intensity);
                    return (
                      <circle
                        key={`${row}-${col}`}
                        cx={x}
                        cy={y}
                        r={radius}
                        fill={fill}
                        className="heatmap-cell"
                        style={{
                          animation: "heatmap-cell-in 0.6s ease-out both",
                          animationDelay: `${Math.min(idx * 12, 400)}ms`,
                        }}
                      />
                    );
                  })}
                </g>
              </svg>

              {/* Pitch lines on top — clear and rounded */}
              <div
                className="absolute inset-0 pointer-events-none border-2 border-white/30 rounded-lg"
                aria-hidden
              />
              <div
                className="absolute left-1/2 top-0 bottom-0 w-[2px] bg-white/30 -translate-x-px rounded-full"
                aria-hidden
              />
              <div
                className="absolute left-1/2 top-1/2 w-8 h-12 border-2 border-white/30 rounded-full -translate-x-1/2 -translate-y-1/2"
                aria-hidden
              />
            </div>
          </div>
        </div>
      </div>

      {/* Legend: зелёный → жёлтый → оранжевый → красный */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Меньше</span>
          <div
            className="h-2.5 rounded-full overflow-hidden flex-1 min-w-[120px] max-w-[200px]"
            style={{
              background: "linear-gradient(90deg, #22c55e 0%, #facc15 35%, #f97316 65%, #dc2626 100%)",
            }}
          />
          <span className="text-xs text-slate-500">Больше</span>
        </div>
        <p className="text-xs text-slate-500">
          Верх — ворота соперника, низ — свои. Режим: {MODE_LABEL[mode].toLowerCase()}.
        </p>
      </div>
    </section>
  );
}
