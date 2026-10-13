"""Subprocess-isolated benchmark harness for N-Queens with resume and smart-skip capability."""

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


def get_python_executable() -> str:
    """Return python executable, preferring virtualenv if present."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    venv_py = os.path.join(root, ".venv", "bin", "python")
    if os.path.exists(venv_py):
        return venv_py
    venv_py_win = os.path.join(root, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_py_win):
        return venv_py_win
    return sys.executable


def load_existing_runs(csv_path: str) -> Tuple[Set[Tuple[Any, ...]], Dict[Tuple[Any, ...], int]]:
    """Load existing configuration keys and failure thresholds from CSV to enable resume and smart-skip."""
    existing: Set[Tuple[Any, ...]] = set()
    failed_min_n: Dict[Tuple[Any, ...], int] = {}

    if not os.path.exists(csv_path):
        return existing, failed_min_n

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get("status", "UNKNOWN")
            if status in ("ERROR", "UNKNOWN"):
                continue  # Never skip previously errored runs
            n_val = int(row["n"])
            method = row["method"]
            amo = row["amo"]
            solver = row["solver"]
            seed = int(row["seed"])
            sym = row["symmetry"].lower() == "true"
            red_alo = row["redundant_alo"].lower() == "true"

            key = (n_val, method, amo, solver, seed, sym, red_alo)
            existing.add(key)

            if status in ("TIMEOUT", "MEMOUT", "LICENSE_LIMIT", "SOLVER_NOT_FOUND"):
                family_key = (method, amo, solver, sym, red_alo)
                if family_key not in failed_min_n or n_val < failed_min_n[family_key]:
                    failed_min_n[family_key] = n_val

    return existing, failed_min_n


def _parse_encode_stats(raw_stdout: Any) -> Dict[str, Any]:
    """Extract pre-solve ENCODE_STATS JSON payload from subprocess stdout if available."""
    if not raw_stdout:
        return {}
    if isinstance(raw_stdout, bytes):
        text = raw_stdout.decode("utf-8", errors="replace")
    else:
        text = str(raw_stdout)

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("ENCODE_STATS:"):
            try:
                return json.loads(line[len("ENCODE_STATS:"):])
            except Exception:
                pass
    return {}


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
    python_bin = get_python_executable()
    cmd = [
        python_bin,
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
            timeout=timeout_s + 3.0,  # grace period before hard kill
            env=env,
        )
        t_wall = time.perf_counter() - t_start

        if proc.returncode != 0:
            err_output = proc.stderr.strip() or proc.stdout.strip()
            enc_stats = _parse_encode_stats(proc.stdout)
            status = (
                "MEMOUT"
                if ("bad_alloc" in err_output.lower() or "memory" in err_output.lower() or proc.returncode == -9)
                else "ERROR"
            )
            return {
                "status": status,
                "t_total_s": t_wall,
                "t_encode_s": enc_stats.get("t_encode_s", 0.0),
                "t_solve_s": max(0.0, t_wall - enc_stats.get("t_encode_s", 0.0)),
                "num_vars": enc_stats.get("num_vars", -1),
                "num_clauses": enc_stats.get("num_clauses", -1),
                "error": err_output,
            }

        stdout_lines = [
            ln.strip()
            for ln in proc.stdout.strip().splitlines()
            if ln.strip() and not ln.strip().startswith("ENCODE_STATS:")
        ]
        if not stdout_lines:
            return {"status": "ERROR", "error": "Empty stdout from run_single"}

        # Last non-ENCODE_STATS line is the JSON payload
        result = json.loads(stdout_lines[-1])
        return result

    except subprocess.TimeoutExpired as e:
        t_wall = time.perf_counter() - t_start
        enc_stats = _parse_encode_stats(e.stdout)
        t_enc = float(enc_stats.get("t_encode_s", 0.0))
        return {
            "status": "TIMEOUT",
            "t_total_s": max(timeout_s, t_wall),
            "t_solve_s": max(0.0, timeout_s - t_enc),
            "t_encode_s": t_enc,
            "verified": False,
            "num_vars": enc_stats.get("num_vars", -1),
            "num_clauses": enc_stats.get("num_clauses", -1),
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
    timeout_s: float = 60.0,
    seeds: List[int] = None,
    force: bool = False,
    smart_skip: bool = True,
):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.exists(csv_path)

    if force:
        existing_runs: Set[Tuple[Any, ...]] = set()
        failed_min_n: Dict[Tuple[Any, ...], int] = {}
    else:
        existing_runs, failed_min_n = load_existing_runs(csv_path)

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
    instances = sorted(list(set(instances)))

    if seeds is None:
        seeds = [0]

    # Generate task list ordered by n ascending so smart_skip can prune larger n
    configs: List[Dict[str, Any]] = []

    for n in instances:
        # E1: Compare AMO encodings (CaDiCaL solver)
        if experiment in ["e1", "all"]:
            amos = ["pairwise", "seq", "binary", "commander", "product", "ladder", "totalizer"]
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

        # E2: Compare SAT solvers (using seq and commander encodings)
        if experiment in ["e2", "all"]:
            solvers = ["cadical195", "glucose42", "kissat404", "maplechrono"]
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
                    configs.append({
                        "exp": "E2",
                        "n": n,
                        "method": "sat",
                        "amo": "commander",
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
            for b in baselines:
                for seed in seeds:
                    configs.append({
                        "exp": "E4",
                        "n": n,
                        "method": b,
                        "amo": "alldifferent" if ("permutation" in b or "cp" in b) else ("binary_matrix" if "binary" in b else "linear_amo"),
                        "solver": "cp-sat" if "cpsat" in b else b,
                        "seed": seed,
                        "symmetry": False,
                        "redundant_alo": True,
                    })

    print(f"Total configurations in grid: {len(configs)}. Existing runs in CSV: {len(existing_runs)}")

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
            f.flush()

        run_idx = len(existing_runs)
        for cfg in configs:
            # Normalize key to match what gets written to CSV
            norm_amo = cfg["amo"]
            norm_solver = cfg["solver"]
            key = (
                cfg["n"],
                cfg["method"],
                norm_amo,
                norm_solver,
                cfg["seed"],
                cfg["symmetry"],
                cfg["redundant_alo"],
            )
            # Also check legacy key variants from earlier runs
            legacy_key_1 = (
                cfg["n"],
                cfg["method"],
                "alldifferent",
                cfg["method"],
                cfg["seed"],
                cfg["symmetry"],
                cfg["redundant_alo"],
            )
            if key in existing_runs or legacy_key_1 in existing_runs:
                continue

            family_key = (
                cfg["method"],
                norm_amo,
                norm_solver,
                cfg["symmetry"],
                cfg["redundant_alo"],
            )
            legacy_family_key = (
                cfg["method"],
                "alldifferent",
                cfg["method"],
                cfg["symmetry"],
                cfg["redundant_alo"],
            )

            # Smart skip if this family already hit TIMEOUT / MEMOUT / LICENSE_LIMIT at a smaller n
            min_fail_n = failed_min_n.get(family_key) or failed_min_n.get(legacy_family_key)
            if smart_skip and min_fail_n is not None and cfg["n"] > min_fail_n:
                continue

            run_idx += 1
            run_id = f"run_{run_idx:05d}"
            timestamp = datetime.datetime.now().isoformat()

            print(
                f"[{run_id}] {cfg['exp']} | n={cfg['n']:4d} | method={cfg['method']:17s} "
                f"| amo={cfg['amo']:12s} | solver={cfg['solver']:11s} | seed={cfg['seed']} ...",
                end="",
                flush=True,
            )

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

            if status == "ERROR":
                err_snippet = res.get("error", "").replace("\n", " ").strip()[:80]
                print(f" -> ERROR ({err_snippet})")
            else:
                print(f" -> {status:10s} (verified={verified}, solve={t_solve:.3f}s, total={t_total:.3f}s)")

            if status in ("TIMEOUT", "MEMOUT", "LICENSE_LIMIT", "SOLVER_NOT_FOUND"):
                if family_key not in failed_min_n or cfg["n"] < failed_min_n[family_key]:
                    failed_min_n[family_key] = cfg["n"]

            solver_ver = solver_versions.get(cfg["solver"], "unknown")

            row_data = {
                "run_id": run_id,
                "timestamp": timestamp,
                "n": cfg["n"],
                "method": cfg["method"],
                "amo": res.get("amo", cfg["amo"]),
                "solver": res.get("solver", cfg["solver"]),
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
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-run timeout in seconds")
    parser.add_argument("--seeds", type=str, default="0", help="Comma-separated random seeds")
    parser.add_argument("--csv", type=str, default="results/raw/benchmark_results.csv", help="CSV output path")
    parser.add_argument("--force", action="store_true", help="Rerun existing configurations")
    parser.add_argument("--no-smart-skip", action="store_true", help="Disable skipping larger n after timeout/memout")

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
        smart_skip=not args.no_smart_skip,
    )


if __name__ == "__main__":
    main()
