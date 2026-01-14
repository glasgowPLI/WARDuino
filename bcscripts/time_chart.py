# bcscripts/time_chart.py
#!/usr/bin/env python3
# Minimal matrix→grouped-bar chart for: Benchmark,<build1>,<build2>,...
# Each cell: "t1;t2;...;FAIL". No pandas required.

import csv, math, os, sys

CSV_IN  = os.environ.get("RESULTS_CSV", "results_matrix.csv")
PNG_OUT = os.environ.get("RESULTS_PNG", "time_chart.png")
TITLE   = os.environ.get("RESULTS_TITLE", "WARDuino – Runtime by Build (mean ± std)")

def parse_cell(cell: str):
    vals = []
    if not cell: return vals
    for tok in cell.split(";"):
        tok = tok.strip()
        if not tok or tok.upper() == "FAIL": continue
        try: vals.append(float(tok))
        except ValueError: pass
    return vals

def mean_std(nums):
    n = len(nums)
    if n == 0: return (math.nan, math.nan, 0)
    if n == 1: return (nums[0], 0.0, 1)
    m = sum(nums) / n
    var = sum((x - m) ** 2 for x in nums) / (n - 1)  # sample std
    return (m, math.sqrt(var), n)

def load_matrix(path):
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    if not rows or rows[0][0] != "Benchmark":
        sys.exit("CSV must start with header: Benchmark,...")
    header = rows[0]
    builds = header[1:]
    data = []
    for r in rows[1:]:
        row = {"Benchmark": r[0]}
        for i, b in enumerate(builds, start=1):
            row[b] = r[i] if i < len(r) else ""
        data.append(row)
    return builds, data

def clean_label(name: str) -> str:
    base = os.path.basename(name)
    return base[:-5] if base.endswith(".wasm") else base  # why: cleaner x-axis

def main():
    if not os.path.exists(CSV_IN):
        sys.exit(f"Missing CSV: {CSV_IN}")
    builds, data = load_matrix(CSV_IN)
    benchmarks_raw = [row["Benchmark"] for row in data]
    benchmarks = [clean_label(bm) for bm in benchmarks_raw]

    means = {b: [] for b in builds}
    stds  = {b: [] for b in builds}
    counts= {b: [] for b in builds}
    for row in data:
        for b in builds:
            m, s, n = mean_std(parse_cell(row.get(b, "")))
            means[b].append(m); stds[b].append(s); counts[b].append(n)

    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not available. Summary:")
        for b in builds:
            vals = [v for v in means[b] if not math.isnan(v)]
            overall = sum(vals) / len(vals) if vals else math.nan
            print(f"{b:>16}: mean={overall if not math.isnan(overall) else 'nan'} (n_bench={len(vals)})")
        return

    x = list(range(len(benchmarks)))
    n_builds = max(1, len(builds))
    bar_w = min(0.8 / n_builds, 0.22)
    offsets = [ (i - (n_builds-1)/2) * (bar_w + 0.02) for i in range(n_builds) ]

    fig, ax = plt.subplots(figsize=(max(8, 0.6*len(benchmarks)), 5))
    for i, b in enumerate(builds):
        bar_x = [xi + offsets[i] for xi in x]
        y     = means[b]
        yerr  = [0 if math.isnan(s) else s for s in stds[b]]
        bx = [bx for bx, yy in zip(bar_x, y) if not math.isnan(yy)]
        by = [yy for yy in y if not math.isnan(yy)]
        be = [ee for yy, ee in zip(y, yerr) if not math.isnan(yy)]
        ax.bar(bx, by, width=bar_w, label=b, yerr=be, capsize=4)

    ax.set_ylabel("Time (s)")
    ax.set_title(TITLE)
    ax.set_xticks(x)
    ax.set_xticklabels(benchmarks, rotation=30, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(PNG_OUT, dpi=144)
    print(f"✅ Chart saved: {PNG_OUT}")

if __name__ == "__main__":
    main()
