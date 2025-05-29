## Branching and Release Workflow (Best Practices)

- The `main` branch always contains the best working, stable, and production-ready code.
- All new features, bugfixes, or experimental work should be done in separate branches (e.g., `feature/xyz`, `experiment/v1.4.0-semi-working`).
- Only merge a feature or experiment branch into `main` after it is fully tested and confirmed to work as intended.
- Use tags (e.g., `v1.4.0`) to mark stable releases on the `main` branch.
- Avoid tagging experimental or semi-working versions as official releases unless needed for reference.
- Never push untested or unstable code directly to `main`.
- Always ensure `main` is deployable and represents the best working state.

This workflow ensures stability, traceability, and safe collaboration for all contributors.
