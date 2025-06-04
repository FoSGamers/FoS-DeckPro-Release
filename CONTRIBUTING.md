# Contributing to FoS-DeckPro

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
- **personal-dev**: Your private development branch. All personal files (backups, inventory, templates, sensitive configs) live here in `user_private/`.
- **v1.5.0-working** (or `main`): Public release branch. No personal files—only code, resources, and docs.

## Keeping Personal Files Private
- All personal files must be in `user_private/`, which is in `.gitignore`.
- Never commit or push personal files to the release branch.
- Use the `clean_for_release.sh` script before every release to ensure no personal files are present.

## Merging Code Changes Safely
1. Commit your work on `personal-dev`.
2. Switch to `v1.5.0-working`.
3. Merge or cherry-pick only code changes (not personal files).
4. Run `./clean_for_release.sh` to verify the branch is clean.
5. Build and push the release.

## Release Checklist
- [ ] Run all tests and verify the app works without personal files.
- [ ] Run `./clean_for_release.sh`.
- [ ] Check that only public files are present.
- [ ] Build and package the app for release.

## Questions?
- Contact the maintainer for help with branch management or the release process.

## Automated Cleaning Script
- The `clean_for_release.sh` script will move all personal files to `user_private/` and ensure only public files are present in the release branch.
- Run the script with:
  ```sh
  ./clean_for_release.sh
  ```

## Checklist for Every Release
- [ ] All personal files are in `user_private/`.
- [ ] `./clean_for_release.sh` has been run.
- [ ] Only public files are present in the release branch.
- [ ] Code changes have been merged/cherry-picked from `personal-dev`.
- [ ] All tests pass and documentation is up to date.
- [ ] Commit and push the release branch. 