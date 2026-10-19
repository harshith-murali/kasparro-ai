"""Run the complete live evaluation pipeline: v1 dev, v2 dev, comparison, v1 check, v2 check."""
import json
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)
ROOT = Path(__file__).resolve().parent.parent

def run_cmd(args):
    print(f"\n>>> Running: {' '.join(args)}", flush=True)
    res = subprocess.run([sys.executable] + args, cwd=ROOT, text=True, capture_output=True)
    print(res.stdout, flush=True)
    if res.returncode != 0:
        print(f"FAILED (code {res.returncode}):\n{res.stderr}", flush=True)
        sys.exit(res.returncode)
    try:
        data = json.loads(res.stdout)
        return data
    except Exception:
        return None

def main():
    print("=== Step 1: Running v1 development ===", flush=True)
    res_v1_dev = run_cmd(["-m", "kasparro", "run", "--version", "v1", "--split", "development"])
    v1_dev_id = res_v1_dev["run_id"]
    print(f"v1 development run_id: {v1_dev_id}", flush=True)

    print("=== Step 2: Running v2 development ===", flush=True)
    res_v2_dev = run_cmd(["-m", "kasparro", "run", "--version", "v2", "--split", "development"])
    v2_dev_id = res_v2_dev["run_id"]
    print(f"v2 development run_id: {v2_dev_id}", flush=True)

    print("=== Step 3: Comparing development runs ===", flush=True)
    v1_report = ROOT / "reports" / v1_dev_id / "report.json"
    v2_report = ROOT / "reports" / v2_dev_id / "report.json"
    comp_res = run_cmd(["-m", "scripts.compare_runs", str(v1_report), str(v2_report)])
    if comp_res:
        (ROOT / "reports" / "comparison.json").write_text(json.dumps(comp_res, indent=2) + "\n")
        print("Updated reports/comparison.json", flush=True)

    print("=== Step 4: Running v1 check ===", flush=True)
    res_v1_chk = run_cmd(["-m", "kasparro", "run", "--version", "v1", "--split", "check"])
    v1_chk_id = res_v1_chk["run_id"]
    print(f"v1 check run_id: {v1_chk_id}", flush=True)

    print("=== Step 5: Running v2 check ===", flush=True)
    res_v2_chk = run_cmd(["-m", "kasparro", "run", "--version", "v2", "--split", "check"])
    v2_chk_id = res_v2_chk["run_id"]
    print(f"v2 check run_id: {v2_chk_id}", flush=True)

    print("\n==========================================", flush=True)
    print("ALL RUNS COMPLETE!", flush=True)
    print(f"  v1 development: {v1_dev_id}")
    print(f"  v2 development: {v2_dev_id}")
    print(f"  v1 check:       {v1_chk_id}")
    print(f"  v2 check:       {v2_chk_id}")
    print("==========================================", flush=True)

if __name__ == "__main__":
    main()
