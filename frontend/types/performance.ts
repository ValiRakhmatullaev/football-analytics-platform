export interface PerformanceMetricComparison {
  percentile: number; // 0–100
  population: string; // например: "CM", "League midfielders"
}

export interface PerformanceMetric {
  key: string;
  label: string;
  value: number;
  unit?: string;
  per90?: boolean;

  explanation?: {
    text: string;
    confidence?: "low" | "medium" | "high";
  };

  comparison?: PerformanceMetricComparison;
}
