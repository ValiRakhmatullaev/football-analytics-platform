"use client";

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUpload, faFilm, faClipboardList, faCheck } from "@fortawesome/free-solid-svg-icons";
import { apiUrl } from "@/lib/api";

interface UploadResponse {
  id: string;
  file_name: string;
  status: string;
  file_size: number;
  uploaded_at: string;
}

interface ProcessResponse {
  status: string;
  events_count: number;
  clips_created?: number;
  events_saved_to_db: boolean;
  match_id?: string;
  analytics_available: boolean;
  clips_url?: string;
  statistics: {
    events_by_type: Record<string, number>;
    avg_confidence: number;
  };
}

export default function VideoUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [matchId, setMatchId] = useState<string>("");
  const [period, setPeriod] = useState<number>(2);
  const [offsetMs, setOffsetMs] = useState<number>(0);
  const [createMatch, setCreateMatch] = useState<boolean>(false);
  const [team1Name, setTeam1Name] = useState<string>("");
  const [team2Name, setTeam2Name] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = useCallback((newFile: File | null) => {
    if (newFile) {
      setFile(newFile);
      setError(null);
    }
  }, []);

  const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) handleFileChange(e.target.files[0]);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!uploading && !processing) setIsDragging(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (uploading || processing) return;
    const f = e.dataTransfer.files?.[0];
    if (f?.type.startsWith("video/")) handleFileChange(f);
    else setError("Выберите видеофайл (MP4, MOV, MKV и т.д.)");
  };

  const handleUpload = useCallback(async () => {
    if (!file) {
      setError("Пожалуйста, выберите файл");
      return;
    }
    if (createMatch && (!team1Name.trim() || !team2Name.trim())) {
      setError("Укажите названия обеих команд для создания матча");
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("video", file);
    if (matchId) formData.append("match_id", matchId);
    if (period) formData.append("period", period.toString());
    if (offsetMs) formData.append("video_start_offset_ms", offsetMs.toString());
    if (createMatch) {
      formData.append("create_match", "true");
      formData.append("team1_name", team1Name.trim());
      formData.append("team2_name", team2Name.trim());
    }

    try {
      const response = await fetch(apiUrl("/api/analytics/videos/upload/"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data: UploadResponse = await response.json();
      setUploadId(data.id);
      setStatus(data.status);
      setUploading(false);
      handleProcess(data.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploading(false);
    }
  }, [file, matchId, period, offsetMs, createMatch, team1Name, team2Name]);

  const handleProcess = useCallback(async (videoId: string) => {
    setProcessing(true);
    setError(null);

    try {
      const response = await fetch(
        apiUrl(`/api/analytics/videos/${videoId}/process/`),
        { method: "POST" }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data: ProcessResponse = await response.json();
      setStatus("completed");
      setProcessing(false);

      if (data.clips_created && data.clips_created > 0) {
        setStatus(`Готово: ${data.events_count} событий, ${data.clips_created} клипов`);
      } else {
        setStatus(`Готово: обнаружено ${data.events_count} событий`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
      setProcessing(false);
    }
  }, []);

  const isBusy = uploading || processing;
  const isSuccess = status && (status.includes("completed") || status.includes("Готово"));

  return (
    <div className="space-y-6">
      {/* Header */}
      <header
        className="animate-fade-in-up"
        style={{ animationDelay: "50ms" }}
      >
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
          Загрузка видео
        </h1>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          Загрузите запись матча для анализа событий и создания клипов
        </p>
      </header>

      {/* Drop zone */}
      <div
        className="animate-fade-in-up"
        style={{ animationDelay: "100ms" }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          onChange={onFileInputChange}
          className="hidden"
          disabled={isBusy}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          disabled={isBusy}
          className={`
            w-full rounded-2xl border-2 border-dashed transition-all duration-300
            flex flex-col items-center justify-center gap-3 py-10 px-6
            ${isDragging
              ? "border-emerald-500 bg-emerald-500/10 scale-[1.02] animate-drop-zone-glow"
              : file
              ? "border-emerald-400/60 bg-emerald-500/5"
              : "border-slate-300 dark:border-slate-600 bg-slate-50/80 dark:bg-slate-800/50 hover:border-emerald-400/50 hover:bg-emerald-500/5"
            }
            ${isBusy ? "pointer-events-none opacity-80" : "cursor-pointer"}
          `}
        >
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl transition-transform duration-300 ${isDragging ? "scale-110" : ""}`}
               style={{ background: "rgba(5, 150, 105, 0.15)" }}>
            <FontAwesomeIcon icon={faUpload} className="text-emerald-600" />
          </div>
          {file ? (
            <div className="text-center">
              <p className="font-semibold text-slate-900 dark:text-white">
                {file.name}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                {(file.size / 1024 / 1024).toFixed(2)} MB · Нажмите или перетащите другой файл
              </p>
            </div>
          ) : (
            <div className="text-center">
              <p className="font-medium text-slate-700 dark:text-slate-300">
                Перетащите видео сюда или нажмите для выбора
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                MP4, AVI, MOV, MKV, WebM · до 2 GB
              </p>
            </div>
          )}
        </button>
      </div>

      {/* Options card */}
      <section
        className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm p-5 sm:p-6 space-y-4 animate-fade-in-up shadow-sm"
        style={{ animationDelay: "150ms" }}
      >
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Параметры
        </h3>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={createMatch}
            onChange={(e) => setCreateMatch(e.target.checked)}
            className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
            disabled={isBusy}
          />
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Создать матч автоматически
          </span>
        </label>

        {createMatch ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Команда 1 *
              </label>
              <input
                type="text"
                value={team1Name}
                onChange={(e) => setTeam1Name(e.target.value)}
                placeholder="Хозяева"
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                disabled={isBusy}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Команда 2 *
              </label>
              <input
                type="text"
                value={team2Name}
                onChange={(e) => setTeam2Name(e.target.value)}
                placeholder="Гости"
                className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                disabled={isBusy}
              />
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              ID матча (UUID)
            </label>
            <input
              type="text"
              value={matchId}
              onChange={(e) => setMatchId(e.target.value)}
              placeholder="Необязательно: привязать к существующему матчу"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
              disabled={isBusy}
            />
            <p className="text-xs text-slate-500 mt-1.5">
              Оставьте пустым и включите «Создать матч» для автосоздания
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Тайм
            </label>
            <select
              value={period}
              onChange={(e) => setPeriod(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 transition"
              disabled={isBusy}
            >
              <option value={1}>1-й тайм</option>
              <option value={2}>2-й тайм</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Смещение начала (мс)
            </label>
            <input
              type="number"
              value={offsetMs}
              onChange={(e) => setOffsetMs(Number(e.target.value))}
              placeholder="0"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 transition"
              disabled={isBusy}
            />
            <p className="text-xs text-slate-500 mt-1.5">например 3600000 для 60:00</p>
          </div>
        </div>
      </section>

      {/* Progress / status */}
      {isBusy && (
        <div
          className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6 animate-scale-in"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-emerald-500/40 border-t-emerald-500 rounded-full animate-spin" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-slate-900 dark:text-white">
                {uploading ? "Загрузка на сервер…" : "Обработка видео…"}
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5 animate-pulse-soft">
                {uploading ? "Не закрывайте страницу" : "Детекция событий и создание клипов"}
              </p>
            </div>
          </div>
          <div className="mt-4 h-1.5 rounded-full bg-emerald-500/20 overflow-hidden">
            <div className="h-full w-1/3 rounded-full bg-emerald-500 animate-progress-bar" />
          </div>
        </div>
      )}

      {/* Success */}
      {isSuccess && uploadId && !isBusy && (
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6 animate-scale-in space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center text-2xl animate-scale-in">
              ✓
            </div>
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">Готово</p>
              <p className="text-sm text-slate-600 dark:text-slate-400">{status}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              href={`/videos/${uploadId}/clips`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium shadow-lg shadow-emerald-500/25 transition-all duration-200 btn-press"
            >
              <FontAwesomeIcon icon={faFilm} />
              <span>Просмотреть клипы</span>
              <span>→</span>
            </Link>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700/50 transition"
            >
              <FontAwesomeIcon icon={faClipboardList} />
              <span>Все матчи</span>
            </Link>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-2xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/20 p-4 animate-fade-in-up">
          <p className="text-sm font-medium text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Upload button */}
      <div
        className="animate-fade-in-up"
        style={{ animationDelay: "200ms" }}
      >
        <button
          onClick={handleUpload}
          disabled={!file || isBusy}
          className="w-full px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-400 disabled:cursor-not-allowed text-white font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/30 transition-all duration-200 btn-press"
        >
          {uploading ? "Загрузка…" : processing ? "Обработка…" : "Загрузить и обработать"}
        </button>
      </div>

      {/* Hint */}
      <p className="text-sm text-slate-500 dark:text-slate-400 text-center animate-fade-in-up" style={{ animationDelay: "250ms" }}>
        Обработка может занять несколько минут в зависимости от длительности видео
      </p>
    </div>
  );
}
