"""Record hardware, OS, and solver versions into results/raw/environment.json."""

import json
import os
import platform
import sys
import psutil

try:
    import pysat
    pysat_version = pysat.__version__
except Exception:
    pysat_version = "unknown"

try:
    import ortools
    ortools_version = ortools.__version__
except Exception:
    ortools_version = "unknown"

try:
    import gurobipy
    gurobi_version = gurobipy.__version__
except Exception:
    gurobi_version = "unknown"

try:
    import docplex
    docplex_version = docplex.__version__
except Exception:
    docplex_version = "unknown"


def record_environment(output_path: str = "results/raw/environment.json") -> dict:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cpu_model = platform.processor()
    if sys.platform == "darwin":
        try:
            import subprocess
            res = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                cpu_model = res.stdout.strip()
        except Exception:
            pass

    env_info = {
        "machine_id": platform.node(),
        "os": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "cpu": cpu_model,
        "physical_cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "python_version": sys.version.split()[0],
        "solvers": {
            "pysat": pysat_version,
            "cadical": "cadical195 (bundled in PySAT)",
            "glucose": "glucose42 (bundled in PySAT)",
            "kissat": "kissat404 (bundled in PySAT)",
            "maplechrono": "maplechrono (bundled in PySAT)",
            "ortools_cpsat": ortools_version,
            "gurobi": gurobi_version,
            "docplex": docplex_version,
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(env_info, f, indent=2)

    return env_info


if __name__ == "__main__":
    info = record_environment()
    print("Environment saved:", json.dumps(info, indent=2))
