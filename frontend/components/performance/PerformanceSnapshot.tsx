import { PerformanceMetric } from "@/types/performance";

interface Props {
  metrics: PerformanceMetric[];
}

export function PerformanceSnapshot({ metrics }: Props) {
  if (!metrics || metrics.length === 0) return null;

  return (
    <section className="rounded-xl border bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold text-gray-700">
        Performance Snapshot
      </h2>

      <div className="space-y-3">
        {metrics.map((metric) => {
          const comparison = metric.comparison;

          return (
            <div
              key={metric.key}
              className="rounded-md border border-gray-100 p-3"
            >
              {/* METRIC LINE */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">
                  {metric.label}
                  {metric.per90 && " /90"}
                </span>

                <span className="font-medium text-gray-900">
                  {metric.value}
                  {metric.unit && ` ${metric.unit}`}
                </span>
              </div>

              {/* EXPLANATION */}
              {metric.explanation?.text && (
                <div className="mt-1 text-xs text-gray-500">
                  {metric.explanation.text}
                </div>
              )}

              {/* COMPARATIVE CONTEXT */}
              {comparison &&
                metric.explanation?.confidence !== "low" && (
                  <div className="mt-1 text-xs text-gray-400">
                    Better than{" "}
                    <span className="font-medium">
                      {comparison.percentile}%
                    </span>{" "}
                    of {comparison.population}
                  </div>
                )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
