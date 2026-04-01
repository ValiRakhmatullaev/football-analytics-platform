"use client";

/**
 * Метрики по позиции игрока (из profile metrics: key/value).
 */

const METRIC_LABELS: Record<string, string> = {
  involvement: "Вовлечённость",
  shooting_activity: "Ударная активность",
  goal_output: "Голевая отдача",
  passing_volume: "Объём передач",
  defensive_actions: "Действия в обороне",
  build_up_involvement: "Участие в розыгрыше",
  distribution: "Распасовка",
};

interface PlayerPositionMetricsCardProps {
  metrics: { key: string; value: number }[];
  title?: string;
}

export function PlayerPositionMetricsCard({
  metrics,
  title = "Метрики по позиции",
}: PlayerPositionMetricsCardProps) {
  if (!metrics || metrics.length === 0) return null;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {metrics.map((m) => (
          <div
            key={m.key}
            className="flex justify-between items-center rounded-lg bg-gray-50 px-4 py-3"
          >
            <span className="text-gray-700">
              {METRIC_LABELS[m.key] || m.key}
            </span>
            <span className="font-semibold text-gray-900">{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
