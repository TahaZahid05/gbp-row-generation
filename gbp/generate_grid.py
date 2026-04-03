# generate_grid.py
import sys
n = int(sys.argv[1])
with open(f"grid_{n:03d}.edges", "w") as f:
    for r in range(n):
        for c in range(n):
            v = r * n + c
            if c + 1 < n:
                f.write(f"{v} {v + 1}\n")
            if r + 1 < n:
                f.write(f"{v} {v + n}\n")