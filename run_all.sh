#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="results_timing.csv"

# If not exists, create header
if [[ ! -f "$RESULT_FILE" ]]; then
  echo "Build,Benchmark,Real(s)" > "$RESULT_FILE"
fi

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
    echo "⚠️  Skipping $build (no wdcli binary)"
    continue
  fi

  for wasm in "$BENCHMARK_DIR"/*.wasm; do
    wasm_name=$(basename "$wasm")
    echo "▶️  Running $wasm_name on $build..."

    real_time=$(/usr/bin/time -f "%e" "$wdcli" "$wasm" --invoke start --no-debug 2>&1 > /dev/null)
    echo "$build,$wasm_name,$real_time" >> "$RESULT_FILE"
  done
done
