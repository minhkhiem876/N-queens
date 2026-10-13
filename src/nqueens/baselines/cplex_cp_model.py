"""IBM ILOG CPLEX CP Optimizer baseline solver for N-Queens using docplex.cp."""

import time
from typing import Dict, Any, List

try:
    from docplex.cp.model import CpoModel
    from docplex.cp.model import all_diff
    DOCPLEX_CP_AVAILABLE = True
except ImportError:
    DOCPLEX_CP_AVAILABLE = False

from src.nqueens.board import verify


def solve_cplex_cp(
    n: int,
    timeout_s: float = 600.0,
    workers: int = 1,
) -> Dict[str, Any]:
    """Solve N-Queens using CPLEX CP Optimizer via docplex.cp (all_diff constraints).
    
    Variables:
      q[i] in [0, n-1]
    Constraints:
      - all_diff(q)
      - all_diff([q[i] + i])
      - all_diff([q[i] - i])
    """
    if not DOCPLEX_CP_AVAILABLE:
        return {
            "n": n,
            "method": "cplex_cp",
            "status": "UNAVAILABLE",
            "error": "docplex.cp not installed",
            "t_encode_s": 0.0,
            "t_solve_s": 0.0,
            "t_total_s": 0.0,
            "queens": [],
            "verified": False,
        }

    t_start = time.perf_counter()
    try:
        mdl = CpoModel(name=f"nqueens_cp_{n}")
        q = [mdl.integer_var(0, n - 1, name=f"q_{i}") for i in range(n)]

        mdl.add(all_diff(q))
        mdl.add(all_diff([q[i] + i for i in range(n)]))
        mdl.add(all_diff([q[i] - i for i in range(n)]))

        t_encode = time.perf_counter() - t_start

        t_solve_start = time.perf_counter()
        msol = mdl.solve(
            TimeLimit=float(timeout_s),
            Workers=int(workers),
            LogVerbosity="Quiet",
        )
        t_solve = time.perf_counter() - t_solve_start
        t_total = time.perf_counter() - t_start

        status = "UNKNOWN"
        queens: List[int] = []
        is_verified = False

        if msol and msol.is_solution():
            status = "SAT"
            queens = [int(msol.get_value(q[i])) for i in range(n)]
            is_verified = verify(queens, n)
        elif msol and msol.get_solve_status() == "Infeasible":
            status = "UNSAT"
        else:
            status = "TIMEOUT"

        return {
            "n": n,
            "method": "cplex_cp",
            "status": status,
            "t_encode_s": t_encode,
            "t_solve_s": t_solve,
            "t_total_s": t_total,
            "queens": queens,
            "verified": is_verified,
            "num_vars": n,
            "num_clauses": 3,
        }

    except Exception as e:
        t_total = time.perf_counter() - t_start
        err_msg = str(e)
        if "not found" in err_msg.lower() or "cpoptimizer" in err_msg.lower():
            status = "SOLVER_NOT_FOUND"
        elif "license" in err_msg.lower() or "limit" in err_msg.lower():
            status = "LICENSE_LIMIT"
        else:
            status = "ERROR"

        return {
            "n": n,
            "method": "cplex_cp",
            "status": status,
            "error": err_msg,
            "t_encode_s": 0.0,
            "t_solve_s": 0.0,
            "t_total_s": t_total,
            "queens": [],
            "verified": False,
        }
