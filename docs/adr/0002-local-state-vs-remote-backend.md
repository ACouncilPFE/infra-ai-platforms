# ADR 0002: Local Terraform state (with remote backend documented, not enabled)

## Status
Accepted for this portfolio project; would be rejected for a team environment.

## Context
Terraform state can be stored locally (a file on disk) or remotely (S3 +
DynamoDB lock table, Terraform Cloud, etc). Remote state with locking is the
standard for any environment with more than one operator, because local
state has no locking and risks corruption or drift if two people run
`apply` concurrently.

## Decision
This repo uses local state, since it has exactly one operator (me) and is
torn down/rebuilt frequently rather than persisted long-term.

The S3 backend configuration is left commented out in `provider.tf` rather
than omitted, specifically so it's visible in a code review or interview
walkthrough that I know the difference and made a deliberate choice — not
that I don't know remote state exists.

## Consequences
- Simpler to run from a laptop with no pre-existing S3 bucket dependency.
- Not safe for team use as-is. If this repo ever supports more than one
  contributor, the first change should be enabling the S3 backend with
  DynamoDB locking before any other infra work.
