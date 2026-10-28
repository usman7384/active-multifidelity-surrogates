import React from "react";
import { AbsoluteFill } from "remotion";
import { CurvePanel, Swatch } from "./components";
import { CONFIRM, FINAL, IVR_FLOOR } from "./data";
import { PickCard } from "./scenes/Picking";
import { C, FONT } from "./theme";

// The one-page result, as a still. Everything is at its final state (no frame dependence).

const Card: React.FC<{ v: "fine" | "cheap" | "mix"; title: string; runs: string; verdict: string }> = ({ v, title, runs, verdict }) => {
  const color = v === "fine" ? C.fine : v === "cheap" ? C.cheap : C.mix;
  return (
    <div style={{ width: 540 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div style={{ fontSize: 34, fontWeight: 600, color }}>{title}</div>
        <div style={{ fontSize: 22, color: C.muted }}>{runs}</div>
      </div>
      <div style={{ marginTop: 14, background: "#fff", borderRadius: 16, padding: 8, boxShadow: `0 1px 0 ${C.border}, 0 8px 24px rgba(11,11,11,0.05)` }}>
        <CurvePanel variant={v} width={524} height={230} progress={1} />
      </div>
      <div style={{ fontSize: 24, color: C.ink, marginTop: 14, lineHeight: 1.3, fontWeight: 500 }}>{verdict}</div>
    </div>
  );
};

const Row: React.FC<{ label: string; value: number; max: number; color: string; text: string; target?: number; strong?: boolean }> = ({
  label, value, max, color, text, target, strong,
}) => {
  const barW = 520;
  return (
    <div style={{ display: "flex", alignItems: "center", height: 44 }}>
      <div style={{ width: 230, fontSize: 24, color: strong ? C.ink : C.ink2, fontWeight: strong ? 600 : 500 }}>{label}</div>
      <div style={{ position: "relative", width: barW, height: 26 }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: 26, width: (barW * value) / max, background: color, borderRadius: "0 5px 5px 0", opacity: strong ? 1 : 0.82 }} />
        {target !== undefined ? <div style={{ position: "absolute", left: (barW * target) / max, top: -7, height: 40, width: 2, background: C.ink2 }} /> : null}
        <div style={{ position: "absolute", left: (barW * value) / max + 12, top: -3, fontSize: 24, fontWeight: 600 }}>{text}</div>
      </div>
    </div>
  );
};

const Tile: React.FC<{ value: string; label: string; color?: string }> = ({ value, label, color = C.ink }) => (
  <div style={{ padding: "18px 24px", borderRadius: 14, background: "#fff", boxShadow: `0 1px 0 ${C.border}, 0 8px 24px rgba(11,11,11,0.05)`, width: 340 }}>
    <div style={{ fontSize: 44, fontWeight: 600, letterSpacing: -1, color, lineHeight: 1.05, whiteSpace: "nowrap" }}>{value}</div>
    <div style={{ fontSize: 20, color: C.ink2, marginTop: 8, lineHeight: 1.3 }}>{label}</div>
  </div>
);

export const Overview: React.FC = () => (
  <AbsoluteFill style={{ background: C.surface, fontFamily: FONT, color: C.ink, padding: "70px 100px" }}>
    <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: 2.5, textTransform: "uppercase", color: C.muted }}>
      Active multi-fidelity surrogates · ring compression test
    </div>
    <div style={{ fontSize: 54, fontWeight: 600, letterSpacing: -1.5, marginTop: 10, lineHeight: 1.1, maxWidth: 1500 }}>
      Mixing cheap and expensive simulations: <span style={{ color: C.mix }}>30% less error</span> for the same hour of compute
    </div>

    <div style={{ display: "flex", gap: 50, marginTop: 44 }}>
      <Card v="fine" title="Fine runs only" runs={FINAL.fine.runs} verdict="Accurate points, too few: the model misses whole features between them." />
      <Card v="cheap" title="Cheap runs only" runs={FINAL.cheap.runs} verdict="Many points, all slightly off: the model becomes confidently wrong." />
      <Card v="mix" title="Mix of both" runs={FINAL.mix.runs} verdict="Cheap runs draw the shape; a few fine runs teach the model the offset." />
    </div>
    <div style={{ display: "flex", gap: 34, marginTop: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 21, color: C.ink2 }}>
        <svg width={34} height={6}><line x1={0} x2={34} y1={3} y2={3} stroke={C.truth} strokeWidth={2} strokeDasharray="6 6" /></svg>
        true answer
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 21, color: C.ink2 }}>
        <div style={{ width: 34, height: 12, background: C.mixSoft, borderRadius: 3 }} />
        how unsure the model is
      </div>
      <Swatch color={C.fine} label="fine run" />
      <Swatch color={C.cheap} label="cheap run" />
    </div>

    <div style={{ display: "flex", gap: 60, marginTop: 44, alignItems: "flex-start" }}>
      <div>
        <div style={{ fontSize: 26, fontWeight: 600 }}>Prediction error after 1 CPU hour <span style={{ color: C.muted, fontWeight: 400 }}>· lower is better · 8 trials</span></div>
        <div style={{ marginTop: 10 }}>
          <Row label="Fine runs only" value={FINAL.fine.rmse} max={0.56} color={C.fine} text={FINAL.fine.rmse.toFixed(2)} />
          <Row label="Cheap runs only" value={FINAL.cheap.rmse} max={0.56} color={C.cheap} text={FINAL.cheap.rmse.toFixed(2)} />
          <Row label="Mix of both" value={FINAL.mix.rmse} max={0.56} color={C.mix} text={FINAL.mix.rmse.toFixed(2)} strong />
        </div>
        <div style={{ fontSize: 26, fontWeight: 600, marginTop: 22 }}>When it says "95% sure", how often is it right? <span style={{ color: C.muted, fontWeight: 400 }}>· target 95%</span></div>
        <div style={{ marginTop: 10 }}>
          <Row label="Fine runs only" value={FINAL.fine.coverage} max={1} color={C.fine} text={`${Math.round(FINAL.fine.coverage * 100)}%`} target={0.95} />
          <Row label="Cheap runs only" value={FINAL.cheap.coverage} max={1} color={C.cheap} text={`${Math.round(FINAL.cheap.coverage * 100)}%`} target={0.95} />
          <Row label="Mix of both" value={FINAL.mix.coverage} max={1} color={C.mix} text={`${Math.round(FINAL.mix.coverage * 100)}%`} target={0.95} strong />
        </div>
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 26, fontWeight: 600 }}>Confirmed on 12 fresh trials <span style={{ color: C.muted, fontWeight: 400 }}>· test written down before running</span></div>
        <div style={{ display: "grid", gridTemplateColumns: "340px 340px", gap: 20, marginTop: 16 }}>
          <Tile value={`${CONFIRM.wins} of 12`} label="trials where the mix had lower error than cheap runs only" color={C.mix} />
          <Tile value={`${Math.round(CONFIRM.relGain * 100)}% lower`} label="error on average, same compute" color={C.mix} />
          <Tile value={`${Math.round(CONFIRM.coverageCheap * 100)}% → ${Math.round(CONFIRM.coverageMix * 100)}%`} label={`"95% sure" actually right, cheap → mix`} />
          <Tile value={`p = ${CONFIRM.p}`} label="pre-registered one-sided Wilcoxon test" />
        </div>
      </div>
    </div>

    <div style={{ marginTop: 40 }}>
      <div style={{ fontSize: 26, fontWeight: 600 }}>
        How the runs were chosen <span style={{ color: C.muted, fontWeight: 400 }}>· a fixed design against active learning</span>
      </div>
      <div style={{ display: "flex", gap: 30, marginTop: 14, alignItems: "stretch" }}>
        <PickCard kind="lhs" from={-100} width={600} compact />
        <PickCard kind="ivr" from={-100} width={600} compact />
        <div style={{ flex: 1, padding: "20px 24px", borderRadius: 14, background: "#fff", boxShadow: `0 1px 0 ${C.border}, 0 8px 24px rgba(11,11,11,0.05)` }}>
          <div style={{ fontSize: 22, fontWeight: 600, color: IVR_FLOOR.verdict ? C.ink : C.muted, lineHeight: 1.3 }}>
            {IVR_FLOOR.verdict ?? "IVR with a fine-run floor: pre-registered run in progress"}
          </div>
          {IVR_FLOOR.detail ? <div style={{ fontSize: 20, color: C.ink2, marginTop: 10, lineHeight: 1.35 }}>{IVR_FLOOR.detail}</div> : null}
          <div style={{ fontSize: 20, color: C.ink2, marginTop: 10, lineHeight: 1.35 }}>
            Without the floor (seeds 1-8) IVR tied the Latin hypercube on average and beat cheap runs in 7 of 8, but its
            result swung with how many fine runs it bought.
          </div>
        </div>
      </div>
    </div>

    <div style={{ position: "absolute", left: 100, right: 100, bottom: 44, display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 60, fontSize: 20, color: C.muted }}>
      <div style={{ maxWidth: 1180, lineHeight: 1.35 }}>Fine mesh: 34 s per run, within 0.013 of the reference mesh. Cheap mesh: 2 s per run. Model: Gaussian process, fine = cheap + a learned correction.</div>
      <div style={{ whiteSpace: "nowrap" }}>github.com/usman7384 · active-multifidelity-surrogates</div>
    </div>
  </AbsoluteFill>
);
