# ManaBox Enhancer

## Version: v1.5.1 (2024-06-XX)

## Quick Start

1. **Install requirements:**
   ```sh
   pip install -r ManaBox_Enhancer/requirements.txt
   ```
2. **Launch the app:**
   ```sh
   python3 ManaBox_Enhancer/main.py
   ```
3. **Access the Break/Autobox Builder:**
   - In the running app, go to the **Tools** menu.
   - Select **Open Break/Autobox Builder**.
   - Use the tabs to filter inventory, curate must-haves, set rules, and generate/export your break list.

## Features & Workflow

- **Advanced Break/Autobox Builder:**
  - Modular, rule-based, and curated break list generation.
  - Dynamic filtering, live preview, cost calculation, and export.
  - Save/load rule sets, batch inventory operations, and undo support.
  - **Filler Cards:** If your rules/curation do not fill the break, remaining slots are filled with available cards ("filler"), and their Whatnot price is shown and used in calculations.
  - **Whatnot Price Minimum Rule:**
    - For all break cost and average calculations, any card with a Whatnot price of 0 is treated as 1 (display still shows the original value).
    - This ensures compliance with Whatnot's minimum price policy and accurate break math.
  - **Break Preview:**
    - All cards (including filler) show their Whatnot price in the preview.
    - Rule-based cards also show the fields that matched the rule.
    - Curated, rule-based, and filler cards are clearly separated in the preview.
  - **Cost/Average Calculation:**
    - The total and average Whatnot price is shown at the bottom of the break builder.
    - All cards (including filler) are included, and 0 prices are counted as 1 for math.

- **Whatnot Packing Slip Processing:**
  - Robust PDF parsing with `pdfplumber`.
  - **Sale Parsing:** Card name and foil/normal status are always split and normalized, even if the status is in the name (e.g., "Bribery normal").
  - **Matching:** Cards are matched using name, set code, collector number, foil/normal, and language. Fuzzy matching and set code aliases are used for best results.
  - **Ambiguity Handling:** If multiple inventory cards match except for language, the user is prompted to resolve the ambiguity.
  - **Undo/Restore:** Every packing slip removal can be undone from the File menu.
  - **No Auto-Remove:** Cards are not removed from inventory or files moved until the user confirms.
  - **Debugging:** All not-found cards are logged with detailed debug output for troubleshooting.

- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.

- **Full test coverage and CI integration.**
  - All core logic is covered by regression and edge-case tests.
  - Sale parsing and matching logic are tested for all known edge cases.

## Requirements

- All dependencies are listed in `ManaBox_Enhancer/requirements.txt`.
- Key packages:
  - `PySide6` (GUI)
  - `pandas`, `requests`, `tqdm`, `pillow`, `pdfplumber`
  - See the requirements file for the full list.

## Testing

- To run tests:
  ```sh
  PYTHONPATH=$PYTHONPATH:$(pwd) pytest ManaBox_Enhancer/tests --maxfail=3 --disable-warnings -v
  ```
- For GUI tests in headless environments, use Xvfb:
  ```sh
  xvfb-run -a pytest ManaBox_Enhancer/tests --maxfail=3 --disable-warnings -v
  ```

## Versioning & GitHub Best Practices

- Each stable, working version is tagged (e.g., `v1.5.1`) and has a dedicated branch (e.g., `v1.5.1-working`).
- All changes are documented in the `CHANGELOG.md` and committed with clear messages.
- Releases are created on GitHub for easy download, rollback, and reproducibility.
- Always use the provided `requirements.txt` and follow the Quick Start for setup on new machines.

## AI Contributor & Developer Guide

- **Modular Design:** All features are implemented as encapsulated modules/classes with clear interfaces.
- **No Cross-Module Manipulation:** Use only public methods/events for communication between modules.
- **Backward Compatibility:** Never break or remove a working feature without a migration plan and tests.
- **Incremental Refactoring:** Refactor in small, testable steps. Run all tests after each change.
- **Unit Testing:** Every module has unit tests for its core logic. All tests must pass before merging.
- **Documentation:** Every class and function has a docstring explaining its purpose and usage.
- **Centralized Configuration:** All config/constants are in a config file or module.
- **Consistent UI/UX:** All UI components follow a consistent style and interaction pattern.
- **Safe Fallbacks and Error Handling:** All features provide safe fallbacks and user-friendly error messages.
- **Feature Isolation:** New features must be independently enable/disable-able and not affect unrelated features.
- **Full-Data Operations:** All filtering/exporting/analytics operate on the full filtered dataset, not just the current GUI page.
- **Extensibility:** The codebase is structured so new features/modules can be added without modifying or risking existing features.
- **Process Documentation:** The process for adding new features/modules is documented for future enhancements.

## Project Tracking & Documentation Policy

- This project is tracked with Git for full version control and history.
- **README.md and CHANGELOG.md are updated for every change, feature, or fix.**
- All contributors must document what was changed, why, and how it was tested in these files.
- Every new feature, bug fix, or refactor must be described here immediately after implementation.

---

## Project Overview

ManaBox Enhancer is a modular, extensible tool for managing and enhancing card inventory workflows. All modules, features, and changes are documented below.

---

## Change Log

See `CHANGELOG.md` for a full history of all changes and releases.

## Notes

- This is the advanced, modular PySide6 version described in the documentation and changelog.
- The Whatnot packing slip PDF feature is under active development.
- For any issues, ensure all requirements are installed and you are running the app from the correct entry point (`main.py`).

## Initial Commit
- Initialized Git repository on this project.
- Established documentation policy: README.md must always be kept up to date.

---

## Project Overview

ManaBox Enhancer is a modular, extensible tool for managing and enhancing card inventory workflows. All modules, features, and changes are documented below.

---

## Change Log

### [Unreleased]
- Project initialized with Git version control.
- Documentation policy established: README.md must be updated with every change.

## Testing

### Current Status
- Logic tests (e.g., inventory bulk edit/remove) pass.
- GUI tests (e.g., export to Whatnot) may fail in headless environments due to Qt GUI requirements.
- Fixed: QAction is now imported from PySide6.QtGui for compatibility with PySide6 6.9.0.

### Limitations
- Some GUI tests require a display environment. Running them in a headless environment (like CI or servers) can cause fatal errors.
- To run GUI tests reliably, use a virtual display (e.g., Xvfb on Linux) or a local desktop environment.

### Plan for 100% Accurate, Human-like GUI Testing
- All future GUI features will be tested using Qt's QTest framework and/or integration tools (e.g., pytest-qt, squish, or Playwright for desktop).
- Tests will simulate real user interactions: clicking, typing, file dialogs, etc.
- All test cases will be documented and updated in this README.
- Regression tests will be added for every bug fix or feature.

### How to Run Tests

```sh
# Always run with the project root on PYTHONPATH:
PYTHONPATH=$PYTHONPATH:$(pwd) pytest ManaBox_Enhancer/tests --maxfail=3 --disable-warnings -v
```

- For GUI tests, ensure you have a display environment or use Xvfb:

```sh
xvfb-run -a pytest ManaBox_Enhancer/tests --maxfail=3 --disable-warnings -v
```
