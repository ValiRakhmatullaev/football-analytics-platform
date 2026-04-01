"use client";

import { useState, useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFutbol, faBullseye, faExclamationTriangle, faUpload, faShieldAlt, faHandPaper, faBolt, faCircle, faSquare, faVideo } from "@fortawesome/free-solid-svg-icons";
import { apiUrl } from "@/lib/api";

interface VideoClip {
  id: string;
  clip_type: string;
  title: string;
  description?: string;
  duration_seconds: number;
  timestamp_ms: number;
  confidence: number;
  thumbnail_url: string | null;
  video_url: string;
  created_at: string;
}

interface ClipsResponse {
  video_id: string;
  video_name: string;
  total_clips: number;
  clips: VideoClip[];
}

interface VideoClipsViewerProps {
  videoId: string;
}

export default function VideoClipsViewer({ videoId }: VideoClipsViewerProps) {
  const [clips, setClips] = useState<VideoClip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedClip, setSelectedClip] = useState<VideoClip | null>(null);
  const [filterType, setFilterType] = useState<string>("all");
  const [videoError, setVideoError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!videoId) return;

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

    const url =
      filterType === "all"
        ? apiUrl(`/api/analytics/videos/${videoId}/clips/`)
        : apiUrl(`/api/analytics/videos/${videoId}/clips/?type=${filterType}`);

    fetch(url, { signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((data: VideoClip[] | ClipsResponse) => {
        if (!signal.aborted) {
          // API returns array directly, not wrapped in object
          const clipsArray = Array.isArray(data) ? data : data.clips || [];
          setClips(clipsArray);
          setError(null);
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') {
          return; // Request was aborted
        }
        if (!signal.aborted) {
          setError(err instanceof Error ? err.message : "Failed to load clips");
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
  }, [videoId, filterType]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const formatTimestamp = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  const getClipTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      goal: "Гол",
      shot: "Удар",
      dangerous_moment: "Опасный момент",
      pass: "Ключевой пас",
      tackle: "Подкат",
      save: "Сейв",
      free_kick: "Штрафной",
      penalty: "Пенальти",
      corner: "Угловой",
      other: "Другое",
    };
    return labels[type] || type;
  };

  const getClipTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      goal: "bg-green-100 text-green-800 border-green-300",
      shot: "bg-red-100 text-red-800 border-red-300",
      dangerous_moment: "bg-orange-100 text-orange-800 border-orange-300",
      pass: "bg-blue-100 text-blue-800 border-blue-300",
      tackle: "bg-purple-100 text-purple-800 border-purple-300",
      save: "bg-yellow-100 text-yellow-800 border-yellow-300",
      other: "bg-gray-100 text-gray-800 border-gray-300",
    };
    return colors[type] || colors.other;
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">Загрузка клипов...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 rounded-md">
        <p className="text-red-800">Ошибка: {error}</p>
      </div>
    );
  }

  if (clips.length === 0) {
    return (
      <div className="p-6 text-center text-gray-600">
        <p>Клипы не найдены</p>
        <p className="text-sm mt-2">
          Клипы создаются автоматически при обработке видео
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with filter */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold">Видео клипы</h2>
        <div className="flex gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Все типы</option>
            <option value="goal">Голы</option>
            <option value="shot">Удары</option>
            <option value="dangerous_moment">Опасные моменты</option>
            <option value="pass">Ключевые пасы</option>
            <option value="free_kick">Штрафные</option>
            <option value="penalty">Пенальти</option>
            <option value="corner">Угловые</option>
          </select>
        </div>
      </div>

      {/* Selected clip player */}
      {selectedClip && (
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-white font-semibold">{selectedClip.title}</h3>
            <button
              onClick={() => {
                setSelectedClip(null);
                setVideoError(null);
              }}
              className="text-white hover:text-gray-300"
            >
              ✕
            </button>
          </div>
          {videoError && (
            <div className="mb-2 p-2 bg-red-900 text-red-100 rounded text-sm">
              {videoError}
            </div>
          )}
          <video
            controls
            className="w-full rounded"
            src={apiUrl(selectedClip.video_url)}
            onError={(e) => {
              const target = e.target as HTMLVideoElement;
              const error = target.error;
              let errorMsg = "Ошибка загрузки видео";
              if (error) {
                switch (error.code) {
                  case error.MEDIA_ERR_ABORTED:
                    errorMsg = "Загрузка видео прервана";
                    break;
                  case error.MEDIA_ERR_NETWORK:
                    errorMsg = "Ошибка сети при загрузке видео";
                    break;
                  case error.MEDIA_ERR_DECODE:
                    errorMsg = "Ошибка декодирования видео";
                    break;
                  case error.MEDIA_ERR_SRC_NOT_SUPPORTED:
                    errorMsg = "Формат видео не поддерживается";
                    break;
                  default:
                    errorMsg = `Ошибка видео: ${error.message || "Неизвестная ошибка"}`;
                }
              }
              console.error("Video load error:", error, e);
              setVideoError(errorMsg);
            }}
            onLoadStart={() => setVideoError(null)}
            onCanPlay={() => setVideoError(null)}
            onLoadedMetadata={() => setVideoError(null)}
            preload="metadata"
            playsInline
            muted={false}
          >
            Ваш браузер не поддерживает видео.
          </video>
          {selectedClip.description && (
            <p className="text-gray-400 text-sm mt-2">{selectedClip.description}</p>
          )}
        </div>
      )}

      {/* Clips grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clips.map((clip) => (
          <div
            key={clip.id}
            className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition cursor-pointer"
            onClick={() => setSelectedClip(clip)}
          >
            {/* Thumbnail */}
            <div className="relative bg-gray-100 aspect-video">
              {clip.thumbnail_url ? (
                <img
                  src={apiUrl(clip.thumbnail_url)}
                  alt={clip.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <svg
                    className="w-16 h-16"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                </div>
              )}
              {/* Play button overlay */}
              <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-30 transition">
                <div className="bg-white bg-opacity-90 rounded-full p-4">
                  <svg
                    className="w-8 h-8 text-blue-600"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
              {/* Duration badge */}
              <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                {formatTime(clip.duration_seconds)}
              </div>
            </div>

            {/* Clip info */}
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded border ${getClipTypeColor(
                    clip.clip_type
                  )}`}
                >
                  {getClipTypeLabel(clip.clip_type)}
                </span>
                <span className="text-xs text-gray-500">
                  {formatTimestamp(clip.timestamp_ms)}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{clip.title}</h3>
              {clip.description && (
                <p className="text-sm text-gray-600 line-clamp-2">{clip.description}</p>
              )}
              <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                <span>Уверенность: {(clip.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="text-center text-gray-600 text-sm">
        Показано {clips.length} клипов
      </div>
    </div>
  );
}
