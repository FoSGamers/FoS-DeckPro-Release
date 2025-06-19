**NOTE:** This summary and checklist must be included at the top of README.md, RELEASE.md, CONTRIBUTING.md, and CHANGELOG.md in every project. All code must have clear comments explaining what each part does, including layman descriptions in code blocks where possible, so anyone (even non-developers) can understand the logic and purpose.

## Code Commenting and Layman Description Rule for All Project Rule Files

All files that contain project rules—including this file, .cursor files, .github workflows, and any configuration or automation files—must explicitly state and enforce the requirement that all code must be clearly commented, with layman descriptions in code blocks where possible. This ensures that anyone, regardless of technical background, can understand the logic, purpose, and workflow of every part of the project.

# All sensitive/private/confidential references have been redacted for public compliance.

# Dummy-Proof, Privacy-Safe, and Automated Project Workflow Template

> **GOLD STANDARD SUMMARY & CHECKLIST**
>
> This project follows a strict, privacy-safe, and automated workflow. Use this summary and checklist to ensure every project is 100% clean, safe, and compliant:
>
> ## Summary
> - Only develop on `[REDACTED]` or `feature/*` branches. Never commit to `main` or release branches.
> - All personal files go in `[REDACTED]/` (in `.gitignore`). Never commit personal files to public branches.
> - Never commit build artifacts or large files (e.g., `dist/`, `build/`, `*.zip`, `*.pkg`, `*.app`, `*.spec`, `*.dmg`, `*.exe`, `*.bin`, `*.tar.gz`, `*.whl`, `*.egg`, `*.pyc`, `__pycache__/`). Always add these to `.gitignore` and clean them from git history.
> - Use the provided scripts for feature, release, onboarding, and cleaning.
> - CI/CD and branch protection block unsafe merges and releases.
> - All code is modular, documented, and tested. All changes update the changelog and docs.
> - All PRs and issues use the provided templates and checklists.
>
> ## Checklist
> - [ ] All personal files are in `[REDACTED]/` and listed in `.gitignore`.
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
> - [ ] No secrets, credentials, or [REDACTED] data are ever committed.
> - [ ] All contributors are aware of and follow these rules.

This document describes a robust, privacy-safe, and highly automated workflow for any software project. Copy, adapt, and use it in your own repositories to ensure:
- No personal or [REDACTED] files are ever released
- Releases are always clean and up-to-date
- Contributors always follow the correct process
- You are protected from accidental mistakes, even when in a hurry
- Code quality, modularity, and test coverage are always enforced

---

## 1. Branch Strategy
- **main**: Always contains the latest public release. Never develop directly here.
- **release branch** (e.g., `v1.5.0-working`): Where releases are prepared and tested. Only clean, public files.
- **[REDACTED]**: Your [REDACTED] branch for development with personal files (never pushed to public).
- **feature/your-feature**: All new work starts here, branched from `[REDACTED]`.

## 2a. Build Artifact Hygiene
- **Never commit build artifacts or large files (e.g., dist/, build/, *.zip, *.pkg, *.app, *.spec, *.dmg, *.exe, *.bin, *.tar.gz, *.whl, *.egg, *.pyc, __pycache__/).**
- Always add these to `.gitignore`.
- Clean them from git tracking before pushing or releasing.
- Only source code, scripts, and documentation should be versioned.

## 2. Personal File Hygiene
- All personal, backup, or [REDACTED] files must be kept in `[REDACTED]/` (add to `.gitignore`).
- Use a script (`clean_for_release.sh`) to move/remove all personal files before any release.
- **Never commit or push personal files to public branches.**
- **Never commit build artifacts or large files. See Build Artifact Hygiene above.**

## 3. Coding Standards & Rules
- All code must be modular, maintainable, and documented.
- No cross-module manipulation: use public interfaces, not internals.
- All configuration and constants must be centralized.
- All features must be independently enable/disable-able.
- All UI/UX must follow a consistent style guide.
- All error handling must be user-friendly and provide safe fallbacks.
- **Every class and function must have a docstring.**
- **No code change (feature, fix, or refactor) should be merged or committed without a corresponding test or test update.**
- **Never break existing functionality when implementing new features or fixes.**
- **Refactor in small, testable steps.**
- **Commit frequently with clear messages.**

