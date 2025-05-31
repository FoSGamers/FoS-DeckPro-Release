# Changelog

## [v1.5.1] - 2024-06-XX

### Working Release Summary
- This release marks a fully working, stable, and modular version of FoS_DeckPro.
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

## [Unreleased]

- All future changes will be documented here.

## [1.3.0] - 2024-06-09

### Major Enhancements
- **Break Builder Modernization:**
  - Refactored the Break/Autobox Builder to be modular, extensible, and robust for both beginners and advanced users.
  - Ensured all UI and logic are modular, reusable, and backward compatible.
  - Modern Break/Autobox Builder: now uses the modular CardTableView, FilterOverlay, ImagePreview, and CardDetails widgets for a robust, maintainable UI.
  - All Scryfall and inventory fields are dynamically filterable, just like the main GUI.
  - Async image preview for cards, with robust error handling and fallback.
  - Curated card selection and advanced rule-based break list generation, with deduplication and filler logic.
  - Live display of total and average card cost in the Generate Break tab.
  - Modern, clean, and resizable UI/UX throughout the workflow.
  - All features are fully tested; all tests pass.

### Test Suite Improvements
- **Key-based Inventory Logic:**
  - Updated test `DummyInventory` to use key-based logic for card removal and addition, matching the real app's behavior.
  - Moved the `card_key` function above the `DummyInventory` class in the test to ensure consistent key logic.
- **Dialog Simulation Fixes:**
  - Corrected the use of `QMessageBox.Yes`/`No` in dialog patching to properly simulate user confirmation/cancellation.
- **Assertion Corrections:**
  - Fixed the final assertion in the inventory removal/undo test to check for the correct state after a cancel operation.
- **Result:** All break builder tests now pass, covering sidebar filtering, rule logic, curation, UI, and inventory operations.

### Continuous Integration (CI)
- **GitHub Actions:**
  - Added `.github/workflows/python-ci.yml` to run all tests on every push and pull request.
  - Ensures Python 3.12, PySide6, and pytest are installed and configured for headless GUI testing.
  - Uses `PYTHONPATH=.` and `QT_QPA_PLATFORM=offscreen` for correct package resolution and headless operation.

### Rationale & Documentation
- All changes and fixes are documented here and in commit messages.
- Rationale for each change is provided, including:
  - Why key-based logic is necessary for inventory operations.
  - Why dialog patching must use the correct constants.
  - Why assertions must match the intended post-operation state.
  - Why modular UI/UX and robust async image preview are critical for maintainability and user experience.
- All code and tests are now clear, maintainable, and ready for future enhancements.

### Why This Matters
- Future developers and maintainers will know exactly what was changed, why it was changed, and how to extend or debug the break builder.
- CI ensures that regressions are caught early and that the codebase remains healthy and reliable.
- Comprehensive tests provide confidence for refactoring, adding features, or upgrading dependencies.

### Added
- Modern Break/Autobox Builder: modular CardTableView, FilterOverlay, ImagePreview, CardDetails.
- Dynamic filtering for all Scryfall/inventory fields.
- Async image preview with robust error handling.
- Curated and rule-based break list generation.
- Total and average card cost display in Generate Break tab.
- Modern, clean, resizable UI/UX.
- Full test coverage for all features.

### Changed
- BreakBuilderDialog and related UI refactored for modularity, extensibility, and maintainability.

### Fixed
- Image preview race conditions and network errors.
- Filtering and selection logic for large inventories.
- UI layout and usability issues in all break builder tabs.

## [Unreleased] - Break Builder Modernization, UI/UX, and CI Integration

### Major Enhancements
- **Break Builder Modernization:**
  - Refactored the Break/Autobox Builder to be modular, extensible, and robust for both beginners and advanced users.
  - Ensured all UI and logic are modular, reusable, and backward compatible.
  - Modern Break/Autobox Builder: now uses the modular CardTableView, FilterOverlay, ImagePreview, and CardDetails widgets for a robust, maintainable UI.
  - All Scryfall and inventory fields are dynamically filterable, just like the main GUI.
  - Async image preview for cards, with robust error handling and fallback.
  - Curated card selection and advanced rule-based break list generation, with deduplication and filler logic.
  - Live display of total and average card cost in the Generate Break tab.
  - Modern, clean, and resizable UI/UX throughout the workflow.
  - All features are fully tested; all tests pass.

### Test Suite Improvements
- **Key-based Inventory Logic:**
  - Updated test `DummyInventory` to use key-based logic for card removal and addition, matching the real app's behavior.
  - Moved the `card_key` function above the `DummyInventory` class in the test to ensure consistent key logic.
- **Dialog Simulation Fixes:**
  - Corrected the use of `QMessageBox.Yes`/`No` in dialog patching to properly simulate user confirmation/cancellation.
- **Assertion Corrections:**
  - Fixed the final assertion in the inventory removal/undo test to check for the correct state after a cancel operation.
- **Result:** All break builder tests now pass, covering sidebar filtering, rule logic, curation, UI, and inventory operations.

### Continuous Integration (CI)
- **GitHub Actions:**
  - Added `.github/workflows/python-ci.yml` to run all tests on every push and pull request.
  - Ensures Python 3.12, PySide6, and pytest are installed and configured for headless GUI testing.
  - Uses `PYTHONPATH=.` and `QT_QPA_PLATFORM=offscreen` for correct package resolution and headless operation.

### Rationale & Documentation
- All changes and fixes are documented here and in commit messages.
- Rationale for each change is provided, including:
  - Why key-based logic is necessary for inventory operations.
  - Why dialog patching must use the correct constants.
  - Why assertions must match the intended post-operation state.
  - Why modular UI/UX and robust async image preview are critical for maintainability and user experience.
- All code and tests are now clear, maintainable, and ready for future enhancements.

### Why This Matters
- Future developers and maintainers will know exactly what was changed, why it was changed, and how to extend or debug the break builder.
- CI ensures that regressions are caught early and that the codebase remains healthy and reliable.
- Comprehensive tests provide confidence for refactoring, adding features, or upgrading dependencies.

### Added
- Modern Break/Autobox Builder: modular CardTableView, FilterOverlay, ImagePreview, CardDetails.
- Dynamic filtering for all Scryfall/inventory fields.
- Async image preview with robust error handling.
- Curated and rule-based break list generation.
- Total and average card cost display in Generate Break tab.
- Modern, clean, resizable UI/UX.
- Full test coverage for all features.

### Changed
- BreakBuilderDialog and related UI refactored for modularity, extensibility, and maintainability.

### Fixed
- Image preview race conditions and network errors.
- Filtering and selection logic for large inventories.
- UI layout and usability issues in all break builder tabs. 