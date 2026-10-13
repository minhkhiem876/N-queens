"""CNF formula builder for the N-Queens problem."""

import math
from typing import Dict, Any, Tuple
from pysat.formula import CNF, IDPool

from .board import var, lines
from .encodings import get_amo


def build_cnf(
    n: int,
    amo_name: str = "seq",
    symmetry: bool = False,
    redundant_alo: bool = True,
) -> Tuple[CNF, IDPool, Dict[str, Any]]:
    """Build a CNF formula for N-Queens using the specified At-Most-One (AMO) encoding.
    
    Args:
        n: Board size (n x n).
        amo_name: Name of the AMO encoding (e.g. 'pairwise', 'seq', 'binary', 'commander', 'product', 'ladder', 'totalizer').
        symmetry: If True, add a horizontal reflection symmetry-breaking clause on the first row.
        redundant_alo: If True, add redundant At-Least-One (ALO) clauses for columns.
        
    Returns:
        A tuple of (cnf, pool, stats) where:
          - cnf: pysat.formula.CNF object containing all generated clauses.
          - pool: pysat.formula.IDPool initialized with start_from=n*n + 1.
          - stats: Dict containing counts of variables, clauses, and line breakdowns.
    """
    amo_func = get_amo(amo_name)
    pool = IDPool(start_from=n * n + 1)
    cnf = CNF()

    board_lines = lines(n)

    # 1. Row constraints: exactly one queen per row (ALO + AMO)
    for row in board_lines["rows"]:
        # At least one
        cnf.append(list(row))
        # At most one
        for cl in amo_func(row, pool):
            cnf.append(cl)

    # 2. Column constraints: AMO, and optional redundant ALO
    for col in board_lines["cols"]:
        if redundant_alo:
            cnf.append(list(col))
        for cl in amo_func(col, pool):
            cnf.append(cl)

    # 3. Major diagonals: AMO for length >= 2
    for diag in board_lines["diag_main"]:
        for cl in amo_func(diag, pool):
            cnf.append(cl)

    # 4. Minor / Anti-diagonals: AMO for length >= 2
    for diag in board_lines["diag_anti"]:
        for cl in amo_func(diag, pool):
            cnf.append(cl)

    # 5. Optional horizontal symmetry breaking
    # Place queen in row 0 in first ceil(n / 2) columns
    if symmetry and n > 1:
        half_cols = math.ceil(n / 2)
        sym_clause = [var(0, j, n) for j in range(half_cols)]
        cnf.append(sym_clause)

    stats = {
        "n": n,
        "amo_name": amo_name,
        "symmetry": symmetry,
        "redundant_alo": redundant_alo,
        "num_primary_vars": n * n,
        "num_aux_vars": max(0, pool.top - n * n),
        "num_vars": max(n * n, pool.top),
        "num_clauses": len(cnf.clauses),
    }

    return cnf, pool, stats
