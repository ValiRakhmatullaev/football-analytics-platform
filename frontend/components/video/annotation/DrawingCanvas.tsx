"use client";

import { createContext, useRef, useState, useCallback, useEffect, useMemo, useContext } from "react";
import type { VideoOverlay, ArrowShape, CircleShape, LineShape, RectShape, MarkerShape, ChainShape } from "@/types/annotation";
import { saveOverlays } from "@/services/annotationService";

type ToolType = "arrow" | "circle" | "line" | "rectangle" | "marker" | "chain" | null;

type DrawingContextValue = {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  containerRef: React.RefObject<HTMLDivElement | null>;
  tool: ToolType;
  setTool: (t: ToolType) => void;
  arrowCurve: number;
  setArrowCurve: (n: number) => void;
  selectedColor: number;
  setSelectedColor: (n: number) => void;
  selectedStrokeWidth: number;
  setSelectedStrokeWidth: (n: number) => void;
  chainPoints: { x: number; y: number }[];
  setChainPoints: React.Dispatch<React.SetStateAction<{ x: number; y: number }[]>>;
  saving: boolean;
  currentColor: { name: string; value: string; glow: string; gradient: [string, string] };
  currentStroke: number;
  handleChainFinish: () => void;
  handleChainCancel: () => void;
  handleClearAtCurrentTime: () => void;
  handleSave: () => void;
  handleMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleMouseUp: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  setIsHovering: (v: boolean) => void;
  setDrawing: (v: boolean) => void;
  setStart: (v: { x: number; y: number } | null) => void;
  setCurrent: (v: { x: number; y: number } | null) => void;
  isHovering: boolean;
  drawing: boolean;
  start: { x: number; y: number } | null;
  current: { x: number; y: number } | null;
  videoWidth: number;
  videoHeight: number;
};

const DrawingContext = createContext<DrawingContextValue | null>(null);

function useDrawingContext() {
  const ctx = useContext(DrawingContext);
  if (!ctx) throw new Error("DrawingCanvasOverlay/Toolbar must be used inside DrawingCanvasProvider");
  return ctx;
}

/**
 * Wyscout-style drawing overlay: arrows, lines, circles, rectangles on video.
 * Enhanced with glow effects, gradients, and smooth animations.
 * Coordinates 0–100 (% of frame). Optional color and stroke width per overlay.
 */

const DASH_LENGTH = 24;
const FLOW_SPEED = 0.8;
const GLOW_BLUR = 12;
const PULSE_SPEED = 0.003;

interface ColorPreset {
  name: string;
  value: string;
  glow: string;
  gradient: [string, string];
}

const PRESET_COLORS: ColorPreset[] = [
  {
    name: "Жёлтый",
    value: "rgba(255, 200, 50, 0.95)",
    glow: "rgba(255, 200, 50, 0.4)",
    gradient: ["rgba(255, 220, 100, 0.95)", "rgba(255, 180, 30, 0.95)"]
  },
  {
    name: "Голубой",
    value: "rgba(0, 200, 255, 0.9)",
    glow: "rgba(0, 200, 255, 0.4)",
    gradient: ["rgba(50, 220, 255, 0.9)", "rgba(0, 170, 230, 0.9)"]
  },
  {
    name: "Зелёный",
    value: "rgba(80, 220, 120, 0.9)",
    glow: "rgba(80, 220, 120, 0.4)",
    gradient: ["rgba(120, 240, 150, 0.9)", "rgba(50, 200, 100, 0.9)"]
  },
  {
    name: "Оранжевый",
    value: "rgba(255, 140, 60, 0.9)",
    glow: "rgba(255, 140, 60, 0.4)",
    gradient: ["rgba(255, 170, 90, 0.9)", "rgba(255, 120, 40, 0.9)"]
  },
  {
    name: "Белый",
    value: "rgba(255, 255, 255, 0.95)",
    glow: "rgba(255, 255, 255, 0.3)",
    gradient: ["rgba(255, 255, 255, 0.95)", "rgba(220, 220, 220, 0.95)"]
  },
  {
    name: "Розовый",
    value: "rgba(255, 120, 180, 0.9)",
    glow: "rgba(255, 120, 180, 0.4)",
    gradient: ["rgba(255, 150, 200, 0.9)", "rgba(255, 90, 160, 0.9)"]
  },
];

const STROKE_WIDTHS = [2, 3, 5, 7] as const;
const MARKER_RADIUS_PCT = 1.4;

export interface DrawingCanvasProps {
  videoId: string;
  videoWidth: number;
  videoHeight: number;
  currentTime: number;
  overlays: VideoOverlay[];
  onOverlaysChange: (overlays: VideoOverlay[]) => void;
  className?: string;
}

// Utility functions
function quadraticTangent(
  x0: number, y0: number, cx: number, cy: number, x2: number, y2: number, t: number
): { x: number; y: number } {
  if (t >= 1) return { x: 2 * (x2 - cx), y: 2 * (y2 - cy) };
  const u = 1 - t;
  return {
    x: 2 * u * (cx - x0) + 2 * t * (x2 - cx),
    y: 2 * u * (cy - y0) + 2 * t * (y2 - cy),
  };
}

