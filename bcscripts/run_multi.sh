#!/bin/bash

N=20  # number of times to run
SCRIPT="./run_all.sh"

for i in $(seq 1 $N); do
  echo "🔁 Run $i of $N..."
  bash "$SCRIPT"
done

echo "✅ All $N runs completed and recorded in results_timing.csv"
