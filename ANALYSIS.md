# Experiment status and ownership

The user subsequently supplied a Groq credential and asked to disclose that Groq was used because they had no credits for the listed providers. A real Groq tool exchange is saved in `reports/provider-checks/A01-probe.json`. Full baseline evaluation is now in progress; no measured v1/v2 quality comparison is claimed yet. Groq is a disclosed provider deviation, with no recruiter approval represented.

## Provisional targeted change

v2 appends one internal clause-by-clause evidence audit to v1. The concrete risk is that a sentence combines an established product fact with an unresolved policy promise or a condition that the catalogue does not cover. Labelling the whole sentence from the first established clause can incorrectly produce supported. The audit maps every factual component to matching date/market/condition rows and applies contradicted > unknown > supported to the complete sentence.

This is a risk-based proposal, not a diagnosis from a completed baseline. After v1 development inference, inspect its saved errors and either substantiate this choice or replace it with one justified change before running v2. Retain the original v1 prompt and its run evidence. No improvement is promised or claimed.

## Results to fill from actual evidence

- v1 development run ID and joint/extraction metrics: pending.
- Observed baseline failure and evidence IDs: pending.
- Confirmed single change: pending baseline review.
- v2 development run ID and joint/extraction metrics: pending.
- Gains and extraction/label regressions: pending.
- Freeze fingerprint and v1/v2 check run IDs: pending.
- One actual sanitized model/tool exchange: pending.

## Checks and limitations

Codex generated the Python implementation, tests, prompts and documentation, installed dependencies, ran the controlled suite, and verified real PostgreSQL persistence/retrieval. The human user has not independently verified the submission. They should describe only checks they actually perform when submitting.

The inherited OpenAI environment key was not used. The user later supplied their own Groq credential, which is stored only in the ignored local `.env`. Groq requests and real fact-tool calls have now been made. Initial integration attempts were interrupted after discovering Groq JSON/tool incompatibilities and rate-limit behavior; their partial evidence remains saved as failed runs. The verified shared adapter separates batched tool lookup from final JSON mode. No final-check labels are present. Final-check input records were loaded by controlled API tests; no live final-check inference or quality-based tuning occurred. Do not describe the checks as a fully blind benchmark.

Semantic extraction completeness, sentence boundaries, catalogue reasoning and occurrence selection depend on the model and remain unmeasured. Programmatic validation ensures structural consistency, not factual correctness. No hosted deployment, UI, authentication, durable recovery, concurrency or idempotency is implemented; these are outside the required scope. The endpoint runs evaluation synchronously and may take several minutes.

Implementation work was done during this Codex session on 19 October 2026. File creation for the project began at 13:27 IST; session preparation and assessment reading preceded it. See WORK_LOG.md for the captured completion time. The requested two-to-three-hour live experiment has not been completed; do not present the implementation time as a completed experiment.
