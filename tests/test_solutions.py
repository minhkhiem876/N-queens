"""Pytest suite for N-Queens solution counts matching OEIS A000170."""

import pytest
from scripts.count_solutions import count_solutions, OEIS_A000170

ENCODINGS = ["pairwise", "seq", "binary", "commander", "product", "ladder", "totalizer"]


@pytest.mark.parametrize("amo_name", ENCODINGS)
@pytest.mark.parametrize("n", [4, 5, 6, 7])
def test_solution_count_oeis(amo_name: str, n: int):
    """Verify that every AMO encoding produces the exact OEIS A000170 solution count."""
    count = count_solutions(n, amo_name=amo_name, solver_name="cadical195")
    assert count == OEIS_A000170[n], f"{amo_name} at n={n}: expected {OEIS_A000170[n]}, got {count}"


@pytest.mark.parametrize("n", [2, 3])
def test_unsat_instances(n: int):
    """Verify that n=2 and n=3 are strictly unsatisfiable (0 solutions)."""
    count = count_solutions(n, amo_name="seq", solver_name="cadical195")
    assert count == 0, f"Expected 0 solutions for n={n}, got {count}"
