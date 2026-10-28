import { Easing, interpolate, spring } from "remotion";

// 0 -> 1 over `dur` frames starting at `from`, with a decelerating ease (the "settle" curve).
export const ease = (frame: number, from: number, dur: number): number =>
  interpolate(frame, [from, from + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

// A push with no bounce, for things that enter.
export const pop = (frame: number, fps: number, from: number): number =>
  spring({ frame: frame - from, fps, config: { damping: 200 }, durationInFrames: 28 });

// A little overshoot, for marks that should feel placed.
export const place = (frame: number, fps: number, from: number): number =>
  spring({ frame: frame - from, fps, config: { damping: 14, stiffness: 120, mass: 0.8 } });

// Entering text: opacity and a short rise.
export const enter = (frame: number, from: number, dur = 22) => {
  const p = ease(frame, from, dur);
  return { opacity: p, translate: `0px ${(1 - p) * 26}px` };
};

// Deterministic noise so every render is identical.
export const rng = (seed: number) => {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
};
