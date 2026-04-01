/**
 * Data persistence for annotation: fetch annotation data, update clip, overlays, export.
 * Keeps UI free of API details.
 */

import { apiUrl } from "@/lib/api";
import type { AnnotationData, ClipUpdatePayload, VideoOverlay } from "@/types/annotation";

export async function fetchAnnotationData(videoId: string): Promise<AnnotationData> {
  const res = await fetch(apiUrl(`/api/analytics/videos/${videoId}/annotation-data/`));
  if (!res.ok) throw new Error(`Failed to load annotation data: ${res.status}`);
  return res.json();
}

export async function updateClip(
  clipId: string,
  payload: ClipUpdatePayload
): Promise<{ start_time_seconds: number; end_time_seconds: number; duration_seconds: number; description: string | null }> {
  const res = await fetch(apiUrl(`/api/analytics/clips/${clipId}/`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || `Failed to update clip: ${res.status}`);
  }
  return res.json();
}

export async function exportAnnotations(videoId: string): Promise<Blob> {
  const res = await fetch(apiUrl(`/api/analytics/videos/${videoId}/export-annotations/`));
  if (!res.ok) throw new Error(`Failed to export: ${res.status}`);
  const json = await res.json();
  return new Blob([JSON.stringify(json, null, 2)], { type: "application/json" });
}

/** Full URL for source video (for <video src>). */
export function sourceVideoUrl(videoId: string): string {
  return apiUrl(`/api/analytics/videos/${videoId}/source/`);
}

export async function saveOverlays(videoId: string, overlays: VideoOverlay[]): Promise<VideoOverlay[]> {
  const res = await fetch(apiUrl(`/api/analytics/videos/${videoId}/overlays/`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ overlays }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || `Failed to save overlays: ${res.status}`);
  }
  const data = await res.json();
  return data.overlays;
}
