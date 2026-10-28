import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { hasClip } from "./vo";
import { ease, enter, place, pop } from "./anim";
import { C, FONT, SAFE_X, SAFE_Y, T } from "./theme";
import * as cv from "./curves";
import type { Pt } from "./curves";

// ---------- page chrome ----------

export const Scene: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill
    style={{
      backgroundColor: C.surface,
      fontFamily: FONT,
      color: C.ink,
      padding: `${SAFE_Y}px ${SAFE_X}px`,
      display: "flex",
      flexDirection: "column",
      ...style,
    }}
  >
    {children}
  </AbsoluteFill>
);

export const Headline: React.FC<{ from?: number; size?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  from = 0,
  size = T.headline,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ fontSize: size, fontWeight: 600, lineHeight: 1.12, letterSpacing: -1.5, ...enter(frame, from), ...style }}>
      {children}
    </div>
  );
};

export const Sub: React.FC<{ from?: number; size?: number; color?: string; children: React.ReactNode; style?: React.CSSProperties }> = ({
  from = 0,
  size = T.sub,
  color = C.ink2,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ fontSize: size, fontWeight: 400, lineHeight: 1.3, color, ...enter(frame, from), ...style }}>{children}</div>
  );
};

export const Kicker: React.FC<{ from?: number; children: React.ReactNode }> = ({ from = 0, children }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        fontSize: T.small,
        fontWeight: 600,
        letterSpacing: 2.5,
        textTransform: "uppercase",
        color: C.muted,
        marginBottom: 22,
        ...enter(frame, from),
      }}
    >
      {children}
    </div>
  );
};

// ---------- a mesh card: fine or cheap ----------

export const MeshCard: React.FC<{ kind: "fine" | "cheap"; from: number; width?: number }> = ({ kind, from, width = 560 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(frame, fps, from);
  const n = kind === "fine" ? 12 : 4;
  const color = kind === "fine" ? C.fine : C.cheap;
  const w = width - 64, h = 180;
  const draw = ease(frame, from + 8, 36);
  return (
    <div
      style={{
        width,
        padding: 32,
        borderRadius: 20,
        background: "#fff",
        boxShadow: `0 1px 0 ${C.border}, 0 14px 40px rgba(11,11,11,0.07)`,
        opacity: p,
        scale: String(0.94 + 0.06 * p),
        translate: `0px ${(1 - p) * 30}px`,
      }}
    >
      <svg width={w} height={h} style={{ display: "block" }}>
        {/* a ring's wall seen in section, split into n rows x 2n columns */}
        {Array.from({ length: n + 1 }, (_, i) => (
          <line key={`h${i}`} x1={0} x2={w * draw} y1={(h / n) * i} y2={(h / n) * i} stroke={color} strokeWidth={1.5} opacity={0.9} />
        ))}
        {Array.from({ length: 2 * n + 1 }, (_, i) => (
          <line
            key={`v${i}`}
            x1={(w / (2 * n)) * i}
            x2={(w / (2 * n)) * i}
            y1={0}
            y2={h * draw}
            stroke={color}
            strokeWidth={1.5}
            opacity={i / (2 * n) <= draw ? 0.9 : 0}
          />
        ))}
      </svg>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginTop: 26 }}>
        <div style={{ fontSize: T.sub, fontWeight: 600 }}>{kind === "fine" ? "Fine mesh" : "Cheap mesh"}</div>
        <div style={{ fontSize: T.sub, fontWeight: 600, color }}>{kind === "fine" ? "34 s" : "2 s"}</div>
      </div>
      <div style={{ fontSize: T.small, color: C.ink2, marginTop: 8 }}>
        {kind === "fine" ? "per run · very accurate" : "per run · slightly off, in a consistent way"}
      </div>
    </div>
  );
};

// ---------- the toy curve panel ----------

type Panel = {
  variant: "fine" | "cheap" | "mix";
  width?: number;
  height?: number;
  progress: number; // 0..1 over the panel's own build-up
};

const toPath = (pts: Pt[], sx: (x: number) => number, sy: (y: number) => number) =>
  pts.map((p, i) => `${i ? "L" : "M"}${sx(p.x).toFixed(1)} ${sy(p.y).toFixed(1)}`).join(" ");

