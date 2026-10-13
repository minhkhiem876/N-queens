"""Generate simple, clean benchmark plots from CSV data.

Produces up to 4 figures:
  1. AMO Encoding Comparison (runtime vs board size)
  2. SAT Solver Comparison (runtime vs board size)
  3. E3 Ablation (symmetry and redundant ALO)
  4. SAT vs Baselines (SAT best configs vs CP-SAT, Gurobi, CPLEX)
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ── Visual Config ────────────────────────────────────────────────────────────

COLORS = {
    # AMO encodings
    "pairwise":  "#D55E00",
    "seq":       "#332288",
    "binary":    "#0072B2",
    "commander": "#E69F00",
    "product":   "#009E73",
    "ladder":    "#56B4E9",
    "totalizer": "#CC79A7",
    # SAT solvers
    "cadical195":  "#0072B2",
    "glucose42":   "#E69F00",
    "kissat404":   "#009E73",
    "maplechrono": "#D55E00",
    # Baselines
    "cpsat_binary":       "#56B4E9",
    "cpsat_permutation":  "#D55E00",
    "gurobi":             "#CC79A7",
    "cplex_mip":          "#009E73",
    "cplex_cp":           "#E69F00",
    "sym_off_alo_on":     "#0072B2",
    "sym_on_alo_on":      "#D55E00",
    "sym_off_alo_off":    "#009E73",
    "sym_on_alo_off":     "#CC79A7",
}

MARKERS = {
    "pairwise": "v", "seq": "P", "binary": "o", "commander": "s",
    "product": "D", "ladder": "^", "totalizer": "X",
    "cadical195": "o", "glucose42": "s", "kissat404": "^", "maplechrono": "D",
    "cpsat_binary": "D", "cpsat_permutation": "v", "gurobi": "X",
    "cplex_mip": "P", "cplex_cp": "*",
    "sym_off_alo_on": "o", "sym_on_alo_on": "s",
    "sym_off_alo_off": "^", "sym_on_alo_off": "D",
}

NICE_NAMES = {
    "pairwise": "Pairwise", "seq": "Sequential", "binary": "Binary",
    "commander": "Commander", "product": "Product", "ladder": "Ladder",
    "totalizer": "Totalizer",
    "cadical195": "CaDiCaL", "glucose42": "Glucose",
    "kissat404": "Kissat", "maplechrono": "MapleChrono",
    "cpsat_binary": "CP-SAT (Binary)", "cpsat_permutation": "CP-SAT (Permutation)",
    "gurobi": "Gurobi (MIP)",
    "cplex_mip": "CPLEX (MIP)", "cplex_cp": "CPLEX (CP)",
    "sym_off_alo_on": "Symmetry off, ALO on",
    "sym_on_alo_on": "Symmetry on, ALO on",
    "sym_off_alo_off": "Symmetry off, ALO off",
    "sym_on_alo_off": "Symmetry on, ALO off",
}


def setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9.5,
        "lines.linewidth": 2.0,
        "lines.markersize": 7,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def set_n_ticks(ax, n_values):
    """Set x-axis to log2 scale with human-readable integer labels."""
    ax.set_xscale("log", base=2)
    ticks = sorted(set(n_values))
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def load_and_clean(csv_path):
    df = pd.read_csv(csv_path)
    df["n"] = df["n"].astype(int)
    df["symmetry"] = df["symmetry"].astype(str).str.lower() == "true"
    df["redundant_alo"] = df["redundant_alo"].astype(str).str.lower() == "true"
    for col in ["t_encode_s", "t_solve_s", "t_total_s", "peak_mem_mb"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["num_vars", "num_clauses"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(-1).astype(int)
    # Deduplicate: keep last run for each config
    df = df.drop_duplicates(
        subset=["n", "method", "amo", "solver", "seed", "symmetry", "redundant_alo"],
        keep="last",
    ).reset_index(drop=True)
    return df


def plot_line(ax, sub, key_col, timeout_s=60.0):
    """Plot a single series with SAT points connected and TIMEOUT/MEMOUT marked."""
    key = sub[key_col].iloc[0]
    color = COLORS.get(key, "gray")
    marker = MARKERS.get(key, "o")
    label = NICE_NAMES.get(key, key)

    sat = sub[sub["status"] == "SAT"].sort_values("n")
    if not sat.empty:
        ax.plot(sat["n"], sat["t_solve_s"], color=color, marker=marker, label=label)

    # Mark first TIMEOUT / MEMOUT / LICENSE_LIMIT with an X
    fail = sub[sub["status"].isin(["TIMEOUT", "MEMOUT", "LICENSE_LIMIT"])].sort_values("n")
    if not fail.empty:
        row = fail.iloc[0]
        y = timeout_s if row["status"] == "TIMEOUT" else timeout_s * 0.7
        ax.scatter([row["n"]], [y], color=color, marker="X", s=100, zorder=5)
        ax.annotate(
            f"{label}\n({row['status']})",
            (row["n"], y), textcoords="offset points", xytext=(5, 5),
            fontsize=7.5, color=color, fontweight="bold",
        )


# ── Figure 1: AMO Encoding Comparison ───────────────────────────────────────

def fig1_amo_encodings(df, out_dir, timeout_s=60.0):
    """Compare all 7 AMO encodings using CaDiCaL solver."""
    e1 = df[
        (df["method"] == "sat")
        & (df["solver"] == "cadical195")
        & (~df["symmetry"])
        & (df["redundant_alo"])
        & (df["seed"] == 0)
    ]
    if e1.empty:
        return

    n_vals = sorted(e1["n"].unique())
    fig, ax = plt.subplots(figsize=(8, 5))

    for amo in ["commander", "binary", "product", "ladder", "seq", "pairwise", "totalizer"]:
        sub = e1[e1["amo"] == amo]
        if not sub.empty:
            plot_line(ax, sub, "amo", timeout_s)

    set_n_ticks(ax, n_vals)
    ax.set_yscale("log")
    ax.axhline(timeout_s, color="gray", ls="--", lw=1, label=f"Timeout ({int(timeout_s)}s)")
    ax.set_xlabel("Board Size $n$")
    ax.set_ylabel("Solve Time [s]")
    ax.set_title("AMO Encoding Comparison (CaDiCaL Solver)")
    ax.grid(True)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_amo_runtime.png"), dpi=300)
    fig.savefig(os.path.join(out_dir, "fig_amo_runtime.pdf"))
    plt.close(fig)
    print("  ✓ fig_amo_runtime")


# ── Figure 2: SAT Solver Comparison ─────────────────────────────────────────

def fig2_solvers(df, out_dir, timeout_s=60.0):
    """Compare 4 SAT solvers using Sequential Counter encoding."""
    e2 = df[
        (df["method"] == "sat")
        & (df["amo"] == "seq")
        & (~df["symmetry"])
        & (df["redundant_alo"])
        & (df["seed"] == 0)
    ]
    if e2.empty:
        return

    n_vals = sorted(e2["n"].unique())
    fig, ax = plt.subplots(figsize=(8, 5))

    for solver in ["kissat404", "cadical195", "glucose42", "maplechrono"]:
        sub = e2[e2["solver"] == solver]
        if not sub.empty:
            plot_line(ax, sub, "solver", timeout_s)

    set_n_ticks(ax, n_vals)
    ax.set_yscale("log")
    ax.axhline(timeout_s, color="gray", ls="--", lw=1, label=f"Timeout ({int(timeout_s)}s)")
    ax.set_xlabel("Board Size $n$")
    ax.set_ylabel("Solve Time [s]")
    ax.set_title("SAT Solver Comparison (Sequential Counter AMO)")
    ax.grid(True)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_solvers_comparison.png"), dpi=300)
    fig.savefig(os.path.join(out_dir, "fig_solvers_comparison.pdf"))
    plt.close(fig)
    print("  ✓ fig_solvers_comparison")

# ── Figure 3: E3 Ablation ────────────────────────────────────────────────────

def fig3_e3_ablation(df, out_dir, timeout_s=60.0):
    """Compare symmetry and redundant ALO settings using Sequential and CaDiCaL."""
    e3 = df[
        (df["method"] == "sat")
        & (df["amo"] == "seq")
        & (df["solver"] == "cadical195")
        & (df["seed"] == 0)
    ]
    if e3.empty:
        return

    settings = [
        (False, True, "sym_off_alo_on"),
        (True, True, "sym_on_alo_on"),
        (False, False, "sym_off_alo_off"),
        (True, False, "sym_on_alo_off"),
    ]
    n_vals = sorted(e3["n"].unique())
    fig, ax = plt.subplots(figsize=(8, 5))

    for symmetry, redundant_alo, label_key in settings:
        sub = e3[
            (e3["symmetry"] == symmetry)
            & (e3["redundant_alo"] == redundant_alo)
        ].copy()
        if not sub.empty:
            sub["e3_config"] = label_key
            plot_line(ax, sub, "e3_config", timeout_s)

    set_n_ticks(ax, n_vals)
    ax.set_yscale("log")
    ax.axhline(timeout_s, color="gray", ls="--", lw=1, label=f"Timeout ({int(timeout_s)}s)")
    ax.set_xlabel("Board Size $n$")
    ax.set_ylabel("Solve Time [s]")
    ax.set_title("E3: Symmetry and Redundant ALO Ablation")
    ax.grid(True)
    ax.legend(loc="upper left", ncol=2, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_e3_ablation.png"), dpi=300)
    fig.savefig(os.path.join(out_dir, "fig_e3_ablation.pdf"))
    plt.close(fig)
    print("  ✓ fig_e3_ablation")

# ── Figure 4: SAT vs Baselines ──────────────────────────────────────────────

def fig4_sat_vs_baselines(df, out_dir, timeout_s=60.0):
    """Compare SAT configs against CP-SAT, Gurobi, and CPLEX baselines."""
    base = df[(~df["symmetry"]) & (df["redundant_alo"]) & (df["seed"] == 0)]
    baseline_methods = ["cpsat_binary", "cpsat_permutation", "gurobi", "cplex_mip", "cplex_cp"]
    if base["method"].isin(baseline_methods).sum() == 0:
        print("  - skipping fig_sat_vs_baselines (no E4 baseline results)")
        return

    series = [
        ("SAT (Commander + CaDiCaL)",
         base[(base["method"] == "sat") & (base["amo"] == "commander") & (base["solver"] == "cadical195")],
         "#0072B2", "s"),
        ("SAT (Binary + CaDiCaL)",
         base[(base["method"] == "sat") & (base["amo"] == "binary") & (base["solver"] == "cadical195")],
         "#56B4E9", "o"),
        ("CP-SAT (Binary Matrix)",
         base[base["method"] == "cpsat_binary"],
         "#E69F00", "D"),
        ("CP-SAT (Permutation)",
         base[base["method"] == "cpsat_permutation"],
         "#D55E00", "v"),
        ("Gurobi (MIP)",
         base[base["method"] == "gurobi"],
         "#CC79A7", "X"),
        ("CPLEX (MIP)",
         base[base["method"] == "cplex_mip"],
         COLORS["cplex_mip"], MARKERS["cplex_mip"]),
        ("CPLEX (CP)",
         base[base["method"] == "cplex_cp"],
         COLORS["cplex_cp"], MARKERS["cplex_cp"]),
    ]

    all_ns = set()
    for _, sub, _, _ in series:
        all_ns.update(sub["n"].unique())
    n_vals = sorted(all_ns)
    if not n_vals:
        return

    fig, ax = plt.subplots(figsize=(8, 5))

    for label, sub, color, marker in series:
        if sub.empty:
            continue
        sat_rows = sub[sub["status"] == "SAT"].sort_values("n")
        if not sat_rows.empty:
            ax.plot(sat_rows["n"], sat_rows["t_total_s"], color=color, marker=marker, label=label)

        # Mark failure
        fail = sub[sub["status"].isin(["TIMEOUT", "MEMOUT", "LICENSE_LIMIT"])].sort_values("n")
        if not fail.empty:
            row = fail.iloc[0]
            y = timeout_s if row["status"] == "TIMEOUT" else timeout_s * 0.7
            ax.scatter([row["n"]], [y], color=color, marker="X", s=100, zorder=5)
            short = label.split("(")[0].strip()
            ax.annotate(
                f"{short}\n({row['status']})",
                (row["n"], y), textcoords="offset points", xytext=(5, 5),
                fontsize=7.5, color=color, fontweight="bold",
            )

    set_n_ticks(ax, n_vals)
    ax.set_yscale("log")
    ax.axhline(timeout_s, color="gray", ls="--", lw=1, label=f"Timeout ({int(timeout_s)}s)")
    ax.set_xlabel("Board Size $n$")
    ax.set_ylabel("Total Time [s] (encode + solve)")
    ax.set_title("SAT vs Exact Baselines")
    ax.grid(True)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_sat_vs_baselines.png"), dpi=300)
    fig.savefig(os.path.join(out_dir, "fig_sat_vs_baselines.pdf"))
    plt.close(fig)
    print("  ✓ fig_sat_vs_baselines")
    

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate simple benchmark plots.")
    parser.add_argument("--csv", default="results/raw/benchmark_results.csv")
    parser.add_argument("--fig-dir", default="results/figures")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"Error: {args.csv} not found")
        return

    os.makedirs(args.fig_dir, exist_ok=True)
    setup_style()

    df = load_and_clean(args.csv)
    print(f"Loaded {len(df)} records from {args.csv}")

    fig1_amo_encodings(df, args.fig_dir)
    fig2_solvers(df, args.fig_dir)
    fig3_e3_ablation(df, args.fig_dir)
    fig4_sat_vs_baselines(df, args.fig_dir)

    print(f"\nAll figures saved to {args.fig_dir}/")


if __name__ == "__main__":
    main()
