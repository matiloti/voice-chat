import { useRef, useEffect } from "react";
import type { AppState } from "../types";

interface VoiceOrbProps {
  appState: AppState;
}

// Color palette
const COLORS: Record<AppState, { r: number; g: number; b: number }> = {
  idle: { r: 100, g: 120, b: 160 },       // Muted blue-gray
  listening: { r: 80, g: 140, b: 220 },    // Active blue
  processing: { r: 160, g: 140, b: 80 },   // Warm yellow
  thinking: { r: 200, g: 160, b: 60 },     // Amber
  speaking: { r: 232, g: 168, b: 56 },     // Bright amber
};

export function VoiceOrb({ appState }: VoiceOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const size = 200;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const baseRadius = 60;

    function draw() {
      if (!ctx) return;
      phaseRef.current += 0.02;
      const t = phaseRef.current;

      ctx.clearRect(0, 0, size, size);

      const color = COLORS[appState] || COLORS.idle;

      // Determine animation intensity
      let pulseAmplitude: number;
      let pulseSpeed: number;
      switch (appState) {
        case "idle":
          pulseAmplitude = 3;
          pulseSpeed = 0.5;
          break;
        case "listening":
          pulseAmplitude = 10;
          pulseSpeed = 2;
          break;
        case "processing":
          pulseAmplitude = 6;
          pulseSpeed = 1.5;
          break;
        case "thinking":
          pulseAmplitude = 8;
          pulseSpeed = 1;
          break;
        case "speaking":
          pulseAmplitude = 12;
          pulseSpeed = 2.5;
          break;
        default:
          pulseAmplitude = 3;
          pulseSpeed = 0.5;
      }

      const pulse = Math.sin(t * pulseSpeed) * pulseAmplitude;
      const radius = baseRadius + pulse;

      // Outer glow
      const glowRadius = radius + 20 + pulse * 0.5;
      const glow = ctx.createRadialGradient(cx, cy, radius * 0.5, cx, cy, glowRadius);
      glow.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, 0.15)`);
      glow.addColorStop(1, `rgba(${color.r}, ${color.g}, ${color.b}, 0)`);
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, glowRadius, 0, Math.PI * 2);
      ctx.fill();

      // Main orb with gradient
      const orbGrad = ctx.createRadialGradient(
        cx - radius * 0.2,
        cy - radius * 0.2,
        radius * 0.1,
        cx,
        cy,
        radius
      );
      orbGrad.addColorStop(0, `rgba(${Math.min(255, color.r + 60)}, ${Math.min(255, color.g + 60)}, ${Math.min(255, color.b + 60)}, 0.9)`);
      orbGrad.addColorStop(0.7, `rgba(${color.r}, ${color.g}, ${color.b}, 0.8)`);
      orbGrad.addColorStop(1, `rgba(${Math.max(0, color.r - 30)}, ${Math.max(0, color.g - 30)}, ${Math.max(0, color.b - 30)}, 0.6)`);

      ctx.fillStyle = orbGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();

      // Inner highlight
      const highlightGrad = ctx.createRadialGradient(
        cx - radius * 0.3,
        cy - radius * 0.3,
        0,
        cx - radius * 0.3,
        cy - radius * 0.3,
        radius * 0.5
      );
      highlightGrad.addColorStop(0, "rgba(255, 255, 255, 0.2)");
      highlightGrad.addColorStop(1, "rgba(255, 255, 255, 0)");
      ctx.fillStyle = highlightGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();

      animationRef.current = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [appState]);

  return <canvas ref={canvasRef} className="voice-orb" />;
}
