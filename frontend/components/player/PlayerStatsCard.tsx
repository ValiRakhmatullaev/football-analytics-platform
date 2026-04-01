"use client";

/**
 * Карточка статистики игрока в матче: голы, передачи, удары, отборы и т.д.
 */

export interface MatchEventsSummary {
  goals?: number;
  assists?: number;
  passes?: number;
  shots?: number;
  tackles?: number;
  interceptions?: number;
  yellow_cards?: number;
  red_cards?: number;
}

const EVENT_LABELS: Record<string, string> = {
  goals: "Голы",
  assists: "Голевые передачи",
  passes: "Передачи",
  shots: "Удары",
  tackles: "Отборы",
  interceptions: "Перехваты",
  yellow_cards: "Жёлтые карточки",
  red_cards: "Красные карточки",
};

const ORDER: (keyof MatchEventsSummary)[] = [
  "goals",
  "assists",
  "passes",
  "shots",
  "tackles",
  "interceptions",
  "yellow_cards",
  "red_cards",
];

interface PlayerStatsCardProps {
  events: MatchEventsSummary;
  title?: string;
}

export function PlayerStatsCard({ events, title = "Статистика матча" }: PlayerStatsCardProps) {
  const entries = ORDER.filter((k) => events[k] !== undefined && events[k] !== null);
  if (entries.length === 0) return null;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {entries.map((key) => (
          <div
            key={key}
            className="rounded-xl bg-gray-50 border border-gray-100 p-4 text-center"
          >
            <div className="text-2xl font-bold text-gray-900">
              {Number(events[key])}
            </div>
            <div className="text-sm text-gray-600 mt-0.5">
              {EVENT_LABELS[key] || key}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
