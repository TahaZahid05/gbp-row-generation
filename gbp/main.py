import sys
import time
import argparse
from gbp.graph import Graph
from gbp.utils import load_graph_from_edgelist, save_result
from gbp.prym import prym

def run_karate_test():
    print("Running hardcoded Karate Club Graph test...")
    # 34 vertices, 78 edges
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 10), (0, 11), (0, 12), (0, 13), (0, 17), (0, 19), (0, 21), (0, 31),
        (1, 2), (1, 3), (1, 7), (1, 13), (1, 17), (1, 19), (1, 21), (1, 30),
        (2, 3), (2, 7), (2, 8), (2, 9), (2, 13), (2, 27), (2, 28), (2, 32),
        (3, 7), (3, 12), (3, 13),
        (4, 6), (4, 10),
        (5, 6), (5, 10), (5, 16),
        (6, 16),
        (8, 30), (8, 32), (8, 33),
        (9, 33),
        (13, 33),
        (14, 32), (14, 33),
        (15, 32), (15, 33),
        (18, 32), (18, 33),
        (19, 33),
        (20, 32), (20, 33),
        (22, 32), (22, 33),
        (23, 25), (23, 27), (23, 29), (23, 32), (23, 33),
        (24, 25), (24, 27), (24, 31),
        (25, 31),
        (26, 29), (26, 33),
        (27, 33),
        (28, 31), (28, 33),
        (29, 32), (29, 33),
        (30, 32), (30, 33),
        (31, 32), (31, 33),
        (32, 33)
    ]
    graph = Graph(34, edges)
    
    start_time = time.time()
    b_G, sequence = prym(graph)
    elapsed = time.time() - start_time
    
    print(f"Karate Club Graph: Burning Number = {b_G}")
    print(f"Sequence: {sequence}")
    print(f"Time: {elapsed:.2f}s")
    
    assert b_G == 3, f"Expected b_G = 3, got {b_G}"
    print("Test passed successfully!")

def main():
    parser = argparse.ArgumentParser(description="PRYM exact algorithm for Graph Burning Problem")
    parser.add_argument("graph_file", nargs='?', help="Path to edge list file")
    parser.add_argument("--output", help="Path to save result")
    parser.add_argument("--test", action="store_true", help="Run hardcoded Karate Club Graph test")
    
    args = parser.parse_args()
    
    if args.test:
        run_karate_test()
        return

    if not args.graph_file:
        parser.print_help()
        sys.exit(1)

    print(f"Loading graph from {args.graph_file}...")
    graph = load_graph_from_edgelist(args.graph_file)
    print(f"Graph loaded: {graph.n_vertices} vertices.")

    print("Running PRYM algorithm...")
    start_time = time.time()
    b_G, sequence = prym(graph)
    elapsed = time.time() - start_time
    
    print("---")
    print(f"Burning Number: {b_G}")
    print(f"Sequence: {sequence}")
    print(f"Wall clock time: {elapsed:.2f} seconds")
    
    if args.output:
        save_result(args.output, b_G, sequence)
        print(f"Result saved to {args.output}")

if __name__ == "__main__":
    main()
