# Project Gold Standard Playbook

This playbook documents the gold-standard rules, automation, documentation, and CI/CD practices implemented in this project. Use it to replicate a professional, privacy-safe, and fully automated workflow in any new project.

---

## 1. Public/Private Separation
- All personal, admin, and legacy files are isolated in `user_restricted/` or private folders, never referenced in public code/docs.
- `.gitignore` and CI workflows block any commit or PR with private/legacy files or references.
- All public docs and code are scrubbed of private/internal references.

## 2. Project Rules & Best Practices
- Modular, encapsulated design for all features.
- No cross-module manipulation; use public interfaces only.
- Backward compatibility and incremental, testable refactoring.
- Unit tests for all core logic; run all tests after each change.
- Clear documentation for every class, function, and module.
- Centralized configuration for all settings and constants.
- Consistent UI/UX, defined in a style guide.
- Safe fallbacks and user-friendly error handling.
- Feature isolation: new features are independently enable/disable-able.
- All data operations work on the full filtered dataset.
- Extensible structure for easy addition of new features/modules.
- Document the process for adding new features/modules.

## 3. Documentation Guidelines
- All public docs are concise, professional, and user-focused.
- `README.md`, `CONTRIBUTING.md`, and `RELEASE.md` reference the GitHub release notes as the single source of truth.
- All legacy/internal docs are moved to private `LEGACY_*_ARCHIVE.md` files.
- MkDocs is used for modern, navigable documentation, with all docs in `docs-site/` and `FoS_DeckPro/docs/`.
- CI workflow ensures docs build cleanly on every push/PR.

## 4. CI/CD & Automation
- **Linting:** Python (flake8, black), Markdown, YAML, and mypy type checks.
- **Testing:** Pytest with 90%+ coverage enforced.
- **Security:** Bandit security scanning, REUSE license compliance, Dependabot for dependencies.
- **Release Hygiene:** Workflows block build artifacts, large files, and personal files from release branches.
- **Changelog:** Auto-generated from PRs/commits.
- **Docs Build:** MkDocs build check on every push/PR.
- **Release Artifacts:** SHA256 checksums and (optionally) GPG signatures for all release assets.
- **Public/Private Separation:** Automated workflow blocks any PR/push with forbidden files or references.
- **Self-Documenting Workflows:** All workflows are summarized in `docs-site/docs/ci-cd.md`.

## 5. Privacy-Respecting Error Reporting
- Optional, opt-in, anonymous error reporting (disabled by default).
- No personal or sensitive data is ever collected or sent.
- Configurable in `FoS_DeckPro/utils/config.py`.

## 6. Community Health
- Professional `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`, and issue/PR templates.
- All contributors must follow the rules and checklists in `CONTRIBUTING.md` and PR templates.

---

## How to Port This to a New Project

1. **Copy the following folders/files:**
   - `.github/` (all workflows, templates, and config)
   - `docs-site/` (MkDocs site)
   - `CONTRIBUTING.md`, `RELEASE.md`, `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`
   - `PROJECT_GOLD_STANDARD_PLAYBOOK.md` (this file)
2. **Update project-specific details:**
   - Project name, URLs, and contact info in all docs and workflows.
   - Any custom config or settings in `config.py`.
3. **Review and update `.gitignore` and CI workflows** for any new private or build files.
4. **Run all tests and CI workflows** to ensure everything is working.
5. **Document any new features or rules** in this playbook and your docs.

---

## Example Workflow: Public/Private Separation Enforcement
```yaml
name: Public/Private Separation Enforcement
on:
  push:
    branches: [main, release/*]
  pull_request:
    branches: [main, release/*]
jobs:
  separation-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Check for forbidden files
        run: |
          forbidden_paths=(user_restricted/ legacy/ LEGACY_*_ARCHIVE.md)
          for path in "${forbidden_paths[@]}"; do
            if git ls-files --error-unmatch "$path" 2>/dev/null; then
              echo "Forbidden file or directory detected: $path"
              exit 1
            fi
          done
      - name: Check for forbidden references in public files
        run: |
          grep -r --exclude-dir=user_restricted --exclude-dir=legacy --exclude=LEGACY_*_ARCHIVE.md -E 'user_restricted/|legacy/|LEGACY_.*_ARCHIVE\.md' src/ docs/ || true
          if grep -r --exclude-dir=user_restricted --exclude-dir=legacy --exclude=LEGACY_*_ARCHIVE.md -E 'user_restricted/|legacy/|LEGACY_.*_ARCHIVE\.md' src/ docs/; then
            echo "Forbidden reference to private or legacy content detected."
            exit 1
          fi
```

---

## Checklist for New Projects
- [ ] All public/private separation rules enforced
- [ ] All automation and CI/CD workflows present and passing
- [ ] All documentation professional, up to date, and user-focused
- [ ] All contributors aware of and following project rules
- [ ] All legacy/internal content archived privately
- [ ] All release assets verified and signed (if desired)
- [ ] All error reporting is opt-in and privacy-respecting

---

**This playbook is your blueprint for building gold-standard, professional, and privacy-safe projects—now and in the future.** 