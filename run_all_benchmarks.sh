#!/bin/sh

# Paths
BENCHMARK_DIR=~/warduino_benchmarks
CSV_FILE=benchmark_results.csv

# Output header
echo "wasm_file,build_config,exit_code,time_ms" > "$CSV_FILE"

# Build folders and readable names
BUILD_CONFIGS="
build-purecap-hw-sw
build-purecap-hw
build-purecap-sw
build-purecap-nocheck
build-native-sw
build-native
"

# Loop through all wasm files
for wasm in "$BENCHMARK_DIR"/*.wasm; do
  wasm_name=$(basename "$wasm")
  
  for build_dir in $BUILD_CONFIGS; do
    cli="./$build_dir/wdcli"

    if [ ! -x "$cli" ]; then
      echo "⚠️  Skipping $cli (not found or not executable)" >&2
      continue
    fi

    echo "▶️  Running $wasm_name on $build_dir..."

    # Capture start time in ms
    start=$(date +%s%3N)
    
    # Run and capture exit code
    "$cli" "$wasm" > /dev/null 2>&1
    exit_code=$?

    # Capture end time and compute elapsed
    end=$(date +%s%3N)
    elapsed=$((end - start))

    # Write to CSV
    echo "$wasm_name,$build_dir,$exit_code,$elapsed" >> "$CSV_FILE"
  done
done

echo "✅ Results saved to $CSV_FILE"

