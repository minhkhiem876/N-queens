"""SAT runner for N-Queens using PySAT solvers and standalone DIMACS solvers."""

import time
from typing import Dict, Any, List, Optional
from pysat.solvers import Solver
from pysat.formula import CNF

from src.nqueens.board import decode, verify
from src.nqueens.cnf_builder import build_cnf


# Common PySAT solvers supported across platforms
PYSAT_SOLVERS = {
    "cadical": "cadical195",
    "cadical195": "cadical195",
    "glucose": "glucose42",
    "glucose42": "glucose42",
    "kissat": "kissat404",
    "kissat404": "kissat404",
    "maplechrono": "maplechrono",
    "minisat": "minisat22",
}


def solve_nqueens_sat(
    n: int,
    amo_name: str = "seq",
    solver_name: str = "cadical195",
    symmetry: bool = False,
    redundant_alo: bool = True,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Build CNF and solve N-Queens using a PySAT solver.
    
    Returns a dictionary of execution metrics and solution validation.
    """
    resolved_solver = PYSAT_SOLVERS.get(solver_name.lower(), solver_name)

    t_start = time.perf_counter()
    cnf, pool, stats = build_cnf(
        n=n,
        amo_name=amo_name,
        symmetry=symmetry,
        redundant_alo=redundant_alo,
    )
    t_encode = time.perf_counter() - t_start

    status = "UNKNOWN"
    queens: List[int] = []
    is_verified = False

    t_solve_start = time.perf_counter()
    try:
        # Initialize solver
        with Solver(name=resolved_solver, bootstrap_with=cnf.clauses) as solver:
            # Set random seed if supported
            if seed is not None and hasattr(solver, "set_rnd_seed"):
                try:
                    solver.set_rnd_seed(int(seed))
                except Exception:
                    pass

            is_sat = solver.solve()
            t_solve = time.perf_counter() - t_solve_start
            t_total = time.perf_counter() - t_start

            if is_sat:
                status = "SAT"
                model = solver.get_model()
                queens = decode(model, n)
                is_verified = verify(queens, n)
            else:
                status = "UNSAT"

    except Exception as e:
        t_solve = time.perf_counter() - t_solve_start
        t_total = time.perf_counter() - t_start
        err_msg = str(e)
        if "out of memory" in err_msg.lower() or "bad_alloc" in err_msg.lower():
            status = "MEMOUT"
        else:
            status = "ERROR"

    return {
        "n": n,
        "method": "sat",
        "amo": amo_name,
        "solver": resolved_solver,
        "seed": seed,
        "symmetry": symmetry,
        "redundant_alo": redundant_alo,
        "status": status,
        "num_vars": stats["num_vars"],
        "num_clauses": stats["num_clauses"],
        "t_encode_s": t_encode,
        "t_solve_s": t_solve,
        "t_total_s": t_total,
        "queens": queens,
        "verified": is_verified,
    }
