# WARDuino Security Check Detailed Performance Report

Generated: 2025-10-30 16:26:01

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
| fann1 | 770,454 | 763,941 | 810,130 | 787,636 | 5,041,217 | 5,135,023 |
| binarytrees | 1,057,906 | 1,049,470 | 1,103,444 | 1,079,020 | 6,908,066 | 7,097,518 |
| knucleotide | 141,873 | 133,067 | 137,830 | 134,668 | 750,149 | 761,427 |
| memory_matrix_w | 4,079,380 | 4,002,656 | 4,298,375 | 4,123,782 | 28,043,894 | 27,942,695 |
| memory_copy_w | 9,759,545 | 9,718,311 | 10,254,770 | 9,929,088 | 66,635,134 | 64,001,469 |
| revcomp_fasta | 24,573 | 24,408 | 25,916 | 24,963 | 162,166 | 161,420 |
| mandelbrot | 709,570 | 702,768 | 742,626 | 726,425 | 4,637,242 | 4,603,667 |
| dijkstra_heap | 16,591 | 16,343 | 17,586 | 16,939 | 119,764 | 118,394 |
| pointer_chase | 6,367,720 | 6,279,175 | 6,669,530 | 6,490,746 | 42,679,550 | 43,450,651 |
| quicksort_warduino | 269,635 | 270,020 | 282,164 | 275,376 | 1,840,126 | 1,833,045 |

## Memory Usage Details (MB)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| fann1 | 0.14 | 0.14 | 0.14 | 0.14 | 0.14 | 0.14 |
| binarytrees | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 |
| knucleotide | 146.16 | 146.16 | 146.16 | 146.16 | 146.16 | 146.16 |
| memory_matrix_w | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 | 7.95 |
| memory_copy_w | 2.14 | 2.14 | 2.14 | 2.14 | 2.14 | 2.14 |
| revcomp_fasta | 0.58 | 0.58 | 0.58 | 0.58 | 0.58 | 0.58 |
| mandelbrot | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 |
| dijkstra_heap | 3.08 | 3.08 | 3.08 | 3.08 | 3.08 | 3.08 |
| pointer_chase | 1.14 | 1.14 | 1.14 | 1.14 | 1.14 | 1.14 |
| quicksort_warduino | 4.08 | 4.08 | 4.08 | 4.08 | 4.08 | 4.08 |

## Test Success Rate (%)

| Test Program | Baseline | Memory Protection | Stack Protection | CFI Protection | Address Sanitizer | Full Protection |
|--------------|----------|-------------------|------------------|----------------|-------------------|-----------------|
| fann1 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| binarytrees | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| knucleotide | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| memory_matrix_w | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| memory_copy_w | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| revcomp_fasta | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| mandelbrot | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| dijkstra_heap | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| pointer_chase | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| quicksort_warduino | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |

## Performance Overhead Analysis (Relative to Baseline)

| Configuration | Average Time Overhead (%) | Average Memory Overhead (%) |
|---------------|--------------------------|----------------------------|
| Memory Protection | +-1.5% | +0.0% |
| Stack Protection | +4.3% | +0.0% |
| CFI Protection | +1.2% | +0.0% |
| Address Sanitizer | +559.4% | +0.0% |
| Full Protection | +559.6% | +0.0% |

## Failed Tests

