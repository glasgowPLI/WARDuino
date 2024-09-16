import pandas as pd
import matplotlib.pyplot as plt

# Define the input CSV file
input_csv = 'time.csv'

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
plt.savefig('time.pdf')

# Show the plot
plt.show()
