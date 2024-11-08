#!/bin/bash

# Define directories and output file
WDCLIS=(
    "/home/yuxin/WARDuino/build-hybird-soft/wdcli"
    "/home/yuxin/WARDuino/build-purecap-soft/wdcli"
    "/home/yuxin/WARDuino/build-purecap-hard/wdcli"
)
BENCHMARKS=("salloc")
OUTPUT_FILE="../data/time-execution.csv"
RUNS=30

# Ensure the data directory exists
mkdir -p ../data

# Initialize CSV file with header
echo "Benchmark,Tool,Time,Error" > $OUTPUT_FILE

# Function to calculate standard deviation
calculate_sd() {
    local times=("$@")
    local count=${#times[@]}
    local sum=0
    local mean
    local sq_diff_sum=0

    if [ "$count" -le 1 ]; then
        echo "NaN"
        return
    fi

    for time in "${times[@]}"; do
        sum=$(echo "$sum + $time" | bc -l)
    done
    mean=$(echo "$sum / $count" | bc -l)

    for time in "${times[@]}"; do
        sq_diff=$(echo "$time - $mean" | bc -l)
        sq_diff=$(echo "$sq_diff * $sq_diff" | bc -l)
        sq_diff_sum=$(echo "$sq_diff_sum + $sq_diff" | bc -l)
    done

    sd=$(echo "scale=10; sqrt($sq_diff_sum / ($count - 1))" | bc -l)
    sem=$(echo "scale=10; $sd / sqrt($count)" | bc -l)

    echo "$sem"
}

# Loop through each wdcli tool
for WDCLI in "${WDCLIS[@]}"; do
    tool_name=$(basename "$WDCLI")

    # Loop through each benchmark
    for benchmark in "${BENCHMARKS[@]}"; do
        total_time=0
        times=()

        # Run the benchmark specified number of times
        for ((i=1; i<=RUNS; i++)); do
            result=$( { time $WDCLI ../$benchmark.wasm --invoke bench --no-debug > /dev/null; } 2>&1 )

            real_time=$(echo "$result" | grep "real" | awk '{print $2}')
            if [[ -z "$real_time" ]]; then
                echo "Error: Could not parse the time output for benchmark $benchmark"
                continue
            fi

            echo "$benchmark,$tool_name,$i,$real_time"

            if [[ "$real_time" == *m* ]]; then
                minutes=$(echo $real_time | cut -d'm' -f1)
                seconds=$(echo $real_time | cut -d'm' -f2 | sed 's/s//')
                current_time=$(echo "$minutes * 60 + $seconds" | bc -l)
            else
                current_time=$(echo $real_time | sed 's/s//' | bc -l)
            fi

            total_time=$(echo "$total_time + $current_time" | bc -l)
            times+=("$current_time")
        done

        average_time=$(echo "$total_time / $RUNS" | bc -l)
        standard_error=$(calculate_sd "${times[@]}")

        echo "$benchmark,$tool_name,$average_time,$standard_error" >> $OUTPUT_FILE
    done
done

echo "Benchmark average times and standard errors have been saved to $OUTPUT_FILE."
