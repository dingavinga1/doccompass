# Phase 7: Frontend Setup

## Goal
Deliver a usable dashboard for ingestion management and documentation browsing with clear status visibility and section exploration.

## Inputs From Master Plan
- Dashboard domain (`app.domain`)
- Features: ingestion listing, status tracking, start/stop controls, tree view, manual re-ingestion
- Minimal monospace retro style

## Scope
- Frontend application bootstrap and routing
- API client integration for ingestion and documentation endpoints
- Core screens and interaction flows
- Basic UX states: loading, empty, error, success
- Build and runtime containerization

## Development Plan
1. Initialize frontend app (React + optional Tailwind) with consistent design tokens.
2. Build API client layer with typed request/response handling.
3. Create pages/components:
   - ingestion list/status dashboard
   - ingestion trigger form (URL, depth, include/exclude patterns)
   - stop ingestion action
   - documentation section tree explorer
   - section content viewer
4. Add polling or refresh controls for ingestion progress.
5. Implement lightweight notification/toast pattern for user actions.
6. Add frontend Dockerfile and Compose integration.
7. Add accessibility basics (keyboard navigation, labels, focus states).
8. Add production build validation and static asset serving config.

## Unit Testing Plan
1. Component rendering tests for each major screen.
2. API client tests with mocked backend responses.
3. State management tests for ingestion lifecycle transitions.
4. Interaction tests for start/stop ingestion controls.
5. Error-state tests for network failure and invalid form input.

## Manual Testing Plan
1. Start full stack and open dashboard in browser.
2. Create an ingestion job and observe live status updates.
3. Stop an active job and verify UI and backend state alignment.
4. Open documentation tree and navigate to deep section content.
5. Validate behavior on mobile and desktop viewport widths.
6. Verify accessibility checks with keyboard-only navigation.

## Exit Criteria
- Dashboard supports core operational flows without API client hacks.
- UI state remains consistent with backend job status.
- Frontend build and container run successfully in Compose.

## Deliverables
- Frontend app scaffold and components
- API integration layer
- Frontend tests
- Frontend Docker/runtime setup
