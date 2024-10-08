import csv
import os

def initialize_categories():
    return {
        'MOVE': 0,
        'ARITH_INT': 0,
        'ARITH_FLOAT': 0,
        'CONTROL': 0,
        'BOUND': 0
    }

def categorize_opcode(opcode, count, categories):
    opcode = opcode.lower()
    if any(substring in opcode for substring in ['size', 'grow', 'copy', 'fill', 'set', 'get', 'slot', 'const', 'trunc', 'extend', 'convert', 'reinterpret']):
        categories['MOVE'] += count
    elif any(substring in opcode for substring in ['add', 'subtract', 'multiply', 'divide', 'shift', 'rotl', 'wrap', 'remainder', 'sqrt', 'pop', 'and', 'than', 'to', 'or', 'equal', 'negate']):
        if 'i32' in opcode or 'i64' in opcode or 'u32' in opcode or 'u64' in opcode:
            categories['ARITH_INT'] += count
        elif 'f32' in opcode or 'f64' in opcode:
            categories['ARITH_FLOAT'] += count
    elif any(substring in opcode for substring in ['promote', 'demote', 'if', 'call', 'select', 'continue', 'abs', 'ctz', 'clz', 'ceil']):
        categories['CONTROL'] += count
    elif any(substring in opcode for substring in ['load', 'store']):
        categories['BOUND'] += count

def categorize_opcodes(datafile, outputfile):
    benchmarks = {}
    with open(datafile, 'r') as f:
        lines = f.readlines()
        benchmark_name = None
        allocator = None
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            if '.wasm' in line:  # This is the benchmark path
                path = line
                allocator, benchmark = path.split('/')[-2:]
                allocator = allocator.split('benchmarks-')[-1]
                benchmark_name = benchmark.split('.wasm')[0]
                benchmarks[(allocator, benchmark_name)] = initialize_categories()
            elif allocator is not None and benchmark_name is not None:
                # This is an opcode line
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    count, opcode = parts
                    categorize_opcode(opcode, int(count), benchmarks[(allocator, benchmark_name)])
                else:
                    print(f"Skipping line due to unexpected format: {line}")
            else:
                print(f"Invalid line encountered: {line}")

    # Create the CSV file
    with open(outputfile, 'w', newline='') as csvfile:
        fieldnames = ['allocator', 'benchmark', 'MOVE', 'ARITH_INT', 'ARITH_FLOAT', 'CONTROL', 'BOUND']
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvwriter.writeheader()

        for (allocator, benchmark), category_counts in benchmarks.items():
            row = {'allocator': allocator, 'benchmark': benchmark}
            row.update(category_counts)
            csvwriter.writerow(row)

if __name__ == "__main__":
    data_dir = '../data'
    datafile = os.path.join(data_dir, "results-opcode.csv")
    outputfile = os.path.join(data_dir, "categorized_results.csv")
    categorize_opcodes(datafile, outputfile)
