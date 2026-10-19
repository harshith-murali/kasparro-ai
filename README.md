# Kasparro factual-claim assessment

Python agent, exact-span evaluator, FastAPI service and PostgreSQL persistence for the issued speaker dataset.

**Provider disclosure:** I used Groq because I did not have credits for OpenAI, Anthropic, or Gemini. The configured model is `openai/gpt-oss-120b`, hosted through Groq. This is a deviation from the assessment's listed providers and is disclosed for the reviewer to assess; it is not an OpenAI API run. Codex assistance and actual checks are documented in `ANALYSIS.md`.

Repository: [harshith-murali/kasparro-ai](https://github.com/harshith-murali/kasparro-ai). Live evidence status is recorded in `reports/live-status.json` and `SUBMISSION.md`.

## Install

Requires Python 3.11+ and PostgreSQL. Verified locally on Python 3.14.6, PostgreSQL 18.4 and the exact dependency versions in `requirements.lock`.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
cp .env.example .env
```

Set `MODEL_PROVIDER=groq`, your own `GROQ_API_KEY`, and `DATABASE_URL` in `.env`. To use the original OpenAI adapter instead, set `MODEL_PROVIDER=openai` and `OPENAI_API_KEY`. Keep `.env` private. The CLI loads `.env` with override enabled, so a key explicitly configured there takes precedence over inherited environment variables. The Groq adapter targets `https://api.groq.com/openai/v1` with model `openai/gpt-oss-120b` and low reasoning effort. The OpenAI adapter retains `gpt-4.1-mini-2025-04-14`. default request timeout: **60 seconds**; retries: **0**; temperature: **0**; output limit: **6,000 tokens**; maximum: **3 model turns per answer**. All four runs must use identical settings.

```sh
docker compose up -d --wait
python -m kasparro init-db
```

The example database URL uses the local Docker database. You can instead use a local PostgreSQL installation and a dedicated database. `init-db` creates the tables; it does not create the database itself.

## Controlled tests

Unit tests run without an API key. Database tests skip unless `TEST_DATABASE_URL` is set:

```sh
python -m pytest -q
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kasparro python -m pytest -q
```

For a clean temporary database, give an administrative connection to this helper. It creates a randomly named database and removes it afterward:

```sh
PG_TEST_ADMIN_URL=postgresql://postgres:postgres@localhost:5432/postgres python -m scripts.test_local
```

Actual captured results are in `reports/tests.txt`. Tests use a fake model provider and a real PostgreSQL database. They do not measure model extraction or classification quality. See `SUBMISSION.md` for evidence status.

## Required live experiment, in order

1. Run the preserved v1 prompt on all 40 development answers:

   ```sh
   python -m kasparro run --version v1 --split development
   ```

2. Inspect that report's `missed_gold_ids`, `unmatched_prediction_ids`, `matched_wrong_label_ids`, `matches`, predictions and answer errors. Record a concrete diagnosis in `ANALYSIS.md`. The included v2 prompt is **provisional**, motivated by the concrete risk of assigning a whole sentence a label from only one clause. Retain or revise that one change based on the actual baseline; do not claim it was diagnosed from a run already performed. Preserve v1.

3. Run v2 on the same 40 inputs and compare the two reports:

   ```sh
   python -m kasparro run --version v2 --split development
   python -m scripts.compare_runs reports/V1_RUN_ID/report.json reports/V2_RUN_ID/report.json > reports/comparison.json
   ```

   Record gains, regressions or no gain in `ANALYSIS.md`. Changing model/settings/data/evaluator makes the comparison invalid. Prompt hashes identify the exact version used.

4. Freeze both versions before either final-check run:

   ```sh
   python -m scripts.freeze
   python -m kasparro run --version v1 --split check
   python -m kasparro run --version v2 --split check
   ```

   Groq requests are paced using remaining-token headers and a conservative estimate of the next request, with no automatic retries. Provider errors remain answer errors. Request pacing may add time outside the 60-second provider-request timeout. Groq rejects JSON mode combined with tools. Its first phase permits batched fact lookups for all needed brands; after tool results, the adapter omits tools and requests the final JSON object. Final claims are validated locally. A Groq answer therefore uses at most two model turns, within the three-turn limit. The OpenAI adapter retains its three-turn tool loop with JSON mode. If Groq reports an exhausted daily token quota, subsequent scheduled answers preserve a `quota_exhausted` error without repeatedly contacting that exhausted quota.

Freezing requires completed live development reports for both current prompts. Live check runs reject a missing or changed freeze fingerprint. Do not edit agent code, prompts, dependencies or settings after freezing. Check reports contain predictions, errors, timings and counts; all gold-dependent fields stay null. No final-check quality score is computed.

Each run writes `reports/<run_id>/report.json`, raw `predictions.json`, and one sanitized `Axx.trace.json` per scheduled answer. The trace contains actual model messages and executed fact-tool results when run live. It excludes credentials, provider headers and raw provider exceptions. The provider is recorded as `groq`, `openai` or `fake`, so controlled traces cannot be confused with live evidence. Outcomes are saved to disk before labels are loaded, then persisted to PostgreSQL. Interrupted or infrastructure-failed runs retain partial files and are marked failed where the database is reachable.

## API

```sh
python -m uvicorn kasparro.api:app --env-file .env --host 127.0.0.1 --port 8000
```

Ensure the shell environment uses your intended credentials; uvicorn's env-file loader does not override existing shell variables. Interactive schemas: [local API docs](http://127.0.0.1:8000/docs).

`POST /classify` takes only `answer_id`, `brand_id`, `question`, `ai_answer`, `agent_version` (`v1` or `v2`). It returns `answer_id` and validated `claims`. Extra fields, including gold/claim lists, return 422; an unknown primary brand returns 404; provider/invalid-output errors return 502; timeout returns 504. This endpoint does not require PostgreSQL.

`POST /evaluation-runs` takes only `agent_version` and `split` (`development` or `check`). It runs synchronously, returns 201 with run ID, terminal status, metadata and counts/metrics. A completed run may contain per-answer errors. Infrastructure failure returns 503 and preserves partial evidence. Initialize the database before using it.

`GET /evaluation-runs/{uuid}` joins run, answer and claim rows. Results have stable answer/span order; missing IDs return 404 and invalid UUIDs return 422. Individual classifications are returned directly; evaluation runs are the persisted unit.

## Implementation

- `kasparro/data.py`: proper UTF-8 CSV parsing with `newline=''`; immutable source wording, typed booleans/numbers, brand-scoped facts.
- `kasparro/agent.py`: OpenAI-compatible function-calling loop (Groq or OpenAI), read-only allowlisted tool, strict argument validation, bounded calls, sanitized answer-level errors. Multiple brands may be requested in one turn. Final output requires a primary-brand lookup; citations must come from retrieved brands.
- `kasparro/models.py`: strict schemas; Python resolves exact quote occurrences; checks Unicode spans, quote equality, IDs, order, overlaps, labels and fact IDs. Repeated quotes use an explicit model-selected occurrence. Reasons have a conservative two-sentence punctuation check.
- `kasparro/evaluation.py`: no fuzzy or LLM matching. G is all scheduled gold claims, P is all accepted predictions, M is exact matches, C is exact matches with correct labels. Extraction F1 is `2M/(P+G)`; main score joint F1 is `2C/(P+G)`. Errors contribute zero P while retaining their gold in G. Missing/duplicate answer outcomes are rejected.
- `kasparro/runner.py`, `store.py`, `schema.sql`: atomic local evidence files and per-answer database transactions; parameterized SQL, foreign keys, unique answer/span constraints, JSONB metadata and optional development matches.
- `prompts/v1.txt`, `prompts/v2.txt`: preserved baseline and provisional single-behavior candidate.

Development labels are opened only by the evaluator, after raw predictions are saved. Agent inputs contain the four required fields; tools expose catalogue rows only. Dataset and prompt SHA-256 hashes, versions, settings, timestamps and available Git revision are recorded. Original supplied CSVs and assessment document remain in place.

The adapters follow [Groq OpenAI compatibility](https://console.groq.com/docs/openai), [Groq local tool calling](https://console.groq.com/docs/tool-use/local-tool-calling), and [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).
