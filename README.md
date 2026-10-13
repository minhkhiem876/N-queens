# N-Queens SAT Solving & Benchmarking Framework

An exact constraint-satisfaction and Boolean Satisfiability (SAT) framework for solving, verifying, and benchmarking the $N$-Queens problem across scalable instances.

Developed for **Assignment 1 — Modern Topics in Computer Science** (VNU University of Engineering and Technology).

---

## 1. Features & Architecture

- **7 At-Most-One (AMO) Encodings**:
  1. `pairwise`: Quadratic binomial encoding ($O(k^2)$ clauses, 0 auxiliary variables).
  2. `seq`: Sinz sequential counter ($3k - 4$ clauses, $k - 1$ auxiliary variables, arc-consistent).
  3. `binary`: Bitwise logarithmic encoding ($k \lceil \log_2 k \rceil$ clauses, $\lceil \log_2 k \rceil$ variables).
  4. `commander`: Recursive commander encoding (Klieber & Kwon, partition size $g=3$).
  5. `product`: Pure 2D grid product encoding (Chen, $O(k)$ clauses, $2\lceil \sqrt{k} \rceil$ variables).
  6. `ladder`: Gent & Nightingale ladder regular constraint via PySAT `CardEnc`.
  7. `totalizer`: Bailleux & Boufkhad totalizer tree via PySAT `CardEnc`.
- **SAT Solvers Supported (PySAT)**:
  - CaDiCaL (`cadical195`)
  - Glucose (`glucose42`)
  - Kissat (`kissat404`)
  - MapleChrono (`maplechrono`)
- **Exact Baselines**:
  - Google OR-Tools CP-SAT (Permutation model with `AllDifferent` and 0-1 binary matrix model).
  - Gurobi Optimizer (MIP binary formulation).
  - IBM ILOG CPLEX (MIP via `docplex.mp` and CP via `docplex.cp`).
- **Correctness & Verification**:
  - Independent $O(n^2)$ solution verifier (`verify()`).
  - Brute-force validation over all $2^k$ assignments for $k \in [1..10]$.
  - Exact solution counting matching OEIS A000170.
- **Benchmarking Infrastructure**:
  - Subprocess isolation with OS-level hard timeout and memory tracking (`psutil`).
  - Append-only CSV logging with resume capability.
  - Automated LaTeX tables and matplotlib scaling plots (PNG & PDF).
- **Scientific Report**:
  - Elsevier `cas-sc` LaTeX manuscript ready for submission / Overleaf.

---

## 2. Directory Structure

```
.
├── README.md                  # Setup, reproduction instructions, report link
├── requirements.txt           # Python dependencies
├── src/nqueens/
│   ├── __init__.py
│   ├── board.py               # var(i,j), lines(n), decode(), verify(), print_board()
│   ├── cnf_builder.py         # build_cnf(n, amo_name, symmetry, redundant_alo) with IDPool
│   ├── encodings/
│   │   ├── __init__.py        # REGISTRY mapping names to AMO implementations
│   │   ├── pairwise.py        # Binomial pairwise encoding
│   │   ├── sequential.py      # Sinz sequential counter encoding
│   │   ├── binary.py          # Bitwise logarithmic encoding
│   │   ├── commander.py       # Recursive commander variable encoding
│   │   ├── product.py         # Pure recursive 2D grid product encoding
│   │   └── pysat_wrappers.py  # Ladder & totalizer via pysat.card.CardEnc
│   ├── sat_runner.py          # PySAT solvers orchestration (CaDiCaL, Glucose, Kissat)
│   └── baselines/
│       ├── cpsat_model.py     # OR-Tools CP-SAT (permutation & binary models)
│       ├── gurobi_model.py    # Gurobi MIP model
│       ├── cplex_mip_model.py # CPLEX MIP model (docplex.mp)
│       └── cplex_cp_model.py  # CPLEX CP model (docplex.cp)
├── scripts/
│   ├── run_single.py          # Single CLI runner emitting 1 JSON line
│   ├── run_benchmark.py       # Subprocess-isolated grid runner with hard timeout & resume
│   ├── count_solutions.py     # Complete solution counting (blocking clauses on x)
│   ├── compare_complexity.py  # Empirical vs theoretical clause/variable comparison
│   ├── record_environment.py  # Logs machine hardware and solver versions
│   └── make_tables_figs.py    # Generates LaTeX tables, cactus plots, and scaling figures
├── tests/
│   ├── test_amo.py            # Brute-force AMO verification for k in 1..10
│   └── test_solutions.py      # Correctness check against OEIS A000170
├── results/
│   ├── raw/                   # Raw CSV and environment.json
│   ├── tables/                # Generated LaTeX tables
│   └── figures/               # Generated PDF and PNG plots
└── report/
    ├── main.tex               # Elsevier cas-sc single-column template
    ├── refs.bib               # BibTeX references
    └── figures/               # Figures for LaTeX inclusion
```

