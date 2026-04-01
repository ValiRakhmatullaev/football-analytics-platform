"use client";

import type { ClipAction } from "@/types/annotation";

/**
 * List of actions/clips for quick navigation. Click to select and jump to that action.
 * UI only: receives clips, selectedClipId, onSelectClip, onSeek.
 */

export interface ActionListProps {
  clips: ClipAction[];
  selectedClipId: string | null;
  onSelectClip: (clip: ClipAction) => void;
  onSeek: (time: number) => void;
  className?: string;
}

const clipTypeLabels: Record<string, string> = {
  goal: "Гол",
  shot: "Удар",
  dangerous_moment: "Опасный момент",
  pass: "Пас",
  tackle: "Подкат",
  save: "Сейв",
  other: "Другое",
};

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function ActionList({
  clips,
  selectedClipId,
  onSelectClip,
  onSeek,
  className = "",
}: ActionListProps) {
  const handleSelect = (clip: ClipAction) => {
    onSelectClip(clip);
    onSeek(clip.start_time_seconds);
  };

  if (clips.length === 0) {
    return (
      <div className={`text-sm text-gray-500 p-4 ${className}`}>
        Нет клипов. Обработайте видео для автоматической нарезки.
      </div>
    );
  }

  return (
    <ul className={`space-y-1 overflow-y-auto max-h-64 ${className}`}>
      {clips.map((clip) => (
        <li key={clip.id}>
          <button
            type="button"
            onClick={() => handleSelect(clip)}
            className={`w-full text-left px-3 py-2 rounded text-sm border transition ${
              selectedClipId === clip.id
                ? "bg-blue-50 border-blue-400"
                : "bg-white border-gray-200 hover:bg-gray-50"
            }`}
          >
            <span className="font-medium">
              {clipTypeLabels[clip.clip_type] ?? clip.clip_type}
            </span>
            <span className="text-gray-500 ml-2">
              {formatTime(clip.start_time_seconds)} – {formatTime(clip.end_time_seconds)}
            </span>
            {clip.description && (
              <p className="text-gray-600 mt-1 line-clamp-2">{clip.description}</p>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}
