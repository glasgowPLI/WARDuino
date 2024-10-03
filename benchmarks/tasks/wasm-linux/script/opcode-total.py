import csv
import os

def count_opcodes(datafile, outputfile):
    benchmarks = {}
    with open(datafile, 'r') as f:
        lines = f.readlines()
        benchmark_name = None
        allocator = None
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            if '.wasm' in line:  # This is the benchmark path line
                path = line
                allocator, benchmark = path.split('/')[-2:]
                allocator = allocator.split('benchmarks-')[-1]
                benchmark_name = benchmark.split('.wasm')[0]
                benchmarks[(allocator, benchmark_name)] = 0
            elif allocator is not None and benchmark_name is not None:
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    count, _ = parts
                    benchmarks[(allocator, benchmark_name)] += int(count)
                else:
                    print(f"Skipping line due to unexpected format: '{line}'")
            else:
                print(f"Invalid line encountered: {line}")

    # Create the CSV file
    with open(outputfile, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['allocator', 'benchmark', 'TOTAL_OPCODES'])

        for (allocator, benchmark), total_opcodes in benchmarks.items():
            csvwriter.writerow([allocator, benchmark, total_opcodes])

if __name__ == "__main__":
    data_dir = '../data'
    datafile = os.path.join(data_dir, "results-opcode.csv")
    outputfile = os.path.join(data_dir, "opcode-total.csv")
    count_opcodes(datafile, outputfile)
