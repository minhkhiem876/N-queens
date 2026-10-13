"""Generate publication-ready figures (PNG & PDF) and LaTeX tables from benchmark CSV."""

import argparse
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def set_plot_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "lines.linewidth": 1.8,
        "lines.markersize": 6,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def generate_figures(df: pd.DataFrame, out_dir: str = "results/figures"):
    os.makedirs(out_dir, exist_ok=True)
    set_plot_style()

    # Filter successful SAT runs
    sat_df = df[df["method"] == "sat"].copy()

    # 1. Figure: Runtime by N for different AMO encodings (CaDiCaL solver)
    e1 = sat_df[(sat_df["solver"] == "cadical195") & (~sat_df["symmetry"]) & (sat_df["redundant_alo"])].copy()
    if not e1.empty:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        amos = sorted(e1["amo"].unique())
        markers = ["o", "s", "^", "v", "D", "P", "X"]
        for idx, amo in enumerate(amos):
            sub = e1[e1["amo"] == amo].sort_values("n")
            # Only plot instances where solve time is available and positive
            sub_valid = sub[sub["status"] == "SAT"]
            if not sub_valid.empty:
                ax.plot(
                    sub_valid["n"],
                    sub_valid["t_solve_s"],
                    label=amo,
                    marker=markers[idx % len(markers)],
                )
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xlabel("Board Size $n$ (log scale)")
        ax.set_ylabel("Solve Time [s] (log scale)")
        ax.set_title("Runtime Scaling Across AMO Encodings (CaDiCaL 1.9.5)")
        ax.grid(True)
        ax.legend(frameon=True)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "fig_amo_runtime.pdf"))
        fig.savefig(os.path.join(out_dir, "fig_amo_runtime.png"), dpi=300)
        plt.close(fig)

    # 2. Figure: Clause and Variable Counts by N across AMO Encodings
    if not e1.empty:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
        amos = sorted(e1["amo"].unique())
        markers = ["o", "s", "^", "v", "D", "P", "X"]
        for idx, amo in enumerate(amos):
            sub = e1[e1["amo"] == amo].sort_values("n")
            sub_valid = sub[sub["num_clauses"] > 0]
            if not sub_valid.empty:
                m = markers[idx % len(markers)]
                ax1.plot(sub_valid["n"], sub_valid["num_clauses"], label=amo, marker=m)
                ax2.plot(sub_valid["n"], sub_valid["num_vars"], label=amo, marker=m)

        ax1.set_xscale("log", base=2)
        ax1.set_yscale("log")
        ax1.set_xlabel("Board Size $n$")
        ax1.set_ylabel("Number of Clauses")
        ax1.set_title("CNF Clause Count Scaling")
        ax1.grid(True)
        ax1.legend()

        ax2.set_xscale("log", base=2)
        ax2.set_yscale("log")
        ax2.set_xlabel("Board Size $n$")
        ax2.set_ylabel("Total Variables ($n^2 +$ aux)")
        ax2.set_title("CNF Variable Count Scaling")
        ax2.grid(True)
        ax2.legend()

        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "fig_clauses_vars_scaling.pdf"))
        fig.savefig(os.path.join(out_dir, "fig_clauses_vars_scaling.png"), dpi=300)
        plt.close(fig)

    # 3. Figure: SAT Solvers Comparison (E2)
    e2 = sat_df[(sat_df["amo"] == "seq") & (~sat_df["symmetry"]) & (sat_df["redundant_alo"])].copy()
    if not e2.empty and len(e2["solver"].unique()) > 1:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        solvers = sorted(e2["solver"].unique())
        markers = ["o", "s", "^", "D"]
        for idx, s in enumerate(solvers):
            sub = e2[e2["solver"] == s].sort_values("n")
            sub_valid = sub[sub["status"] == "SAT"]
            if not sub_valid.empty:
                ax.plot(
                    sub_valid["n"],
                    sub_valid["t_solve_s"],
                    label=s,
                    marker=markers[idx % len(markers)],
                )
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xlabel("Board Size $n$")
        ax.set_ylabel("Solve Time [s] (log scale)")
        ax.set_title("SAT Solvers Comparison (Sequential Counter AMO)")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, "fig_solvers_comparison.pdf"))
        fig.savefig(os.path.join(out_dir, "fig_solvers_comparison.png"), dpi=300)
        plt.close(fig)

    # 4. Figure: Cactus Plot
    fig, ax = plt.subplots(figsize=(7, 4.5))
    solvers_to_plot = ["cadical195", "glucose42", "kissat404", "cpsat_permutation", "gurobi"]
    markers = ["o", "s", "^", "v", "D"]
    for idx, name in enumerate(solvers_to_plot):
        sub = df[(df["solver"] == name) | (df["method"] == name)]
        if not sub.empty:
            solved = sub[sub["status"] == "SAT"]["t_total_s"].sort_values().values
            if len(solved) > 0:
                ax.plot(
                    np.arange(1, len(solved) + 1),
                    solved,
                    label=name,
                    marker=markers[idx % len(markers)],
                    markevery=max(1, len(solved) // 5),
                )
    ax.set_yscale("log")
    ax.set_xlabel("Number of Solved Instances")
    ax.set_ylabel("Time [s] (log scale)")
    ax.set_title("Cactus Plot: Cumulative Solved Instances")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_cactus_plot.pdf"))
    fig.savefig(os.path.join(out_dir, "fig_cactus_plot.png"), dpi=300)
    plt.close(fig)

    # 5. Figure: SAT vs Baselines
    fig, ax = plt.subplots(figsize=(7, 4.5))
    methods = [
        ("SAT (Seq + CaDiCaL)", df[(df["method"] == "sat") & (df["amo"] == "seq") & (df["solver"] == "cadical195")]),
        ("CP-SAT (Permutation)", df[df["method"] == "cpsat_permutation"]),
        ("CP-SAT (Binary)", df[df["method"] == "cpsat_binary"]),
        ("Gurobi (MIP)", df[df["method"] == "gurobi"]),
    ]
    markers = ["o", "s", "^", "D"]
    for idx, (label, sub) in enumerate(methods):
        sub_valid = sub[sub["status"] == "SAT"].sort_values("n")
        if not sub_valid.empty:
            ax.plot(
                sub_valid["n"],
                sub_valid["t_solve_s"],
                label=label,
                marker=markers[idx % len(markers)],
            )
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("Board Size $n$")
    ax.set_ylabel("Solve Time [s]")
    ax.set_title("SAT vs Exact Constraint Baselines")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_sat_vs_baselines.pdf"))
    fig.savefig(os.path.join(out_dir, "fig_sat_vs_baselines.png"), dpi=300)
    plt.close(fig)


def generate_tables(df: pd.DataFrame, out_dir: str = "results/tables"):
    os.makedirs(out_dir, exist_ok=True)

    # Table 1: AMO Encoding Complexity & Runtime
    e1 = df[(df["method"] == "sat") & (df["solver"] == "cadical195") & (~df["symmetry"]) & (df["redundant_alo"])].copy()
    if not e1.empty:
        pivot_t = e1.pivot_table(index="n", columns="amo", values="t_solve_s", aggfunc="median")
        pivot_c = e1.pivot_table(index="n", columns="amo", values="num_clauses", aggfunc="first")
        pivot_v = e1.pivot_table(index="n", columns="amo", values="num_vars", aggfunc="first")

        latex_t = pivot_t.to_latex(float_format="%.4f", caption="Solve time (s) across AMO encodings using CaDiCaL 1.9.5")
        latex_c = pivot_c.to_latex(caption="Clause counts across AMO encodings")
        latex_v = pivot_v.to_latex(caption="Variable counts across AMO encodings")

        with open(os.path.join(out_dir, "table_amo_runtime.tex"), "w") as f:
            f.write(latex_t)
        with open(os.path.join(out_dir, "table_amo_clauses.tex"), "w") as f:
            f.write(latex_c)
        with open(os.path.join(out_dir, "table_amo_vars.tex"), "w") as f:
            f.write(latex_v)

    # Table 2: Solver Comparison
    e2 = df[(df["method"] == "sat") & (df["amo"] == "seq") & (~df["symmetry"]) & (df["redundant_alo"])].copy()
    if not e2.empty:
        pivot_s = e2.pivot_table(index="n", columns="solver", values="t_solve_s", aggfunc="median")
        latex_s = pivot_s.to_latex(float_format="%.4f", caption="Solve time (s) across SAT solvers using Sequential AMO")
        with open(os.path.join(out_dir, "table_solvers_comparison.tex"), "w") as f:
            f.write(latex_s)

    # Table 3: SAT vs Baselines
    base_df = df[df["seed"] == 0].copy()
    pivot_base = base_df.pivot_table(index="n", columns="method", values="t_total_s", aggfunc="median")
    latex_base = pivot_base.to_latex(float_format="%.4f", caption="Total time (s) comparing SAT and Baselines")
    with open(os.path.join(out_dir, "table_baselines_comparison.tex"), "w") as f:
        f.write(latex_base)

    # Table 4: Summary of Solved / Timeout counts
    summary = df.groupby(["method", "amo", "solver"])["status"].value_counts().unstack().fillna(0).astype(int)
    latex_sum = summary.to_latex(caption="Overall status summary by method and solver")
    with open(os.path.join(out_dir, "table_overall_summary.tex"), "w") as f:
        f.write(latex_sum)


def main():
    parser = argparse.ArgumentParser(description="Generate figures and tables from benchmark CSV.")
    parser.add_argument("--csv", type=str, default="results/raw/benchmark_results.csv", help="Input CSV path")
    parser.add_argument("--fig-dir", type=str, default="results/figures", help="Output figures directory")
    parser.add_argument("--table-dir", type=str, default="results/tables", help="Output tables directory")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"Error: CSV file not found at {args.csv}")
        return

    df = pd.read_csv(args.csv)
    print(f"Loaded {len(df)} records from {args.csv}")

    generate_figures(df, out_dir=args.fig_dir)
    print(f"Figures saved to {args.fig_dir}")

    generate_tables(df, out_dir=args.table_dir)
    print(f"LaTeX tables saved to {args.table_dir}")


if __name__ == "__main__":
    main()
