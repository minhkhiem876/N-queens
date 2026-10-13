"""Single configuration CLI runner for N-Queens. Outputs exactly one JSON line."""

import argparse
import json
import os
import resource
import sys
import time
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nqueens.sat_runner import solve_nqueens_sat
from src.nqueens.baselines.cpsat_model import solve_cpsat_permutation, solve_cpsat_binary
from src.nqueens.baselines.gurobi_model import solve_gurobi
from src.nqueens.baselines.cplex_mip_model import solve_cplex_mip
from src.nqueens.baselines.cplex_cp_model import solve_cplex_cp


def get_peak_memory_mb() -> float:
    """Return peak RSS memory in MB for the current process."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return usage / (1024 * 1024)  # bytes on macOS
        else:
            return usage / 1024  # kilobytes on Linux


def main():
    parser = argparse.ArgumentParser(description="Run a single N-Queens instance.")
    parser.add_argument("--n", type=int, required=True, help="Board size")
    parser.add_argument(
        "--method",
        type=str,
        default="sat",
        choices=["sat", "cpsat", "cpsat_permutation", "cpsat_binary", "gurobi", "cplex_mip", "cplex_cp"],
        help="Method to run",
    )
    parser.add_argument("--amo", type=str, default="seq", help="AMO encoding (for SAT)")
    parser.add_argument("--solver", type=str, default="cadical195", help="Solver name")
    parser.add_argument("--timeout", type=float, default=600.0, help="Timeout in seconds")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument("--symmetry", action="store_true", help="Add symmetry breaking clause")
    parser.add_argument("--no-redundant-alo", action="store_true", help="Disable redundant column ALO")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker threads (default: 1)")

    args = parser.parse_args()
    redundant_alo = not args.no_redundant_alo

    result: Dict[str, Any] = {}

    def _emit_encode_stats(stats: Dict[str, Any]) -> None:
        print("ENCODE_STATS:" + json.dumps(stats), flush=True)

    if args.method == "sat":
        result = solve_nqueens_sat(
            n=args.n,
            amo_name=args.amo,
            solver_name=args.solver,
            symmetry=args.symmetry,
            redundant_alo=redundant_alo,
            seed=args.seed,
            on_encoded=_emit_encode_stats,
        )
    elif args.method in ["cpsat", "cpsat_permutation"]:
        result = solve_cpsat_permutation(
            n=args.n,
            timeout_s=args.timeout,
            num_workers=args.workers,
            seed=args.seed,
        )
        result["amo"] = "alldifferent"
        result["solver"] = "cp-sat"
    elif args.method == "cpsat_binary":
        result = solve_cpsat_binary(
            n=args.n,
            timeout_s=args.timeout,
            num_workers=args.workers,
            seed=args.seed,
        )
        result["amo"] = "binary_matrix"
        result["solver"] = "cp-sat"
    elif args.method == "gurobi":
        result = solve_gurobi(
            n=args.n,
            timeout_s=args.timeout,
            threads=args.workers,
            seed=args.seed,
        )
        result["amo"] = "linear_amo"
        result["solver"] = "gurobi"
    elif args.method == "cplex_mip":
        result = solve_cplex_mip(
            n=args.n,
            timeout_s=args.timeout,
            threads=args.workers,
        )
        result["amo"] = "linear_amo"
        result["solver"] = "cplex_mip"
    elif args.method == "cplex_cp":
        result = solve_cplex_cp(
            n=args.n,
            timeout_s=args.timeout,
            workers=args.workers,
        )
        result["amo"] = "alldifferent"
        result["solver"] = "cplex_cp"

    result["peak_mem_mb"] = round(get_peak_memory_mb(), 2)
    result["timeout_s"] = args.timeout

    # Clean queens list from final output JSON if very large to keep line concise
    if len(result.get("queens", [])) > 100:
        result["queens_len"] = len(result["queens"])
        del result["queens"]

    # Print strictly one line JSON
    print(json.dumps(result))


if __name__ == "__main__":
    main()
