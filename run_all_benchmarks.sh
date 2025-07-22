#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="results_timing.csv"

# CSV Header
echo "Benchmark,Build,User(s),Sys(s),Real(s)" > "$RESULT_FILE"

# Ordered build folder names and labels
declare -A BUILD_PATHS=(
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native-nocheck"]="build-native"
)

# Run benchmarks
for build in purecap-hw purecap-sw purecap-hw-sw purecap-nocheck native-sw native-nocheck; do
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
    if { /usr/bin/time "$wdcli" "$wasm" --invoke start --no-debug; } > /dev/null 2> "$tmpfile"; then
      # Parse user, sys, real
      read user sys real < <(awk '
        /user/ { u=$1 }
        /sys/  { s=$1 }
        /real/ { r=$1 }
        END { print u, s, r }
      ' "$tmpfile")
      echo "$wasm_name,$build,$user,$sys,$real" >> "$RESULT_FILE"
    else
      echo "$wasm_name,$build,FAIL,FAIL,FAIL" >> "$RESULT_FILE"
    fi

    rm -f "$tmpfile"
  done
done

echo "✅ Benchmark results saved to $RESULT_FILE"
