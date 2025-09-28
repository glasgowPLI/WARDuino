# bcscripts/norm_pairs_chart.py
#!/usr/bin/env python3
"""
Two-bar normalization per benchmark from results_stats.csv.

Bars:
  A) purecap-hw-sw / purecap-hw
  B) native-sw    / native-nocheck

Notes:
- Strips trailing ".wasm" from benchmark names in the x-axis labels.
- Keeps the two geom-mean print lines exactly as requested.

Zoom controls:
  --ymin/--ymax     Explicit y-axis limits.
  --pad FLOAT       Extra headroom for auto y-limits (default: 0.15; includes error bars).
  --around-one      Zoom around 1.0 using max deviation of (ratio ± err).

Input : results_stats.csv  (Benchmark,Build,N,Mean(s),StdDev(s),Min(s),Max(s))
Output: norm_pairs.png
"""

import csv, math, os, sys, argparse
from typing import Dict, Tuple, List

IN_CSV  = os.environ.get("RESULTS_STATS", "results_stats.csv")
OUT_PNG = os.environ.get("RESULTS_PNG", "norm_pairs.png")
# TITLE   = os.environ.get("RESULTS_TITLE", "Normalization: two bars per benchmark")

# Build keys
NUM_A, DEN_A = "purecap-hw-sw", "purecap-hw"
NUM_B, DEN_B = "native-sw", "native-nocheck"

def f2f(x: str) -> float:
    try: return float(x)
    except Exception: return float("nan")

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

def ratio_and_sigma(num, den) -> Tuple[float, float]:
    nN, muN, sdN = num
    nD, muD, sdD = den
    if math.isnan(muN) or math.isnan(muD) or muD <= 0.0:
        return float("nan"), float("nan")
    r = muN / muD
    if any((math.isnan(sdN), math.isnan(sdD), muN <= 0.0, muD <= 0.0, nN < 2, nD < 2)):
        return r, 0.0
    rel = (sdN / muN) ** 2 + (sdD / muD) ** 2
    return r, r * math.sqrt(rel)

def geom_mean(xs: List[float]) -> float:
    xs = [x for x in xs if x > 0 and not math.isnan(x)]
    if not xs: return float("nan")
    return math.exp(sum(math.log(x) for x in xs) / len(xs))

def parse_args():
    p = argparse.ArgumentParser(description="Plot two normalized bars per benchmark.")
    p.add_argument("--in",   dest="in_csv",  default=IN_CSV)
    p.add_argument("--png",  dest="out_png", default=OUT_PNG)
#    p.add_argument("--title", default=TITLE)
    p.add_argument("--ymin", type=float, default=None)
    p.add_argument("--ymax", type=float, default=None)
    p.add_argument("--pad",  type=float, default=0.15, help="Headroom fraction for auto y-limits.")
    p.add_argument("--around-one", action="store_true", help="Zoom around 1.0 using (ratio±err).")
    return p.parse_args()

def main():
    args = parse_args()
    stats = load_stats(args.in_csv)

    labels: List[str] = []
    ratioA: List[float] = []; errA: List[float] = []
    ratioB: List[float] = []; errB: List[float] = []

    for bm, builds in sorted(stats.items()):
        if NUM_A not in builds or DEN_A not in builds:
            continue
        if NUM_B not in builds or DEN_B not in builds:
            continue

        rA, eA = ratio_and_sigma(builds[NUM_A], builds[DEN_A])
        rB, eB = ratio_and_sigma(builds[NUM_B], builds[DEN_B])
        if math.isnan(rA) or math.isnan(rB):
            continue

        label = bm[:-5] if bm.endswith(".wasm") else bm  # strip .wasm
        labels.append(label)
        ratioA.append(rA); errA.append(eA)
        ratioB.append(rB); errB.append(eB)

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

    # Two bars per benchmark
    ax.bar([i - bar_w/2 for i in x], ratioA, yerr=errA, width=bar_w, capsize=3, label=f"{NUM_A}/{DEN_A}")
    ax.bar([i + bar_w/2 for i in x], ratioB, yerr=errB, width=bar_w, capsize=3, label=f"{NUM_B}/{DEN_B}")

    # Y-limits include error bars, with padding
    lows  = [r - e for r, e in zip(ratioA, errA)] + [r - e for r, e in zip(ratioB, errB)]
    highs = [r + e for r, e in zip(ratioA, errA)] + [r + e for r, e in zip(ratioB, errB)]
    finite_lows  = [v for v in lows  if not math.isnan(v)]
    finite_highs = [v for v in highs if not math.isnan(v)]

    if args.ymin is not None and args.ymax is not None:
        ymin, ymax = args.ymin, args.ymax
    elif finite_lows and finite_highs:
        lo, hi = min(finite_lows), max(finite_highs)
        span = max(1e-6, hi - lo)
        ymin = lo - args.pad * span
        ymax = hi + args.pad * span
    else:
        ymin, ymax = 0.8, 1.2
    ax.set_ylim(ymin, ymax)

    ax.axhline(1.0, linestyle="--", linewidth=1)
    gA = geom_mean(ratioA); gB = geom_mean(ratioB)
    if not math.isnan(gA): ax.axhline(gA, linestyle=":", linewidth=1)
    if not math.isnan(gB): ax.axhline(gB, linestyle=":", linewidth=1)

    ax.set_ylabel("Normalized time (ratio)")
#    ax.set_title(args.title)
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
