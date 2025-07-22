#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="results_timing.csv"

# CSV Header
echo "Build,Benchmark,Real(s)" > "$RESULT_FILE"

# Ordered build folder names and labels
declare -A BUILD_PATHS=(
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native-nocheck"]="build-native"
)

# Iterate builds first
for build in purecap-hw purecap-sw purecap-hw-sw purecap-nocheck native-sw native-nocheck; do
  build_path="${BUILD_PATHS[$build]}"
  wdcli="./$build_path/wdcli"

  if [[ ! -x "$wdcli" ]]; then
    echo "⚠️  Skipping $build (no wdcli binary found)"
    continue
  fi

  echo "▶️ Running all benchmarks for build: $build"

  for wasm in "$BENCHMARK_DIR"/*.wasm; do
    wasm_name=$(basename "$wasm")
    echo "   🧪 $wasm_name..."

    tmpfile=$(mktemp)
    if { /usr/bin/time "$wdcli" "$wasm" --invoke start --no-debug; } > /dev/null 2> "$tmpfile"; then
      real_time=$(awk '/real/ { print $1 }' "$tmpfile")
      echo "$build,$wasm_name,$real_time" >> "$RESULT_FILE"
    else
      echo "$build,$wasm_name,FAIL" >> "$RESULT_FILE"
    fi
    rm -f "$tmpfile"
  done
done

echo "✅ Benchmark results saved to $RESULT_FILE"
