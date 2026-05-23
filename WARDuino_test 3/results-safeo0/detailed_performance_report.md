# WARDuino Security Check Detailed Performance Report

Generated: 2025-10-21 10:14:00

Results Directory: /home/yuxin/WARDuino_test/results-safe

**Note**: All time data comes from WARDuino internal performance counters (clock cycles)

## Performance Comparison Charts

The following charts provide comprehensive performance comparison analysis:

- `all_modules_time_comparison.png` - Execution time comparison across all modules
- `all_modules_memory_comparison.png` - Memory usage comparison across all modules
- `module_*_comparison.png` - Individual module detailed comparisons
- `average_overhead_comparison.png` - Average performance overhead comparison (baseline as reference)
- `success_rate_comparison.png` - Test success rate comparison

## Execution Time Details (Clock Cycles)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| fann1 | 2,209,286 | 2,184,802 | 2,222,377 | 2,201,289 | 8,330,554 | 8,535,909 |
| richards | Failed | Failed | Failed | Failed | Failed | Failed |
| binarytrees | 3,011,136 | 3,002,323 | 3,028,345 | 2,963,353 | 11,531,953 | 11,488,505 |
| mandelbrot | 2,006,094 | 2,024,844 | 2,022,952 | 1,994,453 | 7,438,918 | 7,587,729 |
| memory_matrix1 | 11,470,105 | 11,409,013 | 11,472,016 | 11,357,116 | Failed | Failed |

## Memory Usage Details (MB)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| fann1 | 0.14 | 0.14 | 0.14 | 0.14 | 0.14 | 0.14 |
| richards | N/A | N/A | N/A | N/A | N/A | N/A |
| binarytrees | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 |
| mandelbrot | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 |
| memory_matrix1 | 7.95 | 7.95 | 7.95 | 7.95 | N/A | N/A |

## Test Success Rate (%)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| fann1 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| richards | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| binarytrees | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| mandelbrot | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| memory_matrix1 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 0.0 |

## Performance Overhead Analysis (Relative to Baseline)

| Configuration | Average Time Overhead (%) | Average Memory Overhead (%) |
|---------------|--------------------------|----------------------------|
| Memory Protection | +-0.2% | +0.0% |
| Stack Protection | +0.5% | +0.0% |
| CFI Protection | +-0.9% | +0.0% |
| Address Sanitizer | +inf% | +-25.0% |
| Full Protection | +inf% | +-25.0% |

## Failed Tests

- **baseline - richards.wasm**: Unknown error
- **memory - richards.wasm**: Unknown error
- **stack - richards.wasm**: Unknown error
- **cfi - richards.wasm**: Unknown error
- **address - richards.wasm**: Unknown error
- **full - richards.wasm**: Unknown error
- **address - memory_matrix1.wasm**: Unknown error
- **full - memory_matrix1.wasm**: Unknown error
