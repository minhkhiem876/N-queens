"""Pure 2D Product At-Most-One (AMO) encoding (Chen, 2010)."""

import math
from typing import List
from pysat.formula import IDPool


def amo(lits: List[int], pool: IDPool) -> List[List[int]]:
    """Return CNF clauses enforcing at most one literal in `lits` is true using pure 2D Product encoding.
    
    For k literals:
      - k <= 1: 0 clauses, 0 aux vars
      - k <= 3: pairwise AMO
      - k >= 4:
        p = ceil(sqrt(k))
        q = ceil(k / p)
        Introduce p row variables u_0 .. u_{p-1} and q column variables v_0 .. v_{q-1}.
        For x_i at index i (0 <= i < k):
          row a = i // q
          col b = i % q
          (¬x_i ∨ u_a)
          (¬x_i ∨ v_b)
        Recursively enforce AMO on row variables u and column variables v.
    """
    k = len(lits)
    if k <= 1:
        return []
    if k <= 3:
        # Base case: pairwise AMO
        clauses: List[List[int]] = []
        for i in range(k):
            for j in range(i + 1, k):
                clauses.append([-lits[i], -lits[j]])
        return clauses

    p = math.ceil(math.sqrt(k))
    q = math.ceil(k / p)

    u = [pool.id() for _ in range(p)]
    v = [pool.id() for _ in range(q)]

    clauses: List[List[int]] = []
    for i, lit in enumerate(lits):
        row_idx = i // q
        col_idx = i % q
        clauses.append([-lit, u[row_idx]])
        clauses.append([-lit, v[col_idx]])

    # Recursively enforce AMO on row and column auxiliary variables
    clauses.extend(amo(u, pool))
    clauses.extend(amo(v, pool))

    return clauses


def alo(lits: List[int]) -> List[List[int]]:
    """Return CNF clauses enforcing at least one literal in `lits` is true."""
    return [list(lits)] if lits else []
