"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { fetchAnnotationData, sourceVideoUrl } from "@/services/annotationService";
import type { AnnotationData, ClipAction, VideoOverlay } from "@/types/annotation";
import Timeline from "./Timeline";
import ActionList from "./ActionList";
import ClipEditor from "./ClipEditor";
import { DrawingCanvasProvider, DrawingCanvasOverlay, DrawingCanvasToolbar } from "./DrawingCanvas";

/**
 * Interactive video annotation and clipping player.
 * Orchestrates: video logic (playback, currentTime), UI (timeline, list, editor), data (load, save, export).
 * Architecture: state in container; children are presentational + callbacks.
 */

export interface VideoAnnotationPlayerProps {
  videoId: string;
  className?: string;
}

export default function VideoAnnotationPlayer({ videoId, className = "" }: VideoAnnotationPlayerProps) {
  const [data, setData] = useState<AnnotationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedClip, setSelectedClip] = useState<ClipAction | null>(null);
  const [previewingTrim, setPreviewingTrim] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchAnnotationData(videoId)
      .then((d) => {
        if (!cancelled) {
          setData({ ...d, overlays: d.overlays ?? [] });
          setDuration(d.video.duration_seconds || 0);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [videoId]);

  const handleClipUpdated = useCallback((updated: ClipAction) => {
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        clips: prev.clips.map((c) => (c.id === updated.id ? updated : c)),
      };
    });
    setSelectedClip((prev) => (prev?.id === updated.id ? updated : prev));
  }, []);

  const handleOverlaysChange = useCallback((overlays: VideoOverlay[]) => {
    setData((prev) => (prev ? { ...prev, overlays } : prev));
  }, []);

  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time);
  }, []);

  const handleDuration = useCallback((d: number) => {
    setDuration(d);
  }, []);

  // Trim preview: play from clip.start until clip.end then pause
  useEffect(() => {
    if (!previewingTrim || !selectedClip || !videoRef.current) return;
    const video = videoRef.current;
    const start = selectedClip.start_time_seconds;
    const end = selectedClip.end_time_seconds;

    const onTimeUpdate = () => {
      if (video.currentTime >= end - 0.05) {
        video.pause();
        setPlaying(false);
        setPreviewingTrim(false);
        video.removeEventListener("timeupdate", onTimeUpdate);
      }
    };
    video.currentTime = start;
    video.addEventListener("timeupdate", onTimeUpdate);
    video.play();
    setPlaying(true);
    return () => {
      video.removeEventListener("timeupdate", onTimeUpdate);
    };
  }, [previewingTrim, selectedClip?.id]);

  const getCurrentTime = useCallback(() => currentTime, [currentTime]);

  const seekTo = useCallback((t: number) => {
    const el = videoRef.current;
    if (el) el.currentTime = Math.max(0, Math.min(el.duration || 0, t));
    setCurrentTime(t);
  }, []);

  const sourceUrl = sourceVideoUrl(videoId);
  const eventTimestampsMs = (data?.events ?? []).map((e) => e.timestamp_ms).filter((ms): ms is number => typeof ms === "number");

  if (loading) {
    return (
      <div className={`p-8 text-center ${className}`}>
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <p className="mt-2 text-gray-600">Загрузка данных аннотации…</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={`p-6 bg-red-50 rounded-lg ${className}`}>
        <p className="text-red-800">{error ?? "Нет данных"}</p>
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 ${className}`}>
      {/* Left: video + timeline + trim preview */}
      <div className="lg:col-span-2 space-y-4">
        <div className="bg-gray-900 rounded-lg p-2">
          <DrawingCanvasProvider
            videoId={videoId}
            videoWidth={data.video.width || 640}
            videoHeight={data.video.height || 360}
            currentTime={currentTime}
            overlays={data.overlays}
            onOverlaysChange={handleOverlaysChange}
          >
            <div className="flex flex-col gap-3">
              <div
                className="relative rounded overflow-hidden"
                style={{
                  aspectRatio:
                    data.video.width && data.video.height
                      ? `${data.video.width}/${data.video.height}`
                      : "16/9",
                }}
              >
                <video
                  ref={videoRef}
                  src={sourceUrl}
                  className="absolute inset-0 w-full h-full object-contain rounded"
                  playsInline
                  onTimeUpdate={(e) => setCurrentTime((e.target as HTMLVideoElement).currentTime)}
                  onLoadedMetadata={(e) => {
                    const d = (e.target as HTMLVideoElement).duration;
                    setDuration(d);
                    handleDuration(d);
                  }}
                  onPlay={() => setPlaying(true)}
                  onPause={() => setPlaying(false)}
                />
                <div className="absolute inset-0 flex flex-col">
                  <DrawingCanvasOverlay className="flex-1 min-h-0" />
                </div>
              </div>
              <DrawingCanvasToolbar />
            </div>
          </DrawingCanvasProvider>
          <VideoControls
            videoRef={videoRef}
            currentTime={currentTime}
            onTimeChange={setCurrentTime}
            playing={playing}
            onPlayingChange={setPlaying}
            fps={25}
            className="mt-2"
          />
        </div>
        <Timeline
          duration={duration}
          currentTime={currentTime}
          clips={data.clips}
          selectedClipId={selectedClip?.id ?? null}
          onSeek={seekTo}
          onSelectClip={setSelectedClip}
          eventTimestampsMs={eventTimestampsMs}
        />
        {selectedClip && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPreviewingTrim(true)}
              className="px-4 py-2 rounded bg-green-600 text-white text-sm hover:bg-green-700"
            >
              Предпросмотр нарезки
            </button>
            <span className="text-sm text-gray-500">
              Воспроизведение с {selectedClip.start_time_seconds.toFixed(1)}с по {selectedClip.end_time_seconds.toFixed(1)}с
            </span>
          </div>
        )}
      </div>

      {/* Right: action list + clip editor + export */}
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold mb-2">Действия / клипы</h3>
          <ActionList
            clips={data.clips}
            selectedClipId={selectedClip?.id ?? null}
            onSelectClip={setSelectedClip}
            onSeek={seekTo}
          />
        </div>
        <ClipEditor
          clip={selectedClip}
          duration={duration}
          onClipUpdated={handleClipUpdated}
          onSetStartFromCurrent={getCurrentTime}
          onSetEndFromCurrent={getCurrentTime}
        />
        <ExportButton videoId={videoId} />
      </div>
    </div>
  );
}

/** Frame-by-frame and play/pause controls; operates on parent's video ref. */
function VideoControls({
  videoRef,
  currentTime,
  onTimeChange,
  playing,
  onPlayingChange,
  fps = 25,
  className = "",
}: {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  currentTime: number;
  onTimeChange: (t: number) => void;
  playing: boolean;
  onPlayingChange: (p: boolean) => void;
  fps?: number;
  className?: string;
}) {
  const frameStep = 1 / fps;
  const stepBack = () => {
    const el = videoRef.current;
    if (!el) return;
    el.currentTime = Math.max(0, el.currentTime - frameStep);
    onTimeChange(el.currentTime);
  };
  const stepForward = () => {
    const el = videoRef.current;
    if (!el) return;
    el.currentTime = Math.min(el.duration, el.currentTime + frameStep);
    onTimeChange(el.currentTime);
  };
  const togglePlay = () => {
    const el = videoRef.current;
    if (!el) return;
    if (el.paused) el.play();
    else el.pause();
    onPlayingChange(!el.paused);
  };
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <button type="button" onClick={stepBack} className="px-3 py-1.5 rounded bg-gray-200 hover:bg-gray-300 text-sm">
        −1 frame
      </button>
      <button type="button" onClick={togglePlay} className="px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm">
        {playing ? "Pause" : "Play"}
      </button>
      <button type="button" onClick={stepForward} className="px-3 py-1.5 rounded bg-gray-200 hover:bg-gray-300 text-sm">
        +1 frame
      </button>
    </div>
  );
}

function ExportButton({ videoId }: { videoId: string }) {
  const [exporting, setExporting] = useState(false);
  const handleExport = async () => {
    setExporting(true);
    try {
      const { exportAnnotations } = await import("@/services/annotationService");
      const blob = await exportAnnotations(videoId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `annotations_${videoId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };
  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={exporting}
      className="w-full px-4 py-2 rounded border border-gray-300 bg-white text-sm hover:bg-gray-50 disabled:opacity-50"
    >
      {exporting ? "Экспорт…" : "Скачать аннотации (JSON)"}
    </button>
  );
}
