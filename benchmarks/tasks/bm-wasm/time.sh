#!/bin/bash

# Define directories and output file
BENCHMARKS=("catalan" "fac" "fib" "gcd" "primes" "tak" "tak-mem")
OUTPUT_FILE="time.csv"

# Initialize CSV file with header
echo "Benchmark,Time" > $OUTPUT_FILE

# Loop through each benchmark and run the timing command
for benchmark in "${BENCHMARKS[@]}"; do
    # Run the command and measure time
    result=$( { time wdcli $benchmark.wasm --invoke bench --no-debug > /dev/null; } 2>&1 )
    
    # Extract the real time (format could be XmYs or just Xs)
    real_time=$(echo "$result" | grep "real" | awk '{print $2}')
    
    # Check if there is a minute part in the time
    if [[ "$real_time" == *m* ]]; then
        # Extract minutes and seconds if present
        minutes=$(echo $real_time | cut -d'm' -f1)
        seconds=$(echo $real_time | cut -d'm' -f2 | sed 's/s//')
        total_time=$(echo "$minutes * 60 + $seconds" | bc -l)
    else
        # Only seconds present
        total_time=$(echo $real_time | sed 's/s//' | bc -l)
    fi

    # Save the benchmark name and real time to the CSV file
    echo "$benchmark,$total_time" >> $OUTPUT_FILE
done

echo "Benchmark times have been saved to $OUTPUT_FILE."
