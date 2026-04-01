"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { BackButton } from "@/components/navigation/BackButton";
import { ActionButtons } from "@/components/navigation/ActionButtons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFilm, faChartBar } from "@fortawesome/free-solid-svg-icons";
import { apiUrl } from "@/lib/api";

/* =======================
   API TYPES
   ======================= */

interface PlayerAppearance {
  id: string;
  full_name: string;
  position: string;
  minutes_played: number;
  started: boolean;
}

interface TeamBlock {
  team_id: string;
  name: string;
  metrics: {
    possession_pct: number;
    turnovers: number;
    tempo: number;
  };
  confidence: string;
  players: PlayerAppearance[];
}

interface MatchOverviewResponse {
  match: {
    id: string;
    kickoff_time: string | null;
    status: string;
  };
  score: {
    home: number;
    away: number;
  };
  teams: {
    home: TeamBlock;
    away: TeamBlock;
  };
  key_insights: {
    code: string;
    text: string;
  }[];
  limitations: string[];
}

/* =======================
   PAGE
   ======================= */

export default function MatchOverviewPage() {
  const params = useParams<{ matchId: string }>();
  const { matchId } = params;

  const [data, setData] = useState<MatchOverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!matchId) return;

    // Abort previous request if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Prevent duplicate requests
    if (loading) return;

    setLoading(true);
    setError(null);

    // Create new abort controller
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    fetch(
      apiUrl(`/api/analytics/matches/${matchId}/overview/`),
      { signal }
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: MatchOverviewResponse) => {
        if (!signal.aborted) {
          setData(json);
          setError(null);
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') {
          return; // Request was aborted
        }
        if (!signal.aborted) {
          console.error(err);
          setError("Failed to load match overview");
        }
      })
      .finally(() => {
        if (!signal.aborted) {
          setLoading(false);
        }
      });

    // Cleanup function
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [matchId]);

  if (error) {
    return <div className="p-6 text-red-600">{error}</div>;
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Загрузка матча...</p>
        </div>
      </div>
    );
  }

  const { match, score, teams, key_insights, limitations } = data;

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-10">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight">
          Match Overview
        </h1>
        <div className="text-sm text-gray-500">
          {match.kickoff_time
            ? new Date(match.kickoff_time).toLocaleString()
            : "Unknown kickoff"}{" "}
          · {match.status}
        </div>
      </header>

      {/* Scoreboard */}
      <section className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 shadow-2xl">
        <div className="flex items-center justify-center gap-8">
          <div className="text-center flex-1">
            <div className="text-white text-xl font-semibold mb-2">
              {teams.home.name}
            </div>
            <div className="text-5xl font-bold text-white">
              {score.home}
            </div>
          </div>

          <div className="text-4xl font-bold text-gray-300">:</div>

          <div className="text-center flex-1">
            <div className="text-white text-xl font-semibold mb-2">
              {teams.away.name}
            </div>
            <div className="text-5xl font-bold text-white">
              {score.away}
            </div>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className="flex flex-wrap justify-center gap-4">
        <Link
          href={`/matches/${match.id}/clips`}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-500 text-white rounded-lg font-medium hover:bg-amber-600 transition shadow-md hover:shadow-lg"
        >
          <FontAwesomeIcon icon={faFilm} />
          <span>Просмотр и редактирование клипов</span>
        </Link>
        {(["home", "away"] as const).map((side) => {
          const team = teams[side];

          return (
            <Link
              key={team.team_id}
              href={{
                pathname: `/teams/${team.team_id}/coach-summary`,
                query: {
                  match_ids: [match.id],
                },
              }}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition shadow-md hover:shadow-lg"
            >
              <FontAwesomeIcon icon={faChartBar} />
              <span>Аналитика: {team.name}</span>
            </Link>
          );
        })}
      </div>

      {/* Key insights */}
      {key_insights.length > 0 && (
        <section className="rounded-xl border border-gray-200 bg-gray-50 p-5 space-y-2">
          <div className="text-sm font-medium text-gray-700">
            Key insights
          </div>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            {key_insights.map((insight) => (
              <li key={insight.code}>{insight.text}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Limitations */}
      {limitations.length > 0 && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <div className="font-medium mb-1">
            Data limitations
          </div>
          <ul className="list-disc list-inside space-y-1">
            {limitations.map((l, idx) => (
              <li key={idx}>{l}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Teams */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {(["home", "away"] as const).map((side) => {
          const team = teams[side];
          const starters = team.players.filter((p) => p.started);
          const bench = team.players.filter((p) => !p.started);

          return (
            <div
              key={side}
              className="rounded-2xl border border-gray-200 p-5 space-y-6"
            >
              <div className="space-y-2">
                <h2 className="text-lg font-semibold">
                  {team.name}
                </h2>

                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="px-2 py-1 rounded bg-gray-100">
                    Possession {team.metrics.possession_pct}%
                  </span>
                  <span className="px-2 py-1 rounded bg-gray-100">
                    Turnovers {team.metrics.turnovers}
                  </span>
                  <span className="px-2 py-1 rounded bg-gray-100">
                    Tempo {team.metrics.tempo}
                  </span>
                  <span className="px-2 py-1 rounded bg-blue-50 text-blue-700">
                    Confidence: {team.confidence}
                  </span>
                </div>
              </div>

              {/* Starters */}
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-700">
                  Starting XI
                </div>
                <ul className="divide-y divide-gray-100">
                  {starters.map((player) => (
                    <PlayerRow
                      key={player.id}
                      player={player}
                      matchId={matchId}
                    />
                  ))}
                </ul>
              </div>

              {/* Bench */}
              {bench.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-700">
                    Bench
                  </div>
                  <ul className="divide-y divide-gray-100 opacity-80">
                    {bench.map((player) => (
                      <PlayerRow
                        key={player.id}
                        player={player}
                        matchId={matchId}
                      />
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}

/* =======================
   PLAYER ROW
   ======================= */

function PlayerRow({
  player,
  matchId,
}: {
  player: PlayerAppearance;
  matchId: string;
}) {
  return (
    <li className="py-2 px-2 rounded-md flex items-center justify-between hover:bg-gray-50 transition">
      <div>
        <div className="text-sm font-medium">
          {player.full_name}
        </div>
        <div className="text-xs text-gray-500">
          {player.position} · {player.minutes_played} min
        </div>
      </div>

      <Link
        href={`/matches/${matchId}/players/${player.id}`}
        className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 transition shadow-sm hover:shadow-md"
      >
        <span>Профиль</span>
        <span>→</span>
      </Link>
    </li>
  );
}
