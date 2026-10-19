from uuid import UUID
from fastapi import FastAPI, HTTPException
from .agent import Agent, AgentError, create_provider, Settings
from .models import ClassifyInput, RunInput
from .runner import run_evaluation
from .store import Store
from .data import Catalogue


def create_app(agent=None, store=None):
    app = FastAPI(title="Kasparro factual claim assessment")
    def dependencies():
        nonlocal agent, store
        if agent is None:
            settings = Settings.from_env()
            agent = Agent(create_provider(settings), settings=settings)
        return agent, store

    @app.post("/classify")
    def classify(request: ClassifyInput):
        try:
            if request.brand_id not in Catalogue().by_brand:
                raise AgentError("unknown_brand", "Unknown primary brand")
            worker, _ = dependencies()
            return worker.classify(request.model_dump(exclude={"agent_version"}), request.agent_version)
        except AgentError as exc:
            status = 404 if exc.kind == "unknown_brand" else 504 if exc.kind == "timeout" else 502
            raise HTTPException(status, detail={"type": exc.kind, "message": exc.message}) from None
        except Exception:
            raise HTTPException(502, detail={"type": "configuration_error", "message": "Service is not configured"}) from None

    @app.post("/evaluation-runs", status_code=201)
    def evaluate(request: RunInput):
        try:
            worker, database = dependencies()
            report = run_evaluation(worker, database or Store(), request.agent_version, request.split)
            return {k: report[k] for k in ("run_id", "status", "scores", "metadata")}
        except Exception:
            raise HTTPException(503, detail={"type": "infrastructure_error", "message": "Run failed; partial evidence is preserved"}) from None

    @app.get("/evaluation-runs/{run_id}")
    def get_run(run_id: UUID):
        try:
            database = store or Store()
            result = database.get(str(run_id))
        except Exception:
            raise HTTPException(503, detail={"type": "database_error", "message": "Database unavailable"}) from None
        if result is None:
            raise HTTPException(404, detail="Run not found")
        return result
    return app


app = create_app()
