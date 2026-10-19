CREATE TABLE IF NOT EXISTS runs (
    run_id UUID PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('processing','completed','failed')),
    metadata JSONB NOT NULL,
    scores JSONB,
    error JSONB
);
CREATE TABLE IF NOT EXISTS answer_results (
    run_id UUID NOT NULL REFERENCES runs(run_id),
    answer_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success','error')),
    error JSONB,
    latency_seconds DOUBLE PRECISION NOT NULL CHECK (latency_seconds >= 0),
    trace_reference TEXT,
    PRIMARY KEY (run_id, answer_id),
    CHECK ((status='error' AND error IS NOT NULL) OR (status='success' AND error IS NULL))
);
CREATE TABLE IF NOT EXISTS claim_results (
    run_id UUID NOT NULL,
    answer_id TEXT NOT NULL,
    claim_id TEXT NOT NULL,
    start_char INTEGER NOT NULL CHECK (start_char >= 0),
    end_char INTEGER NOT NULL CHECK (end_char > start_char),
    quote TEXT NOT NULL,
    label TEXT NOT NULL CHECK (label IN ('supported','contradicted','unknown')),
    fact_ids JSONB NOT NULL,
    reason TEXT NOT NULL,
    development_match JSONB,
    PRIMARY KEY (run_id, answer_id, start_char, end_char),
    UNIQUE (run_id, claim_id),
    FOREIGN KEY (run_id, answer_id) REFERENCES answer_results(run_id, answer_id)
);
