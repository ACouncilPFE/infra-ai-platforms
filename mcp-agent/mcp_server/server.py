"""
MCP server exposing two tools over HTTP:

1. get_cluster_pods — queries the *actual* k3s cluster this project runs on
   for live pod status. This is deliberately real, not mocked: it proves
   the MCP layer can reach into real infrastructure, not just toy data.
2. search_docs — simple keyword search over a small local knowledge base.

Uses the official `mcp` Python SDK with the streamable-HTTP transport, so
this can run as a normal container behind a Service — the same deployment
pattern as inference-api, not a special MCP-only setup.
"""
from mcp.server.fastmcp import FastMCP
from kubernetes import client, config

mcp = FastMCP("infra-platform-tools")

# --- Tiny local knowledge base for the search_docs tool ---
DOCS = {
    "k3s": "k3s is a lightweight, CNCF-certified Kubernetes distribution built by Rancher/SUSE. It bundles the control plane into a single binary and swaps etcd for SQLite by default, making it practical to run on small single-node instances while remaining fully API-compatible with standard Kubernetes.",
    "terraform": "Terraform is HashiCorp's infrastructure-as-code tool. It uses a declarative HCL configuration to provision and track cloud resources, storing their state so future runs can compute a diff (plan) before applying changes.",
    "mcp": "The Model Context Protocol (MCP) is a standard that lets an AI model or agent discover and call external tools and data sources in a structured way, separate from the model's own inference.",
    "prometheus": "Prometheus is a metrics collection and alerting system that scrapes numeric time-series data from configured targets on a schedule and stores it for querying via PromQL.",
}


@mcp.tool()
def get_cluster_pods(namespace: str = "default") -> str:
    """Get the current status of all pods in a given Kubernetes namespace
    on the live cluster this platform runs on."""
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    v1 = client.CoreV1Api()
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


@mcp.tool()
def search_docs(query: str) -> str:
    """Search a small local knowledge base of infra/AI terms and return
    the matching explanation, if any."""
    query_lower = query.lower()
    for key, explanation in DOCS.items():
        if key in query_lower:
            return explanation
    return f"No local documentation found for '{query}'. Known terms: {', '.join(DOCS.keys())}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
