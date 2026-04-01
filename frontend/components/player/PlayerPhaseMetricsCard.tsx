"use client";

/**
 * Метрики по фазам игры: атака, оборона, переходы, дисциплина, стандарты.
 */

export interface PhaseMetric {
  events?: number;
  minutes_active?: number;
  passes?: number;
  shots?: number;
  goals?: number;
  assists?: number;
  tackles?: number;
  interceptions?: number;
  clearances?: number;
  turnovers?: number;
  cards?: number;
  set_piece_actions?: number;
}

export type PhaseMetricsRecord = Record<string, PhaseMetric>;

const PHASE_LABELS: Record<string, string> = {
  attack: "Атака",
  defence: "Оборона",
  transition: "Переходы",
  discipline: "Дисциплина",
  set_piece: "Стандарты",
  other: "Прочее",
};

interface PlayerPhaseMetricsCardProps {
  phaseMetrics: PhaseMetricsRecord;
  title?: string;
}

export function PlayerPhaseMetricsCard({
  phaseMetrics,
  title = "По фазам игры",
}: PlayerPhaseMetricsCardProps) {
  const phases = Object.entries(phaseMetrics).filter(
    ([_, data]) => data && (data.events !== undefined || data.minutes_active !== undefined)
  );
  if (phases.length === 0) return null;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-4">
        {phases.map(([phase, data]) => (
          <div
            key={phase}
            className="rounded-xl border border-gray-100 bg-gray-50/50 p-4"
          >
            <div className="font-medium text-gray-800 mb-2">
              {PHASE_LABELS[phase] || phase}
            </div>
            <div className="flex flex-wrap gap-3 text-sm">
              {data.events !== undefined && (
                <span className="text-gray-600">
                  Событий: <span className="font-semibold text-gray-900">{data.events}</span>
                </span>
              )}
              {data.minutes_active !== undefined && (
                <span className="text-gray-600">
                  Минут активности: <span className="font-semibold text-gray-900">{data.minutes_active}</span>
                </span>
              )}
              {data.passes !== undefined && data.passes > 0 && (
                <span className="text-gray-600">Передачи: {data.passes}</span>
              )}
              {data.shots !== undefined && data.shots > 0 && (
                <span className="text-gray-600">Удары: {data.shots}</span>
              )}
              {data.tackles !== undefined && data.tackles > 0 && (
                <span className="text-gray-600">Отборы: {data.tackles}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
