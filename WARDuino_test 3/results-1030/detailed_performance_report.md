# WARDuino Security Check Detailed Performance Report

Generated: 2025-10-30 12:34:27

Results Directory: /home/yuxin/WARDuino_test/results

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
| knucleotide | 227,348 | 132,610 | 186,984 | 143,704 | 760,738 | 732,910 |
| memory_matrix_w | 4,078,664 | 4,008,778 | 4,253,093 | 4,138,108 | 26,339,624 | 27,093,210 |
| memory_copy_w | 9,779,432 | 9,667,554 | 10,278,301 | 9,974,768 | 64,179,578 | 65,000,589 |
| revcomp_fasta | 24,642 | 24,830 | 26,037 | 25,444 | 167,802 | 165,657 |
| dijkstra_heap | 16,839 | 16,555 | 17,564 | 17,116 | 117,503 | 118,700 |
| pointer_chase | 6,385,107 | 6,376,728 | 6,935,263 | 6,506,267 | 42,301,615 | 43,424,788 |
| quicksort_warduino | 269,961 | 269,331 | 282,639 | 277,726 | 1,835,792 | 1,858,741 |

## Memory Usage Details (MB)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| knucleotide | 146.16 | 146.16 | 146.16 | 146.16 | 146.16 | 146.16 |
| memory_matrix_w | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 |
| memory_copy_w | 2.14 | 2.14 | 2.14 | 2.14 | 2.14 | 2.14 |
| revcomp_fasta | 0.58 | 0.58 | 0.58 | 0.58 | 0.58 | 0.58 |
| dijkstra_heap | 3.08 | 3.08 | 3.08 | 3.08 | 3.08 | 3.08 |
| pointer_chase | 1.14 | 1.14 | 1.14 | 1.14 | 1.14 | 1.14 |
| quicksort_warduino | 4.08 | 4.08 | 4.08 | 4.08 | 4.08 | 4.08 |

## Test Success Rate (%)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| knucleotide | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| memory_matrix_w | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| memory_copy_w | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| revcomp_fasta | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| dijkstra_heap | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| pointer_chase | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| quicksort_warduino | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |

## Performance Overhead Analysis (Relative to Baseline)

| Configuration | Average Time Overhead (%) | Average Memory Overhead (%) |
|---------------|--------------------------|----------------------------|
| Memory Protection | +-6.5% | +0.0% |
| Stack Protection | +2.1% | +0.0% |
| CFI Protection | +-3.4% | +0.0% |
| Address Sanitizer | +522.6% | +0.0% |
| Full Protection | +528.2% | +0.0% |

## Failed Tests

