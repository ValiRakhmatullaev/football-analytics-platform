import { Insight } from "@/types/insight";

interface Props {
  insight: Insight;
}

export function ExplainableInsightCard({ insight }: Props) {
  const isLowSample = insight.code === "LOW_SAMPLE_SIZE";

  return (
    <div
      className={`rounded-xl border p-4 ${
        isLowSample
          ? "border-yellow-300 bg-yellow-50"
          : "border-gray-200 bg-white"
      }`}
    >
      {/* TITLE */}
      {isLowSample && (
        <div className="mb-1 text-sm font-semibold text-yellow-600">
          ⚠ Недостаточно данных
        </div>
      )}

      {/* MAIN TEXT */}
      <div className="text-sm text-gray-800">
        {insight.text}
      </div>

      {/* SOURCES */}
      {insight.sources?.minutes_played !== undefined &&
        insight.sources?.threshold_minutes !== undefined && (
          <div className="mt-2 text-xs text-gray-600">
            {insight.sources.minutes_played} минут сыграно · минимальный порог —{" "}
            {insight.sources.threshold_minutes} минут
          </div>
        )}
    </div>
  );
}
