#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="results_timing.csv"

# Only write header if file does not exist
if [[ ! -f "$RESULT_FILE" ]]; then
  echo "Benchmark,Build,Time" > "$RESULT_FILE"
fi

# Ordered build folder names and labels
declare -A BUILD_PATHS=(
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native-nocheck"]="build-native"
)

# List of builds in desired order
BUILD_ORDER=("purecap-hw" "purecap-sw" "purecap-hw-sw" "purecap-nocheck" "native-sw" "native-nocheck")

# Iterate over each benchmark
for wasm in "$BENCHMARK_DIR"/*.wasm; do
  wasm_name=$(basename "$wasm")
  echo "▶️ Running $wasm_name on all builds..."

  # Run this benchmark in each build
  for build in "${BUILD_ORDER[@]}"; do
    build_path="${BUILD_PATHS[$build]}"
    wdcli="./$build_path/wdcli"

    if [[ ! -x "$wdcli" ]]; then
      echo "⚠️  Skipping $build (no wdcli binary found)"
      continue
    fi

    echo "   🧪 $build..."
    tmpfile=$(mktemp)

    if { /usr/bin/time "$wdcli" "$wasm" --invoke start --no-debug; } > /dev/null 2> "$tmpfile"; then
      real_time=$(awk '/real/ { print $1 }' "$tmpfile")
      echo "$wasm_name,$build,$real_time" >> "$RESULT_FILE"
    else
      echo "$wasm_name,$build,FAIL" >> "$RESULT_FILE"
    fi

    rm -f "$tmpfile"
  done
done

echo "✅ Benchmark results saved to $RESULT_FILE"
