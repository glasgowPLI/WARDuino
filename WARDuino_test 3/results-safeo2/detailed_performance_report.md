# WARDuino Security Check Detailed Performance Report

Generated: 2025-10-21 10:27:12

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
| fann1 | 767,582 | 761,045 | 764,466 | 813,242 | 5,161,635 | 5,144,690 |
| richards | Failed | Failed | Failed | Failed | Failed | Failed |
| binarytrees | 1,046,005 | 1,038,509 | 1,037,860 | 1,097,396 | 6,985,729 | 7,050,422 |
| mandelbrot | 711,101 | 703,971 | 703,167 | 740,765 | 4,628,147 | 4,618,090 |
| memory_matrix1 | 4,003,243 | 3,981,085 | 4,010,600 | 4,176,801 | 26,743,755 | 27,297,657 |

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
| Memory Protection | +-0.8% | +0.0% |
| Stack Protection | +-0.5% | +0.0% |
| CFI Protection | +4.8% | +0.0% |
| Address Sanitizer | +564.8% | +0.0% |
| Full Protection | +568.9% | +0.0% |

## Failed Tests

- **baseline - richards.wasm**: Unknown error
- **memory - richards.wasm**: Unknown error
- **stack - richards.wasm**: Unknown error
- **cfi - richards.wasm**: Unknown error
- **address - richards.wasm**: Unknown error
- **full - richards.wasm**: Unknown error
