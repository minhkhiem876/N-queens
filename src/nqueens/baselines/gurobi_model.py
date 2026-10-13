"""Gurobi MIP baseline solver for N-Queens."""

import time
from typing import Dict, Any, List

try:
    import gurobipy as gp
    from gurobipy import GRB
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False

from src.nqueens.board import verify


def solve_gurobi(
    n: int,
    timeout_s: float = 600.0,
    threads: int = 1,
    seed: int = 0,
) -> Dict[str, Any]:
    """Solve N-Queens using Gurobi MIP model.
    
    Variables:
      x[i, j] in {0, 1}
    Constraints:
      - sum_j x[i, j] == 1 for all rows i
      - sum_i x[i, j] == 1 for all cols j
      - sum diag x[i, j] <= 1 for all diagonals length >= 2
    """
    if not GUROBI_AVAILABLE:
        return {
            "n": n,
            "method": "gurobi",
            "status": "UNAVAILABLE",
            "error": "gurobipy not installed",
            "t_encode_s": 0.0,
            "t_solve_s": 0.0,
            "t_total_s": 0.0,
            "queens": [],
            "verified": False,
        }

    t_start = time.perf_counter()
    try:
        # Create environment and model silently
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        model = gp.Model(f"nqueens_{n}", env=env)

        model.setParam("TimeLimit", float(timeout_s))
        model.setParam("Threads", int(threads))
        model.setParam("Seed", int(seed))

        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

        # Row constraints
        for i in range(n):
            model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"row_{i}")

        # Column constraints
        for j in range(n):
            model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"col_{j}")

        # Major diagonals
        for d in range(-(n - 1), n):
            diag_cells = [(i, i - d) for i in range(n) if 0 <= i - d < n]
            if len(diag_cells) >= 2:
                model.addConstr(gp.quicksum(x[i, j] for i, j in diag_cells) <= 1)

        # Minor diagonals
        for s in range(2 * n - 1):
            diag_cells = [(i, s - i) for i in range(n) if 0 <= s - i < n]
            if len(diag_cells) >= 2:
                model.addConstr(gp.quicksum(x[i, j] for i, j in diag_cells) <= 1)

        t_encode = time.perf_counter() - t_start

        t_solve_start = time.perf_counter()
        model.optimize()
        t_solve = time.perf_counter() - t_solve_start
        t_total = time.perf_counter() - t_start

        status = "UNKNOWN"
        queens: List[int] = []
        is_verified = False

        if model.Status == GRB.OPTIMAL or model.SolCount > 0:
            status = "SAT"
            for i in range(n):
                for j in range(n):
                    if x[i, j].X > 0.5:
                        queens.append(j)
                        break
            is_verified = verify(queens, n)
        elif model.Status == GRB.INFEASIBLE:
            status = "UNSAT"
        elif model.Status == GRB.TIME_LIMIT:
            status = "TIMEOUT"

        return {
            "n": n,
            "method": "gurobi",
            "status": status,
            "t_encode_s": t_encode,
            "t_solve_s": t_solve,
            "t_total_s": t_total,
            "queens": queens,
            "verified": is_verified,
            "num_vars": n * n,
            "num_clauses": 2 * n + 2 * (2 * n - 3),
        }

    except gp.GurobiError as e:
        t_total = time.perf_counter() - t_start
        err_msg = str(e)
        status = "LICENSE_LIMIT" if "license" in err_msg.lower() or "size-limited" in err_msg.lower() else "ERROR"
        return {
            "n": n,
            "method": "gurobi",
            "status": status,
            "error": err_msg,
            "t_encode_s": 0.0,
            "t_solve_s": 0.0,
            "t_total_s": t_total,
            "queens": [],
            "verified": False,
        }
