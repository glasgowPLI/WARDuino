import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Define input and output file paths
input_csv = '../data/time-execution.csv'
output_pdf = '../data/time-plot.pdf'

# Load the data from the CSV file into a DataFrame
df = pd.read_csv(input_csv)

# Get unique benchmarks and tools for dynamic plotting
benchmarks = df['Benchmark'].unique()
tools = df['Tool'].unique()

# Set up the figure
bar_width = 0.25
x = np.arange(len(benchmarks))  # The label locations for each benchmark group
fig, ax = plt.subplots(figsize=(10, 7))

# Plot each tool as a separate bar within each benchmark group
for i, tool in enumerate(tools):
    # Filter data for the current tool
    tool_data = df[df['Tool'] == tool]
    
    # Create a bar for each tool at the correct x position
    ax.bar(
        x + i * bar_width, 
        tool_data['Time'], 
        yerr=tool_data['Error'], 
        capsize=5, 
        width=bar_width, 
        label=tool
    )

# Add labels and title
ax.set_xlabel('Benchmark')
ax.set_ylabel('Time (s)')
ax.set_title('Execution Time of Benchmarks by Tool')
ax.set_xticks(x + bar_width * (len(tools) - 1) / 2)
ax.set_xticklabels(benchmarks)
ax.legend(title='Tool')

# Save the plot as a PDF file in the specified directory
os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
plt.tight_layout()
plt.savefig(output_pdf)

# Show the plot
plt.show()
