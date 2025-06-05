# LEGACY_CONTRIBUTING_ARCHIVE.md

> **Private/Internal Archive**
> 
> This file contains all legacy, internal, and detailed process notes, checklists, and historical rules from previous versions of CONTRIBUTING.md. It is for private reference only and should not be distributed publicly. Nothing is ever lost—every rule, checklist, and process is preserved here for your records.

---

## Historical Rules & Checklists

### Gold Standard Summary & Checklist (Legacy)
- All personal files are in user_private/ and listed in .gitignore.
- All build artifacts and large files are in .gitignore and never committed.
- No build artifacts or large files are present in git history (use git filter-repo if needed).
- All code is modular, documented, and tested (with docstrings and unit tests).
- All configuration and constants are centralized.
- All features are independently enable/disable-able.
- All UI/UX follows a consistent style guide.
- All error handling is user-friendly and provides safe fallbacks.
- Every code change is accompanied by a test and documentation update.
- Changelog is updated for every release or significant change.
- All scripts (start_feature.sh, finish_release.sh, onboarding.sh, clean_for_release.sh) are present and used.
- Onboarding script is added to your shell profile for reminders.
- GitHub Actions for release hygiene and old release cleanup are enabled.
- Branch protection rules are set for main and release branches.
- All PRs and issues use the provided templates and checklists.
- All documentation (README.md, RELEASE.md, CONTRIBUTING.md, PROJECT_WORKFLOW_TEMPLATE.md) is up to date and explicit.
- No secrets, credentials, or sensitive data are ever committed.
- All contributors are aware of and follow these rules.

### Legacy Branch and PR Process
- All work must be done in feature branches or personal-dev.
- Never merge unfinished or untested work into main.
- All PRs must be reviewed and pass all CI checks.
- All PRs must update the changelog and documentation as needed.

### Legacy Internal Notes
- Modular Design: All features must be implemented as separate, encapsulated modules or classes with clear, documented interfaces.
- No Cross-Module Manipulation: Modules must not directly access or modify the internals of other modules. Use public methods, events, or signals/slots for communication.
- Backward Compatibility: Never break or remove a working feature without a migration plan and tests. All refactors must maintain backward compatibility.
- Incremental Refactoring: Refactor in small, testable steps. After each step, verify that all features still work before proceeding.
- Unit Testing: Every module must have unit tests for its core logic. Run all tests after each change or refactor.
- Documentation: All code, modules, and changes must be clearly documented. Every class and function should have a docstring explaining its purpose and usage.
- Version Control Discipline: Use git branches for each feature or refactor. Commit frequently with clear messages. Never merge unfinished or untested work into main.
- Centralized Configuration: All configuration, constants, and settings must be centralized in a config file or module.
- Consistent UI/UX: All UI components must follow a consistent style and interaction pattern, defined in a style guide or shared resource.
- Safe Fallbacks and Error Handling: All features must provide safe fallbacks and clear, user-friendly error messages. The app must gracefully recover from failures.
- Feature Isolation: New features must be independently enable/disable-able and must not affect unrelated features.
- Full-Data Operations: All filtering, exporting, and analytics must operate on the full filtered dataset, not just the current GUI page.
- Extensibility: The codebase must be structured so that new features or modules can be added without modifying or risking existing, unrelated features.
- Process Documentation: Document the process for adding new features or modules, so future enhancements are easy, safe, and consistent.

---

## Legacy Pull Request Template
- [ ] All code is modular and documented
- [ ] All tests pass
- [ ] Changelog updated
- [ ] Documentation updated
- [ ] No personal files or build artifacts committed
- [ ] PR description is clear and complete

---

## Notes
- This archive preserves all historical process, rules, and checklists for your private reference. For current contribution guidelines, see CONTRIBUTING.md. 