// types/insight.ts

export interface InsightSource {
  minutes_played?: number;
  threshold_minutes?: number;
}

export interface Insight {
  code: string;
  text: string;
  confidence?: "low" | "medium" | "high";
  sources?: InsightSource;
}
