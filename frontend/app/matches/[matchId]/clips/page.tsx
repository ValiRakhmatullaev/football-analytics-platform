"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiUrl } from "@/lib/api";
import { BackButton } from "@/components/navigation/BackButton";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFilm } from "@fortawesome/free-solid-svg-icons";

interface MatchVideo {
  id: string;
  file_name: string;
  status: string;
  duration_seconds: number | null;
  events_count: number;
  uploaded_at: string | null;
}

interface MatchVideosResponse {
  match_id: string;
  videos: MatchVideo[];
  total: number;
}

export default function MatchClipsPage() {
  const params = useParams<{ matchId: string }>();
  const matchId = params.matchId;
  const [data, setData] = useState<MatchVideosResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!matchId) return;
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();
    const signal = abortRef.current.signal;
    setLoading(true);
    setError(null);

    fetch(apiUrl(`/api/analytics/matches/${matchId}/videos/`), { signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: MatchVideosResponse) => {
        if (!signal.aborted) setData(json);
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        setError("Не удалось загрузить видео матча");
      })
      .finally(() => {
        if (!signal.aborted) setLoading(false);
      });
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, [matchId]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <BackButton href={`/matches/${matchId}`} label="← К матчу" />
          <p className="mt-4 text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          <p className="mt-4 text-gray-600">Загрузка видео матча...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
          <BackButton href={`/matches/${matchId}`} label="← К матчу" />
        </div>

        <div className="bg-white rounded-2xl shadow border border-gray-200 p-6">
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">
            Просмотр и редактирование клипов
          </h1>
          <p className="text-gray-600 mb-6">
            Выберите видео матча, чтобы просмотреть нарезки или отредактировать клипы и аннотации.
          </p>

          {data.videos.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-gray-300 rounded-xl">
              <div className="text-5xl mb-3"><FontAwesomeIcon icon={faFilm} className="text-gray-400" /></div>
              <p className="text-gray-600 mb-2">Нет обработанных видео для этого матча</p>
              <p className="text-sm text-gray-500">
                Загрузите видео матча и дождитесь завершения обработки.
              </p>
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Загрузить видео
              </Link>
            </div>
          ) : (
            <ul className="space-y-4">
              {data.videos.map((video) => (
                <li
                  key={video.id}
                  className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-gray-200 bg-gray-50/50 hover:bg-gray-50 transition"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-gray-900 truncate">{video.file_name}</div>
                    <div className="flex flex-wrap gap-3 mt-1 text-sm text-gray-500">
                      {video.duration_seconds != null && (
                        <span>
                          {Math.floor(video.duration_seconds / 60)}:
                          {String(Math.floor(video.duration_seconds % 60)).padStart(2, "0")}
                        </span>
                      )}
                      <span>{video.events_count} событий</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Link
                      href={`/videos/${video.id}/clips`}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition"
                    >
                      <span>Просмотр клипов</span>
                      <span>→</span>
                    </Link>
                    <Link
                      href={`/videos/${video.id}/annotate`}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-amber-500 text-amber-700 bg-amber-50 text-sm font-medium hover:bg-amber-100 transition"
                    >
                      Аннотация и нарезка
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
