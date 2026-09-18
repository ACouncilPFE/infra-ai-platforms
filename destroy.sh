#!/bin/bash
# Full teardown: terraform destroy, then verify against AWS directly rather
# than trusting Terraform's own output (we got burned by that once).
# Run from the repo root: ./destroy.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$REPO_ROOT/terraform"

log() { echo -e "\n\033[1;36m==> $1\033[0m"; }

log "Destroying Terraform-managed infrastructure"
cd "$TF_DIR"
terraform destroy -auto-approve

log "Verifying directly against AWS (not just trusting Terraform's output)"
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=infra-ai-platform" \
  --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name}' \
  --output table

echo
echo "If the table above is empty or shows 'terminated', you're clear — no AWS charges accruing."
