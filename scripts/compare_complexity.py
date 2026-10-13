"""Compare theoretical vs empirical CNF clause and variable counts across AMO encodings."""

import argparse
import os
import sys
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nqueens.cnf_builder import build_cnf
from src.nqueens.encodings import REGISTRY

ENCODINGS = ["pairwise", "seq", "binary", "commander", "product", "ladder", "totalizer"]


def analyze_complexity(instances: list[int] = [8, 16, 32, 64, 128]):
    rows = []
    for n in instances:
        for amo in ENCODINGS:
            cnf, pool, stats = build_cnf(n=n, amo_name=amo, symmetry=False, redundant_alo=True)
            rows.append({
                "n": n,
                "encoding": amo,
                "primary_vars": stats["num_primary_vars"],
                "aux_vars": stats["num_aux_vars"],
                "total_vars": stats["num_vars"],
                "clauses": stats["num_clauses"],
            })

    df = pd.DataFrame(rows)
    print("\n=== Empirical CNF Complexity Summary ===")
    print(df.to_string(index=False))


    return df


if __name__ == "__main__":
    analyze_complexity()
