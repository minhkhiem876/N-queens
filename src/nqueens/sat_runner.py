"""SAT runner for N-Queens using PySAT solvers and standalone DIMACS solvers."""

import random
import time
from typing import Dict, Any, List, Optional, Callable
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

# Maximum clauses to hold in Python/C++ RAM before declaring MEMOUT (~4 GB RSS)
MAX_CLAUSES_IN_RAM = 16_000_000


def _exact_pairwise_stats(n: int, symmetry: bool, redundant_alo: bool) -> Dict[str, int]:
    """Compute exact variable and clause counts for pairwise encoding without allocating clauses."""
    amo_clauses = (5 * (n ** 3) - 6 * (n ** 2) + n) // 3
    alo_clauses = n + (n if redundant_alo else 0) + (1 if (symmetry and n > 1) else 0)
    return {
        "num_primary_vars": n * n,
        "num_aux_vars": 0,
        "num_vars": n * n,
        "num_clauses": amo_clauses + alo_clauses,
    }


def solve_nqueens_sat(
    n: int,
    amo_name: str = "seq",
    solver_name: str = "cadical195",
    symmetry: bool = False,
    redundant_alo: bool = True,
    seed: Optional[int] = None,
    on_encoded: Optional[Callable[[Dict[str, Any]], None]] = None,
    max_clauses: int = MAX_CLAUSES_IN_RAM,
) -> Dict[str, Any]:
    """Build CNF and solve N-Queens using a PySAT solver.
    
    Returns a dictionary of execution metrics and solution validation.
    """
    resolved_solver = PYSAT_SOLVERS.get(solver_name.lower(), solver_name)

    t_start = time.perf_counter()

    # Fast-fail MEMOUT guard for pairwise/totalizer when clause count would exceed RAM budget
    if amo_name == "pairwise":
        pw_stats = _exact_pairwise_stats(n, symmetry, redundant_alo)
        if pw_stats["num_clauses"] > max_clauses:
            t_encode = time.perf_counter() - t_start
            if on_encoded is not None:
                on_encoded({
                    "num_vars": pw_stats["num_vars"],
                    "num_clauses": pw_stats["num_clauses"],
                    "t_encode_s": t_encode,
                })
            return {
                "n": n,
                "method": "sat",
                "amo": amo_name,
                "solver": resolved_solver,
                "seed": seed,
                "symmetry": symmetry,
                "redundant_alo": redundant_alo,
                "status": "MEMOUT",
                "num_vars": pw_stats["num_vars"],
                "num_clauses": pw_stats["num_clauses"],
                "t_encode_s": t_encode,
                "t_solve_s": 0.0,
                "t_total_s": t_encode,
                "queens": [],
                "verified": False,
                "error": f"CNF clause count ({pw_stats['num_clauses']:,}) exceeds memory limit ({max_clauses:,} clauses)",
            }

    try:
        cnf, pool, stats = build_cnf(
            n=n,
            amo_name=amo_name,
            symmetry=symmetry,
            redundant_alo=redundant_alo,
            max_clauses=max_clauses,
        )
        t_encode = time.perf_counter() - t_start
    except MemoryError as e:
        t_encode = time.perf_counter() - t_start
        return {
            "n": n,
            "method": "sat",
            "amo": amo_name,
            "solver": resolved_solver,
            "seed": seed,
            "symmetry": symmetry,
            "redundant_alo": redundant_alo,
            "status": "MEMOUT",
            "num_vars": -1,
            "num_clauses": -1,
            "t_encode_s": t_encode,
            "t_solve_s": 0.0,
            "t_total_s": t_encode,
            "queens": [],
            "verified": False,
            "error": str(e),
        }

    if on_encoded is not None:
        on_encoded({
            "num_vars": stats["num_vars"],
            "num_clauses": stats["num_clauses"],
            "t_encode_s": t_encode,
        })

    if stats["num_clauses"] > max_clauses:
        return {
            "n": n,
            "method": "sat",
            "amo": amo_name,
            "solver": resolved_solver,
            "seed": seed,
            "symmetry": symmetry,
            "redundant_alo": redundant_alo,
            "status": "MEMOUT",
            "num_vars": stats["num_vars"],
            "num_clauses": stats["num_clauses"],
            "t_encode_s": t_encode,
            "t_solve_s": 0.0,
            "t_total_s": t_encode,
            "queens": [],
            "verified": False,
            "error": f"CNF clause count ({stats['num_clauses']:,}) exceeds memory limit ({max_clauses:,} clauses)",
        }

    status = "UNKNOWN"
    queens: List[int] = []
    is_verified = False

    t_solve_start = time.perf_counter()
    try:
        clauses_to_load = cnf.clauses
        if seed is not None and int(seed) > 0:
            rng = random.Random(int(seed))
            clauses_to_load = list(cnf.clauses)
            rng.shuffle(clauses_to_load)

        # Initialize solver
        with Solver(name=resolved_solver, bootstrap_with=clauses_to_load) as solver:
            # Set random decision phases for seed > 0 if supported by solver
            if seed is not None and int(seed) > 0:
                try:
                    rng_phase = random.Random(int(seed) + 1000)
                    phases = [v if rng_phase.random() < 0.5 else -v for v in range(1, n * n + 1)]
                    solver.set_phases(phases)
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

    except MemoryError as e:
        t_solve = time.perf_counter() - t_solve_start
        t_total = time.perf_counter() - t_start
        status = "MEMOUT"
    except Exception as e:
        t_solve = time.perf_counter() - t_solve_start
        t_total = time.perf_counter() - t_start
        err_msg = str(e)
        if "out of memory" in err_msg.lower() or "bad_alloc" in err_msg.lower() or "memory" in err_msg.lower():
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
