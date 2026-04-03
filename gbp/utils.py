import math
from gbp.graph import Graph

def compute_bounds(S: list[int]) -> tuple[int, int]:
    """Given BFF-d sequence S, return (L, U) where U = len(S), L = ceil((len(S) + 2) / 3)."""
    L = math.ceil((len(S) + 2) / 3)
    U = len(S)
    return L, U

def is_valid_burning_sequence(graph: Graph, S: list[int]) -> bool:
    """Check if S is a valid burning sequence for graph."""
    if not S:
        return False
        
    k = len(S)
    for u in range(graph.n_vertices):
        # Vertex u needs to be covered by some vertex in S.
        # Covered means there exists an index i in [1..k] such that d(u, v_i) <= k - i.
        # i is 1-indexed in the math formula, so k - i becomes k - (idx + 1)
        covered = False
        for idx, vi in enumerate(S):
            if graph.get_distance(vi, u) <= k - (idx + 1):
                covered = True
                break
        if not covered:
            return False
            
    return True

def load_graph_from_edgelist(filepath: str) -> Graph:
    edges_raw = []
    mentions = set()
    header_passed = False

    with open(filepath, 'r') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('%'):
                continue
            tokens = [int(x) for x in stripped.split()]
            if not tokens:
                continue
            # first non-comment line in .mtx is always the metadata header
            if not header_passed and len(tokens) == 3:
                header_passed = True
                continue
            header_passed = True
            for v in tokens:
                mentions.add(v)
            if len(tokens) >= 2:
                edges_raw.append((tokens[0], tokens[1]))

    if not mentions:
        return Graph(0, [])

    min_id = min(mentions)
    max_id = max(mentions)
    shift = min_id
    n_vertices = (max_id - shift) + 1
    edges = [(u - shift, v - shift) for u, v in edges_raw]
    return Graph(n_vertices, edges)

def save_result(filepath: str, burning_number: int, sequence: list[int]):
    """Write burning number and sequence to a text file."""
    with open(filepath, 'w') as f:
        f.write(f"Burning Number: {burning_number}\n")
        f.write(f"Sequence: {' '.join(map(str, sequence))}\n")
