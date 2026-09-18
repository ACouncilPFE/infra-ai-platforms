# MCP + multi-agent demo

A second workload on the same platform as the main `inference-api` project
— reuses the existing Terraform-provisioned EC2/k3s cluster rather than
needing separate infrastructure. This piece demonstrates two concepts that
are distinct from a plain inference API:

- **MCP (Model Context Protocol)**: a standard way for an AI agent to
  discover and call external tools. The MCP server here (`mcp_server/`)
  exposes two tools: `get_cluster_pods` (queries the *live* k3s cluster
  this project runs on — real infra, not mocked data) and `search_docs`
  (keyword lookup over a small local knowledge base).
- **Multi-agent orchestration**: a task is handled by three agents in
  sequence — a Planner decides what information is needed, a Researcher
  calls the MCP tools to gather it, and a Writer produces the final
  answer. See `agents/orchestrator.py` for the full, readable mechanism —
  built on the plain Anthropic SDK rather than a heavier framework so
  every step is visible.

## Architecture

```
POST /run {"task": "..."}
        |
        v
  agent-orchestrator (FastAPI)
        |
        v
  Planner agent -> Researcher agent -> Writer agent
                        |
                        v
              calls MCP server tools over HTTP
                        |
                        v
              mcp-server (get_cluster_pods, search_docs)
                        |
                        v
              Kubernetes API (live pod status)
```

## Running it

Requires an `ANTHROPIC_API_KEY` from console.anthropic.com — this calls a
real model, unlike the placeholder logic in the main `inference-api`.

**Build and push both images** (same CI/CD pattern as the main project —
see `.github/workflows/ci-cd.yml` for how to extend it to build these too):

```bash
docker build -t ghcr.io/acouncilpfe/mcp-server:latest -f mcp_server/Dockerfile .
docker push ghcr.io/acouncilpfe/mcp-server:latest

docker build -t ghcr.io/acouncilpfe/agent-orchestrator:latest .
docker push ghcr.io/acouncilpfe/agent-orchestrator:latest
```

**Create the API key secret on the cluster:**

```bash
kubectl create secret generic anthropic-api-key --from-literal=api-key=YOUR_KEY_HERE
```

**Deploy:**

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/mcp-server.yaml
kubectl apply -f k8s/agent-orchestrator.yaml
```

**Try it:**

```bash
curl -X POST http://<node-ip>:30081/run \
  -H "Content-Type: application/json" \
  -d '{"task": "What pods are currently running in the cluster, and what is k3s?"}'
```

The response includes every stage's output (`plan`, `findings`, `answer`)
so you can see the mechanism working, not just the final text — useful for
a demo or interview walkthrough.
