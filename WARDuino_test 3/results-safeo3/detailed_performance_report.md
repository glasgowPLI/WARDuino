# WARDuino Security Check Detailed Performance Report

Generated: 2025-10-21 09:56:32

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
| fann1 | 746,740 | 715,879 | 715,877 | 703,243 | 4,754,165 | 4,905,185 |
| richards | Failed | Failed | Failed | Failed | Failed | Failed |
| binarytrees | 1,026,711 | 975,973 | 981,640 | 974,983 | 6,392,671 | 6,709,437 |
| mandelbrot | 686,350 | 660,709 | 662,230 | 643,966 | 4,257,667 | 4,430,982 |
| memory_matrix1 | 3,876,290 | 3,691,286 | 3,717,559 | 3,664,732 | 25,483,697 | 25,608,261 |

## Memory Usage Details (MB)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| fann1 | 0.14 | 0.14 | 0.14 | 0.14 | 0.14 | 0.14 |
| richards | N/A | N/A | N/A | N/A | N/A | N/A |
| binarytrees | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 |
| mandelbrot | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 |
| memory_matrix1 | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 |

## Test Success Rate (%)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| fann1 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| richards | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| binarytrees | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| mandelbrot | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| memory_matrix1 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |

## Performance Overhead Analysis (Relative to Baseline)

| Configuration | Average Time Overhead (%) | Average Memory Overhead (%) |
|---------------|--------------------------|----------------------------|
| Memory Protection | +-4.4% | +0.0% |
| Stack Protection | +-4.0% | +0.0% |
| CFI Protection | +-5.6% | +0.0% |
| Address Sanitizer | +534.3% | +0.0% |
| Full Protection | +554.1% | +0.0% |

## Failed Tests

- **baseline - richards.wasm**: Unknown error
- **memory - richards.wasm**: Unknown error
- **stack - richards.wasm**: Unknown error
- **cfi - richards.wasm**: Unknown error
- **address - richards.wasm**: Unknown error
- **full - richards.wasm**: Unknown error
