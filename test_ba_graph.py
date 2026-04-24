#!/usr/bin/env python3
"""Test your code on the Barabási-Albert graph."""

import sys
import os
import time

# Add SCIP and MinGW DLL directories for C++ backend
os.add_dll_directory(r"C:\Program Files\SCIPOptSuite 10.0.2\bin")
os.add_dll_directory(r"C:\msys64\mingw64\bin")

from gbp.graph import Graph
from gbp.utils import load_graph_from_edgelist, save_result
from gbp.prym import prym

def test_ba_graph(edgelist_file="ba5000.edgelist", backend="cpp"):
    print(f"Loading graph from {edgelist_file}...")
    try:
        graph = load_graph_from_edgelist(edgelist_file)
    except FileNotFoundError:
        print(f"Error: {edgelist_file} not found!")
        print("Please run: python generate_ba_graph.py")
        sys.exit(1)

    print(f"✓ Graph loaded: {graph.n_vertices} vertices")

    print("\nRunning prym algorithm...")
    start_time = time.time()
    b_G, sequence = prym(graph, backend=backend)
    elapsed = time.time() - start_time

    print(f"\nResults:")
    print(f"  Burning Number: {b_G}")
    print(f"  Sequence length: {len(sequence)}")
    print(f"  Sequence (first 20): {sequence[:20]}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Backend: {backend}")

    result_file = "ba5000_result.txt"
    save_result(result_file, b_G, sequence)
    print(f"\n✓ Results saved to {result_file}")

    return b_G, sequence

if __name__ == "__main__":
    # Usage:
    #   python test_ba_graph.py           -> uses C++ backend (default)
    #   python test_ba_graph.py --python  -> uses Python backend
    #   python test_ba_graph.py --cpp     -> uses C++ backend explicitly
    backend = "cpp"
    for arg in sys.argv[1:]:
        if arg == "--python":
            backend = "python"
        elif arg == "--cpp":
            backend = "cpp"

    test_ba_graph(backend=backend)