---

## 3. Installation & Setup

1. **Create and activate a Python 3.12 virtual environment**:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Verify the environment**:
```bash
python scripts/record_environment.py
```
This writes hardware and solver versions to `results/raw/environment.json`.

---

## 4. How to Run & Verify

### 4.1. Run Unit Tests (Correctness)
```bash
# Test all 7 AMO encodings exhaustively for k = 1..10
pytest tests/test_amo.py -v

# Test exact solution counts against OEIS A000170 (n=4..7 and UNSAT n=2,3)
pytest tests/test_solutions.py -v
```

### 4.2. Count All Solutions via Blocking Clauses
```bash
# Count solutions for n=2..10 (matches OEIS A000170: n=8 -> 92, n=10 -> 724)
python scripts/count_solutions.py --min-n 2 --max-n 10 --amo seq
```

### 4.3. Run a Single Configuration
```bash
# Solve N=64 with Sequential Counter on CaDiCaL
python scripts/run_single.py --n 64 --method sat --amo seq --solver cadical

# Solve N=64 with Google OR-Tools CP-SAT (permutation model)
python scripts/run_single.py --n 64 --method cpsat_permutation

# Solve N=16 with Gurobi
python scripts/run_single.py --n 16 --method gurobi
```

### 4.4. Run the Benchmark Suite
```bash
# Run benchmark grid for instances n in [8, 16, 32, 64, 128]
python scripts/run_benchmark.py --instances 8,16,32,64,128 --timeout 600
```
Runs are saved to `results/raw/benchmark_results.csv`. If interrupted, rerun the command; it automatically resumes and skips already-completed runs.

### 4.5. Generate Tables & Figures
```bash
python scripts/make_tables_figs.py
```
- Figures saved to `results/figures/` (PNG and PDF):
  - `fig_amo_runtime.pdf`: Runtime scaling across AMO encodings.
  - `fig_clauses_vars_scaling.pdf`: Scaling of clauses and auxiliary variables.
  - `fig_solvers_comparison.pdf`: Comparison across SAT solvers.
  - `fig_cactus_plot.pdf`: Cactus plot of solved instances.
  - `fig_sat_vs_baselines.pdf`: SAT vs CP-SAT and Gurobi.
- Tables saved to `results/tables/` (LaTeX format).

---

## 5. Compiling the Scientific Report

The report is written in Elsevier CAS Single Column format (`\documentclass[a4paper,fleqn]{cas-sc}`):
- Source file: `report/main.tex`
- Bibliography: `report/refs.bib`
- Figures: `report/figures/`

To compile locally (if TeX Live is installed):
```bash
cd report
pdflatex main
bibtex main
pdflatex main
pdflatex main
```
Alternatively, upload the `report/` folder directly to [Overleaf](https://www.overleaf.com) and select XeLaTeX / pdfLaTeX with the Elsevier template.

---

## 6. References & Acknowledgments

- Sample code reference: [nQueens-SAT](https://github.com/Duongsuny/nQueens-SAT).
- Sinz, C. (2005). *Towards an Optimal CNF Encoding of Boolean Cardinality Constraints*. CP 2005.
- Klieber, W., & Kwon, G. (2007). *Efficient CNF Encoding for Selecting at Most One from N Variables*. SAT 2007.
- Chen, J. (2010). *A New SAT Encoding of the At-Most-One Constraint*. Constraint Programming Letters.
- Ignatiev, A., Morgado, A., & Marques-Silva, J. (2018). *PySAT: A Python Toolkit for Prototyping with SAT Oracles*. SAT 2018.
- OEIS Sequence A000170: Queens on an $n \times n$ chessboard.
