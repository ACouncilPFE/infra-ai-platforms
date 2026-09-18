#!/bin/bash
# Full platform deploy: AWS infra -> k3s connect -> all workloads -> health check.
# Run from the repo root: ./deploy.sh
#
# Idempotent-ish: safe to re-run. Terraform skips unchanged resources;
# kubectl apply is naturally idempotent.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$REPO_ROOT/terraform"
KEY_PATH="${INFRA_SSH_KEY:-$HOME/infra-ai-platform-key.pem}"

log() { echo -e "\n\033[1;36m==> $1\033[0m"; }
fail() { echo -e "\033[1;31mERROR: $1\033[0m"; exit 1; }

[ -f "$KEY_PATH" ] || fail "SSH key not found at $KEY_PATH. Set INFRA_SSH_KEY=/path/to/key.pem or place it at the default path."

log "1/7 Applying Terraform (this may take a few minutes on first run)"
cd "$TF_DIR"
terraform init -input=false >/dev/null
terraform apply -auto-approve

NODE_IP=$(terraform output -raw node_public_ip)
log "Node IP: $NODE_IP"

log "2/7 Waiting for k3s to finish installing on the node"
for i in $(seq 1 24); do
  if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
      ubuntu@"$NODE_IP" "sudo test -f /etc/rancher/k3s/k3s.yaml" 2>/dev/null; then
    break
  fi
  echo "  ...not ready yet, waiting 10s (attempt $i/24)"
  sleep 10
done

log "3/7 Fetching kubeconfig and pointing kubectl at the cluster"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
  ubuntu@"$NODE_IP":/etc/rancher/k3s/k3s.yaml "$TF_DIR/kubeconfig.yaml"
sed -i "s/127.0.0.1/$NODE_IP/" "$TF_DIR/kubeconfig.yaml"
export KUBECONFIG="$TF_DIR/kubeconfig.yaml"

kubectl wait --for=condition=ready node --all --timeout=120s
log "Node is Ready"

log "4/7 Deploying base platform (inference-api)"
kubectl apply -f "$REPO_ROOT/k8s/"

if [ "${WITH_MONITORING:-}" = "1" ]; then
  log "4b/7 Deploying Prometheus + Grafana (WITH_MONITORING=1 set)"
  if ! helm repo list 2>/dev/null | grep -q prometheus-community; then
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  fi
  helm repo update >/dev/null
  helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --set prometheus.prometheusSpec.resources.requests.memory=300Mi \
    --set prometheus.prometheusSpec.resources.requests.cpu=100m \
    --set grafana.resources.requests.memory=150Mi \
    --set alertmanager.enabled=false \
    --set prometheus.prometheusSpec.retention=6h \
    --timeout 10m
  echo "  Grafana password: kubectl get secret --namespace monitoring -l app.kubernetes.io/component=admin-secret -o jsonpath='{.items[0].data.admin-password}' | base64 --decode"
  echo "  Grafana access:   kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
fi

log "5/7 Deploying mcp-agent workloads (RBAC, mcp-server, ollama)"
if [ "${WITH_MONITORING:-}" = "1" ]; then
  echo "  NOTE: monitoring + ollama + mcp-agent together need real headroom —"
  echo "  t3.medium or smaller WILL likely repeat the OOM/API-timeout issue"
  echo "  this project hit before. t3.large minimum, t3.xlarge if it's flaky."
fi
cd "$REPO_ROOT/mcp-agent"
kubectl apply -f k8s/rbac.yaml

# GHCR pull secret — only created if it doesn't already exist, since this
# script has no way to know your token. Create it once manually:
#   kubectl create secret docker-registry ghcr-secret \
#     --docker-server=ghcr.io --docker-username=<you> \
#     --docker-password=<token> --docker-email=<any-email>
if ! kubectl get secret ghcr-secret >/dev/null 2>&1; then
  echo "  WARNING: ghcr-secret not found. mcp-server/agent-orchestrator pulls will fail"
  echo "  until you create it (see comment in this script for the command)."
fi

kubectl apply -f k8s/mcp-server.yaml
kubectl apply -f k8s/ollama.yaml

log "6/7 Waiting for ollama, then pulling the model (skips if already pulled)"
kubectl wait --for=condition=ready pod -l app=ollama --timeout=180s
kubectl exec deploy/ollama -- ollama list | grep -q llama3.2:3b || \
  kubectl exec deploy/ollama -- ollama pull llama3.2:3b

log "7/7 Deploying agent-orchestrator"
kubectl apply -f k8s/agent-orchestrator.yaml

echo
log "Deploy complete. Current pod status:"
kubectl get pods
echo
echo "inference-api: curl http://$NODE_IP:30080/health"
echo "agent-orchestrator: curl -X POST http://$NODE_IP:30081/run -H 'Content-Type: application/json' -d '{\"task\": \"...\"}'"
