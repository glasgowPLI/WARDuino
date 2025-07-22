#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RUNS=5
RESULT_FILE="results_timing.csv"
TMP_PREFIX="tmp_run"

declare -A BUILD_PATHS=(
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native"]="build-native"
)

# Create base columns if result file doesn't exist
if [[ ! -f "$RESULT_FILE" ]]; then
  echo -n "Build,Benchmark" > "$RESULT_FILE"
  for i in $(seq 1 $RUNS); do
    echo -n ",Real(s)_$i" >> "$RESULT_FILE"
  done
  echo >> "$RESULT_FILE"
fi

# Build header list of results for merging
declare -A results

for build in "purecap-hw" "purecap-sw" "purecap-hw-sw" "purecap-nocheck" "native-sw" "native"; do
  build_path="${BUILD_PATHS[$build]}"
  wdcli="./$build_path/wdcli"

  if [[ ! -x "$wdcli" ]]; then
    echo "⚠️  Skipping $build (no wdcli)"
    continue
  fi

  for wasm in "$BENCHMARK_DIR"/*.wasm; do
    wasm_name=$(basename "$wasm")
    key="$build,$wasm_name"
    echo "▶️  Running $wasm_name on $build..."

    for i in $(seq 1 $RUNS); do
      time_result=$(/usr/bin/time -f "%e" "$wdcli" "$wasm" --invoke start --no-debug 2>&1 > /dev/null)
      results["$key"]+=",${time_result}"
    done
  done
done

# Write to CSV
> "$RESULT_FILE"
echo -n "Build,Benchmark" > "$RESULT_FILE"
for i in $(seq 1 $RUNS); do
  echo -n ",Real(s)_$i" >> "$RESULT_FILE"
done
echo >> "$RESULT_FILE"

for key in "${!results[@]}"; do
  echo "$key${results[$key]}" >> "$RESULT_FILE"
done

echo "✅ Multi-run results saved to $RESULT_FILE"

