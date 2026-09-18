"""
A minimal multi-agent workflow: Planner -> Researcher -> Writer.

Deliberately built on a thin model_backend abstraction (see
model_backend.py) rather than a heavier framework (LangGraph, CrewAI), and
deliberately backend-agnostic — the same Planner/Researcher/Writer shape
runs identically against Claude or a local Ollama model, controlled by the
MODEL_BACKEND env var. Nothing in this file needs to change to switch.

The Researcher agent is the one that actually calls out to the MCP
server's tools (get_cluster_pods, search_docs) via a simple HTTP client.
"""
import os
import httpx

from agents.model_backend import call_model

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://mcp-server:8000")


def call_mcp_tool(tool_name: str, **kwargs) -> str:
    """Call a tool on the MCP server over its streamable-HTTP endpoint."""
    try:
        resp = httpx.post(
            f"{MCP_SERVER_URL}/tools/{tool_name}",
            json=kwargs,
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json().get("result", str(resp.json()))
    except Exception as e:
        return f"[tool call failed: {e}]"


def planner_agent(task: str) -> str:
    """Breaks the task down into what information is needed."""
    prompt = (
        f"You are a planning agent. Given this task, list which of "
        f"these two tools would help answer it, and why, in 2-3 "
        f"sentences: get_cluster_pods (live pod status from a "
        f"Kubernetes cluster), search_docs (definitions of infra/AI "
        f"terms like k3s, terraform, mcp, prometheus).\n\nTask: {task}"
    )
    return call_model(prompt, max_tokens=300)


def researcher_agent(task: str, plan: str) -> str:
    """Decides which tool(s) to actually call based on the plan, calls them,
    and returns the raw findings."""
    findings = []

    if "cluster" in plan.lower() or "pod" in plan.lower():
        findings.append("get_cluster_pods result:\n" + call_mcp_tool("get_cluster_pods", namespace="default"))

    if "search_docs" in plan.lower() or "term" in plan.lower() or "definition" in plan.lower():
        for term in ["k3s", "terraform", "mcp", "prometheus"]:
            if term in task.lower():
                findings.append(f"search_docs('{term}') result:\n" + call_mcp_tool("search_docs", query=term))

    if not findings:
        findings.append("No tool calls were needed for this task based on the plan.")

    return "\n\n".join(findings)


def writer_agent(task: str, findings: str) -> str:
    """Produces the final answer from the researcher's findings."""
    prompt = (
        f"You are a writing agent. Using ONLY the findings below, "
        f"write a clear, concise answer to the original task.\n\n"
        f"Task: {task}\n\nFindings:\n{findings}"
    )
    return call_model(prompt, max_tokens=500)


def run_agent_workflow(task: str) -> dict:
    """Runs the full Planner -> Researcher -> Writer pipeline and returns
    every stage's output, useful for demoing the mechanism, not just the
    final answer."""
    plan = planner_agent(task)
    findings = researcher_agent(task, plan)
    answer = writer_agent(task, findings)

    return {
        "task": task,
        "plan": plan,
        "findings": findings,
        "answer": answer,
    }
