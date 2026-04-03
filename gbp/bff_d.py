import math
from gbp.graph import Graph
from gbp.utils import is_valid_burning_sequence

def bff_d(graph: Graph) -> list[int]:
    """
    Modified BFF heuristic from the paper.
    Computes distances on demand via a single BFS per iteration.
    """
    if graph.n_vertices == 0:
        return []
        
    S = []
    min_dist = [math.inf] * graph.n_vertices
    
    # Repeat until S is a valid burning sequence for the current |S|
    while True:
        if not S:
            # First iteration: pick any vertex, e.g. vertex 0
            v_i = 0
        else:
            # v_i = argmax_{u in V} min_dist[u]
            v_i = max(range(graph.n_vertices), key=lambda u: min_dist[u])
            
        S.append(v_i)
        
        dist_from_vi = graph.get_distances_from(v_i)
        
        for u in range(graph.n_vertices):
            min_dist[u] = min(min_dist[u], dist_from_vi[u])
            
        if is_valid_burning_sequence(graph, S):
            break
            
    return S
