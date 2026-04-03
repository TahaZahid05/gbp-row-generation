import math
from collections import deque

class Graph:
    def __init__(self, n_vertices: int, edges: list[tuple[int, int]]):
        self.n_vertices = n_vertices
        self.adj: dict[int, list[int]] = {i: [] for i in range(n_vertices)}
        
        for u, v in edges:
            self.adj[u].append(v)
            self.adj[v].append(u)
            
        self.dist_cache: dict[int, dict[int, float]] = {}

    def bfs(self, source: int) -> list[float]:
        """Run BFS from source. Returns [distance]. Caches the result."""
        dist = [math.inf] * self.n_vertices
        dist[source] = 0.0
        
        queue = deque([source])
        while queue:
            u = queue.popleft()
            d = dist[u]
            for v in self.adj[u]:
                if dist[v] == math.inf:
                    dist[v] = d + 1.0
                    queue.append(v)
                    
        self.dist_cache[source] = dist
        return dist

    def get_distances_from(self, source: int) -> list[float]:
        """Return cached BFS result for source, running BFS if not yet cached."""
        if source not in self.dist_cache:
            self.bfs(source)
        return self.dist_cache[source]

    def get_distance(self, u: int, v: int) -> float:
        """Return d(u, v). Runs BFS from u if not cached."""
        return self.get_distances_from(u)[v]
