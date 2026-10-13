"""Compare theoretical vs empirical CNF clause and variable counts across AMO encodings."""

import argparse
import pandas as pd
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

    # Pivot tables for LaTeX inclusion
    p_clauses = df.pivot(index="n", columns="encoding", values="clauses")
    p_vars = df.pivot(index="n", columns="encoding", values="total_vars")

    import os
    os.makedirs("results/tables", exist_ok=True)
    with open("results/tables/empirical_clauses.tex", "w") as f:
        f.write(p_clauses.to_latex(caption="Empirical CNF clause count by board size $n$ and AMO encoding."))
    with open("results/tables/empirical_vars.tex", "w") as f:
        f.write(p_vars.to_latex(caption="Empirical CNF variable count by board size $n$ and AMO encoding."))

    print("\nSaved empirical_clauses.tex and empirical_vars.tex to results/tables/")
    return df


if __name__ == "__main__":
    analyze_complexity()
