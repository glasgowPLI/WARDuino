#!/bin/bash

# Define directories and output file
WASM_DIR="bm-wasm"
BENCHMARKS=("catalan" "fac" "fib" "gcd" "primes" "tak" "tak-mem")
OUTPUT_FILE="time.csv"

# Initialize CSV file with header
echo "Benchmark,Time" > $OUTPUT_FILE

# Loop through each benchmark and run the timing command
for benchmark in "${BENCHMARKS[@]}"; do
    # Run the command and measure time
    result=$( { time wdcli ./$WASM_DIR/$benchmark.wasm --invoke bench --no-debug > /dev/null; } 2>&1 )
    
    # Extract real time and format to seconds
    real_time=$(echo "$result" | grep "real" | awk '{print $2}')
    
    # Convert "m" and "s" to seconds (if in format mm:ss)
    minutes=$(echo $real_time | cut -d'm' -f1)
    seconds=$(echo $real_time | cut -d'm' -f2 | sed 's/s//')

    # If there's no minutes part, just assign seconds
    if [[ "$real_time" != *m* ]]; then
        minutes=0
        seconds=$(echo $real_time | sed 's/s//')
    fi

    # Calculate total time in seconds
    total_time=$(echo "$minutes * 60 + $seconds" | bc)

    # Save the benchmark name and real time to the CSV file
    echo "$benchmark,$total_time" >> $OUTPUT_FILE
done

echo "Benchmark times have been saved to $OUTPUT_FILE."
