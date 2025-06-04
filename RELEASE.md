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