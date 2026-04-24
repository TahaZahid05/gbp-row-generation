# Graph Burning Problem — Row Generation Solver

This project solves the **Graph Burning Problem (GBP)** optimally using Integer Programming with row generation. It supports two backends:

- **Python backend** — uses PySCIPOpt, works out of the box, no compilation needed
- **C++ backend** — uses the native SCIP C API via a compiled DLL, ~10x faster

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Install Python and Dependencies](#install-python-and-dependencies)
3. [Install SCIP](#install-scip)
4. [Generate the Test Graph](#generate-the-test-graph)
5. [Run with Python Backend](#run-with-python-backend)
6. [Install C++ Build Tools](#install-c-build-tools)
7. [Build the C++ DLL](#build-the-c-dll)
8. [Run with C++ Backend](#run-with-c-backend)
9. [Switching Between Backends](#switching-between-backends)
10. [Project Structure](#project-structure)
11. [Troubleshooting](#troubleshooting)

---

## System Requirements

- Windows 10 or 11 (64-bit)
- Python 3.10 or newer
- SCIPOptSuite 10.x
- Visual Studio Build Tools *(C++ backend only)*

---

## Install Python and Dependencies

### 1. Install Python

Download and install Python 3.10+ from https://www.python.org/downloads/

During installation, check **"Add Python to PATH"**.

Verify:
```cmd
python --version
```

### 2. Clone the repository

```cmd
git clone <repo-url>
cd gbp-row-generation
```

### 3. Create a virtual environment (recommended)

```cmd
python -m venv venv
venv\Scripts\activate
```

### 4. Install Python dependencies

```cmd
pip install -r requirements.txt
```

---

## Install SCIP

Download **SCIPOptSuite 10.x** for Windows from:
https://scipopt.org/index.php#download

Run the installer and install to the default path:
```
C:\Program Files\SCIPOptSuite 10.0.2
```

During installation, select the option to **add SCIP to PATH** if offered.

Verify:
```cmd
scip --version
```

---

## Generate the Test Graph

Before running anything, generate the Barabasi-Albert test graph:

```cmd
python generate_ba_graph.py
```

This creates `ba5000.edgelist` — a random BA graph with **5000 vertices** in the project root. You only need to do this once.

---

## Run with Python Backend

No compilation needed. Simply run:

```cmd
python test_ba_graph.py --python
```

**Expected output:**
```
[PRYM] Using Python solver backend
Loading graph from ba5000.edgelist...
Graph loaded: 5000 vertices

Running prym algorithm...
[PRYM] Trying B=4 (L=3, U=6)
[PRYM] B=4 -> infeasible (Initial cuts: 6, Lazy cuts: 4061)
[PRYM] Trying B=5 (L=5, U=6)
[PRYM] B=5 -> infeasible (Initial cuts: 6, Lazy cuts: 33)

Results:
  Burning Number: 6
  Sequence length: 6
  Sequence (first 20): [0, 1448, 2459, 2883, 3070, 3073]
  Time: ~80s
Results saved to ba5000_result.txt
```

---

## Install C++ Build Tools

To use the faster C++ backend, you need the MSVC compiler.

### 1. Download Visual Studio Build Tools

Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/

Click **"Download Build Tools"** and run the installer.

### 2. Select the C++ workload

In the installer, check **"Desktop development with C++"** and click **Install**.

This installs `cl.exe` (the MSVC compiler) and all required libraries. It may take several minutes and requires a few GB of disk space.

### 3. Verify the installation

After installation, open a new Command Prompt and run:

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

You should see output like:
```
**********************************************************************
** Visual Studio 2026 Developer Command Prompt v18.x.x
** Copyright (c) 2026 Microsoft Corporation
**********************************************************************
[vcvarsall.bat] Environment initialized for: 'x64'
```

Then verify cl.exe is available:
```cmd
where cl
```

Expected output:
```
C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\...\cl.exe
```

---

## Build the C++ DLL

### Step 1 — Open a Command Prompt

Open **Command Prompt** (search "cmd" in Start). Do not use PowerShell.

### Step 2 — Initialize the MSVC environment

Run this command exactly:

```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

You should see the environment initialized message as shown above.

> You need to do this once per terminal session before building.
> The build script attempts this automatically, but running it manually
> first ensures it works correctly.

### Step 3 — Navigate to the project root

```cmd
cd D:\path\to\gbp-row-generation
```

### Step 4 — Run the build script

```cmd
gbp\build.bat
```

**Expected output:**
```
==========================================
  Building C++ GBP Solver (MSVC version)
==========================================
SCIP Include : C:\Program Files\SCIPOptSuite 10.0.2\include
SCIP Lib     : C:\Program Files\SCIPOptSuite 10.0.2\lib
Output       : gbp\solver.dll

Step 1: Compiling solver.cpp with MSVC...
Microsoft (R) C/C++ Optimizing Compiler Version 19.x for x64
...
==========================================
SUCCESS: solver.dll built at gbp\solver.dll
==========================================
```

This creates `gbp\solver.dll`. You only need to rebuild if you modify `solver.cpp`.

---

## Run with C++ Backend

After building the DLL, run:

```cmd
python test_ba_graph.py --cpp
```

Or simply (C++ is the default):

```cmd
python test_ba_graph.py
```

**Expected output:**
```
[PRYM] Using C++ solver backend (100x faster)
Loading graph from ba5000.edgelist...
Graph loaded: 5000 vertices

Running prym algorithm...
[PRYM] Trying B=4 (L=3, U=6)
[PRYM] B=4 -> infeasible (Initial cuts: 4, Lazy cuts: 2528)
[PRYM] Trying B=5 (L=5, U=6)
[PRYM] B=5 -> infeasible (Initial cuts: 5, Lazy cuts: 53)

Results:
  Burning Number: 6
  Sequence length: 6
  Sequence (first 20): [0, 1448, 2459, 2883, 3070, 3073]
  Time: ~8s
Results saved to ba5000_result.txt
```

---

## Switching Between Backends

Use the --cpp or --python flag at runtime — no recompilation needed:

| Command | Backend |
|---------|---------|
| `python test_ba_graph.py` | C++ (default) |
| `python test_ba_graph.py --cpp` | C++ explicitly |
| `python test_ba_graph.py --python` | Python |

If the C++ DLL is unavailable, it automatically falls back to Python:
```
[PRYM] C++ backend unavailable (...), falling back to Python
```

---

## Performance Comparison

| Backend | BA-5000 time | Notes |
|---------|:-----------:|-------|
| Python  | ~80s        | No build step needed |
| C++     | ~8s         | Build once, then reuse |

---

## Project Structure

```
gbp-row-generation/
│
├── gbp/
│   ├── __init__.py
│   ├── bff_d.py          # BFF-d heuristic (initial solution)
│   ├── build.bat         # C++ build script (MSVC)
│   ├── graph.py          # Graph data structure
│   ├── model.py          # Python ILP model (PySCIPOpt)
│   ├── model_cpp.py      # ctypes wrapper for C++ backend
│   ├── prym.py           # Main algorithm (binary search + model)
│   ├── separation.py     # Separation routines
│   ├── solver.cpp        # C++ solver implementation
│   ├── solver.dll        # Compiled DLL (generated by build.bat)
│   └── utils.py          # Graph I/O and helpers
│
├── generate_ba_graph.py  # Generates ba5000.edgelist
├── test_ba_graph.py      # Main test runner
├── ba5000.edgelist       # Test graph (generated)
├── ba5000_result.txt     # Output (generated)
├── requirements.txt
└── README.md
```

---

## Troubleshooting

### "cl is not recognized"

MSVC is not initialized. Run vcvars64.bat first:
```cmd
"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
```

If that path does not exist, search for it:
```cmd
dir /s "C:\Program Files (x86)\Microsoft Visual Studio\vcvars64.bat" 2>nul
```

### "SCIP headers/lib not found"

Verify your SCIP installation path. Open `gbp\build.bat` and check:
```bat
set SCIP_DIR=C:\Program Files\SCIPOptSuite 10.0.2
```

Update it to match your actual installation path if different.

### "Could not find module solver.dll"

The DLL's runtime dependencies are not found. Make sure `gbp\model_cpp.py` contains:
```python
os.add_dll_directory(r"C:\Program Files\SCIPOptSuite 10.0.2\bin")
```

This line must appear before the `ctypes.CDLL(...)` call.

### "ba5000.edgelist not found"

Generate the test graph first:
```cmd
python generate_ba_graph.py
```

### Python backend gives import errors

Make sure PySCIPOpt is installed:
```cmd
pip install pyscipopt
```

If it fails, verify your SCIP installation is complete and on PATH.