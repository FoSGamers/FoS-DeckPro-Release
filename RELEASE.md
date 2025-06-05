# RELEASE.md

## 📢 Release Notes Policy

The [GitHub Releases page](https://github.com/FoSGamers/FoS-DeckPro/releases) is the single source of truth for all features, changes, and upgrade instructions. Every public release must have clear, user-focused, and up-to-date release notes. All contributors are responsible for ensuring the release notes are accurate and complete for every release.

---

## 🚀 Public Release Workflow

### 1. Keep Personal Files Private
- All personal files (backups, inventory, templates, sensitive configs) must be kept in `user_private/` (which is in `.gitignore`).
- Never commit or push personal files to public branches.

### 2. Clean the Release Branch
- Run `./clean_for_release.sh` before every release to ensure no personal files or build artifacts are present.
- Only code, resources, and documentation needed for public use should be present in the release branch.

### 3. Build Artifact Hygiene
- Never commit build artifacts or large files (e.g., `dist/`, `build/`, `*.zip`, `*.pkg`, `*.app`, `*.spec`, `*.dmg`, `*.exe`, `*.bin`, `*.tar.gz`, `*.whl`, `*.egg`, `*.pyc`, `__pycache__/`).
- Always add these to `.gitignore` and clean them from git tracking before pushing or releasing.

### 4. Release Notes
- Every public release must have clear, user-focused, and up-to-date release notes on the [GitHub Releases page](https://github.com/FoSGamers/FoS-DeckPro/releases). This is the single source of truth for users and contributors.

### 5. Branch Management
- All development should be done in feature branches or `personal-dev`.
- Only merge tested, clean, and documented code into `main` for public release.

### 6. Final Verification
- Ensure all documentation, changelog, and workflow scripts are up to date.
- Run all tests and verify the app is stable and ready for public use.

---

## 📝 Final Note
- For any questions or clarifications, refer to the [GitHub Releases page](https://github.com/FoSGamers/FoS-DeckPro/releases), `CONTRIBUTING.md`, or contact the maintainer.

<!-- Legacy and detailed process notes have been moved to LEGACY_RELEASE_ARCHIVE.md for private reference. --> 