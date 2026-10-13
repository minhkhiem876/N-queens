"""Subprocess-isolated benchmark harness for N-Queens with resume capability."""

import argparse
import csv
import datetime
import json
import os
import subprocess
import sys
import time
from typing import Dict, Any, List, Set, Tuple


CSV_HEADER = [
    "run_id",
    "timestamp",
    "n",
    "method",
    "amo",
    "solver",
    "seed",
    "symmetry",
    "redundant_alo",
    "num_vars",
    "num_clauses",
    "t_encode_s",
    "t_solve_s",
    "t_total_s",
    "peak_mem_mb",
    "status",
    "verified",
    "timeout_s",
    "solver_version",
    "machine_id",
]


def load_existing_runs(csv_path: str) -> Set[Tuple[Any, ...]]:
    """Load existing configuration keys from CSV to enable resume."""
    existing = set()
    if not os.path.exists(csv_path):
        return existing

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (
                int(row["n"]),
                row["method"],
                row["amo"],
                row["solver"],
                int(row["seed"]),
                row["symmetry"].lower() == "true",
                row["redundant_alo"].lower() == "true",
            )
            existing.add(key)
    return existing


def run_single_subprocess(
    n: int,
    method: str,
    amo: str,
    solver: str,
    seed: int,
    symmetry: bool,
    redundant_alo: bool,
    timeout_s: float,
    workers: int = 1,
) -> Dict[str, Any]:
    """Execute a single configuration in an isolated subprocess with hard OS timeout."""
    cmd = [
        sys.executable,
        "scripts/run_single.py",
        "--n", str(n),
        "--method", method,
        "--amo", amo,
        "--solver", solver,
        "--timeout", str(timeout_s),
        "--seed", str(seed),
        "--workers", str(workers),
    ]
    if symmetry:
        cmd.append("--symmetry")
    if not redundant_alo:
        cmd.append("--no-redundant-alo")

    t_start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = "."

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s + 5.0,  # extra grace period before hard kill
            env=env,
        )
        t_wall = time.perf_counter() - t_start

        if proc.returncode != 0:
            err_output = proc.stderr.strip() or proc.stdout.strip()
            status = "MEMOUT" if ("bad_alloc" in err_output.lower() or "memory" in err_output.lower()) else "ERROR"
            return {
                "status": status,
                "t_total_s": t_wall,
                "error": err_output,
            }

        stdout_lines = proc.stdout.strip().splitlines()
        if not stdout_lines:
            return {"status": "ERROR", "error": "Empty stdout from run_single"}

        # Last line should be the JSON payload
        result = json.loads(stdout_lines[-1])
        return result

    except subprocess.TimeoutExpired:
        t_wall = time.perf_counter() - t_start
        return {
            "status": "TIMEOUT",
            "t_total_s": min(timeout_s, t_wall),
            "t_solve_s": timeout_s,
            "t_encode_s": 0.0,
            "verified": False,
            "num_vars": -1,
            "num_clauses": -1,
            "peak_mem_mb": -1.0,
        }
    except Exception as e:
        t_wall = time.perf_counter() - t_start
        return {
            "status": "ERROR",
            "t_total_s": t_wall,
            "error": str(e),
        }


