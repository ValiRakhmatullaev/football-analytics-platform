"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import { apiUrl } from "@/lib/api";
import { PlayerHeader } from "@/components/player/PlayerHeader";
import { PlayerStatsCard } from "@/components/player/PlayerStatsCard";
import { PlayerPositionMetricsCard } from "@/components/player/PlayerPositionMetricsCard";
import { PlayerPhaseMetricsCard } from "@/components/player/PlayerPhaseMetricsCard";
import { ExplainableInsightCard } from "@/components/insights/ExplainableInsightCard";
import { PerformanceSnapshot } from "@/components/performance/PerformanceSnapshot";
import { MetricTrendList } from "@/components/trends/MetricTrendList";
import { DecisionSummary } from "@/components/decision/DecisionSummary";
import { TeamMetricsCard } from "@/components/analytics/TeamMetricsCard";
import { PlayerMetricsCard } from "@/components/analytics/PlayerMetricsCard";
import { BackButton } from "@/components/navigation/BackButton";
import { PlayerHeatmapCard } from "@/components/analytics/PlayerHeatmapCard";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faChartBar } from "@fortawesome/free-solid-svg-icons";

import {
  sortInsightsByPriority,
  hasBlockingInsight,
} from "@/utils/insightLogic";

import { Player } from "@/types/player";
import { Insight } from "@/types/insight";
import { PerformanceMetric } from "@/types/performance";
import { MetricTrend } from "@/types/trends";

const POSITION_LABEL: Record<string, string> = {
  involvement: "Вовлечённость",
  shooting_activity: "Ударная активность",
  goal_output: "Голевая отдача",
  passing_volume: "Объём передач",
  defensive_actions: "Действия в обороне",
  build_up_involvement: "Участие в розыгрыше",
  distribution: "Распасовка",
};

/* =======================
   API RESPONSE
   ======================= */

interface PlayerProfileResponse {
  player: {
    id: string;
    full_name: string;
    primary_position: string;
    team?: { id: string; name: string };
    nationality?: string | null;
    shirt_number?: number | null;
  };
  match_context: {
    match_id: string;
    minutes_played: number;
    started: boolean;
  };
  events: Record<string, number>;
  metrics: { key: string; value: number }[];
  timeline: unknown[];
  phase_metrics: Record<string, { events?: number; minutes_active?: number; [k: string]: unknown }>;
  insights: Insight[];
  heatmaps?: {
    all_events?: {
      grid_size: number;
      cells: number[][];
      max_value: number;
    };
    passes?: {
      grid_size: number;
      cells: number[][];
      max_value: number;
    };
    shots?: {
      grid_size: number;
      cells: number[][];
      max_value: number;
    };
  };
  team_metrics?: {
    possession_pct: number;
    total_shots: number;
    shots_on_target: number;
    passes: number;
    pass_accuracy_pct: number;
    recoveries: number;
    turnovers: number;
    xg?: number;
  };
  player_metrics?: {
    activity_index: number;
    pass_score: number;
    pressure_resistance: number;
    zone_dominance: number;
    xg?: number;
    xa?: number;
  };
}

/* =======================
   PAGE
   ======================= */

