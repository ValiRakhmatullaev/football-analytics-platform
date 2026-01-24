import { Insight } from "@/types/insight";

const INSIGHT_PRIORITY: Record<string, number> = {
  LOW_SAMPLE_SIZE: 100,
  DATA_INCOMPLETE: 90,
  POSITION_MISMATCH: 80,
  ROLE_UNCERTAIN: 70,
};

const BLOCKING_INSIGHTS = new Set<string>([
  "LOW_SAMPLE_SIZE",
  "DATA_INCOMPLETE",
]);

export function sortInsightsByPriority(
  insights: Insight[]
): Insight[] {
  return [...insights].sort((a, b) => {
    const pa = INSIGHT_PRIORITY[a.code] ?? 0;
    const pb = INSIGHT_PRIORITY[b.code] ?? 0;
    return pb - pa;
  });
}

export function hasBlockingInsight(
  insights: Insight[]
): boolean {
  return insights.some((i) =>
    BLOCKING_INSIGHTS.has(i.code)
  );
}
