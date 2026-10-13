"""Wrappers for PySAT CardEnc at-most-one (ladder, totalizer)."""

from typing import List
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool


def ladder_amo(lits: List[int], pool: IDPool) -> List[List[int]]:
    """Enforce At-Most-One using PySAT's ladder encoding (Gent and Nightingale)."""
    if len(lits) <= 1:
        return []
    cnf = CardEnc.atmost(lits, bound=1, top_id=pool.top, encoding=EncType.ladder)
    if cnf.nv > pool.top:
        pool.top = cnf.nv
    return [list(c) for c in cnf.clauses]


def totalizer_amo(lits: List[int], pool: IDPool) -> List[List[int]]:
    """Enforce At-Most-One using PySAT's totalizer encoding (Bailleux and Boufkhad)."""
    if len(lits) <= 1:
        return []
    cnf = CardEnc.atmost(lits, bound=1, top_id=pool.top, encoding=EncType.totalizer)
    if cnf.nv > pool.top:
        pool.top = cnf.nv
    return [list(c) for c in cnf.clauses]
