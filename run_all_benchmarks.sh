#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="benchmark_results.csv"
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

    # Capture time output to a temp file
    tmpfile=$(mktemp)
    { /usr/bin/time "$wdcli" "$wasm" --invoke start --no-debug; } > /dev/null 2> "$tmpfile"
    
    if [[ $? -eq 0 ]]; then
      # Extract user, sys, and real times
      read real user sys < <(awk '/real/ {r=$2} /user/ {u=$2} /sys/ {s=$2} END {print r, u, s}' "$tmpfile")
      echo "$wasm_name,$build,$user,$sys,$real" >> "$RESULT_FILE"
    else
      echo "$wasm_name,$build,FAIL,FAIL,FAIL" >> "$RESULT_FILE"
    fi

    rm -f "$tmpfile"
  done
done

echo "✅ Benchmark results saved to $RESULT_FILE"
