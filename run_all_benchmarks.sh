#!/bin/bash

# Directory containing wasm benchmarks
BENCHMARK_DIR=../warduino_benchmarks

# Output CSV file
RESULT_FILE="benchmark_results.csv"
echo "Benchmark,Build,Time(s)" > "$RESULT_FILE"

# Build configurations and corresponding paths
declare -A BUILD_PATHS=(
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native"]="build-native"
)

# Check if /usr/bin/time is available
if ! command -v /usr/bin/time &> /dev/null; then
  echo "❌ /usr/bin/time is not available. Install it first."
  exit 1
fi

# Loop over builds and wasm files
for build in "${!BUILD_PATHS[@]}"; do
  build_path=${BUILD_PATHS[$build]}
  wdcli_path="./$build_path/wdcli"

  if [ ! -x "$wdcli_path" ]; then
    echo "⚠️  Skipping $build: $wdcli_path not found or not executable"
    continue
  fi

  for bench_file in "$BENCHMARK_DIR"/*.wasm; do
    bench_name=$(basename "$bench_file")

    echo "▶️  Running $bench_name on $build..."

    # Run and time
    /usr/bin/time -f "%e" -o time_output.txt "$wdcli_path" "$bench_file" --invoke start --no-debug > /dev/null 2>&1
    elapsed=$(cat time_output.txt)

    echo "$bench_name,$build,$elapsed" >> "$RESULT_FILE"
  done
done

echo "✅ Benchmark results saved to $RESULT_FILE"
