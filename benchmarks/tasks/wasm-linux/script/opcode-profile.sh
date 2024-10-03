#!/bin/bash

function profile_runtime() {
    local runtime=$1
    local csv_file="$HOME/Projects/WARDuino/benchmarks/tasks/wasm-linux/data/results-opcode.csv"

    for wasmDir in "${WasmDirs[@]}"; do
        for (( idx=0; idx<${#BenchSuite[@]}; idx++ )); do

            BenchmarkName=${BenchSuite[idx]}
            WasmFile="$BenchmarkName.wasm"
            DirectoryPath="$BenchRoot/$wasmDir"

            if [ -f "$DirectoryPath/$WasmFile" ]; then
                # Navigate to the directory
                cd "$DirectoryPath"
                
                for (( i=1; i<=$Runs; i++ )); do  
                    if [ "$runtime" == "wasm3" ]; then
                        # Special case for gnuchess
                        if [ "$BenchmarkName" == "gnuchess" ]; then
                            echo "Run $i gnuchess (special)"
                            Output=`/usr/bin/time ./runwasm3chess-opcode.sh < ./input 2>&1`
                        else
                            echo "Run $i: /home/yuxin/runtimes/wasm3-opcode/build/wasm3 --func bench $BenchRoot/$wasmDir/$WasmFile"
                            Output=$(/home/yuxin/runtimes/wasm3-opcode/build/wasm3 --func bench "$WasmFile" 2>&1)
                        fi
                    fi

                    # Logging result to CSV
                    echo "$DirectoryPath/$WasmFile" >> "$csv_file"
                    # Grep for "malloc" and log the result
                    OpcodeOutput=$(echo "$Output" | grep "op_")
                    echo "$OpcodeOutput" >> "$csv_file"
                done

                # Navigate back to original directory
                cd "$BenchRoot"
            else
                echo "Wasm file $DirectoryPath/$WasmFile not found!"
            fi
        done
    done
}

BenchRoot="$HOME/Projects/WARDuino/benchmarks/tasks"
WasmDirs=("wasm-linux")
Runs=1

# List of benchmarks
BenchSuite=("catalan" "fac" "fib" "gcd" "primes" "tak-mem" "tak" "salloc")

for arg in "$@"; do
    if [[ "$arg" == "wasm3" || "$arg" == "wasmtime" ]]; then
        profile_runtime "$arg"
    else
        echo "Unknown argument: $arg"
    fi
done
