"""Tool server exposing infra helpers over HTTP for the orchestrator.

The orchestrator calls /tools/<tool_name> with JSON payloads and expects
{"result": "..."}. This implementation keeps that contract explicit so the
service boots reliably in-cluster without MCP transport/version coupling.
"""
import os

import uvicorn
from fastapi import FastAPI
from kubernetes import client, config
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="infra-platform-tools", version="0.1.0")
_instrumentator = Instrumentator().instrument(app)


@app.on_event("startup")
async def _expose_metrics() -> None:
    _instrumentator.expose(app)

# --- Tiny local knowledge base for the search_docs tool ---
DOCS = {
    "k3s": "k3s is a lightweight, CNCF-certified Kubernetes distribution built by Rancher/SUSE. It bundles the control plane into a single binary and swaps etcd for SQLite by default, making it practical to run on small single-node instances while remaining fully API-compatible with standard Kubernetes.",
    "terraform": "Terraform is HashiCorp's infrastructure-as-code tool. It uses a declarative HCL configuration to provision and track cloud resources, storing their state so future runs can compute a diff (plan) before applying changes.",
    "mcp": "The Model Context Protocol (MCP) is a standard that lets an AI model or agent discover and call external tools and data sources in a structured way, separate from the model's own inference.",
    "prometheus": "Prometheus is a metrics collection and alerting system that scrapes numeric time-series data from configured targets on a schedule and stores it for querying via PromQL.",
    "grafana": "Grafana is a visualization and dashboard platform often paired with Prometheus to explore metrics, build dashboards, and configure alerts from time-series data sources.",
}

_KUBE_CONFIG_LOADED = False


def _ensure_kube_config_loaded() -> None:
    global _KUBE_CONFIG_LOADED
    if _KUBE_CONFIG_LOADED:
        return

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    _KUBE_CONFIG_LOADED = True


def _core_v1_api() -> client.CoreV1Api:
    _ensure_kube_config_loaded()
    return client.CoreV1Api()


def _apps_v1_api() -> client.AppsV1Api:
    _ensure_kube_config_loaded()
    return client.AppsV1Api()


def get_cluster_pods(namespace: str = "default") -> str:
    """Get the current status of all pods in a given Kubernetes namespace
    on the live cluster this platform runs on."""
    v1 = _core_v1_api()
    pods = v1.list_namespaced_pod(namespace=namespace)

    if not pods.items:
        return f"No pods found in namespace '{namespace}'."

    lines = [f"Pods in namespace '{namespace}':"]
    for pod in pods.items:
        status = pod.status.phase
        ready = sum(1 for c in (pod.status.container_statuses or []) if c.ready)
        total = len(pod.status.container_statuses or [])
        lines.append(f"  - {pod.metadata.name}: {status} ({ready}/{total} containers ready)")
    return "\n".join(lines)


def get_cluster_services(namespace: str = "default") -> str:
    """Get the services currently exposed in a Kubernetes namespace."""
    v1 = _core_v1_api()
    services = v1.list_namespaced_service(namespace=namespace)

    if not services.items:
        return f"No services found in namespace '{namespace}'."

    lines = [f"Services in namespace '{namespace}':"]
    for service in services.items:
        ports = ", ".join(
            f"{port.port}/{port.protocol} -> {port.target_port}"
            for port in (service.spec.ports or [])
        ) or "no ports"
        cluster_ip = service.spec.cluster_ip or "<none>"
        service_type = service.spec.type or "ClusterIP"
        lines.append(
            f"  - {service.metadata.name}: {service_type} "
            f"(cluster IP: {cluster_ip}, ports: {ports})"
        )
    return "\n".join(lines)


def get_cluster_deployments(namespace: str = "default") -> str:
    """Get deployment rollout and replica health in a namespace."""
    apps_v1 = _apps_v1_api()
    deployments = apps_v1.list_namespaced_deployment(namespace=namespace)

    if not deployments.items:
        return f"No deployments found in namespace '{namespace}'."

    lines = [f"Deployments in namespace '{namespace}':"]
    for deployment in deployments.items:
        desired = deployment.spec.replicas or 0
        ready = deployment.status.ready_replicas or 0
        updated = deployment.status.updated_replicas or 0
        available = deployment.status.available_replicas or 0
        lines.append(
            f"  - {deployment.metadata.name}: desired={desired}, "
            f"updated={updated}, ready={ready}, available={available}"
        )
    return "\n".join(lines)


def search_docs(query: str) -> str:
    """Search a small local knowledge base of infra/AI terms and return
    the matching explanation, if any."""
    query_lower = query.lower()
    for key, explanation in DOCS.items():
        if key in query_lower:
            return explanation
    return f"No local documentation found for '{query}'. Known terms: {', '.join(DOCS.keys())}"


class ClusterPodsRequest(BaseModel):
    namespace: str = "default"


class ClusterServicesRequest(BaseModel):
    namespace: str = "default"


class ClusterDeploymentsRequest(BaseModel):
    namespace: str = "default"


class SearchDocsRequest(BaseModel):
    query: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tools/get_cluster_pods")
def get_cluster_pods_tool(req: ClusterPodsRequest) -> dict:
    return {"result": get_cluster_pods(req.namespace)}


@app.post("/tools/get_cluster_services")
def get_cluster_services_tool(req: ClusterServicesRequest) -> dict:
    return {"result": get_cluster_services(req.namespace)}


@app.post("/tools/get_cluster_deployments")
def get_cluster_deployments_tool(req: ClusterDeploymentsRequest) -> dict:
    return {"result": get_cluster_deployments(req.namespace)}


@app.post("/tools/search_docs")
def search_docs_tool(req: SearchDocsRequest) -> dict:
    return {"result": search_docs(req.query)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
