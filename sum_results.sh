#!/bin/bash

INPUT_FILE="results_matrix.csv"
OUTPUT_FILE="results_sum.csv"

echo "Benchmark,Build,Mean(s),StdDev(s)" > "$OUTPUT_FILE"

# Extract header
IFS=',' read -r -a header < "$INPUT_FILE"

# Process each benchmark row
tail -n +2 "$INPUT_FILE" | while IFS=',' read -r -a row; do
  benchmark="${row[0]}"
  for ((i=1; i<${#row[@]}; i++)); do
    build="${header[$i]}"
    values="${row[$i]}"

    if [[ -z "$values" || "$values" == "FAIL"* ]]; then
      echo "$benchmark,$build,FAIL,FAIL" >> "$OUTPUT_FILE"
      continue
    fi

    IFS=';' read -ra times <<< "$values"
    n=${#times[@]}
    sum=0
    for t in "${times[@]}"; do sum=$(awk "BEGIN {print $sum + $t}"); done
    mean=$(awk "BEGIN {print $sum / $n}")

    sumsq=0
    for t in "${times[@]}"; do sumsq=$(awk "BEGIN {print $sumsq + ($t - $mean)^2}"); done
    stddev=$(awk "BEGIN {print ($n > 1) ? sqrt($sumsq / ($n - 1)) : 0}")

    printf "%s,%s,%.4f,%.4f\n" "$benchmark" "$build" "$mean" "$stddev" >> "$OUTPUT_FILE"
  done
done

echo "✅ Summary written to $OUTPUT_FILE"
