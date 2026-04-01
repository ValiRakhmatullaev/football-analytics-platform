"use client";

interface TeamMetrics {
  possession_pct: number;
  total_shots: number;
  shots_on_target: number;
  passes: number;
  pass_accuracy_pct: number;
  recoveries: number;
  turnovers: number;
  xg?: number;
}

interface TeamMetricsCardProps {
  metrics: TeamMetrics;
  title?: string;
}

export function TeamMetricsCard({ metrics, title = "Командные метрики" }: TeamMetricsCardProps) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* xG */}
        {typeof metrics.xg === "number" && (
          <div className="bg-rose-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Ожидаемые голы (xG)</div>
            <div className="text-2xl font-bold text-rose-700">
              {metrics.xg.toFixed(2)}
            </div>
          </div>
        )}
        {/* Владение мячом */}
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Владение мячом</div>
          <div className="text-2xl font-bold text-blue-700">{metrics.possession_pct}%</div>
        </div>
        
        {/* Общее количество ударов */}
        <div className="bg-red-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Общее количество ударов</div>
          <div className="text-2xl font-bold text-red-700">{metrics.total_shots}</div>
        </div>
        
        {/* Удары в створ */}
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Удары в створ</div>
          <div className="text-2xl font-bold text-green-700">{metrics.shots_on_target}</div>
        </div>
        
        {/* Количество передач */}
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Количество передач</div>
          <div className="text-2xl font-bold text-purple-700">{metrics.passes}</div>
        </div>
        
        {/* Процент успешных передач */}
        <div className="bg-yellow-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Процент успешных передач</div>
          <div className="text-2xl font-bold text-yellow-700">{metrics.pass_accuracy_pct}%</div>
        </div>
        
        {/* Количество отборов */}
        <div className="bg-indigo-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Количество отборов</div>
          <div className="text-2xl font-bold text-indigo-700">{metrics.recoveries}</div>
        </div>
        
        {/* Количество потерь */}
        <div className="bg-orange-50 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">Количество потерь</div>
          <div className="text-2xl font-bold text-orange-700">{metrics.turnovers}</div>
        </div>
      </div>
    </div>
  );
}
