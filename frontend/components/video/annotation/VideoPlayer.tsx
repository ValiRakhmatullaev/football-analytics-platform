"use client";

import { useRef, useEffect, useCallback } from "react";

/**
 * Video player with frame-by-frame navigation and controlled currentTime.
 * UI only: receives src, currentTime, onTimeChange, onDuration; no persistence.
 */

export interface VideoPlayerProps {
  src: string;
  currentTime: number;
  onTimeChange: (time: number) => void;
  onDuration?: (duration: number) => void;
  playing: boolean;
  onPlayingChange: (playing: boolean) => void;
  /** FPS for frame step (e.g. 25). */
  fps?: number;
  className?: string;
}

export default function VideoPlayer({
  src,
  currentTime,
  onTimeChange,
  onDuration,
  playing,
  onPlayingChange,
  fps = 25,
  className = "",
}: VideoPlayerProps) {
  const ref = useRef<HTMLVideoElement>(null);
  const frameStep = 1 / fps;

  // Sync external currentTime to video element when not playing
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (Math.abs(el.currentTime - currentTime) > 0.05) {
      el.currentTime = currentTime;
    }
  }, [currentTime]);

  const handleTimeUpdate = useCallback(() => {
    if (ref.current) onTimeChange(ref.current.currentTime);
  }, [onTimeChange]);

  const handleLoadedMetadata = useCallback(() => {
    if (ref.current && onDuration) onDuration(ref.current.duration);
  }, [onDuration]);

  const handlePlay = useCallback(() => onPlayingChange(true), [onPlayingChange]);
  const handlePause = useCallback(() => onPlayingChange(false), [onPlayingChange]);

  const stepBack = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.currentTime = Math.max(0, el.currentTime - frameStep);
    onTimeChange(el.currentTime);
  }, [frameStep, onTimeChange]);

  const stepForward = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.currentTime = Math.min(el.duration, el.currentTime + frameStep);
    onTimeChange(el.currentTime);
  }, [frameStep, onTimeChange]);

  const togglePlay = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    if (el.paused) el.play();
    else el.pause();
  }, []);

  return (
    <div className={`flex flex-col ${className}`}>
      <video
        ref={ref}
        src={src}
        className="w-full rounded-lg bg-black"
        playsInline
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={handlePlay}
        onPause={handlePause}
        onSeeked={() => ref.current && onTimeChange(ref.current.currentTime)}
      />
      <div className="flex items-center gap-2 mt-2">
        <button
          type="button"
          onClick={stepBack}
          className="px-3 py-1.5 rounded bg-gray-200 hover:bg-gray-300 text-sm"
          title="Previous frame"
        >
          −1 frame
        </button>
        <button
          type="button"
          onClick={togglePlay}
          className="px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm"
        >
          {playing ? "Pause" : "Play"}
        </button>
        <button
          type="button"
          onClick={stepForward}
          className="px-3 py-1.5 rounded bg-gray-200 hover:bg-gray-300 text-sm"
          title="Next frame"
        >
          +1 frame
        </button>
      </div>
    </div>
  );
}
