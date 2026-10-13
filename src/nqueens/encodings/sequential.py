"""Sequential counter (Sinz, 2005) At-Most-One (AMO) encoding."""

from typing import List
from pysat.formula import IDPool


def amo(lits: List[int], pool: IDPool) -> List[List[int]]:
    """Return CNF clauses enforcing at most one literal in `lits` is true using Sinz's sequential counter.
    
    For k literals:
      - k <= 1: 0 clauses, 0 aux vars
      - k == 2: 1 clause (¬x1 ∨ ¬x2), 0 aux vars
      - k > 2: k - 1 auxiliary variables s_1 .. s_{k-1}
        Clauses (3k - 4 total):
          (¬x_1 ∨ s_1)
          For 2 <= i <= k - 1:
            (¬x_i ∨ s_i)
            (¬s_{i-1} ∨ s_i)
            (¬x_i ∨ ¬s_{i-1})
          (¬x_k ∨ ¬s_{k-1})
    """
    k = len(lits)
    if k <= 1:
        return []
    if k == 2:
        return [[-lits[0], -lits[1]]]

    # Allocate k - 1 auxiliary variables s_0 .. s_{k-2}
    s = [pool.id() for _ in range(k - 1)]
    clauses: List[List[int]] = []

    # First variable: (¬x_1 ∨ s_1) -> [-lits[0], s[0]]
    clauses.append([-lits[0], s[0]])

    # Middle variables: i from 1 to k - 2 (0-based) corresponding to x_2 .. x_{k-1}
    for i in range(1, k - 1):
        clauses.append([-lits[i], s[i]])
        clauses.append([-s[i - 1], s[i]])
        clauses.append([-lits[i], -s[i - 1]])

    # Last variable: (¬x_k ∨ ¬s_{k-1}) -> [-lits[k-1], -s[k-2]]
    clauses.append([-lits[k - 1], -s[k - 2]])

    return clauses


def alo(lits: List[int]) -> List[List[int]]:
    """Return CNF clauses enforcing at least one literal in `lits` is true."""
    return [list(lits)] if lits else []
