# Graph Burning Problem: PRYM Implementation Summary

## Current Implementation Architecture

The codebase implements the **PRYM** exact algorithm for the Graph Burning Problem, following the methodology of the ESA 2024 paper (*Pereira et al.*).

### Core Components
- **`gbp/graph.py`**: Optimized for speed using a list-based distance cache. It computes distances on demand and caches them after the first BFS, minimizing redundant graph traversals.
- **`gbp/separation.py`**: Pre-calculates a **Coverage Map** for a given burning length $B$. This allows the solver to identify which variables cover which vertex in $O(1)$ time during the search.
- **`gbp/model.py`**: 
  - **IP Formulation**: Uses binary variables $x_{v,i}$ to represent firing vertex $v$ at time $i$.
  - **Lazy Constraints**: Implements a custom `CoveringConshdlr` that monitors integer solutions. If a solution leaves a vertex uncovered, it injects a "Covering Constraint" on the fly.
  - **Surgical Selection**: Following the paper, it only adds a constraint for the **farthest uncovered vertex**, keeping the LP relaxation small and fast.
- **`gbp/prym.py`**: Handles the binary search over the burning number $B$, using the `BFF-d` heuristic to establish initial lower and upper bounds.

## Performance Analysis & Parity Gap

### The "Python Gap"
The current Python/SCIP implementation solves the 33x33 grid in **71 minutes**, whereas the paper reports **36-95 seconds** for the entire search.
- **Callback Overhead**: In `PySCIPOpt`, integer solution checks context-switch to the Python interpreter. In a search tree of 20,000 nodes, these interruptions accumulate to hours of delay.
- **Node Count**: Our current search explores ~21,000 nodes. Gurobi (used in the paper) likely explores far fewer due to more aggressive internal heuristics and superior feasibility search.

### Search Bottlenecks
- **Dual Bound Strength**: "Surgical Selection" results in a weak Dual Bound (staying at 0 for a long time). This forces the solver to explore nearly the entire feasibility space to prove optimality.
- **Feasibility "Wandering"**: The solver spends significant time searching for a valid sequence of length $B$ even when a heuristic sequence (like BFF-d) already exists.

## Future Recommendations

### 1. C++ Migration (The "Golden" Solution)
To reach sub-60-second parity, the constraint handler and separation logic must be written in **C++** using the SCIP API directly. This removes the Python interpreter bottleneck.

### 2. Algorithmic Optimizations
- **Initial Solution Injection**: Explicitly provide the `BFF-d` sequence as a starting solution (`Primal Solution`) to SCIP.
- **Selective LP Separation**: Enable separation of fractional solutions at the root node to strengthen the initial relaxation.
- **Branching Priorities**: Weight variables from earlier time steps ($i=1, 2...$) more heavily to guide the search towards significant coverage areas earlier.

---

### How to Run
Ensure your virtual environment is active, then run:

```bash
python3 -m gbp.main datasets/grid_033.edges
```