## 4. Scripts for Safety and Automation
- **start_feature.sh**: Prompts for a feature name, creates/switches to a feature branch from `[REDACTED]`.
- **finish_release.sh**: Cleans, merges, tags, updates `main`, deletes old branches, and pushes everything.
- **onboarding.sh**: Prints current branch, last release, and next steps. Warns if on a protected branch.
- **clean_for_release.sh**: Moves/removes all personal files before release.

## 5. CI/CD and GitHub Actions
- **Release Hygiene Action**: Blocks any PR or push to `main`/release branches if personal files are present.
- **Cleanup Old Releases Action**: Deletes all but the latest release and its assets.
- **Test Automation**: All tests must pass before merging or releasing. Use a workflow like:
  ```yaml
  - name: Run tests
    run: pytest path/to/tests --maxfail=3 --disable-warnings -v
  ```
- **Branch Protection**: Require PRs, CI, and at least one approval for `main` and release branches.
- **Require changelog and documentation updates for all code/config changes.**

## 6. Onboarding and Reminders
- Add onboarding.sh to your shell profile (e.g., `.zshrc` or `.bashrc`) to run on every terminal open:
  ```sh
  echo '[ -f ./onboarding.sh ] && ./onboarding.sh' >> ~/.zshrc
  ```
- onboarding.sh prints a big warning if you're on a protected branch.

## 7. Documentation and Templates
- **README.md**, **RELEASE.md**, **CONTRIBUTING.md**: Explicit, visible instructions and warnings about workflow, privacy, and coding standards.
- **PR/Issue Templates**: Require contributors to check off that they've followed all rules and run all scripts.
- **Changelog**: Every release and significant change must be documented in CHANGELOG.md.

## 8. Example Workflow
| Task                | Command/Action                | What It Does                                 |
|---------------------|------------------------------|----------------------------------------------|
| Start new feature   | `./start_feature.sh`         | Creates/switches to a new feature branch     |
| Finish/release      | `./finish_release.sh`        | Cleans, merges, tags, updates main, deletes old branches |
| Clean personal      | `./clean_for_release.sh`     | Removes/moves all personal files             |
| Onboard/remind      | `./onboarding.sh`            | Prints branch, last release, next steps      |
| Check for personal  | `./clean_for_release.sh --check` | Checks for personal files                |
| File PR/issue       | Use GitHub templates         | Ensures all rules are followed               |
| Run tests           | `pytest path/to/tests`       | Ensures all code is tested before merging    |

## 9. What Happens If You Forget?
- CI will block you from merging or releasing if you have personal files, missing tests, or skip a step.
- PR templates will remind you to check everything.
- Onboarding script will remind you of your branch and next steps.
- Branch protection (if enabled) will prevent direct pushes to protected branches.

## 10. How to Set Up in a New Project
1. Copy all scripts (`start_feature.sh`, `finish_release.sh`, `onboarding.sh`, `clean_for_release.sh`) to your repo.
2. Add `.github/workflows/release-hygiene.yml` and `.github/workflows/cleanup-old-releases.yml`.
3. Add `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/` files.
4. Add onboarding.sh to your shell profile.
5. Set up branch protection rules in GitHub for `main` and your release branch.
6. Update your README, RELEASE.md, and CONTRIBUTING.md with explicit instructions and rules.
7. Add a style guide and test policy if needed.
8. **Add build artifacts and large files to `.gitignore` immediately.**
9. **Clean any accidentally committed build artifacts from git history.**

## 11. Customization
- Adjust the list of personal files in `clean_for_release.sh` for your project.
- Update onboarding.sh messages as needed.
- Add more CI checks, scripts, or rules for your workflow.
- Add or update coding standards and test requirements as your project evolves.

---

**This template will help you and your team avoid mistakes, protect privacy, enforce code quality, and always ship clean, professional releases.** 