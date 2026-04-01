/**
 * Types for video annotation and clipping player.
 * Clear separation: UI uses these; persistence layer maps to API.
 */

export interface VideoMeta {
  source_url: string;
  duration_seconds: number;
  width: number;
  height: number;
  file_name?: string;
}

export interface RawEvent {
  event_type?: string;
  timestamp_ms?: number;
  x?: number;
  y?: number;
  confidence?: number;
  [key: string]: unknown;
}

export interface ClipAction {
  id: string;
  clip_type: string;
  title: string;
  description: string;
  start_time_seconds: number;
  end_time_seconds: number;
  timestamp_ms: number;
  duration_seconds: number;
  confidence?: number;
}

/** Arrow overlay: x1,y1 = start, x2,y2 = end (0–100 % of frame). curve: 0 = straight, >0 bend one way, <0 other (e.g. -40..40). */
export interface ArrowShape {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  /** Optional bend: 0 = straight, positive/negative = arc (e.g. -40 to 40). */
  curve?: number;
}

/** Circle overlay: cx,cy = center, r = radius (0–100 % of min dimension). */
export interface CircleShape {
  cx: number;
  cy: number;
  r: number;
}

/** Line overlay (no arrow): x1,y1 to x2,y2 (0–100 %). */
export interface LineShape {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  curve?: number;
}

/** Rectangle overlay: x1,y1 = top-left, x2,y2 = bottom-right (0–100 %). */
export interface RectShape {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/** Marker: один клик по игроку — точка закреплена в этой позиции (0–100 %). */
export interface MarkerShape {
  x: number;
  y: number;
  /** Номер маркера (1, 2, 3…) для связи. */
  label?: number;
}

/** Цепочка связей: несколько точек (игроков), последовательно соединённых. */
export interface ChainShape {
  points: { x: number; y: number }[];
}

export interface VideoOverlay {
  type: "arrow" | "circle" | "line" | "rectangle" | "marker" | "chain";
  start_time_seconds: number;
  end_time_seconds: number;
  shape_data: ArrowShape | CircleShape | LineShape | RectShape | MarkerShape | ChainShape;
  color?: string;
  strokeWidth?: number;
  id?: string;
}

export interface AnnotationData {
  video: VideoMeta;
  events: RawEvent[];
  clips: ClipAction[];
  overlays: VideoOverlay[];
}

export interface ClipUpdatePayload {
  start_time_seconds?: number;
  end_time_seconds?: number;
  description?: string;
}
