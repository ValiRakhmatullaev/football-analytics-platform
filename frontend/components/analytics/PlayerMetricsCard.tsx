"use client";

interface PlayerMetrics {
  activity_index: number;
  pass_score: number;
  pressure_resistance: number;
  zone_dominance: number;
  xg?: number;
  xa?: number;
}

interface PlayerMetricsCardProps {
  metrics: PlayerMetrics;
  title?: string;
}

export function PlayerMetricsCard({ metrics, title = "Игровые метрики" }: PlayerMetricsCardProps) {
  // Helper to get color based on value
  const getActivityColor = (value: number) => {
    if (value >= 120) return "text-green-700 bg-green-50";
    if (value >= 100) return "text-blue-700 bg-blue-50";
    if (value >= 80) return "text-yellow-700 bg-yellow-50";
    return "text-red-700 bg-red-50";
  };
  
  const getPassScoreColor = (value: number) => {
    if (value > 0.3) return "text-green-700 bg-green-50";
    if (value > 0) return "text-blue-700 bg-blue-50";
    if (value > -0.3) return "text-yellow-700 bg-yellow-50";
    return "text-red-700 bg-red-50";
  };
  
  const getPressureColor = (value: number) => {
    if (value >= 0.8) return "text-green-700 bg-green-50";
    if (value >= 0.6) return "text-blue-700 bg-blue-50";
    if (value >= 0.4) return "text-yellow-700 bg-yellow-50";
    return "text-red-700 bg-red-50";
  };
  
  const getZoneColor = (value: number) => {
    if (value >= 50) return "text-green-700 bg-green-50";
    if (value >= 30) return "text-blue-700 bg-blue-50";
    if (value >= 15) return "text-yellow-700 bg-yellow-50";
    return "text-red-700 bg-red-50";
  };
  
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Активность */}
        <div className={`rounded-lg p-4 ${getActivityColor(metrics.activity_index)}`}>
          <div className="text-sm text-gray-600 mb-1">Активность (Activity Index)</div>
          <div className="text-2xl font-bold">{metrics.activity_index}</div>
          <div className="text-xs mt-1 opacity-75">
            Нормализованное пройденное расстояние
          </div>
        </div>
        
        {/* Пас */}
        <div className={`rounded-lg p-4 ${getPassScoreColor(metrics.pass_score)}`}>
          <div className="text-sm text-gray-600 mb-1">Пас (Pass Score)</div>
          <div className="text-2xl font-bold">{metrics.pass_score.toFixed(2)}</div>
          <div className="text-xs mt-1 opacity-75">
            (Вперед - Назад) / Всего передач
          </div>
        </div>
        
        {/* Устойчивость к прессингу */}
        <div className={`rounded-lg p-4 ${getPressureColor(metrics.pressure_resistance)}`}>
          <div className="text-sm text-gray-600 mb-1">Устойчивость к прессингу</div>
          <div className="text-2xl font-bold">{(metrics.pressure_resistance * 100).toFixed(1)}%</div>
          <div className="text-xs mt-1 opacity-75">
            1 - (Потери под прессингом / Касания)
          </div>
        </div>
        
        {/* Доминирование в зоне */}
        <div className={`rounded-lg p-4 ${getZoneColor(metrics.zone_dominance)}`}>
          <div className="text-sm text-gray-600 mb-1">Доминирование в зоне</div>
          <div className="text-2xl font-bold">{metrics.zone_dominance}%</div>
          <div className="text-xs mt-1 opacity-75">
            Касания в атакующей трети
          </div>
        </div>

        {/* xG - ожидаемые голы */}
        {typeof metrics.xg === "number" && (
          <div className="rounded-lg p-4 bg-rose-50 text-rose-800">
            <div className="text-sm text-gray-600 mb-1">Ожидаемые голы (xG)</div>
            <div className="text-2xl font-bold">{metrics.xg.toFixed(2)}</div>
            <div className="text-xs mt-1 opacity-75">
              Суммарная вероятность забитых мячей по ударам
            </div>
          </div>
        )}

        {/* xA - ожидаемые ассисты */}
        {typeof metrics.xa === "number" && (
          <div className="rounded-lg p-4 bg-emerald-50 text-emerald-800">
            <div className="text-sm text-gray-600 mb-1">Ожидаемые ассисты (xA)</div>
            <div className="text-2xl font-bold">{metrics.xa.toFixed(2)}</div>
            <div className="text-xs mt-1 opacity-75">
              xG ударов после передач игрока (примерная оценка)
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
