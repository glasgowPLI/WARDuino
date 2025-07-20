#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="benchmark_results_${TIMESTAMP}.csv"

echo "Benchmark,Build,User(s),Sys(s),Real(s)" > "$RESULT_FILE"

declare -A BUILD_PATHS=(
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native"]="build-native"
)

for build in "${!BUILD_PATHS[@]}"; do
  build_path="${BUILD_PATHS[$build]}"
  wdcli="./$build_path/wdcli"

  if [[ ! -x "$wdcli" ]]; then
    echo "⚠️  Skipping $build (no wdcli binary found)"
    continue
  fi

  for wasm in "$BENCHMARK_DIR"/*.wasm; do
    wasm_name=$(basename "$wasm")
    echo "▶️  Running $wasm_name on $build..."

    tmpfile=$(mktemp)

    if /usr/bin/time -f "%U,%S,%e" -o "$tmpfile" "$wdcli" "$wasm" --invoke start --no-debug > /dev/null 2>&1; then
      result=$(cat "$tmpfile")
    else
      result="FAIL,FAIL,FAIL"
    fi

    echo "$wasm_name,$build,$result" >> "$RESULT_FILE"
    rm -f "$tmpfile"
  done
done

echo "✅ Benchmark results saved to $RESULT_FILE"
