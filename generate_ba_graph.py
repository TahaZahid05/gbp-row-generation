#!/usr/bin/env python3
"""Generate a Barabási-Albert graph and save it as an edgelist."""

import networkx as nx

def generate_ba_graph(n=5000, m=2, output_file="ba5000.edgelist"):
    """
    Generate a Barabási-Albert graph with n vertices and m new edges per vertex.
    
    Args:
        n: Number of vertices
        m: Number of edges to attach from a new vertex to existing vertices
        output_file: Path to save the edgelist
    """
    print(f"Generating Barabási-Albert graph with {n} vertices and m={m}...")
    G = nx.barabasi_albert_graph(n, m, seed=42)
    
    print(f"Graph generated: {G.number_of_nodes()} vertices, {G.number_of_edges()} edges")
    
    print(f"Saving to {output_file}...")
    with open(output_file, "w") as f:
        for u, v in G.edges():
            f.write(f"{u} {v}\n")
    
    print(f"✓ Graph saved to {output_file}")
    return output_file

if __name__ == "__main__":
    generate_ba_graph()
