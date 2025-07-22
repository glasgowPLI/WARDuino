#!/bin/bash

BENCHMARK_DIR=~/warduino_benchmarks
RESULT_FILE="benchmark_results.csv"

# CSV Header
echo "Benchmark,Build,User(s),Sys(s),Real(s)" > "$RESULT_FILE"

# Declare build folder names
declare -A BUILD_PATHS=(
  ["purecap-hw-sw"]="build-purecap-hw-sw"
  ["purecap-hw"]="build-purecap-hw"
  ["purecap-sw"]="build-purecap-sw"
  ["purecap-nocheck"]="build-purecap-nocheck"
  ["native-sw"]="build-native-sw"
  ["native"]="build-native"
)

# Iterate builds
for build in "${!BUILD_PATHS[@]}"; do
  build_path="${BUILD_PATHS[$build]}"
  wdcli="./$build_path/wdcli"

  if [[ ! -x "$wdcli" ]]; then
    echo "⚠️  Skipping $build (no wdcli binary found)"
    continue
  fi

  # Iterate benchmarks
  for wasm in "$BENCHMARK_DIR"/*.wasm; do
    wasm_name=$(basename "$wasm")
    echo "▶️  Running $wasm_name on $build..."

    tmpfile=$(mktemp)
    
    # Run and capture time
    if output=$( /usr/bin/time "$wdcli" "$wasm" --invoke start --no-debug > /dev/null 2>&1 ); then
      { read real user sys < <(/usr/bin/time -p "$wdcli" "$wasm" --invoke start --no-debug 2>&1 | awk '
        BEGIN { r=u=s="FAIL" }
        $1 == "real" { r = $2 }
        $1 == "user" { u = $2 }
        $1 == "sys"  { s = $2 }
        END { print r, u, s }
      '); } 2>/dev/null
    
      echo "$wasm_name,$build,$user,$sys,$real" >> "$RESULT_FILE"
    else
      echo "$wasm_name,$build,FAIL,FAIL,FAIL" >> "$RESULT_FILE"
    fi

    rm -f "$tmpfile"
  done
done

echo "✅ Benchmark results saved to $RESULT_FILE"
