"""Pairwise (binomial) At-Most-One (AMO) encoding."""

from typing import List
from pysat.formula import IDPool


def amo(lits: List[int], pool: IDPool) -> List[List[int]]:
    """Return CNF clauses enforcing at most one literal in `lits` is true.
    
    Generates C(k, 2) clauses: (¬xi ∨ ¬xj) for all i < j.
    No auxiliary variables are introduced.
    """
    clauses: List[List[int]] = []
    k = len(lits)
    if k <= 1:
        return clauses

    for i in range(k):
        for j in range(i + 1, k):
            clauses.append([-lits[i], -lits[j]])
    return clauses


def alo(lits: List[int]) -> List[List[int]]:
    """Return CNF clauses enforcing at least one literal in `lits` is true."""
    return [list(lits)] if lits else []
