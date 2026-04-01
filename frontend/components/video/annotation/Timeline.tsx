"use client";

import { useCallback } from "react";
import type { ClipAction } from "@/types/annotation";

/**
 * Visual timeline with action markers. Click to seek; optional segment bars for clips.
 * UI only: receives duration, currentTime, clips, selectedClipId, onSeek, onSelectClip.
 */

export interface TimelineProps {
  duration: number;
  currentTime: number;
  clips: ClipAction[];
  selectedClipId: string | null;
  onSeek: (time: number) => void;
  onSelectClip: (clip: ClipAction | null) => void;
  /** Raw event timestamps (ms) for small markers. */
  eventTimestampsMs?: number[];
  className?: string;
}

function clipTypeColor(type: string): string {
  const colors: Record<string, string> = {
    goal: "bg-green-500",
    shot: "bg-red-500",
    dangerous_moment: "bg-orange-500",
    pass: "bg-blue-500",
    save: "bg-yellow-500",
    other: "bg-gray-500",
  };
  return colors[type] || colors.other;
}

export default function Timeline({
  duration,
  currentTime,
  clips,
  selectedClipId,
  onSeek,
  onSelectClip,
  eventTimestampsMs = [],
  className = "",
}: TimelineProps) {
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (duration <= 0) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const t = (x / rect.width) * duration;
      onSeek(Math.max(0, Math.min(duration, t)));
    },
    [duration, onSeek]
  );

  if (duration <= 0) {
    return (
      <div className={`h-14 bg-gray-100 rounded ${className}`}>
        <div className="p-2 text-sm text-gray-500">Load video for timeline</div>
      </div>
    );
  }

  const progressPercent = (currentTime / duration) * 100;

  return (
    <div className={`${className}`}>
      <div className="text-xs text-gray-500 mb-1">
        Timeline · {currentTime.toFixed(1)}s / {duration.toFixed(1)}s
      </div>
      <div
        className="relative h-12 bg-gray-200 rounded cursor-pointer overflow-hidden"
        onClick={handleClick}
        role="slider"
        aria-valuenow={currentTime}
        aria-valuemin={0}
        aria-valuemax={duration}
      >
        {/* Clip segments */}
        {clips.map((clip) => {
          const left = (clip.start_time_seconds / duration) * 100;
          const width = ((clip.end_time_seconds - clip.start_time_seconds) / duration) * 100;
          const isSelected = clip.id === selectedClipId;
          return (
            <div
              key={clip.id}
              className={`absolute top-1 bottom-1 rounded ${clipTypeColor(clip.clip_type)} opacity-70 ${
                isSelected ? "ring-2 ring-black" : ""
              }`}
              style={{ left: `${left}%`, width: `${Math.max(1, width)}%` }}
              title={`${clip.clip_type} ${clip.start_time_seconds.toFixed(1)}–${clip.end_time_seconds.toFixed(1)}s`}
              onClick={(e) => {
                e.stopPropagation();
                onSelectClip(clip);
                onSeek(clip.start_time_seconds);
              }}
            />
          );
        })}
        {/* Raw event markers (dots) */}
        {eventTimestampsMs.map((ms, index) => {
          const t = ms / 1000;
          if (t < 0 || t > duration) return null;
          const left = (t / duration) * 100;
          return (
            <div
              key={`event-${index}-${ms}`}
              className="absolute top-1/2 w-1 h-1 -translate-y-1/2 bg-gray-800 rounded-full"
              style={{ left: `${left}%` }}
              title={`${t.toFixed(1)}s`}
              onClick={(e) => {
                e.stopPropagation();
                onSeek(t);
              }}
            />
          );
        })}
        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-600 pointer-events-none"
          style={{ left: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
}
