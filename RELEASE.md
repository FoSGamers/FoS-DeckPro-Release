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
> - All code is modular, documented, and tested. All code must have clear comments explaining what each part does, including layman descriptions in code blocks where possible, so anyone (even non-developers) can understand the logic and purpose.
> - All changes update the changelog and docs.
> - All PRs and issues use the provided templates and checklists.
>
> ## Checklist
> - [ ] All personal files are in `user_private/` and listed in `.gitignore`.
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
> - [ ] No secrets, credentials, or sensitive data are ever committed.
> - [ ] All contributors are aware of and follow these rules.

# Release Process for FoS-DeckPro

> **IMPORTANT:**
> - A GitHub Action enforces release hygiene: any personal files in a PR or push to a release branch will cause the build to fail.
> - You MUST read and follow this file and [CONTRIBUTING.md](CONTRIBUTING.md) before merging or releasing.

## Build Artifact Hygiene
- **Never commit build artifacts or large files (e.g., dist/, build/, *.zip, *.pkg, *.app, *.spec, *.dmg, *.exe, *.bin, *.tar.gz, *.whl, *.egg, *.pyc, __pycache__/).**
- Always add these to `.gitignore`.
- Clean them from git tracking before pushing or releasing.
- Only source code, scripts, and documentation should be versioned.

## 1. Clean Personal Files Before Release
- All personal files (backups, inventory, templates, sensitive configs, etc.) must be moved to `user_private/`.
- `user_private/` is in `.gitignore` and will never be included in a public release.
- **Never commit build artifacts or large files. See Build Artifact Hygiene above.**
- Run the provided script before every release:

```sh
./clean_for_release.sh
```

This script will:
- Move all personal files to `user_private/` (if not already there)
- Remove any lingering personal files from tracked locations
- Verify only public files are present

## 2. Branch Management
- **Develop with personal files** on the `personal-dev` branch.
- **Release code** from the `v1.5.0-working` (or main) branch, which is always clean.
- To merge code changes:
  1. Commit your work on `personal-dev`.
  2. Switch to `v1.5.0-working`.
  3. Merge or cherry-pick code changes (not personal files).
  4. Run `./clean_for_release.sh` and verify.
  5. Build and push the release.

## 3. What Files Are Included in a Release?
- Only code, resources, and documentation needed for others to use or run the app.
- No personal data, backups, or sensitive configs.

## 4. Building and Packaging
- Use PyInstaller as described in the README to build the app for release.
- Package only the cleaned files for distribution.

## 5. Questions?
- Contact the maintainer for help with the release process or branch management.

## 6. CI Release Hygiene Check
- Every PR and push to a release branch runs a GitHub Action that blocks the build if any personal files are present.
- If the check fails:
  1. Run `./clean_for_release.sh` locally.
  2. Commit and push the cleaned branch.
  3. Re-read this file and [CONTRIBUTING.md](CONTRIBUTING.md) to ensure compliance. 