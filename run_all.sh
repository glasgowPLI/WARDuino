#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="results_matrix.csv"

# Build labels in desired order
BUILD_ORDER=("purecap-hw" "purecap-hw-sw" "native-sw" "native-nocheck")

# Map build label to folder
declare -A BUILD_PATHS=(
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["native-sw"]="build-native-sw"
  ["native-nocheck"]="build-native"
)

# Initialize matrix if not exist
if [[ ! -f "$RESULT_FILE" ]]; then
  echo -n "Benchmark" > "$RESULT_FILE"
  for build in "${BUILD_ORDER[@]}"; do
    echo -n ",$build" >> "$RESULT_FILE"
  done
  echo >> "$RESULT_FILE"
fi

# Ensure temporary file
tmpfile=$(mktemp)

# Process each benchmark
for wasm in "$BENCHMARK_DIR"/*.wasm; do
  benchmark=$(basename "$wasm")

  echo "▶️  Running $benchmark..."

  # Read current row if exists
  existing=$(grep "^$benchmark," "$RESULT_FILE")
  if [[ -z "$existing" ]]; then
    existing="$benchmark"
    for _ in "${BUILD_ORDER[@]}"; do
      existing="$existing,"
    done
  fi

  # Convert to array for update
  IFS=',' read -ra row <<< "$existing"

  for i in "${!BUILD_ORDER[@]}"; do
    build="${BUILD_ORDER[$i]}"
    wdcli="./${BUILD_PATHS[$build]}/wdcli"

    echo "   🧪 $build..."

    if [[ ! -x "$wdcli" ]]; then
      echo "     ⚠️  Skipping (no binary)"
      continue
    fi

    if { /usr/bin/time "$wdcli" "$wasm" --invoke start --no-debug; } > /dev/null 2> "$tmpfile"; then
      time=$(awk '/real/ { print $1 }' "$tmpfile")
      if [[ -z "${row[$((i+1))]}" ]]; then
        row[$((i+1))]="$time"
      else
        row[$((i+1))]+=";$time"
      fi
    else
      if [[ -z "${row[$((i+1))]}" ]]; then
        row[$((i+1))]="FAIL"
      else
        row[$((i+1))]+=";FAIL"
      fi
    fi
  done

  # Update or append the row
  grep -v "^$benchmark," "$RESULT_FILE" > "$RESULT_FILE.tmp"
  (IFS=','; echo "${row[*]}") >> "$RESULT_FILE.tmp"
  mv "$RESULT_FILE.tmp" "$RESULT_FILE"
done

rm -f "$tmpfile"
echo "✅ All results appended to $RESULT_FILE"
