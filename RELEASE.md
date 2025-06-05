# RELEASE.md

## 📢 Release Notes Policy

The [GitHub Releases page](https://github.com/FoSGamers/FoS-DeckPro/releases) is the single source of truth for all features, changes, and upgrade instructions. Every public release must have clear, user-focused, and up-to-date release notes. All contributors are responsible for ensuring the release notes are accurate and complete for every release.

---

## 🚀 Public Release Workflow

### 1. Keep Personal Files Private
- All personal files (backups, inventory, templates, sensitive configs) must be kept in `user_restricted/` (which is in `.gitignore`).
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

## GPG Signing of Release Artifacts

To ensure the authenticity and integrity of release assets, maintainers can enable GPG signing:

1. Generate a GPG key pair (if you don't have one):
   ```sh
   gpg --full-generate-key
   gpg --armor --export-secret-keys "Your Name <your@email.com>" > gpg_private_key.asc
   ```
2. Add the contents of `gpg_private_key.asc` as a GitHub Actions secret named `GPG_PRIVATE_KEY`.
3. The release workflow will sign all release assets and upload `.asc` signature files.
4. Users can verify signatures with:
   ```sh
   gpg --verify asset.zip.asc asset.zip
   ```

**Note:** Never share your private key. Only trusted maintainers should have access.

<!-- Legacy and detailed process notes have been moved to LEGACY_RELEASE_ARCHIVE.md for private reference. -->

## 🚀 FoS-DeckPro v1.6.1 – Public Release

Download the ready-to-run app for your platform:
- **Mac:** FoS-DeckPro.app.zip
- **Windows:** FoS-DeckPro.exe
- **Linux:** FoS-DeckPro.AppImage

If you only see the Mac app, Windows and Linux builds are coming soon!

---

**Changelog Highlights:**
- Cross-platform build system (Mac, Windows, Linux)
- Enhanced public/private separation and release hygiene
- Updated documentation and onboarding
- Fully modular, maintainable, and extensible codebase 