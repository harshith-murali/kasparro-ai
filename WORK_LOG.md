# Work log

19 October 2026, Asia/Kolkata.

- Read Assessment.docx and inspected CSV schemas and counts: 50 answers, 132 catalogue facts and 376 development reference sentences.
- Confirmed PostgreSQL 18.4 was installed. Initialized an isolated cluster under `/tmp/kasparro-pgdata`, listening on localhost port 55432 solely for controlled tests.
- Installed the exact dependency versions saved in `requirements.lock` into `.venv`.
- Wrote agent, strict validation, fact tool, evaluator, runner, PostgreSQL schema/storage, FastAPI routes, v1/provisional-v2 prompts and handoff documentation.
- First complete controlled suite: 59 passed. Expanded suite: 67 passed. Final expanded suite: 72 passed. Actual final output is in `reports/tests.txt`. PostgreSQL tests ran against randomly named temporary databases created and dropped by `scripts/test_local.py`.
- The initial attempt to connect to local PostgreSQL from the restricted sandbox failed with an operating-system permission error. The same tests were then run with approved local connection access and passed. Dependency downloads and local Git initialization also required sandbox access.
- No live model requests were made. No inherited provider credential was used. User reported having no keys for the allowed providers and considering Grok. Documented that Grok requires recruiter approval.
- No final-check quality was computed. No Git remote was created and no recruiter message was sent.

Project file creation began at 13:27:39 IST. Reading and setup preceded this; there was no separate stopwatch for those steps. The timestamp below records the final packaging check, not completion of the required live experiment.

Packaging timestamp: 2026-10-19T13:35:11.309318+05:30
