"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

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

  useEffect(() => {
    if (!matchId) return;

    fetch(
      `http://127.0.0.1:8000/api/analytics/matches/${matchId}/overview/`
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: MatchOverviewResponse) => {
        setData(json);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load match overview");
      });
  }, [matchId]);

  if (error) {
    return <div className="p-6 text-red-600">{error}</div>;
  }

  if (!data) {
    return <div className="p-6">Loading match overview…</div>;
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
      <section className="flex items-center justify-center gap-10">
        <span className="text-lg font-medium">
          {teams.home.name}
        </span>

        <div className="px-8 py-4 rounded-2xl bg-black text-white text-3xl font-semibold">
          {score.home} : {score.away}
        </div>

        <span className="text-lg font-medium">
          {teams.away.name}
        </span>
      </section>

      {/* Navigation */}
      <div className="flex justify-center gap-4">
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
              className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Coach summary: {team.name}
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
        className="text-xs font-medium text-blue-600 hover:underline"
      >
        Profile →
      </Link>
    </li>
  );
}
