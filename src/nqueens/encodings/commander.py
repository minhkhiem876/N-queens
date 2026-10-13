"""Commander At-Most-One (AMO) encoding (Klieber & Kwon)."""

from typing import List
from pysat.formula import IDPool


def amo(lits: List[int], pool: IDPool, group_size: int = 3, bidirectional: bool = False) -> List[List[int]]:
    """Return CNF clauses enforcing at most one literal in `lits` is true using Commander variables.
    
    Partitions `lits` into disjoint groups of size <= `group_size`.
    For each group G:
      - Pairwise AMO within G.
      - A commander variable c_G is allocated.
      - For each x in G: (¬x ∨ c_G), ensuring that if any variable in G is true, c_G is true.
      - (Optional bidirectional: (¬c_G ∨ ∨_{x in G} x)).
    Then, AMO is recursively enforced on the set of commander variables.
    Base cases:
      - len(lits) <= 1: []
      - len(lits) <= group_size: pairwise AMO.
    """
    k = len(lits)
    if k <= 1:
        return []
    if k <= group_size:
        # Base case: pairwise AMO
        clauses: List[List[int]] = []
        for i in range(k):
            for j in range(i + 1, k):
                clauses.append([-lits[i], -lits[j]])
        return clauses

    # Partition into groups of size group_size
    clauses: List[List[int]] = []
    commanders: List[int] = []

    for i in range(0, k, group_size):
        group = lits[i : i + group_size]
        if len(group) == 1:
            # Single-element group: the element itself serves as commander
            commanders.append(group[0])
            continue

        # Pairwise AMO within the group
        for p in range(len(group)):
            for q in range(p + 1, len(group)):
                clauses.append([-group[p], -group[q]])

        # Allocate commander variable
        c_g = pool.id()
        commanders.append(c_g)

        # Implication: x -> c_g (¬x ∨ c_g)
        for x in group:
            clauses.append([-x, c_g])

        # Optional bidirectional extension: c_g -> \/ group
        if bidirectional:
            clauses.append([-c_g] + list(group))

    # Recursively enforce AMO on the commanders
    clauses.extend(amo(commanders, pool, group_size=group_size, bidirectional=bidirectional))
    return clauses


def alo(lits: List[int]) -> List[List[int]]:
    """Return CNF clauses enforcing at least one literal in `lits` is true."""
    return [list(lits)] if lits else []
