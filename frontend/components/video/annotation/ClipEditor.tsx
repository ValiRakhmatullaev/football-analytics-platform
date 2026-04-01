"use client";

import { useState, useEffect, useCallback } from "react";
import type { ClipAction } from "@/types/annotation";
import { updateClip } from "@/services/annotationService";

/**
 * Form to adjust clip boundaries (start/end) and add a comment.
 * Saves to backend on Save; optional debounced local state.
 */

export interface ClipEditorProps {
  clip: ClipAction | null;
  duration: number;
  onClipUpdated: (updated: ClipAction) => void;
  onSetStartFromCurrent?: () => number;
  onSetEndFromCurrent?: () => number;
  className?: string;
}

export default function ClipEditor({
  clip,
  duration,
  onClipUpdated,
  onSetStartFromCurrent,
  onSetEndFromCurrent,
  className = "",
}: ClipEditorProps) {
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (clip) {
      setStart(clip.start_time_seconds);
      setEnd(clip.end_time_seconds);
      setComment(clip.description || "");
    }
  }, [clip]);

  const handleSave = useCallback(async () => {
    if (!clip) return;
    setSaving(true);
    setError(null);
    try {
      const res = await updateClip(clip.id, {
        start_time_seconds: start,
        end_time_seconds: end,
        description: comment || undefined,
      });
      onClipUpdated({
        ...clip,
        start_time_seconds: res.start_time_seconds,
        end_time_seconds: res.end_time_seconds,
        duration_seconds: res.duration_seconds,
        description: res.description ?? "",
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }, [clip, start, end, comment, onClipUpdated]);

  const setStartFromCurrent = useCallback(() => {
    if (typeof onSetStartFromCurrent === "function") {
      const t = onSetStartFromCurrent();
      setStart(Math.min(t, end - 0.1));
    }
  }, [onSetStartFromCurrent, end]);

  const setEndFromCurrent = useCallback(() => {
    if (typeof onSetEndFromCurrent === "function") {
      const t = onSetEndFromCurrent();
      setEnd(Math.max(t, start + 0.1));
    }
  }, [onSetEndFromCurrent, start]);

  if (!clip) {
    return (
      <div className={`p-4 text-gray-500 text-sm ${className}`}>
        Выберите клип в списке или на таймлайне для редактирования границ и комментария.
      </div>
    );
  }

  return (
    <div className={`border rounded-lg p-4 bg-white ${className}`}>
      <h3 className="font-semibold mb-3">Границы и комментарий</h3>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Начало (с)</label>
          <input
            type="number"
            min={0}
            max={duration}
            step={0.1}
            value={start.toFixed(2)}
            onChange={(e) => setStart(parseFloat(e.target.value) || 0)}
            className="w-full border rounded px-2 py-1.5 text-sm"
          />
          {onSetStartFromCurrent && (
            <button
              type="button"
              onClick={setStartFromCurrent}
              className="mt-1 text-xs text-blue-600 hover:underline"
            >
              От текущего кадра
            </button>
          )}
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Конец (с)</label>
          <input
            type="number"
            min={0}
            max={duration}
            step={0.1}
            value={end.toFixed(2)}
            onChange={(e) => setEnd(parseFloat(e.target.value) || duration)}
            className="w-full border rounded px-2 py-1.5 text-sm"
          />
          {onSetEndFromCurrent && (
            <button
              type="button"
              onClick={setEndFromCurrent}
              className="mt-1 text-xs text-blue-600 hover:underline"
            >
              От текущего кадра
            </button>
          )}
        </div>
      </div>
      <div className="mb-3">
        <label className="block text-xs text-gray-500 mb-1">Комментарий / заметка</label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Аналитическая заметка для обучения модели..."
          rows={3}
          className="w-full border rounded px-2 py-1.5 text-sm resize-y"
        />
      </div>
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      <button
        type="button"
        onClick={handleSave}
        disabled={saving || start >= end}
        className="px-4 py-2 rounded bg-blue-600 text-white text-sm disabled:opacity-50 hover:bg-blue-700"
      >
        {saving ? "Сохранение…" : "Сохранить"}
      </button>
    </div>
  );
}