export default function PlayerProfilePage() {
  const params = useParams<{ matchId: string; playerId: string }>();
  const { matchId, playerId } = params;

  const [player, setPlayer] = useState<Player | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetric[]>([]);
  const [trends, setTrends] = useState<MetricTrend[]>([]);
  const [eventsSummary, setEventsSummary] = useState<Record<string, number> | null>(null);
  const [phaseMetrics, setPhaseMetrics] = useState<Record<string, unknown> | null>(null);
  const [positionMetrics, setPositionMetrics] = useState<{ key: string; value: number }[]>([]);
  const [matchContext, setMatchContext] = useState<{ minutes_played: number; started: boolean } | null>(null);
  const [teamMetrics, setTeamMetrics] = useState<PlayerProfileResponse["team_metrics"]>(null);
  const [playerMetrics, setPlayerMetrics] = useState<PlayerProfileResponse["player_metrics"]>(null);
  const [heatmaps, setHeatmaps] = useState<PlayerProfileResponse["heatmaps"] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (abortControllerRef.current) abortControllerRef.current.abort();
    if (!matchId || !playerId) return;
    if (loading) return;

    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;
    setLoading(true);
    setError(null);

    fetch(apiUrl(`/api/analytics/matches/${matchId}/players/${playerId}/profile/`), { signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: PlayerProfileResponse) => {
        if (signal.aborted) return;

        const adaptedPlayer: Player = {
          id: data.player.id as unknown as number,
          full_name: data.player.full_name,
          age: null,
          photo_url: null,
          primary_position: data.player.primary_position,
          secondary_positions: [],
          dominant_foot: undefined,
          current_team: data.player.team
            ? { id: data.player.team.id as unknown as number, name: data.player.team.name, logo_url: null }
            : null,
          joined_team_at: null,
          minutes_played_season: data.match_context.minutes_played,
          nationality: data.player.nationality ?? undefined,
          shirt_number: data.player.shirt_number ?? undefined,
        };

        setPlayer(adaptedPlayer);
        setMatchContext(data.match_context);
        setEventsSummary(data.events ?? null);
        setPhaseMetrics(data.phase_metrics ?? null);
        setPositionMetrics(data.metrics ?? []);
        setInsights(data.insights ?? []);
        setPerformanceMetrics(
          (data.metrics ?? []).map((m) => ({
            key: m.key,
            label: POSITION_LABEL[m.key] ?? m.key,
            value: m.value,
          }))
        );
        setTrends([
          { key: "passing_accuracy", label: "Passing accuracy", unit: "%", points: [] },
          { key: "defensive_actions", label: "Defensive actions /90", points: [] },
        ]);
        if (data.team_metrics) setTeamMetrics(data.team_metrics);
        if (data.player_metrics) setPlayerMetrics(data.player_metrics);
        if (data.heatmaps) setHeatmaps(data.heatmaps);
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        console.error(err);
        if (!signal.aborted) setError("Не удалось загрузить профиль игрока");
      })
      .finally(() => {
        if (!signal.aborted) setLoading(false);
      });

    return () => {
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, [matchId, playerId]);

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <BackButton href={`/matches/${matchId}`} label="← Назад к матчу" />
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mt-6">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  if (loading || !player) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <BackButton href={`/matches/${matchId}`} label="← Назад к матчу" />
        <div className="flex items-center justify-center py-12 mt-6">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4" />
            <p className="text-gray-600">Загрузка профиля игрока...</p>
          </div>
        </div>
      </div>
    );
  }

  const sortedInsights = sortInsightsByPriority(insights);
  const isAnalyticsBlocked = hasBlockingInsight(sortedInsights);
  const coachSummaryHref = player.current_team
    ? `/teams/${player.current_team.id}/coach-summary?match_ids=${matchId}`
    : "#";

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Навигация */}
      <div className="flex flex-wrap items-center gap-3">
        <BackButton href={`/matches/${matchId}`} label="← Назад к матчу" />
        {player.current_team && (
          <Link
            href={coachSummaryHref}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition"
          >
            <FontAwesomeIcon icon={faChartBar} />
            <span>Аналитика команды</span>
          </Link>
        )}
      </div>

      {/* Профиль: имя, позиция, команда, минуты */}
      <section className="rounded-2xl border border-gray-200 bg-white p-6">
        <PlayerHeader player={player} seasonStart="2025-08-01" />
        {matchContext && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-4 text-sm text-gray-600">
            <span>Минут в матче: <strong className="text-gray-900">{matchContext.minutes_played}</strong></span>
            <span>В старте: <strong className="text-gray-900">{matchContext.started ? "Да" : "Нет"}</strong></span>
          </div>
        )}
      </section>

      {/* Статистика матча: голы, передачи, удары, отборы и т.д. */}
      {eventsSummary && Object.keys(eventsSummary).length > 0 && (
        <section>
          <PlayerStatsCard events={eventsSummary} title="Статистика матча" />
        </section>
      )}

      {/* Метрики по позиции */}
      {positionMetrics.length > 0 && (
        <section>
          <PlayerPositionMetricsCard metrics={positionMetrics} title="Метрики по позиции" />
        </section>
      )}

      {/* Тепловая карта действий */}
      {heatmaps && (
        <section>
          <PlayerHeatmapCard heatmaps={heatmaps} />
        </section>
      )}

      {/* По фазам игры */}
      {phaseMetrics && Object.keys(phaseMetrics).length > 0 && (
        <section>
          <PlayerPhaseMetricsCard
            phaseMetrics={phaseMetrics as import("@/components/player/PlayerPhaseMetricsCard").PhaseMetricsRecord}
            title="По фазам игры"
          />
        </section>
      )}

      {/* Командные метрики */}
      {teamMetrics && (
        <section>
          <TeamMetricsCard metrics={teamMetrics} title="Командные метрики в матче" />
        </section>
      )}

      {/* Игровые метрики (продвинутые) */}
      {playerMetrics && (
        <section>
          <PlayerMetricsCard metrics={playerMetrics} title="Игровые метрики" />
        </section>
      )}

      {/* Выводы (insights) */}
      {sortedInsights.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Выводы</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {sortedInsights.map((insight) => (
              <ExplainableInsightCard key={insight.code} insight={insight} />
            ))}
          </div>
        </section>
      )}

      {/* Ограничение аналитики */}
      {isAnalyticsBlocked && (
        <section className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
          Аналитические показатели недоступны: недостаточно данных для надёжных выводов.
        </section>
      )}

      {!isAnalyticsBlocked && (
        <>
          {/* Performance snapshot */}
          {performanceMetrics.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Performance snapshot</h2>
              <div className="rounded-2xl border border-gray-200 p-5">
                <PerformanceSnapshot metrics={performanceMetrics} />
              </div>
            </section>
          )}

          {trends.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Тренды</h2>
              <div className="rounded-2xl border border-gray-200 p-5">
                <MetricTrendList trends={trends} />
              </div>
            </section>
          )}

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Рекомендации</h2>
            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
              <DecisionSummary
                insights={sortedInsights}
                metrics={performanceMetrics}
                trends={trends}
              />
            </div>
          </section>
        </>
      )}
    </div>
  );
}
