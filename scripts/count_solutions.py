"""Count all solutions for N-Queens using SAT solver and blocking clauses on primary variables."""

import argparse
import os
import sys
import time
from typing import Dict, List
from pysat.solvers import Solver

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nqueens.board import decode, verify
from src.nqueens.cnf_builder import build_cnf


# OEIS A000170: number of distinct solutions for n = 1, 2, ...
OEIS_A000170: Dict[int, int] = {
    1: 1,
    2: 0,
    3: 0,
    4: 2,
    5: 10,
    6: 4,
    7: 40,
    8: 92,
    9: 352,
    10: 724,
    11: 2680,
    12: 14200,
}


def count_solutions(
    n: int,
    amo_name: str = "seq",
    solver_name: str = "cadical195",
    verbose: bool = False,
) -> int:
    """Enumerate and count all solutions for an n x n board.
    
    Blocking clauses are constructed ONLY over the primary variables x(i, j).
    Symmetry breaking MUST be False to count all distinct solutions.
    """
    cnf, pool, stats = build_cnf(n=n, amo_name=amo_name, symmetry=False, redundant_alo=True)

    count = 0
    with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
        while solver.solve():
            model = solver.get_model()
            queens = decode(model, n)
            assert verify(queens, n), f"Verification failed for solution #{count + 1} at n={n}!"

            count += 1
            if verbose and (count % 100 == 0 or count <= 5):
                print(f"[n={n}] Found solution #{count}: {queens}")

            # Blocking clause on primary variables only: ¬(x_0,c_0 ∧ ... ∧ x_{n-1},c_{n-1})
            # => (¬x_0,c_0 ∨ ... ∨ ¬x_{n-1},c_{n-1})
            from src.nqueens.board import var
            blocking_clause = [-var(r, queens[r], n) for r in range(n)]
            solver.add_clause(blocking_clause)

    return count


def main():
    parser = argparse.ArgumentParser(description="Count all N-Queens solutions with SAT blocking clauses.")
    parser.add_argument("--min-n", type=int, default=2, help="Minimum n (default: 2)")
    parser.add_argument("--max-n", type=int, default=8, help="Maximum n (default: 8)")
    parser.add_argument("--amo", type=str, default="seq", help="AMO encoding name (default: seq)")
    parser.add_argument("--solver", type=str, default="cadical195", help="SAT solver name (default: cadical195)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    print(f"Counting solutions for n={args.min_n}..{args.max_n} using amo='{args.amo}', solver='{args.solver}'")
    all_passed = True
    for n in range(args.min_n, args.max_n + 1):
        t0 = time.perf_counter()
        count = count_solutions(n, amo_name=args.amo, solver_name=args.solver, verbose=args.verbose)
        t_el = time.perf_counter() - t0
        expected = OEIS_A000170.get(n)
        status = "OK" if (expected is None or count == expected) else "MISMATCH"
        print(f"n={n:2d}: found {count:5d} solutions (expected: {expected}) in {t_el:6.3f}s -> {status}")
        if status != "OK":
            all_passed = False

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