function getStrokeWidth(o: VideoOverlay): number {
  return o.strokeWidth && o.strokeWidth >= 1 && o.strokeWidth <= 7 ? o.strokeWidth : 3;
}

function getOverlayColor(o: VideoOverlay, presets: ColorPreset[]): ColorPreset {
  const found = presets.find(p => p.value === o.color);
  return found || presets[0];
}

// Drawing functions with enhanced graphics
function drawGlow(ctx: CanvasRenderingContext2D, color: string, blur: number = GLOW_BLUR) {
  ctx.shadowColor = color;
  ctx.shadowBlur = blur;
}

function resetGlow(ctx: CanvasRenderingContext2D) {
  ctx.shadowColor = "transparent";
  ctx.shadowBlur = 0;
}

function createGradient(
  ctx: CanvasRenderingContext2D,
  x1: number, y1: number, x2: number, y2: number,
  colors: [string, string]
): CanvasGradient {
  const grad = ctx.createLinearGradient(x1, y1, x2, y2);
  grad.addColorStop(0, colors[0]);
  grad.addColorStop(1, colors[1]);
  return grad;
}

function drawArrow(
  ctx: CanvasRenderingContext2D,
  shape: ArrowShape,
  w: number,
  h: number,
  colorPreset: ColorPreset,
  animPhase: number,
  lineW: number,
  pulsePhase: number
) {
  const x1 = (shape.x1 / 100) * w;
  const y1 = (shape.y1 / 100) * h;
  const x2 = (shape.x2 / 100) * w;
  const y2 = (shape.y2 / 100) * h;
  const curve = shape.curve ?? 0;

  // Защита от некорректных координат
  if (![x1, y1, x2, y2].every(isFinite)) return;

  let endAngle: number;
  let cx = 0, cy = 0;

  if (curve === 0) {
    endAngle = Math.atan2(y2 - y1, x2 - x1);
  } else {
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const perpX = (-dy / len) * (len * (Math.abs(curve) / 100) * 0.6);
    const perpY = (dx / len) * (len * (Math.abs(curve) / 100) * 0.6);
    cx = midX + (curve > 0 ? perpX : -perpX);
    cy = midY + (curve > 0 ? perpY : -perpY);
    const tan = quadraticTangent(x1, y1, cx, cy, x2, y2, 1);
    endAngle = Math.atan2(tan.y, tan.x);
  }

  const headLen = Math.min(26, (w + h) / 24);
  const pulseScale = 1 + Math.sin(pulsePhase) * 0.05;

  // Outer glow
  drawGlow(ctx, colorPreset.glow, GLOW_BLUR * 1.5);

  // Main stroke with gradient
  const gradient = createGradient(ctx, x1, y1, x2, y2, colorPreset.gradient);
  ctx.strokeStyle = gradient;
  ctx.lineWidth = lineW * pulseScale;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.setLineDash([12, 16]);
  ctx.lineDashOffset = -(animPhase * (DASH_LENGTH * 2)) % (DASH_LENGTH * 2);

  ctx.beginPath();
  if (curve === 0) {
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
  } else {
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(cx, cy, x2, y2);
  }
  ctx.stroke();

  // Inner highlight
  ctx.setLineDash([]);
  resetGlow(ctx);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
  ctx.lineWidth = Math.max(1, lineW * 0.3);
  ctx.beginPath();
  if (curve === 0) {
    ctx.moveTo(x1, y1 - lineW * 0.2);
    ctx.lineTo(x2, y2 - lineW * 0.2);
  } else {
    ctx.moveTo(x1, y1 - lineW * 0.2);
    ctx.quadraticCurveTo(cx, cy - lineW * 0.2, x2, y2 - lineW * 0.2);
  }
  ctx.stroke();

  // Arrowhead with glow
  drawGlow(ctx, colorPreset.glow, GLOW_BLUR);
  ctx.strokeStyle = colorPreset.value;
  ctx.lineWidth = lineW * pulseScale;
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(
    x2 - headLen * Math.cos(endAngle - 0.5) * pulseScale,
    y2 - headLen * Math.sin(endAngle - 0.5) * pulseScale
  );
  ctx.moveTo(x2, y2);
  ctx.lineTo(
    x2 - headLen * Math.cos(endAngle + 0.5) * pulseScale,
    y2 - headLen * Math.sin(endAngle + 0.5) * pulseScale
  );
  ctx.stroke();

  resetGlow(ctx);
}

