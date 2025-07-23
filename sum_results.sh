#!/bin/bash

INPUT_FILE="results_timing.csv"
OUTPUT_FILE="results_sum.csv"

# Write header
echo "Benchmark,Build,Mean(s),StdDev(s)" > "$OUTPUT_FILE"

# Use awk to compute mean and stddev grouped by Benchmark + Build
awk -F',' '
NR > 1 && $3 != "FAIL" {
  key = $1 "," $2  # Benchmark,Build
  times[key] = times[key] " " $3
  count[key]++
}
END {
  for (key in times) {
    n = count[key]
    split(times[key], tlist, " ")
    sum = 0
    for (i = 1; i <= n; i++) {
      sum += tlist[i]
    }
    mean = sum / n

    sumsq = 0
    for (i = 1; i <= n; i++) {
      sumsq += (tlist[i] - mean)^2
    }
    stddev = (n > 1) ? sqrt(sumsq / (n - 1)) : 0

    printf "%s,%.4f,%.4f\n", key, mean, stddev
  }
}
' "$INPUT_FILE" >> "$OUTPUT_FILE"

echo "✅ Summary saved to $OUTPUT_FILE"
