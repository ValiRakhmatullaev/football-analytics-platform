"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";

import { DecisionSummary } from "@/components/decision/DecisionSummary";
import { ExplainableInsightCard } from "@/components/insights/ExplainableInsightCard";
import { PerformanceSnapshot } from "@/components/performance/PerformanceSnapshot";

import { Insight } from "@/types/insight";
import { PerformanceMetric } from "@/types/performance";

/* =======================
   API TYPES
   ======================= */

interface CoachSummaryResponse {
  meta: {
    matches_count: number;
  };
  load: {
    total_minutes: number;
    expected_minutes: number;
    players_used: number;
    load_ratio: number;
    load_level: "low" | "medium" | "high";
  };
  usage: {
    players_used: number;
    starts: number;
  };
  strengths: {
    code: string;
    text: string;
    evidence?: Record<string, any>;
  }[];
  weaknesses: {
    code: string;
    text: string;
    evidence?: Record<string, any>;
  }[];
  text: string;
}

/* =======================
   PAGE
   ======================= */

export default function CoachSummaryPage() {
  const params = useParams<{ teamId: string }>();
  const searchParams = useSearchParams();

  const teamId = params.teamId;
  const matchIds = searchParams.getAll("match_ids");

  const [data, setData] = useState<CoachSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  /* =======================
     FETCH
     ======================= */

  useEffect(() => {
    if (!teamId || matchIds.length === 0) return;

    const query = new URLSearchParams();
    query.append("team_id", teamId);
    matchIds.forEach((id) => query.append("match_ids", id));

    fetch(
      `http://127.0.0.1:8000/api/analytics/coach-summary/?${query.toString()}`
    )
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((json: CoachSummaryResponse) => {
        setData(json);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load coach summary");
      });
  }, [teamId, matchIds]);

  /* =======================
     STATES
     ======================= */

  if (error) {
    return <div className="p-6 text-red-600">{error}</div>;
  }

  if (!data) {
    return <div className="p-6">Loading coach summary…</div>;
  }

  /* =======================
     ADAPTERS
     ======================= */

  const insights: Insight[] = [
    ...data.strengths.map((s) => ({
      code: s.code,
      text: s.text,
      confidence: "high",
      sources: s.evidence ?? {},
    })),
    ...data.weaknesses.map((w) => ({
      code: w.code,
      text: w.text,
      confidence: "medium",
      sources: w.evidence ?? {},
    })),
  ];

  const loadMetrics: PerformanceMetric[] = [
    {
      key: "load_ratio",
      label: "Squad load",
      value: data.load.load_ratio,
      explanation: {
        text:
          data.load.load_level === "high"
            ? "Высокая игровая нагрузка на состав"
            : data.load.load_level === "medium"
            ? "Средняя игровая нагрузка"
            : "Низкая игровая нагрузка",
        confidence: "high",
      },
    },
    {
      key: "players_used",
      label: "Players used",
      value: data.usage.players_used,
      explanation: {
        text: "Количество игроков, задействованных в матчах",
        confidence: "high",
      },
    },
  ];

  /* =======================
     RENDER
     ======================= */

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-10">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-xl font-semibold tracking-tight">
          Coach Summary
        </h1>
        <div className="text-sm text-gray-500">
          Matches analyzed: {data.meta.matches_count}
        </div>
      </header>

      {/* Executive summary */}
      <section className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
        <div className="text-sm font-medium text-gray-700 mb-1">
          Executive summary
        </div>
        <p className="text-sm text-gray-800 leading-relaxed">
          {data.text}
        </p>
      </section>

      {/* Strengths */}
      {data.strengths.length > 0 && (
        <section className="space-y-3">
          <div className="text-sm font-medium text-gray-700">
            Team strengths
          </div>
          <div className="grid grid-cols-1 gap-3">
            {data.strengths.map((s) => (
              <ExplainableInsightCard
                key={s.code}
                insight={{
                  code: s.code,
                  text: s.text,
                  confidence: "high",
                  sources: s.evidence ?? {},
                }}
              />
            ))}
          </div>
        </section>
      )}

      {/* Weaknesses */}
      {data.weaknesses.length > 0 && (
        <section className="space-y-3">
          <div className="text-sm font-medium text-gray-700">
            Team weaknesses
          </div>
          <div className="grid grid-cols-1 gap-3">
            {data.weaknesses.map((w) => (
              <ExplainableInsightCard
                key={w.code}
                insight={{
                  code: w.code,
                  text: w.text,
                  confidence: "medium",
                  sources: w.evidence ?? {},
                }}
              />
            ))}
          </div>
        </section>
      )}

      {/* Load & usage */}
      <section className="space-y-3">
        <div className="text-sm font-medium text-gray-700">
          Squad load & usage
        </div>
        <div className="rounded-2xl border border-gray-200 p-5">
          <PerformanceSnapshot metrics={loadMetrics} />
        </div>
      </section>

      {/* Decision support */}
      <section className="space-y-3">
        <div className="text-sm font-medium text-gray-700">
          Decision support
        </div>
        <div className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
          <DecisionSummary
            insights={insights}
            metrics={loadMetrics}
            trends={[]}
          />
        </div>
      </section>
    </div>
  );
}
