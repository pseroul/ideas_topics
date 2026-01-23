import time
import tracemalloc
import psutil
import os
import sys
from pathlib import Path

# Add current directory to Python path to ensure we can import data_similarity
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_similarity import Embedder
import numpy as np

def measure_time_and_memory(func, *args, **kwargs):
    """
    Measure execution time and memory usage of a function.
    
    Args:
        func: Function to measure
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        tuple: (execution_time, memory_used, peak_memory_mb, result)
    """
    # Start time measurement
    start_time = time.perf_counter()
    
    # Start memory tracing
    tracemalloc.start()
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Execute the function
    result = func(*args, **kwargs)
    
    # Get final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Stop memory tracing and get peak memory
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Calculate metrics
    execution_time = time.perf_counter() - start_time
    memory_used = final_memory - initial_memory
    peak_memory_mb = peak / 1024 / 1024  # Convert bytes to MB
    
    return execution_time, memory_used, peak_memory_mb, result

def test_generate_toc_structure_performance():
    """
    Test the performance of generate_toc_structure method.
    """
    print("Testing generate_toc_structure performance...")

    dir_name = os.path.dirname(__file__)
    print("dir_name", dir_name)
    
    # Create a test embedder instance
    embedder = Embedder(db_path=os.path.join(dir_name,"data"), collection_name="test_collection")
    
    # Load test data from dedicated file
    test_data = []

    with open(os.path.join(dir_name, "test_data_100.txt"), "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Parse the line (format: "Idea X|Description")
                parts = line.split("|", 1)
                if len(parts) == 2:
                    name, description = parts
                    test_data.append((name, description))

    # Insert test data
    for name, description in test_data:
        embedder.insert_data(name, description)
    
    # Measure performance
    execution_time, memory_used, peak_memory, result = measure_time_and_memory(
        embedder.generate_toc_structure, 
        max_items=100
    )
    
    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Memory used: {memory_used:.2f} MB")
    print(f"Peak memory: {peak_memory:.2f} MB")
    print(f"Result length: {len(result) if isinstance(result, list) else 'N/A'}")
    
    # Clean up test data
    for name, _ in test_data:
        embedder.remove_data(name)
    
    return {
        'execution_time': execution_time,
        'memory_used': memory_used,
        'peak_memory': peak_memory,
        'result_length': len(result) if isinstance(result, list) else 0
    }

if __name__ == "__main__":

    test_generate_toc_structure_performance()
