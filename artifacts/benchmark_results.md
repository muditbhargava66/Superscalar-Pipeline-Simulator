# Benchmark Suite Results

![Benchmark Comparison](benchmark_comparison.png)

![Stall Breakdown](stall_breakdown.png)

## Detailed Metrics

| Benchmark | IPC | Cycles | Branch Accuracy | Cache Hit Rate | EPI (pJ) | Issue Slot Stalls |
|-----------|-----|--------|-----------------|----------------|----------|--------------|
| basic_operations | 0.641 | 78 | 87.5% | 0.0% | 512.9 | 73 |
| bubble_sort | 1.125 | 10000 | 99.9% | 99.8% | 364.1 | 9999 |
| fibonacci_recursive | 1.176 | 10000 | 95.6% | 76.6% | 356.8 | 8971 |
| dhrystone_like | 1.041 | 10000 | 99.0% | 99.5% | 380.2 | 8498 |
| quicksort | 1.425 | 10000 | 99.6% | 99.6% | 322.3 | 9394 |
| matrix_multiplication | 1.438 | 251 | 71.4% | 84.6% | 329.9 | 246 |
| streaming_access | 1.333 | 10000 | 100.0% | 99.8% | 334.0 | 9999 |
| memory_access_patterns | 1.330 | 880 | 97.9% | 97.3% | 342.3 | 730 |
| compute_intensive | 1.333 | 10000 | 100.0% | 99.8% | 334.0 | 9999 |
| simple_arithmetic | 0.881 | 10000 | 92.7% | 99.2% | 421.1 | 8333 |
| simple_fibonacci | 1.111 | 10000 | 99.8% | 0.0% | 372.5 | 9722 |
| simple_sort | 0.913 | 23 | 100.0% | 17.6% | 409.8 | 19 |
| simple_test | 1.143 | 7 | 0.0% | 0.0% | 368.0 | 3 |
| validation_suite | 1.000 | 19 | 66.7% | 0.0% | 396.7 | 14 |
