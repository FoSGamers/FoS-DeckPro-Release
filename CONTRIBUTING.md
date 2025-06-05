# CONTRIBUTING.md

## 📢 Release Notes Policy

The [GitHub Releases page](https://github.com/FoSGamers/FoS-DeckPro/releases) is the single source of truth for all features, changes, and upgrade instructions. Every public release must have clear, user-focused, and up-to-date release notes. All contributors are responsible for ensuring the release notes are accurate and complete for every release.

---

## 🤝 How to Contribute

- Fork the repository and clone it locally.
- Create a new branch for your change (feature, fix, or documentation).
- Make your changes (code or docs).
- Write or update tests as needed.
- Ensure all tests pass (`pytest FoS_DeckPro/tests`).
- Commit with a clear message and push to your fork.
- Open a pull request (PR) to the main repo.

---

## 🧑‍💻 Code Style & Best Practices

- Follow PEP8 for Python code.
- Use clear, descriptive variable and function names.
- Add docstrings to all public classes and functions.
- Keep code modular and avoid cross-module manipulation.
- All configuration and constants must be centralized.
- All features must be independently enable/disable-able.
- All UI/UX must follow a consistent style guide.
- All error handling must be user-friendly and provide safe fallbacks.

---

## 🔀 Branch Workflow

- **personal-dev**: Your private development branch. All personal files (backups, inventory, templates, sensitive configs) live here in `user_private/`.
- **main**: Public release branch. No personal files—only code, resources, and docs.

---

## 🧹 Build Artifact Hygiene
- **Never commit build artifacts or large files (e.g., `dist/`, `build/`, `*.zip`, `*.pkg`, `*.app`, `*.spec`, `*.dmg`, `*.exe`, `*.bin`, `*.tar.gz`, `*.whl`, `*.egg`, `*.pyc`, `__pycache__/`).**
- Always add these to `.gitignore`.
- Clean them from git tracking before pushing or releasing.
- Only source code, scripts, and documentation should be versioned.

---

## ✅ Pull Request Process

- All PRs are reviewed by maintainers.
- Address any requested changes.
- PRs must pass all tests and CI checks before merging.
- Every PR must update the release notes if it changes user-facing features or behavior.

---

## 📝 Final Note
- Every public release must have clear, user-focused, and up-to-date release notes on the [GitHub Releases page](https://github.com/FoSGamers/FoS-DeckPro/releases). This is the single source of truth for users and contributors.

<!-- Legacy and detailed process notes have been moved to LEGACY_CONTRIBUTING_ARCHIVE.md for private reference. -->