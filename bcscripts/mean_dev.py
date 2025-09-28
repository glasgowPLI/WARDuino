# bcscripts/compute_stats.py
#!/usr/bin/env python3
"""
Compute mean/std per (Benchmark, Build) from matrix CSV:
  Benchmark,<build1>,<build2>,...
  foo.wasm,0.12;0.11;FAIL,0.09;0.10;...

Outputs: results_stats.csv with columns:
  Benchmark,Build,N,Mean(s),StdDev(s),Min(s),Max(s)
"""

import csv
import math
import os
import sys
from typing import List, Tuple

IN_CSV  = os.environ.get("RESULTS_CSV", "results_matrix.csv")
OUT_CSV = os.environ.get("RESULTS_STATS", "results_stats.csv")

def parse_cell(cell: str) -> List[float]:
    xs: List[float] = []
    if not cell:
        return xs
    for tok in cell.split(";"):
        t = tok.strip()
        if not t or t.upper() == "FAIL":
            continue
        try:
            xs.append(float(t))
        except ValueError:
            # why: tolerate stray tokens
            pass
    return xs

def mean_std(vals: List[float]) -> Tuple[int, float, float, float, float]:
    n = len(vals)
    if n == 0:
        return 0, math.nan, math.nan, math.nan, math.nan
    if n == 1:
        v = vals[0]
        return 1, v, 0.0, v, v
    s = sum(vals)
    m = s / n
    var = sum((x - m) ** 2 for x in vals) / (n - 1)  # sample stddev
    return n, m, math.sqrt(var), min(vals), max(vals)

def load_matrix(path: str):
    if not os.path.exists(path):
        sys.exit(f"Missing CSV: {path}")
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    if not rows or rows[0][0] != "Benchmark":
        sys.exit("CSV header must start with 'Benchmark'")
    header = rows[0]
    builds = header[1:]
    data = rows[1:]
    return builds, data

def main():
    builds, data = load_matrix(IN_CSV)

    # Write tidy stats
    with open(OUT_CSV, "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["Benchmark", "Build", "N", "Mean(s)", "StdDev(s)", "Min(s)", "Max(s)"])

        # Track per-build overall mean of per-benchmark means
        per_build_means = {b: [] for b in builds}

        for r in data:
            bench = r[0]
            for i, b in enumerate(builds, start=1):
                cell = r[i] if i < len(r) else ""
                vals = parse_cell(cell)
                n, mu, sd, mn, mx = mean_std(vals)
                w.writerow([
                    bench,
                    b,
                    n,
                    "" if math.isnan(mu) else f"{mu:.6g}",
                    "" if math.isnan(sd) else f"{sd:.6g}",
                    "" if math.isnan(mn) else f"{mn:.6g}",
                    "" if math.isnan(mx) else f"{mx:.6g}",
                ])
                if not math.isnan(mu):
                    per_build_means[b].append(mu)

    print(f"✅ Wrote {OUT_CSV}")

    # Short summary to stdout
    print("📄 Overall (mean of per-benchmark means):")
    for b in builds:
        vals = per_build_means[b]
        overall = (sum(vals) / len(vals)) if vals else math.nan
        msg = "nan" if math.isnan(overall) else f"{overall:.6g}"
        print(f"  {b:>16}: {msg}  (n_bench={len(vals)})")

if __name__ == "__main__":
    main()