function drawLine(
  ctx: CanvasRenderingContext2D,
  shape: LineShape,
  w: number,
  h: number,
  colorPreset: ColorPreset,
  animPhase: number,
  lineW: number
) {
  const x1 = (shape.x1 / 100) * w;
  const y1 = (shape.y1 / 100) * h;
  const x2 = (shape.x2 / 100) * w;
  const y2 = (shape.y2 / 100) * h;
  const curve = shape.curve ?? 0;

  // Защита от некорректных координат
  if (![x1, y1, x2, y2].every(isFinite)) return;

  drawGlow(ctx, colorPreset.glow, GLOW_BLUR);

  const gradient = createGradient(ctx, x1, y1, x2, y2, colorPreset.gradient);
  ctx.strokeStyle = gradient;
  ctx.lineWidth = lineW;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.setLineDash([10, 14]);
  ctx.lineDashOffset = -(animPhase * (DASH_LENGTH * 2)) % (DASH_LENGTH * 2);

  ctx.beginPath();
  if (curve === 0) {
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
  } else {
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const perpX = (-dy / len) * (len * (Math.abs(curve) / 100) * 0.6);
    const perpY = (dx / len) * (len * (Math.abs(curve) / 100) * 0.6);
    const cx = midX + (curve > 0 ? perpX : -perpX);
    const cy = midY + (curve > 0 ? perpY : -perpY);
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(cx, cy, x2, y2);
  }
  ctx.stroke();

  resetGlow(ctx);
}

function drawCircle(
  ctx: CanvasRenderingContext2D,
  shape: CircleShape,
  w: number,
  h: number,
  colorPreset: ColorPreset,
  lineW: number,
  pulsePhase: number
) {
  const cx = (shape.cx / 100) * w;
  const cy = (shape.cy / 100) * h;
  const r = (shape.r / 100) * Math.min(w, h);

  // Защита от отрицательного, нулевого или некорректного радиуса
  if (!isFinite(cx) || !isFinite(cy) || r <= 0 || !isFinite(r)) return;

  const pulseR = Math.max(lineW * 0.5, r * (1 + Math.sin(pulsePhase) * 0.03));

  // Outer glow ring
  drawGlow(ctx, colorPreset.glow, GLOW_BLUR * 2);
  ctx.strokeStyle = colorPreset.glow;
  ctx.lineWidth = lineW * 2;
  ctx.beginPath();
  ctx.arc(cx, cy, pulseR, 0, 2 * Math.PI);
  ctx.stroke();

  // Main circle
  ctx.strokeStyle = colorPreset.value;
  ctx.lineWidth = lineW;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.setLineDash([8, 10]);
  ctx.beginPath();
  ctx.arc(cx, cy, pulseR, 0, 2 * Math.PI);
  ctx.stroke();

  // Highlight arc - защита от отрицательного радиуса
  const highlightRadius = Math.max(0.1, pulseR - lineW * 0.3);
  ctx.setLineDash([]);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
  ctx.lineWidth = Math.max(1, lineW * 0.4);
  ctx.beginPath();
  ctx.arc(cx, cy, highlightRadius, -Math.PI * 0.8, -Math.PI * 0.2);
  ctx.stroke();

  resetGlow(ctx);
}

function drawRect(
  ctx: CanvasRenderingContext2D,
  shape: RectShape,
  w: number,
  h: number,
  colorPreset: ColorPreset,
  lineW: number,
  pulsePhase: number
) {
  const x1 = (shape.x1 / 100) * w;
  const y1 = (shape.y1 / 100) * h;
  const x2 = (shape.x2 / 100) * w;
  const y2 = (shape.y2 / 100) * h;

  // Защита от некорректных координат
  if (![x1, y1, x2, y2].every(isFinite)) return;

  const left = Math.min(x1, x2);
  const top = Math.min(y1, y2);
  const width = Math.abs(x2 - x1);
  const height = Math.abs(y2 - y1);

  // Защита от нулевых или отрицательных размеров
  if (width <= 0 || height <= 0) return;

  const pulseOffset = Math.sin(pulsePhase) * 2;

  drawGlow(ctx, colorPreset.glow, GLOW_BLUR);
  ctx.strokeStyle = colorPreset.value;
  ctx.lineWidth = lineW;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.setLineDash([6, 8]);
  ctx.strokeRect(left - pulseOffset, top - pulseOffset, width + pulseOffset * 2, height + pulseOffset * 2);

  // Corner highlights
  ctx.setLineDash([]);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
  ctx.lineWidth = Math.max(1, lineW * 0.5);
  const cornerSize = Math.min(20, width * 0.15, height * 0.15);

  if (cornerSize > 0) {
    // Top-left corner
    ctx.beginPath();
    ctx.moveTo(left + cornerSize, top);
    ctx.lineTo(left, top);
    ctx.lineTo(left, top + cornerSize);
    ctx.stroke();

    // Bottom-right corner
    ctx.beginPath();
    ctx.moveTo(left + width - cornerSize, top + height);
    ctx.lineTo(left + width, top + height);
    ctx.lineTo(left + width, top + height - cornerSize);
    ctx.stroke();
  }

  resetGlow(ctx);
}

