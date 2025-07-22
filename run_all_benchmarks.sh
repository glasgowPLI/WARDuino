#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="results_timing.csv"

echo "Build,Benchmark,Real(s)" > "$RESULT_FILE"

declare -A BUILD_PATHS=(
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native"]="build-native"
)

for build in "purecap-hw" "purecap-sw" "purecap-hw-sw" "purecap-nocheck" "native-sw" "native"; do
  build_path="${BUILD_PATHS[$build]}"
  wdcli="./$build_path/wdcli"

  if [[ ! -x "$wdcli" ]]; then
    echo "⚠️  Skipping $build (no wdcli)"
    continue
  fi

  for wasm in "$BENCHMARK_DIR"/*.wasm; do
    wasm_name=$(basename "$wasm")
    echo "▶️  Running $wasm_name on $build..."

    time_output=$(/usr/bin/time -f "%e" "$wdcli" "$wasm" --invoke start --no-debug 2>&1 > /dev/null)
    echo "$build,$wasm_name,$time_output" >> "$RESULT_FILE"
  done
done

echo "✅ Results saved to $RESULT_FILE"
