# LEGACY_RELEASE_ARCHIVE.md

> **Private/Internal Archive**
> 
> This file contains all legacy, internal, and detailed process notes, checklists, and historical rules from previous versions of RELEASE.md. It is for private reference only and should not be distributed publicly. Nothing is ever lost—every rule, checklist, and process is preserved here for your records.

---

## Historical Release Process & Checklists

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

### Legacy Release Branch and Artifact Process
- All work must be done in feature branches or personal-dev.
- Never merge unfinished or untested work into main.
- All PRs must be reviewed and pass all CI checks.
- All PRs must update the changelog and documentation as needed.
- Only code, resources, and documentation needed for others to use or run the app are included in a release.
- No personal data, backups, or sensitive configs.
- Use PyInstaller or your preferred tool as described in the README to build the app for release.
- Package only the cleaned files for distribution.

### Legacy CI/CD and Release Hygiene
- Every PR and push to a release branch runs a GitHub Action that blocks the build if any personal files are present.
- If the check fails:
  1. Run `./clean_for_release.sh` locally.
  2. Commit and push the cleaned branch.
  3. Re-read this file and [CONTRIBUTING.md](CONTRIBUTING.md) to ensure compliance.

---

## Notes
- This archive preserves all historical process, rules, and checklists for your private reference. For current release workflow, see RELEASE.md. 