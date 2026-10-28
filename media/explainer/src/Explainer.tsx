import React from "react";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { Budget } from "./scenes/Budget";
import { Confirm } from "./scenes/Confirm";
import { Goal } from "./scenes/Goal";
import { Hook } from "./scenes/Hook";
import { Results } from "./scenes/Results";
import { Takeaway } from "./scenes/Takeaway";
import { ThreeWays } from "./scenes/ThreeWays";

// Scene lengths in frames at 30 fps. Transitions overlap, so the total is the sum minus 6 x FADE.
export const SCENES = { hook: 170, goal: 210, budget: 230, three: 640, results: 400, confirm: 330, takeaway: 230 };
export const FADE = 14;
export const TOTAL = Object.values(SCENES).reduce((a, b) => a + b, 0) - 6 * FADE;

// TransitionSeries checks its direct children, so the transitions are written out rather than wrapped.
export const Explainer: React.FC = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence durationInFrames={SCENES.hook}><Hook /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
    <TransitionSeries.Sequence durationInFrames={SCENES.goal}><Goal /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
    <TransitionSeries.Sequence durationInFrames={SCENES.budget}><Budget /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
    <TransitionSeries.Sequence durationInFrames={SCENES.three}><ThreeWays /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
    <TransitionSeries.Sequence durationInFrames={SCENES.results}><Results /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
    <TransitionSeries.Sequence durationInFrames={SCENES.confirm}><Confirm /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
    <TransitionSeries.Sequence durationInFrames={SCENES.takeaway}><Takeaway /></TransitionSeries.Sequence>
  </TransitionSeries>
);
