# EventRadar P0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a read-only real-source crypto event pipeline with observable routing and dashboard presentation.

**Architecture:** Dockerized PostgreSQL/Redis support FastAPI bounded modules. Public RSS is the first live source; Binance confirms ticker market context.

**Tech Stack:** Python 3.12, FastAPI, PostgreSQL, Redis, Docker Compose, Next.js/TypeScript.

## Global Constraints

Read-only integrations only. No credentials in source control. P0 adapters must disclose unavailable credential-gated integrations.

### Task 1: Local service topology
- [ ] Add PostgreSQL and Redis to Docker Compose with health checks and environment-only credentials.

### Task 2: Normalized event contract
- [ ] Add event type, direction, volatility, severity, confidence, correlation ID, and summaries.
- [ ] Classify real RSS items through this contract and persist/display the result.

### Task 3: Alert routing and web migration
- [ ] Make delivery idempotent by severity; keep unavailable destinations disabled.
- [ ] Add a Next.js dashboard consuming API/SSE updates.
