# Results, targeted change and limitations

## Provider and evidence disclosure

I used Groq because I did not have credits for OpenAI, Anthropic, or Gemini. The model is `openai/gpt-oss-120b` hosted by Groq; these are not OpenAI API runs. Groq is a deviation from the assessment's listed providers. No recruiter approval is represented.

All four provider-backed run attempts were saved with PostgreSQL outcomes and local traces. Groq's daily token quota was exhausted during the baseline. The later attempts therefore contain quota errors rather than accepted model predictions. **The required live-quality experiment is unfinished.** The main live comparison is confounded by provider availability and cannot establish the effect of v2.

| Attempt | Run ID | Answers | Accepted claims | Answer errors | Joint F1 |
|---|---|---:|---:|---:|---:|
| v1 development | e137a189-2643-4ee3-90ac-3b11bc8ed417 | 40 | 103 | 29 | 0.405010 |
| v2 development | 938be519-95bb-4d37-ab02-b229c428d432 | 40 | 0 | 40 | 0.000000 |
| v1 check | f9c567ec-5dc9-489c-ae52-2966c05fc05a | 10 | 0 | 10 | null |
| v2 check | 049197e2-386d-4a74-b9e7-578698130862 | 10 | 0 | 10 | null |

The baseline has G=376, P=103, M=102, C=97. Extraction F1 is 0.425887; joint F1 is 0.405010; correct-gold coverage is 97/376 = 0.257979. Its 29 answer errors are nine invalid outputs and twenty daily-quota errors. Missing, extra and wrong-label IDs are in its saved report. Nothing is dropped from the scheduled denominator.

The live v2 score delta is -0.405010. All forty v2 answers failed on quota, so this is not evidence that quote resolution reduced quality. Both check runs retain null gold-dependent fields, not zero quality scores. The account was contacted at the start of each attempt; after an explicit daily-quota response, the provider circuit breaker records the same sanitized quota error for remaining answers without repeatedly contacting that exhausted quota. These are run attempts, not 100 successful model inferences.

## One targeted improvement

After the full v1 development run finished, its saved rejected outputs were investigated without changing the predictions or gold. On A04 and A07, for example, the model used list positions 0,1,2,... as `occurrence`, although each sentence appeared exactly once. This invalidated the entire answer. Seven rejected answers had this recoverable case. A02 and A12 also contained non-exact Unicode punctuation and remain invalid under v2.

v2 changes only quote location resolution: when an exact quote occurs once in the original answer, Python derives its unambiguous position directly. Repeated quotes still require a valid explicit occurrence index. Altered wording, negative/non-integer indexes, duplicated claims, overlaps, unsupported labels and invalid fact IDs remain errors. No normalization, fuzzy span matching or gold-based repair is used.

v1 retains the original behavior. The v1 and v2 prompt files are identical: the final candidate change is in Python postprocessing, not a prompt change. The earlier provisional clause-audit prompt was replaced after investigating actual baseline failures. Provider, model, data, evaluator, settings and classification behavior are unchanged.

## Controlled replay: additional evidence, not a live v2 run

Because live v2 inference was blocked by quota, `scripts/replay_outputs.py` reprocessed the actual saved v1 model messages through the v2 quote resolver. It makes **zero provider calls**, writes replay predictions before joining development labels, and uses the unchanged scorer on all forty answers and all 376 gold claims. It never changes a model label or supplies gold to inference.

- Recovered answers: A04, A07, A14, A17, A18, A19, A20.
- Replay counts: G=376, P=168, M=167, C=160; 22 answer errors remain.
- Replay extraction F1: 0.613971; replay joint F1: 0.588235.
- Joint F1 delta versus the recorded baseline: +0.183225 (18.32 percentage points).
- All 103 previously accepted claims remain identical. There are 65 newly accepted claims: 63 exact correct-label matches and two exact wrong-label matches. The baseline's one unmatched prediction remains unmatched. No previously correct claim is lost in this replay.

These are controlled postprocessing results on recorded v1 outputs, not an independent live v2 model-quality measurement. They do not replace the required live candidate and final-check predictions. Artifacts are explicitly labeled `recorded_output_replay` under `reports/controlled-replay/` and excluded from the live-run manifest.

## Labeling and extraction issues inspected

The baseline wrongly marked four below-freezing battery-runtime guarantees as supported when the catalogue supplied no temperature guarantee: A06:1432:1621, A13:324:510, A15:306:495 and A16:1423:1613. It also labeled A16:455:618 supported although the sentence reversed the direction of the current-price difference; the reference label is contradicted. Its unmatched prediction is A09:2277:2340. The saved reports retain complete missing/extra/wrong-label records.

These classification issues were documented but not tuned, to keep the candidate to one explained behavior. The replay exposes two additional wrong labels among newly accepted claims; more accepted output does not imply perfect factual reasoning. The main live-run comparison's apparent extraction and labeling regressions are dominated by quota failures, not an observed change in those predictions.

## Checks, ownership and unfinished work

Codex generated the implementation, prompts, tests and documentation, verified real model-requested fact-tool use, executed 81 controlled tests against real PostgreSQL, and checked joined retrieval of the actual live-run records through FastAPI. The fake-provider tests cover structural and failure behavior; they do not substitute for live inference. The human user supplied the repository and Groq credential and requested the provider disclosure. No independent human verification is claimed.

The inherited OpenAI credential was never used. The Groq key is stored only in a permission-restricted, ignored `.env`; it is absent from tracked files. Model/tool evidence excludes authorization headers and credentials. The key was shared in chat and should be rotated.

Two earlier integration attempts were interrupted after discovering Groq JSON/tool incompatibilities and pacing problems; their partial records remain marked failed and are excluded from the four-attempt comparison. The corrected common adapter was fixed before the main v1 baseline and retained for v2. The versions were frozen after both development attempts and before either saved check attempt; see `reports/freeze.json`.

Final-check inputs were loaded by controlled tests and provider-backed attempts, but no final-check gold exists locally and no tuning on final-check quality occurred. This is not claimed as a fully blind benchmark.

Unfinished: rerun all four live evaluations with sufficient quota, obtain real v2 and final-check predictions, and assess the measured live effect and regressions. The reviewer must also decide whether the Groq provider deviation is acceptable. No hosted deployment, authentication, durable recovery, idempotency or UI is provided; these were outside required scope.

Timing is recorded in WORK_LOG.md. Live work stopped at the daily-quota blocker; the process did not wait for tomorrow's quota reset or fabricate successful results.
