import { Insight } from "@/types/insight";
import { PerformanceMetric } from "@/types/performance";
import { MetricTrend } from "@/types/trends";

interface Props {
  insights: Insight[];
  metrics: PerformanceMetric[];
  trends: MetricTrend[];
}

export function DecisionSummary({
  insights,
  metrics,
  trends,
}: Props) {
  if (!insights || insights.length === 0) return null;

  const hasBlocking = insights.some(
    (i) => i.code === "LOW_SAMPLE_SIZE"
  );

  if (hasBlocking) {
    return (
      <section className="rounded-xl border bg-gray-50 p-4">
        <h2 className="mb-2 text-sm font-semibold text-gray-700">
          Decision Summary
        </h2>
        <p className="text-sm text-gray-600">
          Недостаточно данных для формирования надёжного
          аналитического вывода по этому игроку.
        </p>
      </section>
    );
  }

  const positiveSignals = insights.filter(
    (i) => i.priority === "high"
  );

  const hasPositiveTrend =
    trends.some((t) => t.points.length >= 3);

  return (
    <section className="rounded-xl border bg-white p-4">
      <h2 className="mb-2 text-sm font-semibold text-gray-700">
        Decision Summary
      </h2>

      <div className="space-y-2 text-sm text-gray-700">
        {positiveSignals.length > 0 && (
          <p>
            Игрок демонстрирует устойчивые положительные
            сигналы, подтверждённые аналитическими
            наблюдениями.
          </p>
        )}

        {hasPositiveTrend && (
          <p>
            Динамика показателей указывает на стабильность
            или постепенное улучшение игровых действий
            в последних матчах.
          </p>
        )}

        {!positiveSignals.length && !hasPositiveTrend && (
          <p>
            Текущие данные не выявляют выраженных
            положительных или отрицательных тенденций,
            однако игрок демонстрирует предсказуемый
            уровень исполнения.
          </p>
        )}

        <p>
          Рекомендуется учитывать контекст роли игрока
          и игровые задачи при принятии тренерских решений.
        </p>
      </div>
    </section>
  );
}
