# ADR 0001: k3s on a single EC2 node instead of managed EKS

## Status
Accepted

## Context
This project needs real Kubernetes to be a credible demonstration of
container orchestration skill, but it also needs to run entirely within the
AWS Free Tier for a portfolio project with no ongoing budget.

Managed EKS bills its control plane at a flat hourly rate regardless of free
tier status — roughly $70+/month before any worker nodes are added. That's
not viable for something meant to be spun up and torn down repeatedly for
demos and interviews.

## Decision
Run k3s (a lightweight, CNCF-certified Kubernetes distribution) as a
single-node cluster on one free-tier-eligible EC2 instance.

## Consequences
- **Pro:** Zero control-plane cost. Same `kubectl` interface, same manifest
  format as EKS — the deployment/service YAML in this repo is portable to a
  managed cluster with no changes.
- **Pro:** Fast to provision and destroy — good for repeated interview demos.
- **Con:** No real high availability — this is explicitly a demo/learning
  environment, not a production topology. In a real production job, EKS (or
  self-managed HA control plane) would be the correct choice, and that
  trade-off is one I'd flag explicitly in an interview rather than let go
  unstated.
- **Con:** No managed node autoscaling — replicas are fixed at 2 in the
  Deployment spec rather than driven by a Horizontal Pod Autoscaler against
  cluster capacity.

## What I'd change for production
Swap `terraform/ec2.tf` + `user_data.sh.tpl` for an `aws_eks_cluster` module,
move node provisioning to managed node groups or Fargate profiles, and add
Cluster Autoscaler. The Kubernetes manifests in `k8s/` would not need to
change.
