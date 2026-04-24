"""
C++ GBP Solver wrapper using ctypes.
Provides the same interface as model.py but uses the native C++ backend.
"""

import ctypes
import os
from typing import Tuple, List, Optional

# Add required DLL directories before loading solver.dll
os.add_dll_directory(r"C:\Program Files\SCIPOptSuite 10.0.2\bin")
os.add_dll_directory(r"C:\msys64\mingw64\bin")

_lib_path = os.path.join(os.path.dirname(__file__), "solver.dll")

if not os.path.exists(_lib_path):
    raise FileNotFoundError(f"solver.dll not found at {_lib_path}. Run gbp\\build.bat first.")

_lib = ctypes.CDLL(_lib_path)

_lib.solve_gbp.restype = ctypes.c_int
_lib.solve_gbp.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
]


class GBPModel:
    def __init__(self, graph, B: int, S_init: List[int]):
        self.graph = graph
        self.B = B
        self.S_init = S_init

    def solve(self) -> Tuple[str, Optional[List[int]], int, int]:
        n = self.graph.n_vertices
        B = self.B

        adj_offsets = [0] * (n + 1)
        for v in range(n):
            adj_offsets[v + 1] = adj_offsets[v] + len(self.graph.adj[v])

        adj_data = []
        for v in range(n):
            adj_data.extend(self.graph.adj[v])

        if not adj_data:
            adj_data.append(0)

        c_adj_data = (ctypes.c_int * len(adj_data))(*adj_data)
        c_adj_offsets = (ctypes.c_int * (n + 1))(*adj_offsets)

        s_init_capped = self.S_init[:B] or [-1]
        c_s_init = (ctypes.c_int * len(s_init_capped))(*s_init_capped)

        c_result = (ctypes.c_int * B)()
        c_n_init = ctypes.c_int(0)
        c_n_lazy = ctypes.c_int(0)

        ret = _lib.solve_gbp(
            n, B,
            c_adj_data, c_adj_offsets,
            c_s_init, len(s_init_capped),
            c_result,
            ctypes.byref(c_n_init),
            ctypes.byref(c_n_lazy),
        )

        if ret == 1:
            return "feasible", list(c_result), c_n_init.value, c_n_lazy.value
        elif ret == 0:
            return "infeasible", None, c_n_init.value, c_n_lazy.value
        else:
            return "unknown", None, c_n_init.value, c_n_lazy.value