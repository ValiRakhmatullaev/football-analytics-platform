export interface TrendPoint {
  match_id: number;
  match_date: string;
  value: number;
  minutes_played: number;
}

export interface MetricTrend {
  key: string;
  label: string;
  unit?: string;
  points: TrendPoint[];
}
