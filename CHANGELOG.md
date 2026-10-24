# Changelog

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
- MIT License, README with architecture diagram and API reference
- Portfolio.json metadata for portfolio tracking
