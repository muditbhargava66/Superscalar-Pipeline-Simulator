# Benchmark Suite Results

![Benchmark Comparison](benchmark_comparison.png)

## Detailed Metrics

| Benchmark | IPC | Cycles | Branch Accuracy | Cache Hit Rate | EPI (pJ) |
|-----------|-----|--------|-----------------|----------------|----------|
| basic_operations | 0.620 | 10000 | 95.9% | 99.1% | 104925.4 |
| bubble_sort | 0.923 | 10000 | 100.0% | 99.7% | 80930.7 |
| fibonacci_recursive | 0.833 | 10000 | 96.7% | 80.3% | 87015.1 |
| dhrystone_like | 0.781 | 8043 | 95.9% | 91.0% | 90897.3 |
| quicksort | 0.946 | 10000 | 99.6% | 99.4% | 80525.6 |
| matrix_multiplication | 0.921 | 38 | 0.0% | 0.0% | 80242.3 |
| streaming_access | 0.876 | 10000 | 99.7% | 99.6% | 83988.4 |
| memory_access_patterns | 0.889 | 10000 | 100.0% | 99.6% | 83946.0 |
| compute_intensive | 0.739 | 2881 | 93.6% | 95.0% | 93901.1 |
| simple_arithmetic | 0.604 | 48 | 76.9% | 0.0% | 100287.8 |
| simple_fibonacci | 0.688 | 48 | 66.7% | 0.0% | 94089.1 |
| simple_sort | 0.826 | 23 | 100.0% | 25.0% | 79600.2 |
| simple_test | 0.667 | 9 | 0.0% | 0.0% | 79066.9 |
| validation_suite | 0.826 | 10000 | 99.9% | 99.5% | 88478.3 |
