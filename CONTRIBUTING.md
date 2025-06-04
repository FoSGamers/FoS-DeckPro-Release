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

## Personal Files and Privacy
- All personal files (backups, inventory, templates, sensitive configs, etc.) must be kept in the `user_private/` directory.
- `user_private/` is listed in `.gitignore` and will never be committed or pushed to public branches.
- Never add or commit personal files to the release branch.

## Release Process
- Before every release, run the `clean_for_release.sh` script to ensure no personal files are present.
- Only code, resources, and documentation needed for others to use or run the app should be present in the release branch.

## Safe Merging Between Branches
- Do all development (including with personal files) on the `personal-dev` branch.
- When ready to release:
  1. Switch to the release branch (`v1.5.0-working`).
  2. Merge or cherry-pick code changes from `personal-dev` (avoid merging personal files).
  3. Run `./clean_for_release.sh` to ensure the release is clean.
  4. Commit and push the release branch.
- Never merge `user_private/` or personal files into the release branch.

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