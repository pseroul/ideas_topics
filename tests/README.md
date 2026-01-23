# Performance Testing

This directory contains performance tests for the `generate_toc_structure` method in `data_similarity.py`.

## Available Tests

### 1. Basic Performance Test (`test_performance.py`)

A comprehensive test that measures:
- Execution time using `time.perf_counter()`
- Memory usage using `psutil` and `tracemalloc`
- Basic functionality verification
- Tests with real data from `test_data_100.txt`

### 2. Rendering Performance Test (`test_render_toc_performance.py`)

A test specifically designed to measure:
- Performance of `render_toc_from_structure` function
- Memory usage when rendering larger hierarchical structures
- Execution time for complex TOC rendering scenarios

### 3. Flamegraph Generation

To create flamegraphs for profiling:

```bash
# Method 1: Using py-spy (recommended)
python tests/test_performance.py &
PID=$!
py-spy record -o flamegraph.svg --pid $PID

# Method 2: Using cProfile
python -m cProfile -o profile_output.prof tests/test_performance.py
snakeviz profile_output.prof
```

## Requirements

The test requires the following Python packages:
- psutil
- py-spy (for flamegraphs)
- All packages from requirements.txt

Install with:
```bash
pip install psutil py-spy
```

## Running Tests

```bash
# Run basic performance test
python tests/test_performance.py

# Run rendering performance test
python tests/test_render_toc_performance.py
```

## Test Data

The tests use `tests/test_data_100.txt` which contains sample data for performance testing. The file format is:
```
Idea 1|Description of idea 1
Idea 2|Description of idea 2
...
```

## Limitations

Due to the UMAP algorithm requirements, the test may fail with "k >= N" errors when using very small datasets. The test automatically handles this by providing alternative profiling methods.

## Manual Flamegraph Creation

1. Run the test in background: `python tests/test_performance.py &`
2. Get the PID: `ps aux | grep test_performance`
3. Generate flamegraph: `py-spy record -o flamegraph.svg --pid <PID>`
4. View: `firefox flamegraph.svg`

## Test Structure

### test_performance.py
- Measures execution time and memory usage of `generate_toc_structure`
- Uses real test data from `test_data_100.txt`
- Tests with 100 items from the test dataset
- Includes cleanup of test data after execution

### test_render_toc_performance.py
- Measures performance of `render_toc_from_structure` function
- Tests with larger, more complex hierarchical structures
- Provides comprehensive metrics for rendering performance
- Simulates realistic TOC structures with multiple levels