def run_benchmark(
    experiment: str = "all",
    instances: List[int] = None,
    csv_path: str = "results/raw/benchmark_results.csv",
    timeout_s: float = 600.0,
    seeds: List[int] = None,
    force: bool = False,
):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.exists(csv_path)

    existing_runs = set() if force else load_existing_runs(csv_path)

    # Load machine and solver metadata
    env_file = "results/raw/environment.json"
    machine_id = "unknown"
    solver_versions = {}
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            env_data = json.load(f)
            machine_id = env_data.get("machine_id", "unknown")
            solver_versions = env_data.get("solvers", {})

    if instances is None:
        instances = [8, 16, 32, 64, 100, 128, 200, 256, 400, 512]
    if seeds is None:
        seeds = [0]

    # Generate task list based on experiment type
    configs: List[Dict[str, Any]] = []

    # E1: Compare AMO encodings (CaDiCaL solver)
    if experiment in ["e1", "all"]:
        amos = ["pairwise", "seq", "binary", "commander", "product", "ladder", "totalizer"]
        for n in instances:
            for amo in amos:
                for seed in seeds:
                    configs.append({
                        "exp": "E1",
                        "n": n,
                        "method": "sat",
                        "amo": amo,
                        "solver": "cadical195",
                        "seed": seed,
                        "symmetry": False,
                        "redundant_alo": True,
                    })

    # E2: Compare SAT solvers (using seq encoding)
    if experiment in ["e2", "all"]:
        solvers = ["cadical195", "glucose42", "kissat404", "maplechrono"]
        for n in instances:
            for s in solvers:
                for seed in seeds:
                    configs.append({
                        "exp": "E2",
                        "n": n,
                        "method": "sat",
                        "amo": "seq",
                        "solver": s,
                        "seed": seed,
                        "symmetry": False,
                        "redundant_alo": True,
                    })

    # E3: Ablations on symmetry and redundant ALO
    if experiment in ["e3", "all"]:
        ablation_settings = [
            (False, True),   # baseline: no symmetry, redundant ALO
            (True, True),    # symmetry ON, redundant ALO
            (False, False),  # no symmetry, redundant ALO OFF
            (True, False),   # symmetry ON, redundant ALO OFF
        ]
        for n in instances:
            for sym, red_alo in ablation_settings:
                for seed in seeds:
                    configs.append({
                        "exp": "E3",
                        "n": n,
                        "method": "sat",
                        "amo": "seq",
                        "solver": "cadical195",
                        "seed": seed,
                        "symmetry": sym,
                        "redundant_alo": red_alo,
                    })

    # E4: Compare SAT vs Baselines (CP-SAT permutation & binary, Gurobi, CPLEX)
    if experiment in ["e4", "all"]:
        baselines = ["cpsat_permutation", "cpsat_binary", "gurobi", "cplex_mip", "cplex_cp"]
        for n in instances:
            for b in baselines:
                for seed in seeds:
                    configs.append({
                        "exp": "E4",
                        "n": n,
                        "method": b,
                        "amo": "alldifferent" if "permutation" in b or "cp" in b else "linear_amo",
                        "solver": b,
                        "seed": seed,
                        "symmetry": False,
                        "redundant_alo": True,
                    })

    print(f"Total configurations planned: {len(configs)}. Existing already: {len(existing_runs)}")

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
            f.flush()

        run_idx = len(existing_runs)
        for cfg in configs:
            key = (
                cfg["n"],
                cfg["method"],
                cfg["amo"],
                cfg["solver"],
                cfg["seed"],
                cfg["symmetry"],
                cfg["redundant_alo"],
            )
            if key in existing_runs:
                continue

            run_idx += 1
            run_id = f"run_{run_idx:05d}"
            timestamp = datetime.datetime.now().isoformat()

            print(f"[{run_id}] Running {cfg['exp']}: n={cfg['n']:4d} method={cfg['method']:16s} amo={cfg['amo']:10s} solver={cfg['solver']:12s} ...", end="", flush=True)

            res = run_single_subprocess(
                n=cfg["n"],
                method=cfg["method"],
                amo=cfg["amo"],
                solver=cfg["solver"],
                seed=cfg["seed"],
                symmetry=cfg["symmetry"],
                redundant_alo=cfg["redundant_alo"],
                timeout_s=timeout_s,
            )

            status = res.get("status", "UNKNOWN")
            verified = res.get("verified", False)
            t_solve = res.get("t_solve_s", 0.0)
            t_total = res.get("t_total_s", 0.0)

            print(f" -> {status:10s} (verified={verified}, solve={t_solve:.3f}s, total={t_total:.3f}s)")

            solver_ver = solver_versions.get(cfg["solver"], "unknown")

            row_data = {
                "run_id": run_id,
                "timestamp": timestamp,
                "n": cfg["n"],
                "method": cfg["method"],
                "amo": cfg["amo"],
                "solver": cfg["solver"],
                "seed": cfg["seed"],
                "symmetry": cfg["symmetry"],
                "redundant_alo": cfg["redundant_alo"],
                "num_vars": res.get("num_vars", -1),
                "num_clauses": res.get("num_clauses", -1),
                "t_encode_s": res.get("t_encode_s", 0.0),
                "t_solve_s": t_solve,
                "t_total_s": t_total,
                "peak_mem_mb": res.get("peak_mem_mb", -1.0),
                "status": status,
                "verified": verified,
                "timeout_s": timeout_s,
                "solver_version": solver_ver,
                "machine_id": machine_id,
            }

            writer.writerow(row_data)
            f.flush()
            existing_runs.add(key)


def main():
    parser = argparse.ArgumentParser(description="Run N-Queens benchmark suite.")
    parser.add_argument("--exp", type=str, default="all", choices=["e1", "e2", "e3", "e4", "all"], help="Experiment set")
    parser.add_argument("--instances", type=str, default="8,16,32,64,100,128,200,256,400,512", help="Comma-separated n values")
    parser.add_argument("--timeout", type=float, default=600.0, help="Per-run timeout in seconds")
    parser.add_argument("--seeds", type=str, default="0", help="Comma-separated random seeds")
    parser.add_argument("--csv", type=str, default="results/raw/benchmark_results.csv", help="CSV output path")
    parser.add_argument("--force", action="store_true", help="Rerun existing configurations")

    args = parser.parse_args()
    instances = [int(x.strip()) for x in args.instances.split(",") if x.strip()]
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]

    run_benchmark(
        experiment=args.exp,
        instances=instances,
        csv_path=args.csv,
        timeout_s=args.timeout,
        seeds=seeds,
        force=args.force,
    )


if __name__ == "__main__":
    main()