function drawMarker(
  ctx: CanvasRenderingContext2D,
  shape: MarkerShape,
  w: number,
  h: number,
  colorPreset: ColorPreset,
  pulsePhase: number
) {
  const cx = (shape.x / 100) * w;
  const cy = (shape.y / 100) * h;
  const baseR = (MARKER_RADIUS_PCT / 100) * Math.min(w, h);

  // Защита от некорректных значений
  if (!isFinite(cx) || !isFinite(cy) || baseR <= 0 || !isFinite(baseR)) return;

  const r = Math.max(1, baseR * (1 + Math.sin(pulsePhase) * 0.1));

  // Outer pulse ring
  const pulseRingR = Math.max(1, baseR * (1.8 + Math.sin(pulsePhase * 2) * 0.3));
  drawGlow(ctx, colorPreset.glow, GLOW_BLUR * 2);
  ctx.fillStyle = colorPreset.glow;
  ctx.globalAlpha = 0.3;
  ctx.beginPath();
  ctx.arc(cx, cy, pulseRingR, 0, 2 * Math.PI);
  ctx.fill();
  ctx.globalAlpha = 1;

  // Main marker with gradient
  const gradient = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 0, cx, cy, r);
  gradient.addColorStop(0, colorPreset.gradient[0]);
  gradient.addColorStop(1, colorPreset.gradient[1]);

  ctx.fillStyle = gradient;
  ctx.strokeStyle = "rgba(0, 0, 0, 0.6)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, 2 * Math.PI);
  ctx.fill();
  ctx.stroke();

  // Inner highlight
  ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
  ctx.beginPath();
  ctx.arc(cx - r * 0.3, cy - r * 0.3, Math.max(0.5, r * 0.25), 0, 2 * Math.PI);
  ctx.fill();

  // Label
  if (shape.label != null) {
    ctx.fillStyle = "#000";
    ctx.font = `bold ${Math.max(12, r * 1.2)}px system-ui, -apple-system, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(shape.label), cx, cy + 1);
  }

  resetGlow(ctx);
}

function drawChain(
  ctx: CanvasRenderingContext2D,
  shape: ChainShape,
  w: number,
  h: number,
  colorPreset: ColorPreset,
  animPhase: number,
  lineW: number,
  pulsePhase: number
) {
  const pts = shape.points;
  if (pts.length < 2) return;

  const headLen = Math.min(16, (w + h) / 35);

  drawGlow(ctx, colorPreset.glow, GLOW_BLUR);
  ctx.strokeStyle = colorPreset.value;
  ctx.lineWidth = lineW;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.setLineDash([8, 10]);
  ctx.lineDashOffset = -(animPhase * 20) % 20;

  for (let i = 0; i < pts.length - 1; i++) {
    const x1 = (pts[i].x / 100) * w;
    const y1 = (pts[i].y / 100) * h;
    const x2 = (pts[i + 1].x / 100) * w;
    const y2 = (pts[i + 1].y / 100) * h;

    // Пропускаем некорректные точки
    if (![x1, y1, x2, y2].every(isFinite)) continue;

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    const angle = Math.atan2(y2 - y1, x2 - x1);
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - headLen * Math.cos(angle - 0.4), y2 - headLen * Math.sin(angle - 0.4));
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - headLen * Math.cos(angle + 0.4), y2 - headLen * Math.sin(angle + 0.4));
    ctx.stroke();
    ctx.setLineDash([8, 10]);
    ctx.lineDashOffset = -(animPhase * 20) % 20;
  }

  ctx.setLineDash([]);

  pts.forEach((p, i) => {
    const cx = (p.x / 100) * w;
    const cy = (p.y / 100) * h;
    const baseR = (MARKER_RADIUS_PCT / 100) * Math.min(w, h);

    // Защита от некорректных значений
    if (!isFinite(cx) || !isFinite(cy) || baseR <= 0) return;

    const r = Math.max(1, baseR * (1 + Math.sin(pulsePhase + i * 0.5) * 0.08));

    const gradient = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 0, cx, cy, r);
    gradient.addColorStop(0, colorPreset.gradient[0]);
    gradient.addColorStop(1, colorPreset.gradient[1]);

    ctx.fillStyle = gradient;
    ctx.strokeStyle = "rgba(0, 0, 0, 0.6)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#000";
    ctx.font = `bold ${Math.max(11, r)}px system-ui, -apple-system, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(i + 1), cx, cy + 1);
  });

  resetGlow(ctx);
}

