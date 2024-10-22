#!/bin/bash

# Define directories and output file
WDCLI="/home/yuxin/WARDuino/build-emu/wdcli"
# BENCHMARKS=("catalan" "fac" "fib" "gcd" "primes" "tak" "tak-mem")
BENCHMARKS=("salloc")
OUTPUT_FILE="../data/time-execution.csv"
RUNS=1

# Ensure the data directory exists
mkdir -p ../data

# Initialize CSV file with header
echo "Benchmark,Time,Error" > $OUTPUT_FILE

# Function to calculate standard deviation
calculate_sd() {
    local times=("$@")
    local count=${#times[@]}
    local sum=0
    local mean
    local sq_diff_sum=0

    if [ "$count" -le 1 ]; then
        # Not enough data to calculate standard deviation
        echo "NaN"
        return
    fi

    # Calculate the mean
    for time in "${times[@]}"; do
        sum=$(echo "$sum + $time" | bc -l)
    done
    mean=$(echo "$sum / $count" | bc -l)

    # Calculate the sum of squared differences from the mean
    for time in "${times[@]}"; do
        sq_diff=$(echo "$time - $mean" | bc -l)
        sq_diff=$(echo "$sq_diff * $sq_diff" | bc -l)
        sq_diff_sum=$(echo "$sq_diff_sum + $sq_diff" | bc -l)
    done

    # Calculate standard deviation
    sd=$(echo "scale=10; sqrt($sq_diff_sum / ($count - 1))" | bc -l)

    # Calculate standard error
    sem=$(echo "scale=10; $sd / sqrt($count)" | bc -l)

    echo "$sem"
}

# Loop through each benchmark
for benchmark in "${BENCHMARKS[@]}"; do
    total_time=0
    times=()

    # Run the benchmark specified number of times
    for ((i=1; i<=RUNS; i++)); do
        # Run the command and measure time
        result=$( { time $WDCLI ../$benchmark.wasm --invoke bench --no-debug > /dev/null; } 2>&1 )
        
        # Extract the real time (format could be XmYs or just Xs)
        real_time=$(echo "$result" | grep "real" | awk '{print $2}')

        # Check if the real time was captured correctly
        if [[ -z "$real_time" ]]; then
            echo "Error: Could not parse the time output for benchmark $benchmark"
            continue
        fi

        # Print benchmark and time result
        echo "$benchmark,$i,$real_time"

        # Check if there is a minute part in the time
        if [[ "$real_time" == *m* ]]; then
            # Extract minutes and seconds if present
            minutes=$(echo $real_time | cut -d'm' -f1)
            seconds=$(echo $real_time | cut -d'm' -f2 | sed 's/s//')
            current_time=$(echo "$minutes * 60 + $seconds" | bc -l)
        else
            # Only seconds present
            current_time=$(echo $real_time | sed 's/s//' | bc -l)
        fi

        # Add the current time to the total time
        total_time=$(echo "$total_time + $current_time" | bc -l)
        # Save each time for standard deviation calculation
        times+=("$current_time")
    done

    # Calculate the average time over the number of runs
    average_time=$(echo "$total_time / $RUNS" | bc -l)

    # Calculate the standard error
    standard_error=$(calculate_sd "${times[@]}")

    # Save the benchmark name, average time, and standard error to the CSV file
    echo "$benchmark,$average_time,$standard_error" >> $OUTPUT_FILE
done

echo "Benchmark average times and standard errors have been saved to $OUTPUT_FILE."
