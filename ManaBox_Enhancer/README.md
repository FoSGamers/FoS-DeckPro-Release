# ManaBox Enhancer

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
