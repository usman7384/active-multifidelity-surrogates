import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ease, enter, place } from "../anim";
import { CONFIRM } from "../data";
import { Headline, Kicker, Narration, Scene, Stat, Sub, Swatch } from "../components";
import { C, FONT, T } from "../theme";

// Twelve fresh trials, each a dumbbell from the cheap-only error to the mix error.
const Dumbbells: React.FC<{ from: number }> = ({ from }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const W = 980, H = 470, padL = 110, padR = 40, padT = 16, padB = 50;
  const n = CONFIRM.seeds.length;
  const rowH = (H - padT - padB) / n;
  const sx = (v: number) => padL + (v / 0.35) * (W - padL - padR);
  return (
    <svg width={W} height={H} style={{ display: "block", overflow: "visible", opacity: ease(frame, from - 8, 14) }}>
      {[0, 0.1, 0.2, 0.3].map((v) => (
        <g key={v}>
          <line x1={sx(v)} x2={sx(v)} y1={padT} y2={H - padB} stroke={C.grid} strokeWidth={1} />
          <text x={sx(v)} y={H - padB + 30} textAnchor="middle" fontFamily={FONT} fontSize={22} fill={C.muted}>
            {v.toFixed(1)}
          </text>
        </g>
      ))}
      <text x={sx(0.175)} y={H + 8} textAnchor="middle" fontFamily={FONT} fontSize={22} fill={C.muted}>
        prediction error, lower is better
      </text>
      {CONFIRM.seeds.map((s, i) => {
        const y = padT + rowH * (i + 0.5);
        const t = place(frame, fps, from + 6 + i * 7);
        const a = CONFIRM.cheap[i], b = CONFIRM.mix[i];
        const win = b < a;
        return (
          <g key={s} opacity={Math.min(1, t * 1.5)}>
            <text x={padL - 18} y={y + 8} textAnchor="end" fontFamily={FONT} fontSize={23} fill={C.ink2}>
              trial {i + 1}
            </text>
            <line x1={sx(a)} x2={sx(a) + (sx(b) - sx(a)) * t} y1={y} y2={y} stroke={win ? C.mix : C.cheap} strokeWidth={3} opacity={0.45} />
            <circle cx={sx(a)} cy={y} r={9} fill={C.cheap} stroke={C.surface} strokeWidth={2} />
            <circle cx={sx(a) + (sx(b) - sx(a)) * t} cy={y} r={10} fill={C.mix} stroke={C.surface} strokeWidth={2} />
          </g>
        );
      })}
    </svg>
  );
};

// Scene 6: the pre-registered check on fresh trials.
export const Confirm: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene>
      <Narration k="long_confirm" />
      <Kicker from={0}>Then we checked it properly</Kicker>
      <Headline from={6} size={76}>Test written down first. Then 12 fresh trials.</Headline>
      <Sub from={18} size={T.body} style={{ marginTop: 10 }}>
        Cheap runs only against the mix, same hour of computer time, trials the method had never seen.
      </Sub>
      <div style={{ display: "flex", gap: 70, marginTop: 36, alignItems: "flex-start" }}>
        <div>
          <Dumbbells from={40} />
          <div style={{ display: "flex", gap: 36, marginTop: 34, marginLeft: 110, ...enter(frame, 48) }}>
            <Swatch color={C.cheap} label="cheap runs only" />
            <Swatch color={C.mix} label="mix of both" />
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 22, marginTop: 4 }}>
          <Stat from={150} value={`${CONFIRM.wins} of 12`} label="trials where the mix had lower error" color={C.mix} width={520} />
          <Stat from={168} value={`${Math.round(CONFIRM.relGain * 100)}% lower`} label="error on average, for the same compute" color={C.mix} width={520} />
          <Stat from={186} value={`${Math.round(CONFIRM.coverageCheap * 100)}% → ${Math.round(CONFIRM.coverageMix * 100)}%`} label={`how often "95% sure" was right, cheap → mix`} width={520} />
        </div>
      </div>
      <div style={{ position: "absolute", left: 120, bottom: 66, fontSize: T.tiny, color: C.muted, ...enter(frame, 230) }}>
        Pre-registered one-sided Wilcoxon test, p = {CONFIRM.p}. A result this strong by chance: about 1 in 2,000.
      </div>
    </Scene>
  );
};
