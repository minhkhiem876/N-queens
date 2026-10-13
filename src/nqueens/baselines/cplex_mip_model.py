"""IBM ILOG CPLEX MIP baseline solver for N-Queens using docplex.mp."""

import time
from typing import Dict, Any, List

try:
    from docplex.mp.model import Model
    from docplex.mp.utils import DOcplexException
    DOCPLEX_MP_AVAILABLE = True
except ImportError:
    DOCPLEX_MP_AVAILABLE = False

from src.nqueens.board import verify


def solve_cplex_mip(
    n: int,
    timeout_s: float = 600.0,
    threads: int = 1,
) -> Dict[str, Any]:
    """Solve N-Queens using CPLEX MIP model via docplex.mp.
    
    Variables:
      x[i, j] in {0, 1}
    Constraints:
      - row sum == 1
      - col sum == 1
      - diagonal sum <= 1
    """
    if not DOCPLEX_MP_AVAILABLE:
        return {
            "n": n,
            "method": "cplex_mip",
            "status": "UNAVAILABLE",
            "error": "docplex not installed",
            "t_encode_s": 0.0,
            "t_solve_s": 0.0,
            "t_total_s": 0.0,
            "queens": [],
            "verified": False,
        }

    t_start = time.perf_counter()
    try:
        mdl = Model(name=f"nqueens_{n}")
        mdl.parameters.timelimit = float(timeout_s)
        mdl.parameters.threads = int(threads)

        x = {(i, j): mdl.binary_var(name=f"x_{i}_{j}") for i in range(n) for j in range(n)}

        # Row constraints
        for i in range(n):
            mdl.add_constraint(mdl.sum(x[i, j] for j in range(n)) == 1)

        # Col constraints
        for j in range(n):
            mdl.add_constraint(mdl.sum(x[i, j] for i in range(n)) == 1)

        # Major diagonals
        for d in range(-(n - 1), n):
            diag = [x[i, i - d] for i in range(n) if 0 <= i - d < n]
            if len(diag) >= 2:
                mdl.add_constraint(mdl.sum(diag) <= 1)

        # Minor diagonals
        for s in range(2 * n - 1):
            diag = [x[i, s - i] for i in range(n) if 0 <= s - i < n]
            if len(diag) >= 2:
                mdl.add_constraint(mdl.sum(diag) <= 1)

        t_encode = time.perf_counter() - t_start

        t_solve_start = time.perf_counter()
        solution = mdl.solve(log_output=False)
        t_solve = time.perf_counter() - t_solve_start
        t_total = time.perf_counter() - t_start

        status = "UNKNOWN"
        queens: List[int] = []
        is_verified = False

        if solution:
            status = "SAT"
            for i in range(n):
                for j in range(n):
                    if solution.get_value(x[i, j]) > 0.5:
                        queens.append(j)
                        break
            is_verified = verify(queens, n)
        else:
            solve_details = mdl.get_solve_details()
            if "time limit" in str(solve_details.status).lower():
                status = "TIMEOUT"
            else:
                status = "UNSAT"

        return {
            "n": n,
            "method": "cplex_mip",
            "status": status,
            "t_encode_s": t_encode,
            "t_solve_s": t_solve,
            "t_total_s": t_total,
            "queens": queens,
            "verified": is_verified,
            "num_vars": n * n,
            "num_clauses": 2 * n + 2 * (2 * n - 3),
        }

    except Exception as e:
        t_total = time.perf_counter() - t_start
        err_msg = str(e)
        status = "LICENSE_LIMIT" if "license" in err_msg.lower() or "limit" in err_msg.lower() or "cplex" in err_msg.lower() else "ERROR"
        return {
            "n": n,
            "method": "cplex_mip",
            "status": status,
            "error": err_msg,
            "t_encode_s": 0.0,
            "t_solve_s": 0.0,
            "t_total_s": t_total,
            "queens": [],
            "verified": False,
        }
