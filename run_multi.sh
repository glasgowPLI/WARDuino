#!/bin/bash

RUN_SCRIPT="./run_all_benchmarks.sh"
TMP_PREFIX="tmp_results_run"
FINAL_RESULT="results_timing.csv"
NUM_RUNS=2

# Clean up any existing temp files
rm -f ${TMP_PREFIX}_*.csv "$FINAL_RESULT"

echo "Build,Benchmark" > "$FINAL_RESULT"

# Run multiple times and collect results
for run in $(seq 1 $NUM_RUNS); do
  echo "▶️ Run #$run..."
  TMP_FILE="${TMP_PREFIX}_${run}.csv"

  # Run once and save intermediate results (assumes run_all_benchmarks.sh can reuse RESULT_FILE variable)
  RESULT_FILE="$TMP_FILE" bash "$RUN_SCRIPT"

  # Prepare columns: Build,Benchmark,Real
  if [[ $run -eq 1 ]]; then
    # Initialize with Build and Benchmark
    awk -F',' 'NR>1 { print $1","$2 }' "$TMP_FILE" >> "$FINAL_RESULT"
  fi

  # Extract the "Real(s)" column and paste into final CSV
  paste -d',' "$FINAL_RESULT" <(awk -F',' 'NR==1{print "Run'$run'"} NR>1{print $3}' "$TMP_FILE") > "${FINAL_RESULT}.tmp"
  mv "${FINAL_RESULT}.tmp" "$FINAL_RESULT"
done

echo "✅ Final result saved to $FINAL_RESULT"

