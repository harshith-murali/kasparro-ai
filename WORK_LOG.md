# Work log

19 October 2026, Asia/Kolkata. The initial-build entries below preceded the Groq credential and repository follow-up.

- Read Assessment.docx and inspected CSV schemas and counts: 50 answers, 132 catalogue facts and 376 development reference sentences.
- Confirmed PostgreSQL 18.4 was installed. Initialized an isolated cluster under `/tmp/kasparro-pgdata`, listening on localhost port 55432 solely for controlled tests.
- Installed the exact dependency versions saved in `requirements.lock` into `.venv`.
- Wrote agent, strict validation, fact tool, evaluator, runner, PostgreSQL schema/storage, FastAPI routes, v1/provisional-v2 prompts and handoff documentation.
- First complete controlled suite: 59 passed. Expanded suite: 67 passed. Final expanded suite: 72 passed. Actual final output is in `reports/tests.txt`. PostgreSQL tests ran against randomly named temporary databases created and dropped by `scripts/test_local.py`.
- The initial attempt to connect to local PostgreSQL from the restricted sandbox failed with an operating-system permission error. The same tests were then run with approved local connection access and passed. Dependency downloads and local Git initialization also required sandbox access.
- No live model requests were made. No inherited provider credential was used. I had no keys for the allowed providers and considered Grok. Documented that Grok requires recruiter approval.
- No final-check quality was computed. No Git remote was created and no recruiter message was sent.

Project file creation began at 13:27:39 IST. Reading and setup preceded this; there was no separate stopwatch for those steps. The timestamp below records the final packaging check, not completion of the required live experiment.

Packaging timestamp: 2026-10-19T13:35:11.309318+05:30


## Groq continuation

- Configured GitHub origin and Groq key, using Groq with lack-of-credits explanation in README.
- Added Groq via the OpenAI-compatible API, separate tool/final JSON phases, low reasoning effort and token-header pacing. No inherited OpenAI credential was used.
- Validated the Groq key and a real A01 tool exchange returning nine accepted claims. Saved the sanitized exchange.
- Preserved two interrupted integration attempts as failed runs, then started the full baseline using the corrected common adapter. These failed attempts are not the main quality comparison.
- Expanded controlled suite: 75 passed against a real isolated PostgreSQL database.
- Configured the repository remote origin. `.env` is ignored and permission-restricted; tracked-file scanning found no copy of the credential.

## Final experiment outcomes

- Main v1 development completed all 40 answer outcomes: 103 accepted claims; 9 invalid-output errors and 20 daily-quota errors; G=376, M=102, C=97; joint F1 0.405010.
- Inspected all nine rejected outputs. Seven had exact unique quotes with incorrect model occurrence counters. Implemented only v2 unique-quote location resolution; v1 behavior and both identical prompts are preserved.
- Final controlled suite: 81 passed. New checks verify preserved v1 rejection, unique-quote recovery in v2, and continued rejection of altered Unicode, duplicates and ambiguous repeated quotes.
- Controlled replay of recorded baseline messages recovered seven answers, 65 claims and 63 correct exact matches; joint F1 0.588235. Replay made zero provider requests and is explicitly not live v2 evidence.
- The live v2 development attempt produced 40 daily-quota error outcomes. Froze both versions after development attempts, then saved both check attempts with 10 daily-quota errors each and null quality scores. One premature freeze command was correctly blocked while v2 was still processing; no check requests passed the guard at that time.
- All four attempts preserve 100 terminal answer rows. Required live quality is incomplete; the main live comparison is confounded by quota. No successful candidate/check outputs or score gain were invented.
- Published the implementation and requested Groq disclosure to the supplied GitHub repository. Final update contains all attempts, controlled replay, actual test output and explicit limitations.

Final evidence packaging timestamp: 2026-10-19T14:23:24.508686+05:30

## Replacement-key retry

- User supplied a replacement Groq credential; updated only the ignored, permission-restricted `.env`. A minimal inference check succeeded.
- Automatic approval review initially blocked the run because its own usage limit was reached. The user requested a retry; it executed successfully.
- Verified unchanged freeze and database access, then reran frozen v1 check: a6df95a1-f62f-40ad-b7cb-b85c4f44d7c8. A41 produced nine validated claims; A42–A50 have daily-quota errors. Check quality fields remain null.
- The replacement key did not provide enough daily quota to resume the full evaluation. No further quota-exhausted model calls were scheduled. Original attempts remain retained.
- No source changes or new test execution were needed; the latest controlled test result remains 81 passed.

Retry evidence timestamp: 2026-10-19T18:30:22.013762+05:30
