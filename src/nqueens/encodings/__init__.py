"""Registry of At-Most-One (AMO) encodings."""

from typing import Callable, Dict, List
from pysat.formula import IDPool

from . import pairwise
from . import sequential
from . import binary
from . import commander
from . import product
from . import pysat_wrappers

AMOFunction = Callable[[List[int], IDPool], List[List[int]]]

REGISTRY: Dict[str, AMOFunction] = {
    "pairwise": pairwise.amo,
    "binomial": pairwise.amo,
    "seq": sequential.amo,
    "sequential": sequential.amo,
    "binary": binary.amo,
    "bitwise": binary.amo,
    "commander": commander.amo,
    "product": product.amo,
    "ladder": pysat_wrappers.ladder_amo,
    "totalizer": pysat_wrappers.totalizer_amo,
}


def get_amo(name: str) -> AMOFunction:
    """Retrieve the AMO encoding function by name."""
    normalized = name.lower().strip()
    if normalized not in REGISTRY:
        available = ", ".join(sorted(REGISTRY.keys()))
        raise ValueError(f"Unknown AMO encoding: '{name}'. Available: {available}")
    return REGISTRY[normalized]


__all__ = [
    "REGISTRY",
    "get_amo",
    "pairwise",
    "sequential",
    "binary",
    "commander",
    "product",
    "pysat_wrappers",
]
