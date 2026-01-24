"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import { PlayerHeader } from "@/components/player/PlayerHeader";
import { ExplainableInsightCard } from "@/components/insights/ExplainableInsightCard";
import { PerformanceSnapshot } from "@/components/performance/PerformanceSnapshot";
import { MetricTrendList } from "@/components/trends/MetricTrendList";
import { DecisionSummary } from "@/components/decision/DecisionSummary";

import {
  sortInsightsByPriority,
  hasBlockingInsight,
} from "@/utils/insightLogic";

import { Player } from "@/types/player";
import { Insight } from "@/types/insight";
import { PerformanceMetric } from "@/types/performance";
import { MetricTrend } from "@/types/trends";

/* =======================
   API RESPONSE
   ======================= */

interface PlayerProfileResponse {
  player: {
    id: string;
    full_name: string;
    primary_position: string;
    team?: {
      id: string;
      name: string;
      logo_url?: string | null;
    };
    nationality?: string;
    shirt_number?: number;
  };

  match_context: {
    minutes_played: number;
    started: boolean;
  };

  metrics: PerformanceMetric[];
  insights: Insight[];
  timeline: any[];
  phase_metrics: Record<string, any>;
}

/* =======================
   PAGE
   ======================= */

export default function PlayerProfilePage() {
  const params = useParams<{
    matchId: string;
    playerId: string;
  }>();

  const { matchId, playerId } = params;

  const [player, setPlayer] = useState<Player | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [performanceMetrics, setPerformanceMetrics] =
    useState<PerformanceMetric[]>([]);
  const [trends, setTrends] = useState<MetricTrend[]>([]);
  const [error, setError] = useState<string | null>(null);

  /* =======================
     FETCH
     ======================= */

  useEffect(() => {
    if (!matchId || !playerId) return;

    fetch(
      `http://127.0.0.1:8000/api/analytics/matches/${matchId}/players/${playerId}/profile/`
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: PlayerProfileResponse) => {
        const adaptedPlayer: Player = {
          id: data.player.id,
          full_name: data.player.full_name,
          age: null,
          photo_url: null,

          primary_position: data.player.primary_position,
          secondary_positions: [],

          dominant_foot: undefined,

          current_team: data.player.team
            ? {
                id: data.player.team.id,
                name: data.player.team.name,
                logo_url: data.player.team.logo_url ?? null,
              }
            : null,

          joined_team_at: null,
          minutes_played_season: data.match_context.minutes_played,

          nationality: data.player.nationality,
          shirt_number: data.player.shirt_number,
        };

        setPlayer(adaptedPlayer);
        setInsights(data.insights ?? []);
        setPerformanceMetrics(data.metrics ?? []);

        // временные тренды (mock)
        setTrends([
          {
            key: "passing_accuracy",
            label: "Passing accuracy",
            unit: "%",
            points: [],
          },
          {
            key: "defensive_actions",
            label: "Defensive actions /90",
            points: [],
          },
        ]);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load player profile");
      });
  }, [matchId, playerId]);

  /* =======================
     STATES
     ======================= */

  if (error) {
    return <div className="p-6 text-red-600">{error}</div>;
  }

  if (!player) {
    return <div className="p-6">Loading player profile…</div>;
  }

  /* =======================
     INSIGHT LOGIC
     ======================= */

  const sortedInsights = sortInsightsByPriority(insights);
  const isAnalyticsBlocked = hasBlockingInsight(sortedInsights);

  /* =======================
     RENDER
     ======================= */

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-10">
      {/* Back to match */}
      <Link
        href={`/matches/${matchId}`}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        ← Back to match
      </Link>

      {/* Player header */}
      <section className="rounded-2xl border border-gray-200 p-5">
        <PlayerHeader
          player={player}
          seasonStart="2025-08-01"
        />

        {/* Team coach summary */}
        {player.current_team && (
          <div className="mt-2">
            <Link
              href={{
                pathname: `/teams/${player.current_team.id}/coach-summary`,
                query: { match_ids: [matchId] },
              }}
              className="inline-flex items-center text-sm text-blue-600 hover:underline"
            >
              View team coach summary →
            </Link>
          </div>
        )}
      </section>

      {/* Insights */}
      {sortedInsights.length > 0 && (
        <section className="space-y-3">
          <div className="text-sm font-medium text-gray-700">
            Key insights
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {sortedInsights.map((insight) => (
              <ExplainableInsightCard
                key={insight.code}
                insight={insight}
              />
            ))}
          </div>
        </section>
      )}

      {/* Analytics blocked */}
      {isAnalyticsBlocked ? (
        <section className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
          Аналитические показатели недоступны, так как данных
          недостаточно для надёжных выводов.
        </section>
      ) : (
        <>
          {/* Performance */}
          <section className="space-y-3">
            <div className="text-sm font-medium text-gray-700">
              Performance snapshot
            </div>
            <div className="rounded-2xl border border-gray-200 p-5">
              {performanceMetrics.length > 0 ? (
                <PerformanceSnapshot metrics={performanceMetrics} />
              ) : (
                <div className="text-sm text-gray-400">
                  Performance data not available for this match
                </div>
              )}
            </div>
          </section>

          {/* Trends */}
          {trends.length > 0 && (
            <section className="space-y-3">
              <div className="text-sm font-medium text-gray-700">
                Trends
              </div>
              <div className="rounded-2xl border border-gray-200 p-5">
                <MetricTrendList trends={trends} />
              </div>
            </section>
          )}

          {/* Decision */}
          <section className="space-y-3">
            <div className="text-sm font-medium text-gray-700">
              Decision support
            </div>
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
