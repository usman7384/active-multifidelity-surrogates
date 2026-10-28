import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ease, enter, pop, rng } from "../anim";
import { IVR_FLOOR } from "../data";
import { Headline, Kicker, Narration, Scene, Sub } from "../components";
import { C, FONT, T } from "../theme";
import { clipFrames } from "../vo";

// Latin hypercube: one point per row and per column, decided before any run.
const lhsPts = (() => {
  const r = rng(11);
  const cols = [0, 1, 2, 3, 4, 5, 6, 7];
  for (let i = cols.length - 1; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    [cols[i], cols[j]] = [cols[j], cols[i]];
  }
  return cols.map((c, row) => ({ x: (c + 0.3 + 0.4 * r()) / 8, y: (row + 0.3 + 0.4 * r()) / 8 }));
})();

// IVR: points land where the model is unsure, and some of them are fine runs (rings).
const ivrPts = (() => {
  const r = rng(5);
  const out: { x: number; y: number; fine: boolean }[] = [];
  for (let i = 0; i < 14; i++) {
    const near = r() < 0.6;
    const x = near ? 0.62 + 0.25 * (r() - 0.5) : r();
    const y = near ? 0.35 + 0.3 * (r() - 0.5) : r();
    out.push({ x, y, fine: i % 4 === 0 });
  }
  return out;
})();

export const PickCard: React.FC<{ kind: "lhs" | "ivr"; from: number; width?: number; compact?: boolean }> = ({
  kind,
  from,
  width = 760,
  compact,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(frame, fps, from);
  const W = compact ? 220 : 360, H = compact ? 150 : 240;
  const sx = (x: number) => 12 + x * (W - 24), sy = (y: number) => 12 + y * (H - 24);
  const color = kind === "lhs" ? C.cheap : C.mix;
  return (
    <div
      style={{
        width,
        display: "flex",
        gap: compact ? 24 : 36,
        padding: compact ? 20 : 28,
        borderRadius: 20,
        background: "#fff",
        boxShadow: `0 1px 0 ${C.border}, 0 14px 40px rgba(11,11,11,0.07)`,
        opacity: p,
        translate: `0px ${(1 - p) * 30}px`,
      }}
    >
      <svg width={W} height={H} style={{ flex: "none", background: C.plane, borderRadius: 12 }}>
        {kind === "ivr" ? (
          <ellipse cx={sx(0.62)} cy={sy(0.35)} rx={W * 0.2} ry={H * 0.2} fill={C.mixSoft} opacity={0.8 * ease(frame, from + 8, 30)} />
        ) : null}
        {kind === "lhs"
          ? lhsPts.map((q, i) => {
              const t = ease(frame, from + 6 + i * 3, 16);
              return <circle key={i} cx={sx(q.x)} cy={sy(q.y)} r={7 * t} fill={color} />;
            })
          : ivrPts.map((q, i) => {
              const t = ease(frame, from + 14 + i * 4, 16);
              return q.fine ? (
                <circle key={i} cx={sx(q.x)} cy={sy(q.y)} r={8 * t} fill={C.surface} stroke={color} strokeWidth={3} />
              ) : (
                <circle key={i} cx={sx(q.x)} cy={sy(q.y)} r={6 * t} fill={color} />
              );
            })}
        {kind === "ivr" ? (
          <text x={sx(0.62)} y={sy(0.35) - H * 0.2 - 8} textAnchor="middle" fontFamily={FONT} fontSize={18} fill={C.ink2} opacity={ease(frame, from + 20, 20)}>
            model unsure here
          </text>
        ) : null}
      </svg>
      <div>
        <div style={{ fontSize: compact ? 28 : T.sub, fontWeight: 600, color, lineHeight: 1.15 }}>
          {kind === "lhs" ? "Latin hypercube" : "Integrated variance reduction"}
        </div>
        <div style={{ fontSize: compact ? 20 : T.small, color: C.ink2, marginTop: compact ? 8 : 10, lineHeight: 1.35 }}>
          {kind === "lhs"
            ? compact
              ? "Runs spread evenly, decided before any run. Simple, and hard to beat."
              : "Spread the runs evenly, one per row and column, decided before any run. Simple, and hard to beat."
            : compact
              ? "Each round the model picks the runs and the mesh that shrink its uncertainty most per CPU second."
              : "Each round the model picks the runs, and the mesh, that would shrink its uncertainty most per CPU second."}
        </div>
        <div style={{ fontSize: compact ? 20 : T.small, color: C.muted, marginTop: compact ? 6 : 10 }}>
          {kind === "lhs" ? "used by the winning method" : "active learning"}
        </div>
      </div>
    </div>
  );
};

// Scene: how the runs were chosen, and what letting the model choose did.
export const pickingVerdictAt = (fps: number) => clipFrames("long_picking", fps, 300, 0.3);

export const Picking: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const at = pickingVerdictAt(fps);
  const pending = IVR_FLOOR.verdict === null;
  return (
    <Scene>
      <Narration k="long_picking" />
      <Narration k="long_ivr" from={at} />
      <Kicker from={0}>One more question</Kicker>
      <Headline from={6} size={76}>How were the runs chosen?</Headline>
      <div style={{ display: "flex", gap: 40, marginTop: 56 }}>
        <PickCard kind="lhs" from={40} />
        <PickCard kind="ivr" from={130} />
      </div>
      <div style={{ marginTop: "auto", ...enter(frame, at + 10) }}>
        <div style={{ fontSize: T.sub, fontWeight: 600, color: pending ? C.muted : C.ink }}>
          {pending ? "IVR result: pending the pre-registered run" : IVR_FLOOR.verdict}
        </div>
        {IVR_FLOOR.detail ? <Sub size={T.body} style={{ marginTop: 10 }}>{IVR_FLOOR.detail}</Sub> : null}
      </div>
    </Scene>
  );
};
