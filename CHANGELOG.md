# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-24

### Added
- FastAPI backend with health, models, chat, and cache API endpoints
- React + TypeScript + Vite frontend with dashboard, models, chat, and cache pages
- Docker Compose stack with backend, frontend, and Keycloak services
- Keycloak realm configuration with OIDC roles (viewer, operator, admin)
- Backend tests for health, models, and cache endpoints
- Frontend tests for App component rendering
- CI workflow for backend pytest and frontend build/test
- Streaming chat completion endpoint (SSE) with realistic token-by-token simulation
- Chat API tests (3 tests) covering streaming and non-streaming completions
- All 11 backend tests and 3 frontend tests passing
- Portfolio.json metadata for portfolio tracking
