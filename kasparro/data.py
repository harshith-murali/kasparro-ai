"""Inference data only: this module never opens development_gold.csv."""
import csv
import hashlib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET_VERSION = "long-brand-answers-50-v4"
FACT_VERSION = "speaker-catalogue-v4"
EVALUATOR_VERSION = "sentence-spans-and-labels-v4"


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_answers(split=None):
    rows = read_csv(ROOT / "answers.csv")
    if len({r["answer_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate answer IDs")
    return [r for r in rows if split is None or r["split"] == split]


class Catalogue:
    def __init__(self, path=None):
        self.rows = read_csv(path or ROOT / "brand_facts.csv")
        self.by_brand = {}
        self.ids = set()
        for raw in self.rows:
            row = dict(raw)
            kind, value = row["value_type"], row["value"]
            if kind == "boolean":
                if value not in ("true", "false"):
                    raise ValueError("Invalid boolean")
                row["value"] = value == "true"
            elif kind == "number":
                row["value"] = float(value)
            elif kind != "string":
                raise ValueError("Invalid fact type")
            for key in ("valid_from", "valid_to"):
                if row[key]:
                    date.fromisoformat(row[key])
            if row["fact_id"] in self.ids:
                raise ValueError("Duplicate fact IDs")
            self.ids.add(row["fact_id"])
            self.by_brand.setdefault(row["brand_id"], []).append(row)

    def get_brand_facts(self, brand_id):
        if brand_id not in self.by_brand:
            raise ValueError("Unknown requested brand")
        return {"fact_version": FACT_VERSION, "facts": self.by_brand[brand_id]}


def file_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("answers.csv", "brand_facts.csv", "development_gold.csv")}
