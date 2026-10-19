import hashlib
import json
import subprocess
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from .data import ROOT, DATASET_VERSION, FACT_VERSION, EVALUATOR_VERSION, file_hashes, load_answers
from .evaluation import load_gold, score


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def revision():
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        return {"commit": sha, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return None


def run_evaluation(agent, store, version, split, output_dir=None):
    if version not in ("v1", "v2") or split not in ("development", "check"):
        raise ValueError("Invalid run configuration")
    if split == "check" and agent.provider.__class__.__name__ == "OpenAIProvider":
        from .freeze import require_frozen
        require_frozen(agent.settings)
    answers = load_answers(split)
    run_id = str(uuid.uuid4())
    directory = Path(output_dir or ROOT / "reports") / run_id
    directory.mkdir(parents=True, exist_ok=False)
    metadata = {"agent_version": version, "prompt_version": version,
        "prompt_sha256": hashlib.sha256((ROOT / "prompts" / f"{version}.txt").read_bytes()).hexdigest(),
        "dataset_version": DATASET_VERSION, "fact_version": FACT_VERSION, "evaluator_version": EVALUATOR_VERSION,
        "split": split, "provider": "openai" if agent.provider.__class__.__name__ == "OpenAIProvider" else "fake",
        "model": agent.settings.model, "settings": asdict(agent.settings),
        "timestamp": datetime.now(timezone.utc).isoformat(), "source_revision": revision(), "file_hashes": file_hashes(),
        "scheduled_answers": [a["answer_id"] for a in answers]}
    report = {"run_id": run_id, "status": "processing", "metadata": metadata, "answers": [], "scores": None, "error": None}
    save_json(directory / "report.json", report)
    created = False
    try:
        store.create(run_id, metadata)
        created = True
        for answer in answers:
            outcome = agent.outcome({k: v for k, v in answer.items() if k != "split"}, version)
            trace = outcome.pop("trace")
            trace_ref = str((directory / f'{answer["answer_id"]}.trace.json').relative_to(ROOT)) if directory.is_relative_to(ROOT) else str(directory / f'{answer["answer_id"]}.trace.json')
            save_json(directory / f'{answer["answer_id"]}.trace.json', trace)
            outcome["trace_reference"] = trace_ref
            report["answers"].append(outcome)
            # Save raw outcomes BEFORE gold can be loaded or joined, preserving partial evidence.
            save_json(directory / "predictions.json", report["answers"])
            store.save_answer(run_id, outcome, trace_ref)
            save_json(directory / "report.json", report)
        report["scores"] = score(answers, report["answers"], agent.catalogue,
                                  load_gold() if split == "development" else None)
        report["status"] = "completed"
        store.finish(run_id, "completed", report["scores"])
    except BaseException:
        report.update(status="failed", error={"type": "infrastructure_error", "message": "Run interrupted or infrastructure failed"})
        if created:
            try:
                store.finish(run_id, "failed", error=report["error"])
            except Exception:
                pass
        raise
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        save_json(directory / "report.json", report)
    return report
