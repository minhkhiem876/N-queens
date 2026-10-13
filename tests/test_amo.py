"""Exhaustive brute-force correctness test for At-Most-One (AMO) encodings."""

import itertools
import pytest
from pysat.formula import IDPool
from pysat.solvers import Solver

from src.nqueens.encodings import REGISTRY


AMO_ENCODINGS = ["pairwise", "seq", "binary", "commander", "product", "ladder", "totalizer"]


@pytest.mark.parametrize("amo_name", AMO_ENCODINGS)
@pytest.mark.parametrize("k", list(range(1, 11)))
def test_amo_exhaustive(amo_name: str, k: int):
    """Test that the AMO encoding is satisfiable iff at most one variable is True.
    
    Checks all 2^k assignments of input variables x_1 .. x_k.
    """
    amo_func = REGISTRY[amo_name]
    lits = list(range(1, k + 1))
    pool = IDPool(start_from=k + 1)
    clauses = amo_func(lits, pool)

    with Solver(name="glucose42") as solver:
        for cl in clauses:
            solver.add_clause(cl)

        # Check all 2^k truth assignments
        for assignment in itertools.product([False, True], repeat=k):
            true_count = sum(assignment)
            expected_sat = (true_count <= 1)

            # Build unit assumptions for x_1 .. x_k
            assumptions = [lit if assignment[i] else -lit for i, lit in enumerate(lits)]
            actual_sat = solver.solve(assumptions=assumptions)

            assert actual_sat == expected_sat, (
                f"Encoding {amo_name} failed for k={k}, assignment={assignment}: "
                f"expected SAT={expected_sat} (count={true_count}), got {actual_sat}"
            )
