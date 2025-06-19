# All sensitive/private/confidential references have been redacted for public compliance.

> **GOLD STANDARD SUMMARY & CHECKLIST**
>
> This project follows a strict, privacy-safe, and automated workflow. Use this summary and checklist to ensure every project is 100% clean, safe, and compliant:
>
> ## Summary
> - Only develop on `[REDACTED]` or `feature/*` branches. Never commit to `main` or release branches.
> - All personal files go in a [REDACTED] directory (in `.gitignore`). Never commit personal files to public branches.
> - Never commit build artifacts or large files (e.g., `dist/`, `build/`, `*.zip`, `*.pkg`, `*.app`, `*.spec`, `*.dmg`, `*.exe`, `*.bin`, `*.tar.gz`, `*.whl`, `*.egg`, `*.pyc`, `__pycache__/`). Always add these to `.gitignore` and clean them from git history.
> - Use the provided scripts for feature, release, onboarding, and cleaning.
> - CI/CD and branch protection block unsafe merges and releases.
> - All code is modular, documented, and tested. All code must have clear comments explaining what each part does, including layman descriptions in code blocks where possible, so anyone (even non-developers) can understand the logic and purpose.
> - All changes update the changelog and docs.
> - All PRs and issues use the provided templates and checklists.
>
> ## Checklist
> - [ ] All personal files are in a [REDACTED] directory and listed in `.gitignore`.
> - [ ] All build artifacts and large files are in `.gitignore` and **never** committed.
> - [ ] No build artifacts or large files are present in git history (use `git filter-repo` if needed).
> - [ ] All code is modular, documented, and tested (with docstrings and unit tests).
> - [ ] All code is clearly commented, with layman descriptions in code blocks where possible, so anyone can understand what it does and why.
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

## Code Commenting and Layman Description Rule for All Project Rule Files

All files that contain project rules—including this file, .cursor files, .github workflows, and any configuration or automation files—must explicitly state and enforce the requirement that all code must be clearly commented, with layman descriptions in code blocks where possible. This ensures that anyone, regardless of technical background, can understand the logic, purpose, and workflow of every part of the project.

# Contributing to FoS-DeckPro

> **IMPORTANT:**
> - A GitHub Action enforces release hygiene: any personal files in a PR or push to a release branch will cause the build to fail.
> - You MUST read and follow this file and [RELEASE.md](RELEASE.md) before merging or releasing.

Thank you for your interest in contributing! We welcome all contributions, from code to documentation, bug reports, and feature requests.

## How to Contribute

### Reporting Bugs
- Open an issue on GitHub with a clear title and description.
- Include steps to reproduce, expected behavior, and screenshots/logs if possible.

### Requesting Features
- Open a feature request issue on GitHub.
- Describe the use case and why it would be helpful.

### Submitting Code or Documentation
1. Fork the repository and clone it locally.
2. Create a new branch for your change.
3. Make your changes (code or docs).
4. Write or update tests as needed.
5. Ensure all tests pass (`pytest FoS_DeckPro/tests`).
6. Commit with a clear message and push to your fork.
7. Open a pull request (PR) to the main repo.

### Code Style
- Follow PEP8 for Python code.
- Use clear, descriptive variable and function names.
- Add docstrings to all public classes and functions.
- Keep code modular and avoid cross-module manipulation.

### Pull Request Process
- All PRs are reviewed by maintainers.
- Address any requested changes.
- PRs must pass all tests and CI checks before merging.

### Marking Beginner-Friendly Issues
- Use the label `good first issue` for tasks suitable for new contributors.
- Add clear instructions and context to these issues.

### Getting Help
- For questions, open a GitHub Discussion or join our community chat.
- See [Code of Conduct](CODE_OF_CONDUCT.md) for community guidelines.

---

We appreciate your help in making FoS-DeckPro better for everyone!

# Contributing Guide

## Branch Workflow
- **[REDACTED]**: Your [REDACTED] development branch. All personal files (backups, inventory, templates, [REDACTED] configs) should be kept in a [REDACTED] directory.
- **v1.5.0-working** (or `main`): Public release branch. No personal files—only code, resources, and docs.

## Build Artifact Hygiene
- **Never commit build artifacts or large files (e.g., dist/, build/, *.zip, *.pkg, *.app, *.spec, *.dmg, *.exe, *.bin, *.tar.gz, *.whl, *.egg, *.pyc, __pycache__/).**
- Always add these to `.gitignore`.
- Clean them from git tracking before pushing or releasing.
- Only source code, scripts, and documentation should be versioned.

## Keeping Personal Files [REDACTED]
- All personal files must be kept in a [REDACTED] directory that is listed in `.gitignore`.
- Never commit or push personal files to the release branch.
- **Never commit build artifacts or large files. See Build Artifact Hygiene above.**
- Use the `clean_for_release.sh` script before every release to ensure no personal files are present.

## Merging Code Changes Safely
1. Commit your work on `[REDACTED]`.
2. Switch to `v1.5.0-working`.
3. Merge or cherry-pick only code changes (not personal files).
4. Run `./clean_for_release.sh` to verify the branch is clean.
5. Build and push the release.

## Release Checklist
- [ ] Run all tests and verify the app works without personal files.
- [ ] Run `./clean_for_release.sh`.
- [ ] Check that only public files are present.
- [ ] **Check that no build artifacts or large files are present.**
- [ ] Build and package the app for release.

## Questions?
- Contact the maintainer for help with branch management or the release process.

## Automated Cleaning Script
- The `clean_for_release.sh` script will move all personal files to a [REDACTED] directory and ensure only public files are present in the release branch.
- Run the script with:
  ```sh
  ./clean_for_release.sh
  ```

## Checklist for Every Release
- [ ] All personal files are in a [REDACTED] directory.
- [ ] `./clean_for_release.sh`