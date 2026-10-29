import React from "react";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { Budget } from "./scenes/Budget";
import { Confirm } from "./scenes/Confirm";
import { Goal } from "./scenes/Goal";
import { Hook } from "./scenes/Hook";
import { Picking } from "./scenes/Picking";
import { Results } from "./scenes/Results";
import { Takeaway } from "./scenes/Takeaway";
import { ThreeWays, threeWaysStarts } from "./scenes/ThreeWays";
import { clipFrames } from "./vo";

export const FPS = 30;
export const FADE = 14;

// Scene lengths: long enough for the narration, never shorter than the visuals need.
export const scenes = (fps: number) => ({
  hook: clipFrames("long_hook", fps, 170),
  goal: clipFrames("long_goal", fps, 210),
  budget: clipFrames("long_budget", fps, 230),
  three: threeWaysStarts(fps).end,
  results: clipFrames("long_results", fps, 400),
  confirm: clipFrames("long_confirm", fps, 330),
  picking: clipFrames("long_picking", fps, 360, 1.0),
  takeaway: clipFrames("long_takeaway", fps, 230),
});
export const totalFrames = (fps: number) => Object.values(scenes(fps)).reduce((a, b) => a + b, 0) - 7 * FADE;

// TransitionSeries checks its direct children, so the transitions are written out rather than wrapped.
export const Explainer: React.FC = () => {
  const s = scenes(FPS);
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={s.hook}><Hook /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.goal}><Goal /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.budget}><Budget /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.three}><ThreeWays /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.results}><Results /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.confirm}><Confirm /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.picking}><Picking /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.takeaway}><Takeaway /></TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
