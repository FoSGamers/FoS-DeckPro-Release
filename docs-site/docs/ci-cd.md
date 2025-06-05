# CI/CD Workflows

This project uses GitHub Actions for continuous integration, testing, security, and release automation. Below is a summary of all workflows:

## Linting & Quality
- **Python Lint:** Runs flake8 and black on all Python code on push/PR.
- **Markdown Lint:** Lints all markdown files, excluding private/legacy docs.
- **YAML Lint:** Lints all YAML files for syntax and style.
- **Mypy Type Check:** Runs static type checking on all Python code.

## Testing & Coverage
- **Test Coverage:** Runs all tests with pytest and enforces 90%+ coverage.

## Security & Compliance
- **Python Security (Bandit):** Scans for Python security issues.
- **License Scan (REUSE):** Ensures all files are properly licensed.
- **Dependabot:** Checks for dependency and GitHub Actions updates weekly.
- **Public/Private Separation Enforcement:** Blocks any PR or push that includes private, legacy, or forbidden files or references.

## Documentation
- **Docs Build (MkDocs):** Builds the documentation site to ensure it compiles cleanly.

## Release Automation
- **Release Artifact Verification:** Generates and uploads SHA256 checksums for all release assets.
- **Changelog Auto-Generation:** Updates CHANGELOG.md from PRs and commits.

## Release Artifact Signing (GPG)
- **Release artifacts can be cryptographically signed with GPG.** Maintainers can add their GPG private key as a GitHub Actions secret (`GPG_PRIVATE_KEY`) and the workflow will sign all release assets. See [RELEASE.md](../RELEASE.md) for setup instructions.

## Error Reporting
- **Opt-in, privacy-respecting error reporting** is available. Disabled by default; see [Architecture](architecture.md#error-reporting-privacy-respecting-opt-in) for details and privacy statement.

---

For details, see the workflow YAML files in `.github/workflows/`. 