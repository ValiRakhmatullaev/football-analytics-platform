"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { useParams, useSearchParams } from "next/navigation";

import { DecisionSummary } from "@/components/decision/DecisionSummary";
import { ExplainableInsightCard } from "@/components/insights/ExplainableInsightCard";
import { PerformanceSnapshot } from "@/components/performance/PerformanceSnapshot";
import { BackButton } from "@/components/navigation/BackButton";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { apiUrl } from "@/lib/api";

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
  const matchIdsParam = searchParams.getAll("match_ids");

  // Stabilize matchIds array to prevent infinite loops
  const matchIds = useMemo(() => {
    return matchIdsParam.filter((id) => id && id.trim()).map((id) => id.trim());
  }, [matchIdsParam.join(",")]); // Join to create stable dependency

  // Create stable string key for dependencies
  const matchIdsKey = useMemo(() => {
    // IMPORTANT: don't mutate matchIds via sort()
    return [...matchIds].sort().join(",");
  }, [matchIds.join(",")]);

  const [data, setData] = useState<CoachSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastRequestKeyRef = useRef<string | null>(null);

  /* =======================
     FETCH
     ======================= */

  useEffect(() => {
    const requestKey = `${teamId ?? ""}|${matchIdsKey}`;

    // In Next.js dev (React StrictMode), effects can fire twice.
    // This guard prevents sending the same request twice.
    if (lastRequestKeyRef.current === requestKey && (loading || data)) {
      return;
    }

    // Abort previous request if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    if (!teamId) {
      setError("Team ID is required");
      setLoading(false);
      return;
    }

    if (matchIds.length === 0) {
      setError("At least one match ID is required");
      setLoading(false);
      return;
    }

    // Prevent duplicate requests
    if (loading) {
      return;
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    setError(null);
    setLoading(true);
    lastRequestKeyRef.current = requestKey;

    const query = new URLSearchParams();
    query.append("team_id", teamId);
    matchIds.forEach((id) => {
      query.append("match_ids", id);
    });

    fetch(
      apiUrl(`/api/analytics/coach-summary/?${query.toString()}`),
      { signal }
    )
      .then((res) => {
        if (!res.ok) {
          return res.json().then((errData) => {
            throw new Error(errData.detail || errData.error || `HTTP ${res.status}`);
          });
        }
        return res.json();
      })
      .then((json: CoachSummaryResponse) => {
        if (!signal.aborted) {
          setData(json);
          setError(null);
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') {
          // Request was aborted, ignore
          return;
        }
        console.error("Coach summary error:", err);
        if (!signal.aborted) {
          setError(err instanceof Error ? err.message : "Failed to load coach summary");
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
  }, [teamId, matchIdsKey]); // Use stable string key instead of array

  /* =======================
     STATES
     ======================= */

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <BackButton href="/" label="← Назад к главной" />
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mt-6">
          <div className="flex items-center gap-3 mb-2">
            <FontAwesomeIcon icon={faExclamationTriangle} className="text-2xl text-red-500" />
            <h2 className="text-lg font-semibold text-red-800">Ошибка загрузки аналитики</h2>
          </div>
          <p className="text-red-700 mb-4">{error}</p>
          <div className="text-sm text-red-600">
            <p>Проверьте:</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Указан ли правильный ID команды</li>
              <li>Указаны ли ID матчей</li>
              <li>Существуют ли матчи в базе данных</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <BackButton href="/" label="← Назад к главной" />
        <div className="flex items-center justify-center py-12 mt-6">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Загрузка аналитики команды...</p>
          </div>
        </div>
      </div>
    );
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
      {/* Back Button */}
      <div>
        <BackButton href="/" label="← Назад к главной" />
      </div>
      
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
