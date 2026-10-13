"""Google OR-Tools CP-SAT baseline solver for N-Queens."""

import time
from typing import Dict, Any, List
from ortools.sat.python import cp_model

from src.nqueens.board import verify


def solve_cpsat_permutation(
    n: int,
    timeout_s: float = 600.0,
    num_workers: int = 1,
    seed: int = 0,
) -> Dict[str, Any]:
    """Solve N-Queens using CP-SAT with a permutation model (AllDifferent constraints).
    
    Variables:
      q[i] in [0, n-1] for each row i.
    Constraints:
      - AllDifferent(q)
      - AllDifferent([q[i] + i])
      - AllDifferent([q[i] - i])
    """
    t_start = time.perf_counter()
    model = cp_model.CpModel()

    q = [model.NewIntVar(0, n - 1, f"q_{i}") for i in range(n)]

    # Row/Column distinctness
    model.AddAllDifferent(q)

    # Minor diagonals: q[i] + i must be distinct
    model.AddAllDifferent([q[i] + i for i in range(n)])

    # Major diagonals: q[i] - i must be distinct
    model.AddAllDifferent([q[i] - i for i in range(n)])

    t_encode = time.perf_counter() - t_start

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(timeout_s)
    solver.parameters.num_search_workers = int(num_workers)
    solver.parameters.random_seed = int(seed)

    t_solve_start = time.perf_counter()
    res = solver.Solve(model)
    t_solve = time.perf_counter() - t_solve_start
    t_total = time.perf_counter() - t_start

    status = "UNKNOWN"
    queens: List[int] = []
    is_verified = False

    if res == cp_model.OPTIMAL or res == cp_model.FEASIBLE:
        status = "SAT"
        queens = [int(solver.Value(q[i])) for i in range(n)]
        is_verified = verify(queens, n)
    elif res == cp_model.INFEASIBLE:
        status = "UNSAT"
    elif res == cp_model.UNKNOWN:
        status = "TIMEOUT"

    return {
        "n": n,
        "method": "cpsat_permutation",
        "status": status,
        "t_encode_s": t_encode,
        "t_solve_s": t_solve,
        "t_total_s": t_total,
        "queens": queens,
        "verified": is_verified,
        "num_vars": n,
        "num_clauses": 3,  # 3 AllDifferent global constraints
    }


def solve_cpsat_binary(
    n: int,
    timeout_s: float = 600.0,
    num_workers: int = 1,
    seed: int = 0,
) -> Dict[str, Any]:
    """Solve N-Queens using CP-SAT with a binary 0-1 matrix model (AddExactlyOne / AddAtMostOne)."""
    t_start = time.perf_counter()
    model = cp_model.CpModel()

    # x[i][j] is True if a queen is at (i, j)
    x = [[model.NewBoolVar(f"x_{i}_{j}") for j in range(n)] for i in range(n)]

    # Row constraints: exactly one queen
    for i in range(n):
        model.AddExactlyOne(x[i])

    # Column constraints: exactly one queen
    for j in range(n):
        model.AddExactlyOne([x[i][j] for i in range(n)])

    # Major diagonals: i - j = const
    for d in range(-(n - 1), n):
        diag = [x[i][i - d] for i in range(n) if 0 <= i - d < n]
        if len(diag) >= 2:
            model.AddAtMostOne(diag)

    # Minor diagonals: i + j = const
    for s in range(2 * n - 1):
        diag = [x[i][s - i] for i in range(n) if 0 <= s - i < n]
        if len(diag) >= 2:
            model.AddAtMostOne(diag)

    t_encode = time.perf_counter() - t_start

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(timeout_s)
    solver.parameters.num_search_workers = int(num_workers)
    solver.parameters.random_seed = int(seed)

    t_solve_start = time.perf_counter()
    res = solver.Solve(model)
    t_solve = time.perf_counter() - t_solve_start
    t_total = time.perf_counter() - t_start

    status = "UNKNOWN"
    queens: List[int] = []
    is_verified = False

    if res == cp_model.OPTIMAL or res == cp_model.FEASIBLE:
        status = "SAT"
        for i in range(n):
            for j in range(n):
                if solver.Value(x[i][j]):
                    queens.append(j)
                    break
        is_verified = verify(queens, n)
    elif res == cp_model.INFEASIBLE:
        status = "UNSAT"
    elif res == cp_model.UNKNOWN:
        status = "TIMEOUT"

    return {
        "n": n,
        "method": "cpsat_binary",
        "status": status,
        "t_encode_s": t_encode,
        "t_solve_s": t_solve,
        "t_total_s": t_total,
        "queens": queens,
        "verified": is_verified,
        "num_vars": n * n,
        "num_clauses": 2 * n + 2 * (2 * n - 3),
    }
