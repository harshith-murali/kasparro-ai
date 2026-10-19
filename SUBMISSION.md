# Submission status

Repository: https://github.com/harshith-murali/kasparro-ai

**Implementation is published. Required live-quality evidence remains incomplete because Groq's daily token quota was exhausted.** Groq was used because the user had no credits for OpenAI, Anthropic or Gemini; this provider deviation is disclosed for the reviewer to assess.

| Requirement | Actual status |
|---|---|
| Agent, live fact-tool execution and strict span validation | Implemented; real Groq traces and controlled tests saved |
| Deterministic evaluator and full error accounting | Implemented and tested |
| FastAPI and PostgreSQL | Implemented; controlled tests and actual run retrieval verified |
| v1/v2 preservation and one targeted change | v1 unchanged; v2 resolves uniquely occurring exact quotes in Python |
| Controlled tests actually run | 81 passed; `reports/tests.txt` |
| v1 development attempt | `reports/e137a189-2643-4ee3-90ac-3b11bc8ed417/report.json`; 11 valid answers, 29 errors |
| v2 development attempt | `reports/938be519-95bb-4d37-ab02-b229c428d432/report.json`; 40 quota errors |
| Frozen v1 check attempt | `reports/f9c567ec-5dc9-489c-ae52-2966c05fc05a/report.json`; 10 quota errors; quality null |
| Frozen v2 check attempt | `reports/049197e2-386d-4a74-b9e7-578698130862/report.json`; 10 quota errors; quality null |
| Real sanitized model/tool exchange | `reports/provider-checks/A01-probe.json` and main baseline A01 trace |
| Main live comparison | `reports/comparison.json`; inconclusive because v2 had no quota |
| Additional controlled replay | `reports/controlled-replay/report.json`; explicitly not a live v2 run |
| Freeze and exact dataset hashes | `reports/freeze.json`, `reports/dataset-hashes.json`; original CSV bytes retained |
| Install, test and run commands | `README.md`, `requirements.lock`, `.env.example` |
| AI assistance, checks and limitations | `ANALYSIS.md`, `WORK_LOG.md` |

The four reports preserve actual provider-backed attempts, not four successful quality runs. Subsequent answers in an explicitly exhausted run are circuit-broken with preserved errors. The offline replay is additional deterministic evidence and must not be presented as one of the required live runs.

Before claiming the assessment complete, obtain enough quota and rerun all four evaluations with the frozen versions/settings. Update the report links and analysis with real outcomes and regressions. Keep the existing failed attempts and distinguish reruns. The hiring team alone scores final checks with private labels. The recruiter supplies the deadline and submission channel; no recruiter message has been sent.
