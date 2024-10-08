import pandas as pd
import matplotlib.pyplot as plt
import os

# Define the input CSV file and output PDF file paths
input_csv = '../data/time-execution.csv'
output_pdf = '../graphs/time-plot.pdf'

# Load the CSV file into a pandas DataFrame
df = pd.read_csv(input_csv)

# Check if the DataFrame is loaded correctly
print(df.head())

# Plotting
plt.figure(figsize=(12, 7))
plt.bar(df['Benchmark'], df['Time'], yerr=df['Error'], 
        capsize=5, color='skyblue', edgecolor='black')

# Adding labels and title
plt.ylabel('Time(s)')
plt.title('Average Execution Time of Benchmarks with Standard Error')
plt.xticks(rotation=45)  # Rotate benchmark names for better readability

# Save the plot as a PDF file
plt.tight_layout()

# Ensure the output directory exists
os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

plt.savefig(output_pdf)

# Show the plot
plt.show()