// Icon components
const ToolIcon = ({ type, active }: { type: ToolType; active: boolean }) => {
  const iconClass = `w-5 h-5 transition-transform ${active ? "scale-110" : ""}`;

  switch (type) {
    case "marker":
      return (
        <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="6" fill="currentColor" fillOpacity="0.3" />
          <circle cx="12" cy="12" r="6" />
          <circle cx="12" cy="12" r="2" fill="currentColor" />
        </svg>
      );
    case "chain":
      return (
        <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="6" cy="12" r="3" fill="currentColor" fillOpacity="0.3" />
          <circle cx="18" cy="6" r="3" fill="currentColor" fillOpacity="0.3" />
          <circle cx="18" cy="18" r="3" fill="currentColor" fillOpacity="0.3" />
          <path d="M9 12L15.5 7.5M9 12L15.5 16.5" strokeLinecap="round" />
          <text x="6" y="13" textAnchor="middle" fontSize="8" fill="currentColor">1</text>
          <text x="18" y="7" textAnchor="middle" fontSize="8" fill="currentColor">2</text>
          <text x="18" y="19" textAnchor="middle" fontSize="8" fill="currentColor">3</text>
        </svg>
      );
    case "arrow":
      return (
        <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 12H16M16 12L12 8M16 12L12 16" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "line":
      return (
        <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 20L20 4" strokeLinecap="round" />
        </svg>
      );
    case "circle":
      return (
        <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="7" />
        </svg>
      );
    case "rectangle":
      return (
        <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="5" y="7" width="14" height="10" rx="1" />
        </svg>
      );
    default:
      return null;
  }
};

export function DrawingCanvasProvider({
  videoId,
  videoWidth,
  videoHeight,
  currentTime,
  overlays,
  onOverlaysChange,
  children,
}: DrawingCanvasProps & { children: React.ReactNode }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tool, setTool] = useState<ToolType>(null);
  const [arrowCurve, setArrowCurve] = useState<number>(0);
  const [selectedColor, setSelectedColor] = useState(0);
  const [selectedStrokeWidth, setSelectedStrokeWidth] = useState(1);
  const [drawing, setDrawing] = useState(false);
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);
  const [current, setCurrent] = useState<{ x: number; y: number } | null>(null);
  const [chainPoints, setChainPoints] = useState<{ x: number; y: number }[]>([]);
  const [saving, setSaving] = useState(false);
  const [animPhase, setAnimPhase] = useState(0);
  const [pulsePhase, setPulsePhase] = useState(0);
  const [isHovering, setIsHovering] = useState(false);

  const currentColor = PRESET_COLORS[selectedColor];
  const currentStroke = STROKE_WIDTHS[selectedStrokeWidth];

  const overlayDuration = 15;

  const visibleOverlays = useMemo(() =>
    overlays.filter((o) => currentTime >= o.start_time_seconds && currentTime <= o.end_time_seconds),
    [overlays, currentTime]
  );

  const markersInRange = useMemo(() =>
    visibleOverlays.filter((o) => o.type === "marker"),
    [visibleOverlays]
  );

  const nextMarkerLabel = markersInRange.length + 1;

  // Setup canvas with device pixel ratio for sharp rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || videoWidth <= 0 || videoHeight <= 0) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = container.getBoundingClientRect();

    // Set actual canvas size accounting for DPR
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    // Scale context to match DPR
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.scale(dpr, dpr);
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
    }

    // Set display size via CSS
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
  }, [videoWidth, videoHeight]);

  const toPercent = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * 100;
    const y = ((clientY - rect.top) / rect.height) * 100;
    return {
      x: Math.max(0, Math.min(100, x)),
      y: Math.max(0, Math.min(100, y))
    };
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!tool) return;
    e.preventDefault();
    const p = toPercent(e.clientX, e.clientY);

    if (tool === "marker") {
      const common = {
        start_time_seconds: currentTime,
        end_time_seconds: currentTime + overlayDuration,
        color: currentColor.value,
        strokeWidth: currentStroke,
      };
      onOverlaysChange([
        ...overlays,
        {
          ...common,
          type: "marker" as const,
          shape_data: { x: p.x, y: p.y, label: nextMarkerLabel },
        },
      ]);
      return;
    }

    if (tool === "chain") {
      setChainPoints((prev) => [...prev, p]);
      return;
    }

    setStart(p);
    setCurrent(p);
    setDrawing(true);
  }, [tool, toPercent, currentTime, overlayDuration, currentColor, currentStroke, nextMarkerLabel, overlays, onOverlaysChange]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing) return;
    setCurrent(toPercent(e.clientX, e.clientY));
  }, [drawing, toPercent]);

  const handleMouseUp = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (tool === "marker" || tool === "chain") return;
    if (!drawing || !start) {
      setDrawing(false);
      setStart(null);
      setCurrent(null);
      return;
    }

    const end = toPercent(e.clientX, e.clientY);
    const minDistance = 1; // Minimum 1% distance to create overlay
    const distance = Math.hypot(end.x - start.x, end.y - start.y);

    if (distance < minDistance) {
      setDrawing(false);
      setStart(null);
      setCurrent(null);
      return;
    }

    const common = {
      start_time_seconds: currentTime,
      end_time_seconds: currentTime + overlayDuration,
      color: currentColor.value,
      strokeWidth: currentStroke,
    };

    switch (tool) {
      case "arrow":
        onOverlaysChange([
          ...overlays,
          {
            ...common,
            type: "arrow" as const,
            shape_data: {
              x1: start.x,
              y1: start.y,
              x2: end.x,
              y2: end.y,
              ...(arrowCurve !== 0 && { curve: arrowCurve }),
            },
          },
        ]);
        break;
      case "circle": {
        const r = Math.max(1, Math.min(50, distance)); // Min 1%, Max 50% radius
        onOverlaysChange([
          ...overlays,
          {
            ...common,
            type: "circle" as const,
            shape_data: { cx: start.x, cy: start.y, r }
          },
        ]);
        break;
      }
      case "line":
        onOverlaysChange([
          ...overlays,
          {
            ...common,
            type: "line" as const,
            shape_data: {
              x1: start.x,
              y1: start.y,
              x2: end.x,
              y2: end.y,
              ...(arrowCurve !== 0 && { curve: arrowCurve }),
            },
          },
        ]);
        break;
      case "rectangle":
        onOverlaysChange([
          ...overlays,
          {
            ...common,
            type: "rectangle" as const,
            shape_data: { x1: start.x, y1: start.y, x2: end.x, y2: end.y },
          },
        ]);
        break;
    }

    setDrawing(false);
    setStart(null);
    setCurrent(null);
  }, [drawing, start, tool, currentTime, overlayDuration, overlays, onOverlaysChange, toPercent, arrowCurve, currentColor, currentStroke]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await saveOverlays(videoId, overlays);
    } catch (error) {
      console.error("Failed to save overlays:", error);
    } finally {
      setSaving(false);
    }
  }, [videoId, overlays]);

  const handleClearAtCurrentTime = useCallback(() => {
    const filtered = overlays.filter(
      (o) => !(currentTime >= o.start_time_seconds && currentTime <= o.end_time_seconds)
    );
    onOverlaysChange(filtered);
  }, [currentTime, overlays, onOverlaysChange]);

  const handleChainFinish = useCallback(() => {
    if (chainPoints.length < 2) return;
    const common = {
      start_time_seconds: currentTime,
      end_time_seconds: currentTime + overlayDuration,
      color: currentColor.value,
      strokeWidth: currentStroke,
    };
    onOverlaysChange([
      ...overlays,
      { ...common, type: "chain" as const, shape_data: { points: [...chainPoints] } },
    ]);
    setChainPoints([]);
  }, [chainPoints, currentTime, overlayDuration, currentColor, currentStroke, overlays, onOverlaysChange]);

  const handleChainCancel = useCallback(() => {
    setChainPoints([]);
  }, []);

  // Animation loop
  useEffect(() => {
    let raf: number;
    let lastTime = performance.now();

    const tick = (now: number) => {
      const delta = now - lastTime;
      lastTime = now;

      setAnimPhase((p) => (p + delta * 0.001 * FLOW_SPEED) % 1);
      setPulsePhase((p) => (p + delta * PULSE_SPEED) % (Math.PI * 2));

      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // Clear chain when switching tools
  useEffect(() => {
    if (tool !== "chain" && chainPoints.length > 0) {
      setChainPoints([]);
    }
  }, [tool, chainPoints.length]);

  // Main draw effect
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;

    ctx.clearRect(0, 0, w, h);

    // Draw visible overlays
    visibleOverlays.forEach((o) => {
      const colorPreset = getOverlayColor(o, PRESET_COLORS);
      const lw = getStrokeWidth(o);

      switch (o.type) {
        case "arrow":
          drawArrow(ctx, o.shape_data as ArrowShape, w, h, colorPreset, animPhase, lw, pulsePhase);
          break;
        case "line":
          drawLine(ctx, o.shape_data as LineShape, w, h, colorPreset, animPhase, lw);
          break;
        case "circle":
          drawCircle(ctx, o.shape_data as CircleShape, w, h, colorPreset, lw, pulsePhase);
          break;
        case "rectangle":
          drawRect(ctx, o.shape_data as RectShape, w, h, colorPreset, lw, pulsePhase);
          break;
        case "marker":
          drawMarker(ctx, o.shape_data as MarkerShape, w, h, colorPreset, pulsePhase);
          break;
        case "chain":
          drawChain(ctx, o.shape_data as ChainShape, w, h, colorPreset, animPhase, lw, pulsePhase);
          break;
      }
    });

    // Draw chain preview
    if (tool === "chain" && chainPoints.length > 0) {
      const previewColor: ColorPreset = {
        name: "Preview",
        value: "rgba(150, 255, 150, 0.95)",
        glow: "rgba(150, 255, 150, 0.5)",
        gradient: ["rgba(180, 255, 180, 0.95)", "rgba(120, 240, 120, 0.95)"]
      };

      chainPoints.forEach((p, i) => {
        drawMarker(ctx, { x: p.x, y: p.y, label: i + 1 }, w, h, previewColor, pulsePhase);
      });

      if (chainPoints.length >= 2) {
        drawChain(ctx, { points: chainPoints }, w, h, previewColor, animPhase, currentStroke, pulsePhase);
      }
    }

    // Draw preview while dragging
    if (drawing && start && current) {
      const previewColor: ColorPreset = {
        name: "Preview",
        value: "rgba(255, 255, 200, 0.9)",
        glow: "rgba(255, 255, 200, 0.4)",
        gradient: ["rgba(255, 255, 220, 0.9)", "rgba(255, 255, 180, 0.9)"]
      };

      switch (tool) {
        case "arrow":
          drawArrow(
            ctx,
            {
              x1: start.x,
              y1: start.y,
              x2: current.x,
              y2: current.y,
              ...(arrowCurve !== 0 && { curve: arrowCurve }),
            },
            w, h, previewColor, animPhase, currentStroke, pulsePhase
          );
          break;
        case "line":
          drawLine(
            ctx,
            {
              x1: start.x,
              y1: start.y,
              x2: current.x,
              y2: current.y,
              ...(arrowCurve !== 0 && { curve: arrowCurve }),
            },
            w, h, previewColor, animPhase, currentStroke
          );
          break;
        case "circle": {
          const dx = current.x - start.x;
          const dy = current.y - start.y;
          const r = Math.sqrt(dx * dx + dy * dy);
          drawCircle(ctx, { cx: start.x, cy: start.y, r: Math.max(1, Math.min(50, r)) }, w, h, previewColor, currentStroke, pulsePhase);
          break;
        }
        case "rectangle":
          drawRect(ctx, { x1: start.x, y1: start.y, x2: current.x, y2: current.y }, w, h, previewColor, currentStroke, pulsePhase);
          break;
      }
    }
  }, [visibleOverlays, drawing, start, current, tool, arrowCurve, animPhase, pulsePhase, videoWidth, videoHeight, currentStroke, chainPoints]);

  const value: DrawingContextValue = {
    canvasRef,
    containerRef,
    tool,
    setTool,
    arrowCurve,
    setArrowCurve,
    selectedColor,
    setSelectedColor,
    selectedStrokeWidth,
    setSelectedStrokeWidth,
    chainPoints,
    setChainPoints,
    saving,
    currentColor,
    currentStroke,
    handleChainFinish,
    handleChainCancel,
    handleClearAtCurrentTime,
    handleSave,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    setIsHovering,
    setDrawing,
    setStart,
    setCurrent,
    isHovering,
    drawing,
    start,
    current,
    videoWidth,
    videoHeight,
  };

  return <DrawingContext.Provider value={value}>{children}</DrawingContext.Provider>;
}

