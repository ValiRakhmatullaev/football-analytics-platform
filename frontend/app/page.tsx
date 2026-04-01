"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { ActionButtons } from "@/components/navigation/ActionButtons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUpload, faClipboardList, faFutbol, faClock, faChartBar, faCheckCircle, faFilm, faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { apiUrl } from "@/lib/api";

interface MatchTeam {
  id: string;
  name: string;
  side: string;
}

interface Match {
  id: string;
  kickoff_time: string | null;
  status: string;
  video_count?: number;
  events_count?: number;
  analytics_available?: boolean;
  teams?: MatchTeam[];
}

export default function HomePage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (loading) return;

    setLoading(true);
    setError(null);
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    fetch(apiUrl("/api/analytics/matches/"), { signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!signal.aborted) {
          setMatches(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        if (!signal.aborted) {
          console.error(err);
          setError("Не удалось загрузить матчи");
        }
      })
      .finally(() => {
        if (!signal.aborted) setLoading(false);
      });

    return () => {
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, []);

  const actionButtons = [
    {
      href: "/upload",
      label: "Загрузить видео",
      description: "Загрузить видео матча для анализа",
      icon: "fa-upload",
      color: "blue" as const,
      size: "lg" as const,
    },
  ];

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-12 h-12 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin" />
          <p className="mt-4 text-slate-600 dark:text-slate-400">Загрузка матчей...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="w-16 h-16 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-2xl mx-auto mb-4">
            <FontAwesomeIcon icon={faExclamationTriangle} className="text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">Ошибка загрузки</h2>
          <p className="text-slate-600 dark:text-slate-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-10 lg:py-14">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Hero */}
        <header className="text-center space-y-5">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-sm font-medium mb-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Аналитика матчей в реальном времени
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 dark:text-white">
            <span className="gradient-text">Football Analytics</span>
            <br />
            <span className="text-slate-600 dark:text-slate-300 font-normal text-2xl sm:text-3xl mt-2 block">
              Платформа для анализа футбольных матчей
            </span>
          </h1>
          <p className="text-slate-600 dark:text-slate-400 text-lg max-w-xl mx-auto">
            Загружайте видео, получайте события, владение и статистику по игрокам.
          </p>
        </header>

        {/* CTA */}
        <div className="max-w-xl mx-auto">
          <ActionButtons buttons={actionButtons} columns={1} />
        </div>

        {/* Matches */}
        <section className="max-w-5xl mx-auto">
          <div className="rounded-2xl border border-slate-200/80 dark:border-slate-700/80 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-xl shadow-slate-200/50 dark:shadow-none p-6 sm:p-8">
            <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                <span className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-lg">
                  <FontAwesomeIcon icon={faClipboardList} className="text-slate-600 dark:text-slate-300" />
                </span>
                Матчи
              </h2>
              <span className="px-4 py-2 rounded-full bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 text-sm font-semibold">
                {matches.length} матчей
              </span>
            </div>

            {matches.length === 0 ? (
              <div className="text-center py-16">
                <div className="w-20 h-20 rounded-2xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-4xl mx-auto mb-5">
                  <FontAwesomeIcon icon={faFutbol} className="text-slate-400" />
                </div>
                <p className="text-slate-600 dark:text-slate-400 text-lg mb-6">
                  Нет доступных матчей
                </p>
                <Link
                  href="/upload"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/30 transition-all duration-200 btn-press"
                >
                  <FontAwesomeIcon icon={faUpload} />
                  <span>Загрузить первое видео</span>
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {matches.map((match) => (
                  <article
                    key={match.id}
                    className="rounded-xl border border-slate-200 dark:border-slate-600/50 bg-white dark:bg-slate-800/50 p-5 card-hover shadow-sm hover:shadow-md"
                  >
                    <Link href={`/matches/${match.id}`} className="block">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                            Матч
                          </p>
                          <p className="text-lg font-bold text-slate-900 dark:text-white truncate">
                            {match.id.slice(0, 8)}…
                          </p>
                        </div>
                        <span className="shrink-0 px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
                          {match.status}
                        </span>
                      </div>

                      <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
                        {match.teams && match.teams.length >= 2 && (
                          <p className="font-semibold text-slate-800 dark:text-slate-200">
                            {match.teams.find((t) => t.side === "home")?.name}{" "}
                            <span className="text-slate-400 font-normal">vs</span>{" "}
                            {match.teams.find((t) => t.side === "away")?.name}
                          </p>
                        )}
                        {match.kickoff_time && (
                          <div className="flex items-center gap-2">
                            <FontAwesomeIcon icon={faClock} className="text-slate-400" />
                            <span>
                              {new Date(match.kickoff_time).toLocaleString("ru-RU", {
                                day: "2-digit",
                                month: "2-digit",
                                year: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                        )}
                        {match.events_count !== undefined && (
                          <div className="flex items-center gap-2">
                            <FontAwesomeIcon icon={faChartBar} className="text-slate-400" />
                            <span>{match.events_count} событий</span>
                          </div>
                        )}
                        {match.analytics_available && (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 text-xs font-medium">
                            <FontAwesomeIcon icon={faCheckCircle} className="mr-1" /> Аналитика доступна
                          </span>
                        )}
                      </div>
                    </Link>

                    <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-600/50 flex flex-wrap items-center gap-2">
                      <Link
                        href={`/matches/${match.id}`}
                        className="inline-flex items-center text-emerald-600 dark:text-emerald-400 text-sm font-semibold hover:underline"
                      >
                        Открыть матч →
                      </Link>
                      <Link
                        href={`/matches/${match.id}/clips`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/15 text-amber-700 dark:text-amber-400 text-sm font-medium hover:bg-amber-500/25 transition"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <FontAwesomeIcon icon={faFilm} />
                        <span>Клипы</span>
                      </Link>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
