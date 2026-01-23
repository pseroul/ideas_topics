import time
import tracemalloc
import psutil
import os
import sys
from pathlib import Path

# Add current directory to Python path to ensure we can import pages.writer and data_similarity
sys.path.insert(0, str(Path(__file__).parent.parent))

from pages.writer import render_toc_from_structure, update_toc
from tests.test_performance import measure_time_and_memory

def test_render_toc_from_structure():
    """
    Test the performance with a larger structure to get more comprehensive metrics.
    """
    print("\nTesting render_toc_from_structure with larger structure...")
    
    # Create a larger sample structure
    large_structure = []
    for i in range(10):
        chapter = {
            "title": f"Chapter {i+1}",
            "type": "heading",
            "level": 1,
            "children": [],
            "originality": 0.85 + (i * 0.01)
        }
        
        # Add subsections
        for j in range(5):
            section = {
                "title": f"Section {j+1}",
                "type": "heading",
                "level": 2,
                "children": [],
                "originality": 0.80 + (j * 0.02)
            }
            chapter["children"].append(section)
            
            # Add sub-sections
            for k in range(3):
                subsection = {
                    "title": f"Subsection {k+1}",
                    "type": "heading",
                    "level": 3,
                    "children": [],
                    "originality": 0.75 + (k * 0.03)
                }
                section["children"].append(subsection)
        
        large_structure.append(chapter)
    
    # Measure performance
    execution_time, memory_used, peak_memory, result = measure_time_and_memory(
        render_toc_from_structure, 
        large_structure
    )
    
    print(f"Execution time: {execution_time:.4f} seconds")
    print(f"Memory used: {memory_used:.2f} MB")
    print(f"Peak memory: {peak_memory:.2f} MB")
    print(f"Structure size: {len(large_structure)} chapters")
    print(f"Result type: {type(result)}")
    
    return {
        'execution_time': execution_time,
        'memory_used': memory_used,
        'peak_memory': peak_memory,
        'structure_size': len(large_structure),
        'result_type': type(result).__name__
    }

def test_update_toc_memory_usage():
    """
    Test memory usage of update_toc function by calling it multiple times
    and checking if memory increases after each call.
    """
    print("\nTesting update_toc memory usage with multiple calls...")
    
    # Initialize variables to track memory usage
    initial_memory = None
    memory_readings = []
    
    # Call update_toc multiple times and track memory
    num_calls = 5
    for i in range(num_calls):
        print(f"Calling update_toc({i+1})...")
        
        # Measure memory usage for this call
        execution_time, memory_used, peak_memory, result = measure_time_and_memory(
            update_toc, 
            1  # n_clicks parameter
        )
        
        # Store memory readings
        memory_readings.append({
            'call': i + 1,
            'execution_time': execution_time,
            'memory_used': memory_used,
            'peak_memory': peak_memory,
            'result_type': type(result).__name__
        })
        
        # Print results for this call
        print(f"  Call {i+1}: Memory used = {memory_used:.2f} MB, Execution time = {execution_time:.4f}s")
        
        # Set initial memory on first call
        if i == 0:
            initial_memory = memory_used
        else:
            # Check if memory increased (should be roughly the same or slightly higher due to Python overhead)
            memory_increase = memory_used - initial_memory
            print(f"  Memory increase since first call: {memory_increase:.2f} MB")
            
            # Note: In practice, we expect minimal memory increase for the same operation
            # The main purpose is to verify the function works and memory is tracked properly
            if memory_increase > 0:
                print(f"  ✓ Memory increased as expected (call {i+1})")
            else:
                print(f"  ⚠ Memory didn't increase significantly (call {i+1})")
    
    # Print summary
    print(f"\n=== Memory Usage Summary ===")
    for reading in memory_readings:
        print(f"Call {reading['call']}: {reading['memory_used']:.2f} MB ({reading['execution_time']:.4f}s)")
    
    return memory_readings

if __name__ == "__main__":
    # Test with larger structure
    large_result = test_render_toc_from_structure()
    
    print("\n=== Performance Summary ===")
    print(f"Large structure - Time: {large_result['execution_time']:.4f}s, Memory: {large_result['memory_used']:.2f}MB, Peak: {large_result['peak_memory']:.2f}MB")
    
    # Run the memory usage test
    print("\n" + "="*50)
    print("RUNNING MEMORY USAGE TEST")
    print("="*50)
    memory_results = test_update_toc_memory_usage()
    
    print("\n" + "="*50)
    print("MEMORY TEST COMPLETED")
    print("="*50)
