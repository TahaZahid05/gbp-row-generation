import math
from gbp.graph import Graph

class SeparationProcedure:
    def __init__(self, graph: Graph, B: int):
        self.graph = graph
        self.B = B
        self._coverage_map = self._precalculate_coverage()

    def _precalculate_coverage(self) -> list[list[tuple[int, int]]]:
        """
        Pre-calculate exactly which (u, i) variables cover each vertex w.
        Returns mapping w -> list of (u, i).
        """
        n = self.graph.n_vertices
        B = self.B
        coverage = [[] for _ in range(n)]
        
        for u in range(n):
            dist_from_u = self.graph.get_distances_from(u)
            for w in range(n):
                d_uw = dist_from_u[w]
                if d_uw <= B - 1: # Max possible radius is B-1
                    for i in range(1, B + 1):
                        if d_uw <= B - i:
                            coverage[w].append((u, i))
        return coverage

    def get_covering_variables(self, w: int) -> list[tuple[int, int]]:
        return self._coverage_map[w]

    def check_and_separate(self, sequence: list[int], max_cuts: int | None = 1) -> tuple[bool, list[int], float]:
        """
        Check if sequence is a valid burning sequence.
        Returns (is_valid, list_of_violated_vertices, max_violation).
        If max_cuts is None, all violations are returned.
        """
        B = self.B
        n = self.graph.n_vertices
        
        # min_cov[u] will store min_{idx} { d(u, v_idx) - (B - (idx+1)) }
        min_cov = [math.inf] * n
        
        for idx, v_i in enumerate(sequence):
            radius = B - (idx + 1)
            dist_from_vi = self.graph.get_distances_from(v_i)
            if radius < 0: continue
            for u in range(n):
                c = dist_from_vi[u] - radius
                if c < min_cov[u]:
                    min_cov[u] = c
        
        violations = []
        for u in range(n):
            if min_cov[u] > 0:
                violations.append((min_cov[u], u))
        
        if not violations:
            return True, [], 0.0
            
        violations.sort(key=lambda x: x[0], reverse=True)
        max_v = violations[0][0]
        
        # Return at most max_cuts, or all if None
        if max_cuts is None:
            report = [v[1] for v in violations]
        else:
            report = [v[1] for v in violations[:max_cuts]]
            
        return False, report, max_v
