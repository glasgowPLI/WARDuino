import csv
import matplotlib.pyplot as plt
import numpy as np
import os

# Read data from CSV
data_dir = '../data'
with open(os.path.join(data_dir, f"categorized_results.csv"), "r") as f:
    reader = csv.reader(f)
    headers = next(reader)
    data = list(reader)

# Group data by benchmark
benchmarks = {}
for row in data:
    allocator, benchmark, *totals = row
    # Now normalise the totals (absolute values)-> percents
    sumtotal = sum([float (t) for t in totals])
    percentages = [((100*float(t)/sumtotal) if sumtotal>0 else 0) for t in totals]
    
    if benchmark not in benchmarks:
        benchmarks[benchmark] = []
    benchmarks[benchmark].append((allocator, [float(p) for p in percentages]))

# Sort benchmarks by the first letter of the benchmark name
benchmarks = dict(sorted(benchmarks.items(), key=lambda x: x[0]))

# Define colors for the categories
colors = {
    'MOVE': 'silver',      
    'ARITH_INT': 'salmon', 
    'ARITH_FLOAT': 'sandybrown', 
    'CONTROL': 'dodgerblue', 
    'BOUND': 'lightgreen'
}

# Plot the data
bar_width = 0.15
index = np.arange(len(benchmarks.keys()))

fig, ax = plt.subplots(figsize=(12, 7))

# We will store the legend handles here to ensure proper order
legend_handles = []

for idx, benchmark in enumerate(benchmarks.keys()):
    for allocator_idx, (allocator, percentages) in enumerate(benchmarks[benchmark]):
        # Stack the percentages on top of each other in the bar
        bottoms = [sum(percentages[:i]) for i in range(len(percentages))]
        for p_idx, percentage in enumerate(percentages):
            category = headers[p_idx + 2]
            bar = plt.bar(index[idx] + allocator_idx*bar_width, percentage, bar_width, 
                          color=colors[category], 
                          label=category,  # We use category as label directly
                          bottom=bottoms[p_idx], 
                          edgecolor='black')
            # Adding edgecolor
            if idx == 0 and allocator_idx == 0:  # We add legend handles only once
                legend_handles.append(bar)

legend_handles.reverse()
labels = list(colors.keys())
labels.reverse()

# Create legend with the handles
ax.legend(handles=legend_handles, labels=labels, loc='upper left', bbox_to_anchor=(1, 1))

plt.ylabel('Percentage')
plt.xticks(index + (bar_width * len(benchmarks[benchmark]) / 2) - bar_width/2, benchmarks.keys(), rotation=0)

plt.tight_layout()
graph_dir = "../graph"
plt.savefig(os.path.join(graph_dir, f"opcode_graph.pdf"), format='pdf', bbox_inches='tight')
