# Submission readiness

**Not ready for final submission: the four full live runs and measured comparison are still in progress.**

| Requirement | Status |
|---|---|
| Python agent, real function-calling implementation, span/output validation | Implemented; controlled tests and a real Groq tool probe passed |
| Deterministic evaluator and error accounting | Implemented and tested |
| Thin FastAPI service and PostgreSQL storage | Implemented and tested against real PostgreSQL |
| v1 and v2 prompts | Present; v2 is provisional pending baseline diagnosis |
| Controlled test output | `reports/tests.txt`; actual execution, not merely written tests |
| v1 development live report | In progress with disclosed Groq provider deviation |
| v2 development live report | Not run; requires baseline inspection first |
| Frozen v1/v2 final-check live reports | Not run; freeze occurs after development runs |
| Actual sanitized live model/tool exchange | Real probe: `reports/provider-checks/A01-probe.json` |
| Measured improvement/regression explanation | Pending live runs |
| Issued CSVs and hashes | Original files retained; `reports/dataset-hashes.json` |
| Secret-free environment example and exact dependency versions | `.env.example`, `requirements.lock` |
| Git repository | Origin configured: https://github.com/harshith-murali/kasparro-ai; publication status will be updated after push |
| Human ownership and AI assistance disclosure | `ANALYSIS.md`; human checks still pending |

Follow README.md in order. Preserve all four reports and traces, update ANALYSIS.md with actual results, publish this repository without secrets, and share an accessible repository URL through the recruiter's supplied channel. Never replace missing runs with fake-provider outputs or invented metrics.
