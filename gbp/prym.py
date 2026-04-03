from gbp.graph import Graph
from gbp.utils import compute_bounds, is_valid_burning_sequence
from gbp.bff_d import bff_d
from gbp.model import GBPModel

def prym(graph: Graph) -> tuple[int, list[int]]:
    """
    Returns (burning_number, optimal_burning_sequence).
    """
    if graph.n_vertices == 0:
        return 0, []
        
    S = bff_d(graph)
    L, U = compute_bounds(S)
    best_S = S

    # Note: paper uses while L < U
    while L < U:
        B = (L + U) // 2
        print(f"[PRYM] Trying B={B} (L={L}, U={U})", flush=True)
        model = GBPModel(graph, B, S_init=S)
        status, S_prime, n_init, n_lazy = model.solve()
        print(f"[PRYM] B={B} -> {status} (Initial cuts: {n_init}, Lazy cuts: {n_lazy})", flush=True)
        if status == "feasible":
            best_S = S_prime
            U = B
        else:
            L = B + 1

    # Before return, ensure validity
    if not is_valid_burning_sequence(graph, best_S):
        raise AssertionError("The sequence found is not valid.")
        
    return U, best_S
