// Every number shown in the video, with where it comes from in the repository.

// README main table: results/final/summary.md, seeds 1-8, final scores at about 1.05-1.10 CPU hours.
export const FINAL = {
  fine: { label: "Fine runs only", runs: "~125 fine runs", rmse: 0.484, coverage: 0.9 },
  cheap: { label: "Cheap runs only", runs: "~1,700 cheap runs", rmse: 0.257, coverage: 0.68 },
  mix: { label: "Mix of both", runs: "~1,160 cheap + 50 fine", rmse: 0.205, coverage: 0.91 },
};

// Pre-registered confirmation: results/confirm/confirm.md, seeds 9-20, scores at 1.0 CPU hour.
export const CONFIRM = {
  seeds: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
  cheap: [0.212, 0.216, 0.254, 0.27, 0.261, 0.255, 0.252, 0.224, 0.237, 0.295, 0.234, 0.301],
  mix: [0.172, 0.126, 0.112, 0.162, 0.11, 0.29, 0.161, 0.149, 0.195, 0.25, 0.147, 0.26],
  meanCheap: 0.251,
  meanMix: 0.178,
  coverageCheap: 0.67,
  coverageMix: 0.94,
  wins: 11,
  relGain: 0.295,
  p: 0.0005,
};

// Solver cost per run, CPU seconds (README, "The fidelity pair").
export const COST = { fine: 34, cheap: 2, budget: 3600 };
