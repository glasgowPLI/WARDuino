#!/bin/bash

# Path to benchmarks and output
BENCHMARK_DIR="../warduino_benchmarks"
OUTPUT_CSV="benchmark_results.csv"

# List of build directories and names
declare -A BUILD_DIRS=(
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native"]="build-native"
  ["native-sw"]="build-native-sw"
)

# Write CSV header
echo "benchmark,build,elapsed_ms,stdout" > "$OUTPUT_CSV"

# Loop over benchmarks
for wasm_file in "$BENCHMARK_DIR"/*.wasm; do
  bench_name=$(basename "$wasm_file")

  # Loop over builds
  for label in "${!BUILD_DIRS[@]}"; do
    build_path="${BUILD_DIRS[$label]}"
    wdcli_path="./$build_path/wdcli"

    echo "▶️  Running $bench_name on $label..."

    if [[ ! -x "$wdcli_path" ]]; then
      echo "⚠️  Skipping $label: wdcli not found or not executable"
      continue
    fi

    # Run benchmark and time it in milliseconds
    start_time=$(date +%s%3N)
    output=$("$wdcli_path" "$BENCHMARK_DIR/$bench_name" --invoke start --no-debug 2>&1)
    end_time=$(date +%s%3N)
    elapsed=$((end_time - start_time))

    # Sanitize output
    clean_output=$(echo "$output" | tr '\n' ' ' | tr -d '\r' | cut -c1-200)

    # Save to CSV
    echo "$bench_name,$label,$elapsed,\"$clean_output\"" >> "$OUTPUT_CSV"
  done
done

echo "✅ Benchmark results saved to $OUTPUT_CSV"