const TOOLS = [
  { id: "marker" as const, label: "Маркер", title: "Клик по игроку — закрепить точку" },
  { id: "chain" as const, label: "Связать", title: "Кликайте по игрокам по порядку, затем «Готово»" },
  { id: "arrow" as const, label: "Стрелка", title: "Направление передачи/бега" },
  { id: "line" as const, label: "Линия", title: "Траектория" },
  { id: "circle" as const, label: "Круг", title: "Обвести игрока" },
  { id: "rectangle" as const, label: "Прямоугольник", title: "Зона" },
];

export function DrawingCanvasOverlay({ className = "" }: { className?: string }) {
  const ctx = useDrawingContext();
  const { containerRef, canvasRef, tool, handleMouseDown, handleMouseMove, handleMouseUp, setIsHovering, setDrawing, setStart, setCurrent, isHovering, chainPoints, arrowCurve } = ctx;
  return (
    <div className={`flex flex-col w-full h-full ${className}`}>
      <div ref={containerRef} className="relative flex-1 w-full overflow-hidden rounded-lg bg-black/20">
        <canvas
          ref={canvasRef}
          className={`absolute inset-0 w-full h-full transition-opacity duration-200 ${tool ? "cursor-crosshair" : "cursor-default"}`}
          style={{ pointerEvents: tool ? "auto" : "none" }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => {
            setIsHovering(false);
            setDrawing(false);
            setStart(null);
            setCurrent(null);
          }}
        />
        {isHovering && tool && (
          <div className="absolute top-3 left-3 px-2 py-1 bg-black/70 backdrop-blur-sm rounded text-xs text-white/80 pointer-events-none">
            {tool === "marker" && "Клик для маркера"}
            {tool === "chain" && `Точек: ${chainPoints.length}`}
            {tool === "arrow" && `Стрелка (${arrowCurve === 0 ? "прямая" : "дуга"})`}
            {tool === "line" && `Линия (${arrowCurve === 0 ? "прямая" : "дуга"})`}
            {tool === "circle" && "Клик и перетаскивание"}
            {tool === "rectangle" && "Клик и перетаскивание"}
          </div>
        )}
      </div>
    </div>
  );
}

