"""Binary (bitwise) At-Most-One (AMO) encoding."""

from typing import List
from pysat.formula import IDPool


def amo(lits: List[int], pool: IDPool) -> List[List[int]]:
    """Return CNF clauses enforcing at most one literal in `lits` is true using bitwise encoding.
    
    For k literals:
      - k <= 1: 0 clauses, 0 aux vars
      - k == 2: 1 clause [-lits[0], -lits[1]]
      - k > 2: m = ceil(log2(k)) = (k - 1).bit_length() auxiliary bits y_0 .. y_{m-1}.
        Assign each literal x_i a unique binary code i (0 <= i < k).
        For each bit position j (0 <= j < m):
          If j-th bit of i is 1: (¬x_i ∨ y_j)
          If j-th bit of i is 0: (¬x_i ∨ ¬y_j)
        Total clauses: k * m, auxiliary variables: m.
    """
    k = len(lits)
    if k <= 1:
        return []
    if k == 2:
        return [[-lits[0], -lits[1]]]

    m = (k - 1).bit_length()
    y = [pool.id() for _ in range(m)]
    clauses: List[List[int]] = []

    for i, lit in enumerate(lits):
        for j in range(m):
            bit = (i >> j) & 1
            if bit == 1:
                clauses.append([-lit, y[j]])
            else:
                clauses.append([-lit, -y[j]])

    return clauses


def alo(lits: List[int]) -> List[List[int]]:
    """Return CNF clauses enforcing at least one literal in `lits` is true."""
    return [list(lits)] if lits else []
