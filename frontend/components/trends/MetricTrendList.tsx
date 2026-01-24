import { MetricTrend } from "@/types/trends";

interface Props {
  trends: MetricTrend[];
}

export function MetricTrendList({ trends }: Props) {
  if (!trends || trends.length === 0) return null;

  return (
    <section className="rounded-xl border bg-white p-4">
      {/* Disclaimer */}
      <div className="mb-3 text-xs text-gray-500">
        Предварительные тренды (низкая надёжность из-за малого времени)
      </div>

      <h2 className="mb-3 text-sm font-semibold text-gray-700">
        Trends & Dynamics
      </h2>

      <div className="space-y-4">
        {trends.map((trend) => (
          <div key={trend.key}>
            <div className="mb-1 text-sm text-gray-600">
              {trend.label}
            </div>

            <div className="flex gap-2">
              {trend.points.map((p) => (
                <div
                  key={p.match_id}
                  className={`h-8 w-4 rounded-sm ${
                    p.minutes_played < 30
                      ? "bg-gray-200"
                      : "bg-blue-500"
                  }`}
                  title={`${p.value}${trend.unit ?? ""} · ${p.minutes_played} min`}
                />
              ))}
            </div>

            <div className="mt-1 text-xs text-gray-500">
              Серые столбцы — низкая надёжность (мало минут)
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
