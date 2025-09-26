import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the CSV file
df = pd.read_csv("results_summary.csv")

# Get unique benchmarks and builds
benchmarks = sorted(df["Benchmark"].unique())
builds = ["native-nocheck", "native-sw", "purecap-nocheck", "purecap-sw", "purecap-hw", "purecap-hw-sw"]

# Set positions for bars
x = np.arange(len(benchmarks))  # the label locations
bar_width = 0.13
offsets = np.linspace(-bar_width*2.5, bar_width*2.5, len(builds))

# Create plot
fig, ax = plt.subplots(figsize=(10, 5))

for i, build in enumerate(builds):
    build_data = df[df["Build"] == build]
    means = []
    stds = []

    for bm in benchmarks:
        row = build_data[build_data["Benchmark"] == bm]
        if not row.empty:
            means.append(row["Mean(s)"].values[0])
            stds.append(row["StdDev(s)"].values[0])
        else:
            means.append(0)
            stds.append(0)

    bar_pos = x + offsets[i]
    ax.bar(bar_pos, means, width=bar_width, label=build, yerr=stds, capsize=4)

# Customize axes and legend
ax.set_ylabel('Time (s)')
ax.set_title('Benchmark Execution Time by Build (with StdDev)')
ax.set_xticks(x)
ax.set_xticklabels(benchmarks, rotation=30)
ax.legend(loc='upper right', fontsize=9)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()

