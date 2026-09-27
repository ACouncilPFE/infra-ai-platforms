"""
FastAPI wrapper around the multi-agent workflow — same deployment shape as
inference-api (a container behind a Service), so it reuses everything you
already built (Terraform, k3s, CI/CD) rather than needing new infrastructure.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from agents.orchestrator import run_agent_workflow

app = FastAPI(title="Multi-agent MCP demo", version="0.1.0")
_instrumentator = Instrumentator().instrument(app)


@app.on_event("startup")
async def _expose_metrics() -> None:
    _instrumentator.expose(app)


class TaskRequest(BaseModel):
    task: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(req: TaskRequest):
    return run_agent_workflow(req.task)
