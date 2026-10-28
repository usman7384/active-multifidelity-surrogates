// The toy one-dimensional picture used to explain the three strategies: a true curve, a cheap curve that is
// offset from it (the coarse mesh's bias, growing to the right as it does on thick rings), and what a model
// fitted to each kind of data would predict, with how unsure it is.
import { rng } from "./anim";

export type Pt = { x: number; y: number };

// A smooth hill plus a narrow dip at x = 0.78 (the fold-over region): four fine points straddle the dip and
// never see it, many cheap points do.
export const truth = (x: number) =>
  0.5 + 0.24 * Math.sin(5.6 * x - 1.1) + 0.08 * x - 0.16 * Math.exp(-(((x - 0.78) / 0.055) ** 2));
export const cheap = (x: number) => truth(x) + 0.13 + 0.1 * x;

const sample = (f: (x: number) => number, n = 80): Pt[] =>
  Array.from({ length: n + 1 }, (_, i) => ({ x: i / n, y: f(i / n) }));

// Fine-only: four accurate points at uneven spots; the model is a smooth curve through them (Catmull-Rom) and
// misses the dip it never sampled. Unsure far from its points.
const FINE_X = [0.04, 0.4, 0.58, 0.97];
export const finePts: Pt[] = FINE_X.map((x) => ({ x, y: truth(x) }));

const catmull = (pts: Pt[], x: number): number => {
  const n = pts.length;
  let i = 0;
  while (i < n - 2 && x > pts[i + 1].x) i++;
  const p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, n - 1)];
  const t = (x - p1.x) / (p2.x - p1.x);
  const t2 = t * t, t3 = t2 * t;
  return 0.5 * (2 * p1.y + (-p0.y + p2.y) * t + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3);
};
const nearest = (x: number, xs: number[]) => Math.min(...xs.map((p) => Math.abs(x - p)));

export const fineModel = sample((x) => catmull(finePts, x));
export const fineBand = sample((x) => 0.025 + 0.42 * nearest(x, FINE_X));

// Cheap-only: many points on the offset curve; the model follows them tightly.
const r = rng(7);
export const cheapPts: Pt[] = Array.from({ length: 34 }, (_, i) => {
  const x = (i + 0.5) / 34 + (r() - 0.5) * 0.02;
  return { x, y: cheap(x) + (r() - 0.5) * 0.03 };
});
export const cheapModel = sample(cheap);
export const cheapBand = sample(() => 0.028);

// Mix: the same cheap points plus four fine anchors; the correction pulls the curve onto the truth.
const MIX_X = [0.1, 0.38, 0.66, 0.9];
export const mixFinePts: Pt[] = MIX_X.map((x) => ({ x, y: truth(x) }));
export const mixModel = sample((x) => truth(x) + 0.012 * Math.sin(23 * x));
export const mixBand = sample((x) => 0.04 + 0.06 * nearest(x, MIX_X));

export const truthLine = sample(truth);
export const cheapLine = sample(cheap);
