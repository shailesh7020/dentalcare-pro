# Contributing to DentalCare Pro

Thank you for your interest in contributing to **DentalCare Pro**, an enterprise dental practice management platform.

---

## Code of Conduct
This project and everyone participating in it is governed by the DentalCare Pro [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## Development Workflow

1. **Fork & Branch**: Create a feature branch from `main`:
   ```bash
   git checkout -b feature/clinical-enhancement
   ```
2. **Coding Standards**:
   - Backend: Format and lint with `ruff check app/ tests/`.
   - Frontend: Verify TypeScript types and run `npx vitest run`.
   - Mobile: Follow Clean Architecture patterns in `apps/mobile/lib/`.
3. **Testing**:
   - Every bugfix or feature requires associated automated tests.
   - Run the full test suite: `pytest tests/ -q`.
4. **Pull Requests**:
   - Ensure all CI/CD checks pass.
   - Provide a concise description of the changes, clinical rationale, and screenshots for UI updates.
