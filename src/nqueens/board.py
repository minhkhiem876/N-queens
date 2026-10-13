"""Board representation, variable indexing, diagonal generation, and solution verification for N-Queens."""

from typing import List, Tuple, Dict, Union


def var(i: int, j: int, n: int) -> int:
    """Return 1-based propositional variable index for cell (i, j) on an n x n board.
    
    Variables are indexed 1 .. n*n in row-major order:
    x(i, j) = i * n + j + 1 for 0 <= i, j < n.
    """
    assert 0 <= i < n and 0 <= j < n, f"Coordinates ({i}, {j}) out of bounds for n={n}"
    return i * n + j + 1


def inv_var(v: int, n: int) -> Tuple[int, int]:
    """Inverse mapping: convert variable index v in [1, n*n] back to (row, col) (0-indexed)."""
    assert 1 <= v <= n * n, f"Variable {v} out of bounds for n={n}"
    idx = v - 1
    return idx // n, idx % n


def lines(n: int) -> Dict[str, List[List[int]]]:
    """Enumerate all rows, columns, and diagonal lines of length >= 2 on an n x n board.
    
    Returns a dictionary with keys:
      - 'rows': n rows, each of length n
      - 'cols': n columns, each of length n
      - 'diag_main': major diagonals (i - j = const) with length >= 2
      - 'diag_anti': minor diagonals (i + j = const) with length >= 2
    """
    rows: List[List[int]] = []
    for i in range(n):
        rows.append([var(i, j, n) for j in range(n)])

    cols: List[List[int]] = []
    for j in range(n):
        cols.append([var(i, j, n) for i in range(n)])

    # Major diagonals: i - j = d, where -(n-1) <= d <= n-1
    diag_main: List[List[int]] = []
    for d in range(-(n - 1), n):
        diag: List[int] = []
        for i in range(n):
            j = i - d
            if 0 <= j < n:
                diag.append(var(i, j, n))
        if len(diag) >= 2:
            diag_main.append(diag)

    # Minor / anti-diagonals: i + j = s, where 0 <= s <= 2*n - 2
    diag_anti: List[List[int]] = []
    for s in range(2 * n - 1):
        diag = []
        for i in range(n):
            j = s - i
            if 0 <= j < n:
                diag.append(var(i, j, n))
        if len(diag) >= 2:
            diag_anti.append(diag)

    return {
        "rows": rows,
        "cols": cols,
        "diag_main": diag_main,
        "diag_anti": diag_anti,
    }


def decode(model: List[int], n: int) -> List[int]:
    """Decode a satisfying SAT model into queen positions.
    
    Returns a list `queens` of length n, where `queens[i]` is the column index (0-indexed)
    of the queen in row i.
    """
    true_lits = set(lit for lit in model if lit > 0 and lit <= n * n)
    queens: List[int] = [-1] * n
    for lit in true_lits:
        r, c = inv_var(lit, n)
        if queens[r] != -1:
            raise ValueError(f"Multiple queens assigned to row {r}: columns {queens[r]} and {c}")
        queens[r] = c

    for r, c in enumerate(queens):
        if c == -1:
            raise ValueError(f"No queen assigned to row {r}")

    return queens


def verify(queens_or_board: Union[List[int], List[List[int]]], n: int) -> bool:
    """Independent verifier for N-Queens.
    
    Accepts either:
      - a list of column positions `queens` of length n (where queens[i] is col of queen at row i)
      - a 2D matrix of shape n x n containing 1s for queens and 0s elsewhere.
      
    Checks:
      1. Exactly n queens are placed.
      2. Exactly one queen per row.
      3. Exactly one queen per column (all column indices unique).
      4. No two queens share a major diagonal (row - col are all distinct).
      5. No two queens share a minor diagonal (row + col are all distinct).
      
    Returns True if valid, False otherwise.
    """
    if not queens_or_board:
        return False

    if isinstance(queens_or_board[0], list):
        # 2D grid
        grid = queens_or_board
        if len(grid) != n:
            return False
        queens = []
        for r in range(n):
            if len(grid[r]) != n:
                return False
            row_queens = [c for c in range(n) if grid[r][c] == 1]
            if len(row_queens) != 1:
                return False
            queens.append(row_queens[0])
    else:
        queens = queens_or_board

    if len(queens) != n:
        return False

    for c in queens:
        if not (0 <= c < n):
            return False

    # Check distinct columns
    if len(set(queens)) != n:
        return False

    # Check distinct major diagonals (r - c)
    main_diags = set(r - queens[r] for r in range(n))
    if len(main_diags) != n:
        return False

    # Check distinct minor diagonals (r + c)
    anti_diags = set(r + queens[r] for r in range(n))
    if len(anti_diags) != n:
        return False

    return True


def print_board(queens: List[int], n: int) -> str:
    """Return an ASCII representation of the chessboard."""
    lines_out = []
    for r in range(n):
        col = queens[r]
        row_str = " ".join("Q" if c == col else "." for c in range(n))
        lines_out.append(row_str)
    return "\n".join(lines_out)
