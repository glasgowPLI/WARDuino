# bcscripts/norm_pairs_chart.py
#!/usr/bin/env python3
"""
Two-bar normalization per benchmark from results_stats.csv (no error bars).

Bars:
  A) purecap-hw-sw / purecap-hw
  B) native-sw    / native-nocheck

Options:
  --ymin/--ymax     Explicit y-axis limits.
  --pad FLOAT       Headroom for auto y-limits (default: 0.15).
  --around-one      Zoom around 1.0 using max deviation of ratios.

Input : results_stats.csv  (Benchmark,Build,N,Mean(s),StdDev(s),Min(s),Max(s))
Output: norm_pairs.png

Note: Strips trailing ".wasm" from benchmark labels.
"""

import csv, math, os, sys, argparse
from typing import Dict, Tuple, List

IN_CSV  = os.environ.get("RESULTS_STATS", "results_stats.csv")
OUT_PNG = os.environ.get("RESULTS_PNG", "norm_pairs.png")

NUM_A, DEN_A = "purecap-hw-sw", "purecap-hw"
NUM_B, DEN_B = "native-sw", "native-nocheck"

def f2f(x: str) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")

def load_stats(path: str) -> Dict[str, Dict[str, Tuple[int, float, float]]]:
    if not os.path.exists(path):
        sys.exit(f"Missing input: {path}")
    out: Dict[str, Dict[str, Tuple[int, float, float]]] = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        need = {"Benchmark","Build","N","Mean(s)","StdDev(s)"}
        if not need.issubset(set(r.fieldnames or [])):
            sys.exit("CSV must have columns: " + ", ".join(sorted(need)))
        for row in r:
            bm  = row["Benchmark"]
            bld = row["Build"]
            n   = int(row["N"]) if row["N"] and row["N"].isdigit() else 0
            mu  = f2f(row["Mean(s)"]) if row["Mean(s)"] else float("nan")
            sd  = f2f(row["StdDev(s)"]) if row["StdDev(s)"] else float("nan")
            out.setdefault(bm, {})[bld] = (n, mu, sd)
    return out

def ratio(num, den) -> float:
    _, muN, _ = num
    _, muD, _ = den
    if math.isnan(muN) or math.isnan(muD) or muD <= 0.0:
        return float("nan")
    return muN / muD

def geom_mean(xs: List[float]) -> float:
    xs = [x for x in xs if x > 0 and not math.isnan(x)]
    if not xs:
        return float("nan")
    return math.exp(sum(math.log(x) for x in xs) / len(xs))

def parse_args():
    p = argparse.ArgumentParser(description="Plot two normalized bars per benchmark (no error bars).")
    p.add_argument("--in",   dest="in_csv",  default=IN_CSV)
    p.add_argument("--png",  dest="out_png", default=OUT_PNG)
    p.add_argument("--ymin", type=float, default=None)
    p.add_argument("--ymax", type=float, default=None)
    p.add_argument("--pad",  type=float, default=0.15, help="Headroom fraction for auto y-limits.")
    p.add_argument("--around-one", action="store_true", help="Zoom around 1.0 using max deviation of ratios.")
    return p.parse_args()

def main():
    args = parse_args()
    stats = load_stats(args.in_csv)

    labels: List[str] = []
    ratioA: List[float] = []
    ratioB: List[float] = []

    for bm, builds in sorted(stats.items()):
        if NUM_A not in builds or DEN_A not in builds:
            continue
        if NUM_B not in builds or DEN_B not in builds:
            continue

        rA = ratio(builds[NUM_A], builds[DEN_A])
        rB = ratio(builds[NUM_B], builds[DEN_B])
        if math.isnan(rA) or math.isnan(rB):
            continue

        label = bm[:-5] if bm.endswith(".wasm") else bm
        labels.append(label)
        ratioA.append(rA)
        ratioB.append(rB)

    if not labels:
        sys.exit("No benchmarks with both pairs available.")

    # Plot (falls back to text if matplotlib missing)
    try:
        import matplotlib.pyplot as plt
    except Exception:
        gA = geom_mean(ratioA); gB = geom_mean(ratioB)
        print(f"📄 geom mean A (purecap-hw-sw / purecap-hw): {gA}")
        print(f"📄 geom mean B (native-sw / native-nocheck): {gB}")
        for bm, a, b in zip(labels, ratioA, ratioB):
            print(f"{bm:25}  A={a:.3f}  B={b:.3f}")
        return

    x = list(range(len(labels)))
    bar_w = 0.38
    fig, ax = plt.subplots(figsize=(max(8, 0.5 * len(labels)), 4.5))

    # Two bars per benchmark (no yerr)
    ax.bar([i - bar_w/2 for i in x], ratioA, width=bar_w, label=f"{NUM_A}/{DEN_A}")
    ax.bar([i + bar_w/2 for i in x], ratioB, width=bar_w, label=f"{NUM_B}/{DEN_B}")

    # Y-limits from ratios only, with padding
    all_y = [v for v in (ratioA + ratioB) if not math.isnan(v)]
    if args.ymin is not None and args.ymax is not None:
        ymin, ymax = args.ymin, args.ymax
    elif args.around_one and all_y:
        dev = max(abs(v - 1.0) for v in all_y) or 0.05
        ymin = 1.0 - dev * (1 + args.pad)
        ymax = 1.0 + dev * (1 + args.pad)
    elif all_y:
        lo, hi = min(all_y), max(all_y)
        span = max(1e-6, hi - lo)
        ymin = lo - args.pad * span
        ymax = hi + args.pad * span
    else:
        ymin, ymax = 0.8, 1.2
    ax.set_ylim(ymin, ymax)

    ax.axhline(1.0, linestyle="--", linewidth=1, label="parity (1.0)")
    gA = geom_mean(ratioA); gB = geom_mean(ratioB)
    if not math.isnan(gA):
        ax.axhline(gA, linestyle=":", linewidth=1,
                   label=f"geom mean A: {NUM_A}/{DEN_A} = {gA:.4g}×")
    if not math.isnan(gB):
        ax.axhline(gB, linestyle=":", linewidth=1,
                   label=f"geom mean B: {NUM_B}/{DEN_B} = {gB:.4g}×")

    ax.set_ylabel("Normalized time (ratio)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out_png, dpi=144)
    print(f"✅ Chart saved: {args.out_png}")
    print(f"📄 geom mean A (purecap-hw-sw / purecap-hw): {gA}")
    print(f"📄 geom mean B (native-sw / native-nocheck): {gB}")

if __name__ == "__main__":
    main()
