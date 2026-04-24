from gbp.graph import Graph
from gbp.utils import compute_bounds, is_valid_burning_sequence
from gbp.bff_d import bff_d

def prym(graph: Graph, backend: str = "cpp") -> tuple[int, list[int]]:
    """
    Returns (burning_number, optimal_burning_sequence).

    Args:
        graph: the input graph
        backend: "cpp" to use C++ solver (default), "python" to use pure Python solver
    """
    if graph.n_vertices == 0:
        return 0, []

    # Select backend
    if backend == "cpp":
        try:
            from gbp.model_cpp import GBPModel
            print("[PRYM] Using C++ solver backend (100x faster)", flush=True)
        except Exception as e:
            print(f"[PRYM] C++ backend unavailable ({e}), falling back to Python", flush=True)
            from gbp.model import GBPModel
    else:
        print("[PRYM] Using Python solver backend", flush=True)
        from gbp.model import GBPModel

    S = bff_d(graph)
    L, U = compute_bounds(S)
    best_S = S

    while L < U:
        B = (L + U) // 2
        print(f"[PRYM] Trying B={B} (L={L}, U={U})", flush=True)
        model = GBPModel(graph, B, S_init=S)
        status, S_prime, n_init, n_lazy = model.solve()
        print(f"[PRYM] B={B} -> {status} (Initial cuts: {n_init}, Lazy cuts: {n_lazy})", flush=True)
        if status == "feasible":
            best_S = S_prime
            U = B
        elif status == "infeasible":
            L = B + 1
        else:
            print(f"[PRYM] B={B} timed out or reached limit, stopping search.", flush=True)
            break

    if not is_valid_burning_sequence(graph, best_S):
        raise AssertionError("The sequence found is not valid.")

    return U, best_S