const bandPath = (mid: Pt[], half: Pt[], sx: (x: number) => number, sy: (y: number) => number) => {
  const up = mid.map((p, i) => `${i ? "L" : "M"}${sx(p.x).toFixed(1)} ${sy(p.y + half[i].y).toFixed(1)}`).join(" ");
  const dn = [...mid]
    .reverse()
    .map((p, i) => `L${sx(p.x).toFixed(1)} ${sy(p.y - half[mid.length - 1 - i].y).toFixed(1)}`)
    .join(" ");
  return `${up} ${dn} Z`;
};

const length = (pts: Pt[], sx: (x: number) => number, sy: (y: number) => number) => {
  let L = 0;
  for (let i = 1; i < pts.length; i++) L += Math.hypot(sx(pts[i].x) - sx(pts[i - 1].x), sy(pts[i].y) - sy(pts[i - 1].y));
  return L;
};

export const CurvePanel: React.FC<Panel> = ({ variant, width = 540, height = 300, progress }) => {
  const padL = 18, padR = 18, padT = 14, padB = 22;
  const sx = (x: number) => padL + x * (width - padL - padR);
  const sy = (y: number) => padT + (1 - (y - 0.05) / 1.05) * (height - padT - padB);
  const color = variant === "fine" ? C.fine : variant === "cheap" ? C.cheap : C.mix;
  const soft = variant === "fine" ? C.fineSoft : variant === "cheap" ? C.cheapSoft : C.mixSoft;
  const model = variant === "fine" ? cv.fineModel : variant === "cheap" ? cv.cheapModel : cv.mixModel;
  const band = variant === "fine" ? cv.fineBand : variant === "cheap" ? cv.cheapBand : cv.mixBand;

  // build-up: points 0-0.35, line 0.3-0.65, band 0.6-0.8, truth 0.75-1
  const seg = (a: number, b: number) => Math.min(1, Math.max(0, (progress - a) / (b - a)));
  const pPts = seg(0, 0.35), pLine = seg(0.3, 0.65), pBand = seg(0.6, 0.8), pTruth = seg(0.75, 1);
  const L = length(model, sx, sy);

  const dots = (pts: Pt[], r: number, fill: string, stroke: string, start: number, span: number, ring = false) =>
    pts.map((p, i) => {
      const t = Math.min(1, Math.max(0, (pPts - start - (i / pts.length) * span) / 0.25));
      const s = 1 - Math.pow(1 - t, 3);
      return (
        <circle
          key={i}
          cx={sx(p.x)}
          cy={sy(p.y)}
          r={r * s}
          fill={ring ? C.surface : fill}
          stroke={stroke}
          strokeWidth={ring ? 3 : 2}
          opacity={s}
        />
      );
    });

  return (
    <svg width={width} height={height} style={{ display: "block", overflow: "visible" }}>
      {/* recessive baseline and one hairline */}
      <line x1={padL} x2={width - padR} y1={height - padB} y2={height - padB} stroke={C.axis} strokeWidth={1} />

      {/* uncertainty band */}
      <path d={bandPath(model, band, sx, sy)} fill={soft} opacity={0.75 * pBand} />

      {/* cheap curve shown faintly under the mix, to show what is being corrected */}
      {variant === "mix" ? (
        <path d={toPath(cv.cheapLine, sx, sy)} fill="none" stroke={C.cheap} strokeWidth={2} opacity={0.35 * pLine} />
      ) : null}

      {/* the true answer */}
      <path d={toPath(cv.truthLine, sx, sy)} fill="none" stroke={C.truth} strokeWidth={2} strokeDasharray="7 7" opacity={pTruth} />

      {/* the model's prediction, drawn left to right */}
      <path
        d={toPath(model, sx, sy)}
        fill="none"
        stroke={color}
        strokeWidth={3.5}
        strokeLinecap="round"
        strokeDasharray={L}
        strokeDashoffset={L * (1 - pLine)}
      />

      {/* data */}
      {variant === "fine" ? dots(cv.finePts, 8, color, C.surface, 0, 0.6) : null}
      {variant === "cheap" ? dots(cv.cheapPts, 4.5, color, C.surface, 0, 0.8) : null}
      {variant === "mix" ? (
        <>
          {dots(cv.cheapPts, 3.5, C.cheap, C.surface, 0, 0.55)}
          {cv.mixFinePts.map((p, i) => {
            const t = Math.min(1, Math.max(0, (pPts - 0.55 - i * 0.1) / 0.25));
            return (
              <line
                key={`a${i}`}
                x1={sx(p.x)}
                x2={sx(p.x)}
                y1={sy(cv.cheap(p.x))}
                y2={sy(cv.cheap(p.x)) + (sy(p.y) - sy(cv.cheap(p.x))) * t}
                stroke={C.mix}
                strokeWidth={2}
                opacity={0.7 * t}
              />
            );
          })}
          {dots(cv.mixFinePts, 9, C.mix, C.mix, 0.55, 0.4, true)}
        </>
      ) : null}

      {/* truth label, once drawn */}
      <text x={sx(0.3)} y={sy(cv.truth(0.3)) + 44} textAnchor="middle" fontFamily={FONT} fontSize={21} fill={C.truth} opacity={pTruth}>
        true answer
      </text>
    </svg>
  );
};

