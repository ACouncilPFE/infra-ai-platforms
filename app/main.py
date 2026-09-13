"""
Placeholder inference API.

Deliberately simple — the point of this project is the platform around it
(provisioning, CI/CD, observability), not the model. Swap the /predict
logic for a real model call when you're ready to extend this.
"""
from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI(title="Inference API", version="0.1.0")

START_TIME = time.time()


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    input_length: int
    prediction: str
    latency_ms: float


@app.get("/health")
def health():
    """Used by the k8s liveness/readiness probes."""
    return {"status": "ok", "uptime_seconds": time.time() - START_TIME}


@app.get("/metrics")
def metrics():
    """Minimal metrics endpoint — swap for prometheus_client if you extend this."""
    return {"uptime_seconds": time.time() - START_TIME}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    start = time.time()
    # Placeholder "prediction" — replace with a real model call.
    prediction = "positive" if len(req.text) % 2 == 0 else "negative"
    latency = (time.time() - start) * 1000
    return PredictResponse(
        input_length=len(req.text),
        prediction=prediction,
        latency_ms=round(latency, 3),
    )
