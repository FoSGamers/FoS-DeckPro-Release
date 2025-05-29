# Changelog

## [Unreleased]

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