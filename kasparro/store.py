import os
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .data import ROOT


class Store:
    def __init__(self, url=None):
        self.url = url or os.environ["DATABASE_URL"]

    def connect(self):
        return psycopg.connect(self.url, row_factory=dict_row, connect_timeout=5)

    def initialize(self):
        with self.connect() as conn:
            conn.execute((ROOT / "schema.sql").read_text())

    def create(self, run_id, metadata):
        with self.connect() as conn:
            conn.execute("INSERT INTO runs(run_id,status,metadata) VALUES (%s,'processing',%s)",
                         (run_id, Jsonb(metadata)))

    def save_answer(self, run_id, outcome, trace_reference):
        with self.connect() as conn:
            conn.execute("""INSERT INTO answer_results
                (run_id,answer_id,status,error,latency_seconds,trace_reference) VALUES (%s,%s,%s,%s,%s,%s)""",
                (run_id, outcome["answer_id"], outcome["status"], Jsonb(outcome["error"]) if outcome["error"] else None,
                 outcome["latency_seconds"], trace_reference))
            for c in outcome["claims"]:
                conn.execute("""INSERT INTO claim_results (run_id,answer_id,claim_id,start_char,end_char,
                    quote,label,fact_ids,reason) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (run_id, outcome["answer_id"], c["claim_id"], c["start_char"], c["end_char"], c["quote"],
                     c["label"], Jsonb(c["fact_ids"]), c["reason"]))

    def finish(self, run_id, status, scores=None, error=None):
        with self.connect() as conn:
            conn.execute("UPDATE runs SET status=%s,scores=%s,error=%s WHERE run_id=%s",
                         (status, Jsonb(scores) if scores is not None else None, Jsonb(error) if error else None, run_id))
            for match in (scores or {}).get("matches") or []:
                conn.execute("UPDATE claim_results SET development_match=%s WHERE run_id=%s AND claim_id=%s",
                             (Jsonb(match), run_id, match["prediction_id"]))

    def get(self, run_id):
        with self.connect() as conn:
            run = conn.execute("SELECT * FROM runs WHERE run_id=%s", (run_id,)).fetchone()
            if run is None:
                return None
            rows = conn.execute("""SELECT a.answer_id,a.status,a.error,a.latency_seconds,a.trace_reference,
                c.claim_id,c.start_char,c.end_char,c.quote,c.label,c.fact_ids,c.reason,c.development_match
                FROM answer_results a LEFT JOIN claim_results c
                ON a.run_id=c.run_id AND a.answer_id=c.answer_id
                WHERE a.run_id=%s ORDER BY a.answer_id,c.start_char,c.end_char""", (run_id,)).fetchall()
        answers = {}
        for row in rows:
            aid = row["answer_id"]
            if aid not in answers:
                answers[aid] = {k: row[k] for k in ("answer_id", "status", "error", "latency_seconds", "trace_reference")}
                answers[aid]["claims"] = []
            if row["claim_id"] is not None:
                answers[aid]["claims"].append({k: row[k] for k in ("claim_id", "start_char", "end_char", "quote", "label", "fact_ids", "reason", "development_match")})
        return {**run, "run_id": str(run["run_id"]), "answers": list(answers.values())}