// ---------- horizontal bar ----------

export const Bar: React.FC<{
  label: string;
  note?: string;
  value: number;
  max: number;
  color: string;
  from: number;
  format: (v: number) => string;
  width: number;
  target?: number;
  emphasis?: boolean;
}> = ({ label, note, value, max, color, from, format, width, target, emphasis }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = place(frame, fps, from);
  const shown = ease(frame, from, 36) * value;
  const labelW = 420;
  const barW = width - labelW - 140;
  const H = 40;
  return (
    <div style={{ display: "flex", alignItems: "center", height: note ? H + 38 : H + 22, opacity: ease(frame, from - 6, 14) }}>
      <div style={{ width: labelW, paddingRight: 28 }}>
        <div style={{ fontSize: T.body, fontWeight: emphasis ? 600 : 500, color: emphasis ? C.ink : C.ink2 }}>{label}</div>
        {note ? <div style={{ fontSize: T.tiny, color: C.muted, marginTop: 3 }}>{note}</div> : null}
      </div>
      <div style={{ position: "relative", width: barW, height: H }}>
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            height: H,
            width: Math.max(0, (barW * value) / max) * p,
            background: color,
            borderRadius: "0 6px 6px 0",
            opacity: emphasis ? 1 : 0.82,
          }}
        />
        {target !== undefined ? (
          <div style={{ position: "absolute", left: (barW * target) / max, top: -10, height: H + 20, width: 2, background: C.ink2 }} />
        ) : null}
        <div
          style={{
            position: "absolute",
            left: ((barW * value) / max) * p + 16,
            top: 0,
            height: H,
            display: "flex",
            alignItems: "center",
            fontSize: T.body,
            fontWeight: 600,
            color: C.ink,
            whiteSpace: "nowrap",
          }}
        >
          {format(shown)}
        </div>
      </div>
    </div>
  );
};

// ---------- a stat tile ----------

export const Stat: React.FC<{ label: string; value: string; from: number; color?: string; width?: number }> = ({
  label,
  value,
  from,
  color = C.ink,
  width = 380,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(frame, fps, from);
  return (
    <div
      style={{
        width,
        padding: "20px 28px",
        borderRadius: 18,
        background: "#fff",
        boxShadow: `0 1px 0 ${C.border}, 0 10px 30px rgba(11,11,11,0.06)`,
        opacity: p,
        translate: `0px ${(1 - p) * 24}px`,
      }}
    >
      <div style={{ fontSize: 54, fontWeight: 600, letterSpacing: -1.5, color, lineHeight: 1.05 }}>{value}</div>
      <div style={{ fontSize: T.tiny, color: C.ink2, marginTop: 8, lineHeight: 1.3 }}>{label}</div>
    </div>
  );
};

// ---------- legend swatch ----------

export const Swatch: React.FC<{ color: string; label: string; ring?: boolean }> = ({ color, label, ring }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: T.small, color: C.ink2 }}>
    <div
      style={{
        width: 18,
        height: 18,
        borderRadius: 9,
        background: ring ? C.surface : color,
        border: `3px solid ${color}`,
        boxSizing: "border-box",
      }}
    />
    {label}
  </div>
);

// ---------- narration ----------

export const Narration: React.FC<{ k: string; from?: number }> = ({ k, from = 0 }) =>
  hasClip(k) ? (
    <Sequence from={from} layout="none">
      <Audio src={staticFile(`vo/${k}.wav`)} />
    </Sequence>
  ) : null;
