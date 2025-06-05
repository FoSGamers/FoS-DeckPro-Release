> **GOLD STANDARD SUMMARY & CHECKLIST**
>
> This project follows a strict, privacy-safe, and automated workflow. Use this summary and checklist to ensure every project is 100% clean, safe, and compliant:
>
> ## Summary
> - Only develop on `personal-dev` or `feature/*` branches. Never commit to `main` or release branches.
> - All personal files go in `user_private/` (in `.gitignore`). Never commit personal files to public branches.
> - Never commit build artifacts or large files (e.g., `dist/`, `build/`, `*.zip`, `*.pkg`, `*.app`, `*.spec`, `*.dmg`, `*.exe`, `*.bin`, `*.tar.gz`, `*.whl`, `*.egg`, `*.pyc`, `__pycache__/`). Always add these to `.gitignore` and clean them from git history.
> - Use the provided scripts for feature, release, onboarding, and cleaning.
> - CI/CD and branch protection block unsafe merges and releases.
> - All code is modular, documented, and tested. All changes update the changelog and docs.
> - All PRs and issues use the provided templates and checklists.
>
> ## Checklist
> - [ ] All personal files are in `user_private/` and listed in `.gitignore`.
> - [ ] All build artifacts and large files are in `.gitignore` and **never** committed.
> - [ ] No build artifacts or large files are present in git history (use `git filter-repo` if needed).
> - [ ] All code is modular, documented, and tested (with docstrings and unit tests).
> - [ ] All configuration and constants are centralized.
> - [ ] All features are independently enable/disable-able.
> - [ ] All UI/UX follows a consistent style guide.
> - [ ] All error handling is user-friendly and provides safe fallbacks.
> - [ ] Every code change is accompanied by a test and documentation update.
> - [ ] Changelog is updated for every release or significant change.
> - [ ] All scripts (`start_feature.sh`, `finish_release.sh`, `onboarding.sh`, `clean_for_release.sh`) are present and used.
> - [ ] Onboarding script is added to your shell profile for reminders.
> - [ ] GitHub Actions for release hygiene and old release cleanup are enabled.
> - [ ] Branch protection rules are set for `main` and release branches.
> - [ ] All PRs and issues use the provided templates and checklists.
> - [ ] All documentation (`README.md`, `RELEASE.md`, `CONTRIBUTING.md`, `PROJECT_WORKFLOW_TEMPLATE.md`) is up to date and explicit.
> - [ ] No secrets, credentials, or sensitive data are ever committed.
> - [ ] All contributors are aware of and follow these rules.

## Code Commenting and Layman Description Rule for All Project Rule Files

All files that contain project rules—including this file, .cursor files, .github workflows, and any configuration or automation files—must explicitly state and enforce the requirement that all code must be clearly commented, with layman descriptions in code blocks where possible. This ensures that anyone, regardless of technical background, can understand the logic, purpose, and workflow of every part of the project.

# Changelog

## [v1.6.0] - 2024-06-05

### Public Release: Gold-Standard License & Trial System
- All paid features now use a unified, user-friendly dialog: users can start a free trial or enter a license key at any time.
- Backend (Google Cloud Function) is robust, secure, and auto-manages all trial/license logic and Google Sheet structure.
- Admin tool and backend are fully documented, with gold-standard deployment, onboarding, and security rules.
- All documentation, ignore files, and workflow scripts are up to date and enforce privacy, safety, and compliance.
- CHANGELOG, README, and all onboarding docs are current and explicit for public release.
- All code is modular, maintainable, and extensible for future features.
- This release is tagged and published for public use.

### Major Features
- **Break Builder**: Build and export Whatnot breaks with advanced filtering, curation, and rule-based workflows.
- **Packing Slip Processor**: Scan Whatnot packing slip PDFs, extract singles sold, and remove them from inventory with best-match logic.
- **Buyers Database & Analytics**: Track all buyers, purchase history, and analytics in a modular, extensible database.
- **Undo/Restore**: Instantly undo packing slip removals for safety and flexibility.
- **Scryfall Enrichment**: Instantly auto-fill card details and images using Scryfall for any card in your inventory or break.
- **Product Listing Export**: Export your inventory or break as a CSV for easy copy/paste into product listings (Whatnot, Shopify, TCGplayer, eBay, etc.).
- **Modern UI/UX**: Clean, resizable, and user-friendly interface throughout the app.
- **Full Test Coverage**: All core logic is fully tested for reliability.

### Roadmap & Future Directions
- **Upcoming Integrations:**
  - Direct export and integration with Shopify, TCGplayer, and eBay for seamless product listing management (planned).
- **Deckbuilding Features:**
  - Future versions will include a full-featured deckbuilder, allowing users to build, save, and analyze decks like a pro (FoS-DeckPro).

