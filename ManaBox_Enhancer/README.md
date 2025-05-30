# ManaBox Enhancer

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

- **Whatnot Packing Slip Processing (in progress):**
  - Scan a folder of Whatnot packing slip PDFs and update inventory automatically (requires `pdfplumber`).
  - Buyer analytics and robust error handling.

- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.

- **Full test coverage and CI integration.**

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

- Each stable, working version is tagged (e.g., `v1.5.0`) and has a dedicated branch (e.g., `v1.5.0-working`).
- All changes are documented in the `CHANGELOG.md` and committed with clear messages.
- Releases are created on GitHub for easy download, rollback, and reproducibility.
- Always use the provided `requirements.txt` and follow the Quick Start for setup on new machines.

## Notes

- This is the advanced, modular PySide6 version described in the documentation and changelog.
- The Whatnot packing slip PDF feature is under active development.
- For any issues, ensure all requirements are installed and you are running the app from the correct entry point (`main.py`).

## Project Tracking & Documentation Policy

- This project is now tracked with Git for full version control and history.
- **README.md will be updated for every change, feature, or fix.**
- All contributors must document what was changed, why, and how it was tested in this file.
- Every new feature, bug fix, or refactor must be described here immediately after implementation.

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