export function DrawingCanvasToolbar() {
  const ctx = useDrawingContext();
  const {
    tool,
    setTool,
    arrowCurve,
    setArrowCurve,
    selectedColor,
    setSelectedColor,
    selectedStrokeWidth,
    setSelectedStrokeWidth,
    chainPoints,
    handleChainFinish,
    handleChainCancel,
    handleClearAtCurrentTime,
    handleSave,
    saving,
  } = ctx;
  return (
    <div className="flex-none mt-3 rounded-xl overflow-hidden shadow-2xl border border-white/10 backdrop-blur-xl bg-gradient-to-b from-gray-900/95 to-black/95">
      <div className="p-4 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:block">Инструменты</span>
          <div className="flex items-center gap-1.5 p-1 bg-white/5 rounded-lg">
            {TOOLS.map(({ id, label, title }) => (
              <button
                key={id}
                type="button"
                title={title}
                onClick={() => setTool(tool === id ? null : id)}
                className={`group relative flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  tool === id ? "bg-gradient-to-r from-amber-500 to-amber-400 text-black shadow-lg shadow-amber-500/30" : "text-gray-300 hover:text-white hover:bg-white/10"
                }`}
              >
                <ToolIcon type={id} active={tool === id} />
                <span className="hidden md:inline">{label}</span>
                {tool === id && <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-amber-300 rounded-full" />}
              </button>
            ))}
          </div>
          {tool === "chain" && (
            <div className="flex items-center gap-2 pl-3 border-l border-white/10 animate-in fade-in slide-in-from-left-2">
              <span className="text-sm text-gray-400">Точек: <span className="text-white font-semibold">{chainPoints.length}</span></span>
              <button type="button" onClick={handleChainFinish} disabled={chainPoints.length < 2} className="px-3 py-1.5 rounded-lg text-sm font-medium bg-emerald-500/90 text-white hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-500/20">Готово</button>
              <button type="button" onClick={handleChainCancel} className="px-3 py-1.5 rounded-lg text-sm border border-white/20 text-gray-300 hover:bg-white/10 hover:text-white transition-all">Отмена</button>
            </div>
          )}
          {(tool === "arrow" || tool === "line") && (
            <div className="flex items-center gap-1 pl-3 border-l border-white/10 animate-in fade-in slide-in-from-left-2">
              <button type="button" onClick={() => setArrowCurve(0)} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${arrowCurve === 0 ? "bg-white/20 border-white/40 text-white" : "border-white/10 text-gray-400 hover:bg-white/10 hover:text-white"}`}>Прямая</button>
              <button type="button" onClick={() => setArrowCurve(28)} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${arrowCurve !== 0 ? "bg-white/20 border-white/40 text-white" : "border-white/10 text-gray-400 hover:bg-white/10 hover:text-white"}`}>Дуга</button>
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-4 pt-3 border-t border-white/10">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Цвет</span>
            <div className="flex items-center gap-1.5">
              {PRESET_COLORS.map((c, i) => (
                <button key={i} type="button" title={c.name} onClick={() => setSelectedColor(i)} className={`group relative w-8 h-8 rounded-full transition-all duration-200 ${selectedColor === i ? "scale-110 ring-2 ring-white ring-offset-2 ring-offset-gray-900" : "hover:scale-105 opacity-70 hover:opacity-100"}`} style={{ backgroundColor: c.value }}>
                  <span className={`absolute inset-0 rounded-full blur-md transition-opacity ${selectedColor === i ? "opacity-60" : "opacity-0 group-hover:opacity-40"}`} style={{ backgroundColor: c.glow }} />
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 pl-4 border-l border-white/10">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Толщина</span>
            <div className="flex items-center gap-1">
              {STROKE_WIDTHS.map((width, i) => (
                <button key={width} type="button" onClick={() => setSelectedStrokeWidth(i)} className={`flex items-center justify-center w-9 h-9 rounded-lg border transition-all ${selectedStrokeWidth === i ? "bg-white/20 border-white/40" : "border-white/10 hover:bg-white/10 hover:border-white/20"}`}>
                  <span className="rounded-full bg-white transition-all" style={{ width: Math.max(3, width), height: Math.max(3, width), opacity: selectedStrokeWidth === i ? 1 : 0.6 }} />
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 ml-auto pl-4 border-l border-white/10">
            <button type="button" onClick={handleClearAtCurrentTime} className="group flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 hover:border-red-500/50 transition-all">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              <span className="hidden sm:inline">Удалить здесь</span>
            </button>
            <button type="button" onClick={handleSave} disabled={saving} className="group flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-emerald-600 to-emerald-500 text-white hover:from-emerald-500 hover:to-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-900/30">
              {saving ? (<><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg><span>Сохранение...</span></>) : (<><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg><span>Сохранить</span></>)}
            </button>
          </div>
        </div>
        {tool && (
          <div className="flex items-center gap-2 text-xs text-gray-400 animate-in fade-in slide-in-from-top-1">
            <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>
              {tool === "marker" && "Кликните на видео, чтобы разместить маркер на игроке"}
              {tool === "chain" && "Кликайте по игрокам в порядке действия, затем нажмите «Готово»"}
              {tool === "arrow" && `Проведите от начала к концу (${arrowCurve === 0 ? "прямая линия" : "дуга"})`}
              {tool === "line" && `Проведите линию (${arrowCurve === 0 ? "прямая" : "с изгибом"})`}
              {tool === "circle" && "Кликните для центра, протяните для радиуса"}
              {tool === "rectangle" && "Кликните и протяните для создания зоны"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DrawingCanvas({ className = "", ...props }: DrawingCanvasProps) {
  return (
    <DrawingCanvasProvider {...props}>
      <div className={`flex flex-col w-full h-full ${className}`}>
        <DrawingCanvasOverlay className="flex-1 min-h-0" />
        <DrawingCanvasToolbar />
      </div>
    </DrawingCanvasProvider>
  );
}