### Release Checklist (per project rules)
- [x] All personal files are in `user_private/` and listed in `.gitignore`.
- [x] No build artifacts or large files are present in git history.
- [x] All code is modular, documented, and tested (with docstrings and unit tests).
- [x] All configuration and constants are centralized.
- [x] All features are independently enable/disable-able.
- [x] All UI/UX follows a consistent style guide.
- [x] All error handling is user-friendly and provides safe fallbacks.
- [x] Every code change is accompanied by a test and documentation update.
- [x] Changelog is updated for every release or significant change.
- [x] All scripts (`start_feature.sh`, `finish_release.sh`, `onboarding.sh`, `clean_for_release.sh`) are present and used.
- [x] Onboarding script is added to your shell profile for reminders.
- [x] GitHub Actions for release hygiene and old release cleanup are enabled.
- [x] Branch protection rules are set for `main` and release branches.
- [x] All PRs and issues use the provided templates and checklists.
- [x] All documentation (`README.md`, `RELEASE.md`, `CONTRIBUTING.md`, `PROJECT_WORKFLOW_TEMPLATE.md`) is up to date and explicit.
- [x] No secrets, credentials, or sensitive data are ever committed.
- [x] All contributors are aware of and follow these rules.

## [v1.5.1] - 2024-06-XX

### Working Release Summary
- This release marks a fully working, stable, and modular version of FoS-DeckPro.
- All core workflows (break builder, Whatnot packing slip processing, inventory management, buyers database, and analytics) are robust and tested.
- All break templates and configuration files are present and correctly referenced.
- All tests pass except for known GUI headless environment issues (see README for details).
- The codebase is clean, with legacy and backup files isolated in the `legacy/` folder.
- Documentation and changelog are up to date for all features and fixes.

### Major Enhancements
- **Whatnot Packing Slip Processing:**
  - End-to-end workflow for scanning Whatnot packing slip PDFs, extracting singles sold, and removing them from inventory.
  - Robust PDF parsing, dynamic field extraction, and modular parser for Whatnot slip format.
  - Buyer info (name, username, address) is extracted and tracked for analytics/CRM.
  - All non-card items are ignored; only real singles are processed.
  - Modern, scrollable summary dialog shows cards removed, not found, ambiguous, buyers updated, files processed, and errors.
  - Option to export summary as CSV/JSON for record-keeping.
- **Buyers Database & Analytics:**
  - Modular buyers database (JSON) tracks all buyers, purchase history, totals, and analytics.
  - Buyers DB is updated on every slip processed; supports future CRM/marketing features.
- **Inventory Removal Logic:**
  - Best-match logic for removing sold cards from inventory, with logging for ambiguous/not-found cases.
  - Fully tested for edge cases (quantity, ambiguous, partial match, etc.).
- **File/Folder Workflow:**
  - Only processes new PDFs; after processing, moves/renames to a `done/` subfolder with safe filenames.
  - Robust file handling and error logging.
- **UI Integration:**
  - "Process Whatnot Packing Slips..." menu action in the main GUI.
  - Folder selection, progress, and summary dialog for user review.
  - All actions are user-friendly, robust, and follow modern UX patterns.

### Tests & Reliability
- **Full Unit and Integration Test Coverage:**
  - All new modules (parser, buyers DB, inventory removal, file manager) are fully tested.
  - Integration tests for the end-to-end workflow.
  - All previous tests pass; no regressions.

### Fixed
- **Break Builder Indentation Bug:**
  - Fixed an IndentationError in break_builder.py that could prevent app startup.
  - Reformatted and checked for hidden tab/space issues.

### Added
- Marked as stable, modular, and fully working release.
- All license prompts and documentation updated to use Thereal.FosGameres@gmail.com for access/support.
- Paid features require a license key; users must contact that email for access.
- All documentation and in-app prompts are up to date and consistent with the current licensing model.
- Added per-feature subscription/lifetime license system with automated expiration.
- License key generator and app now handle all Google Sheet columns automatically; no manual editing required.
- Expired features prompt for renewal in-app.
- Marked as official v1.5.1 stable release.
- Per-feature subscription/lifetime licensing, automated expiration, and user-friendly paywall UX.
- All documentation and code up to date for public release.
- Only core app and documentation included in release commit; backups and user data excluded.
- License generator scripts removed from public release; only core app and documentation are included.
- Integrated secure license check backend: all license validation is now performed via a Google Cloud Function (Python, Flask) that checks the Google Sheet and returns license status via a secure API.
- Updated `FoS_DeckPro/utils/license.py` to use the new API endpoint: `https://us-central1-fosbot-456712.cloudfunctions.net/license_check`.
- Automated deployment script (`deploy_license_check.sh`) for the backend, with full documentation and idempotent, safe operation.
- All documentation, code, and workflow updated to reflect the new secure, privacy-safe, and scalable license management system.
- **Full trial support:** The backend and app now support checking trial status and starting new trials via the API. The app will never incorrectly report a trial as expired for new users or features. Trial logic is now robust, privacy-safe, and fully automated.

### Changed
- Whatnot packing slip PDF removal logic now matches cards if at least three fields match, prioritizing collector number, foil/normal, and set code after name.
- If multiple languages are found and language is not specified, user intervention is required to resolve ambiguity.
- All relevant documentation and tests updated to reflect new matching logic and user prompt behavior.

# [Unreleased]
// This section intentionally left blank after v1.6.0 public release. All future changes will be documented here.