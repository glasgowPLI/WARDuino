#!/bin/bash

# Define directories and output file
BENCHMARKS=("catalan" "fac" "fib" "gcd" "primes" "tak" "tak-mem")
OUTPUT_FILE="time.csv"
RUNS=30

# Initialize CSV file with header
echo "Benchmark,Time" > $OUTPUT_FILE

# Loop through each benchmark
for benchmark in "${BENCHMARKS[@]}"; do
    total_time=0

    # Run the benchmark 30 times
    for ((i=1; i<=RUNS; i++)); do
        # Run the command and measure time
        result=$( { time wdcli $benchmark.wasm --invoke bench --no-debug > /dev/null; } 2>&1 )
        
        # Extract the real time (format could be XmYs or just Xs)
        real_time=$(echo "$result" | grep "real" | awk '{print $2}')
        
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
    done

    # Calculate the average time over 30 runs
    average_time=$(echo "$total_time / $RUNS" | bc -l)

    # Save the benchmark name and average time to the CSV file
    echo "$benchmark,$average_time" >> $OUTPUT_FILE
done

echo "Benchmark average times have been saved to $OUTPUT_FILE."
