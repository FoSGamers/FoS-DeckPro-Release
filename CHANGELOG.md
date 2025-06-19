> **GOLD STANDARD SUMMARY & CHECKLIST**
>
> This project follows a strict, privacy-safe, and automated workflow. Use this summary and checklist to ensure every project is 100% clean, safe, and compliant:
>
> ## Summary
> - Only develop on `personal-dev` or `feature/*` branches. Never commit to `main` or release branches.
> - All personal files go in `user_restricted/` (in `.gitignore`). Never commit personal files to public branches.
> - Never commit build artifacts or large files (e.g., `dist/`, `build/`, `*.zip`, `*.pkg`, `*.app`, `*.spec`, `*.dmg`, `*.exe`, `*.bin`, `*.tar.gz`, `*.whl`, `*.egg`, `*.pyc`, `__pycache__/`). Always add these to `.gitignore` and clean them from git history.
> - Use the provided scripts for feature, release, onboarding, and cleaning.
> - CI/CD and branch protection block unsafe merges and releases.
> - All code is modular, documented, and tested. All changes update the changelog and docs.
> - All PRs and issues use the provided templates and checklists.
>
> ## Checklist
> - [ ] All personal files are in `user_restricted/` and listed in `.gitignore`.
> - [ ] All build artifacts and large files are in `.gitignore` and **never** committed.
> - [ ] No build artifacts or large files are present in git history (use `git filter-repo` if needed).
> - [ ] All code is modular, documented, and tested (with docstrings and unit tests).
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

## Code Commenting and Layman Description Rule for All Project Rule Files

All files that contain project rules—including this file, .cursor files, .github workflows, and any configuration or automation files—must explicitly state and enforce the requirement that all code must be clearly commented, with layman descriptions in code blocks where possible. This ensures that anyone, regardless of technical background, can understand the logic, purpose, and workflow of every part of the project.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions workflow for cross-platform builds (Windows, Mac, Linux) to ensure every release includes all platform-specific executables.
- Updated release hygiene workflow to exclude `.github/workflows/` files from personal files check, ensuring workflow files can reference private patterns without triggering the hygiene check.

### Fixed
- Use correct stable version for `actions/download-artifact` in build-and-upload workflow to prevent linter errors and ensure reliability.

## [v1.6.1] - 2024-06-19

### Added
- Mac app bundle (`FoS-DeckPro.app.zip`) for easy installation and usage.
- Enhanced public/private separation to ensure only public files are included in releases.
- Automated release hygiene workflows to maintain clean, professional releases.
- APTPT (Adaptive Phase-Targeted Pulse/Trajectory) integration for robust control systems
- Comprehensive GUI testing framework with automated screenshot analysis
- Enhanced error logging and reporting system
- New pricing dashboard and price tracking features
- Improved card management and inventory systems
- Advanced filtering and export capabilities
- Real-time validation and testing infrastructure

### Changed
- Updated documentation for clarity and ease of use.
- Enhanced APTPT control system with improved stability and performance
- Improved error handling and user feedback mechanisms
- Updated UI components for better user experience
- Enhanced modular architecture for better maintainability

### Fixed
- Resolved merge conflicts and ensured compliance with project standards.
- Fixed GUI responsiveness and performance issues
- Improved error recovery and system stability
- Enhanced data validation and integrity checks
- Fixed compatibility issues across different platforms

### Security
- Enhanced APTPT security protocols
- Improved data protection and privacy measures
- Better access control and authentication systems

## [v1.6.0] - 2024-03-19

### Added
- Enhanced git hooks for better security
- Improved debugging documentation
- New release process documentation

### Changed
- Updated all Standards files to use generic private directory references
- Improved error handling in security checks
- Enhanced documentation structure

### Fixed
- Git hooks now properly handle private content
- Documentation now uses consistent terminology
- Release process now follows best practices

### Security
- Enhanced protection of private content
- Improved security documentation
- Better error handling in security checks

## [v1.5.4] - 2024-06-02

### Added
- Dummy-proof scripts and improved onboarding experience.

### Changed
- Updated README with Whatnot packing slip processing and workflow details.

## [v1.5.3] - 2024-06-01

### Added
- Release hygiene CI, updated documentation, and contribution guidelines.

### Changed
- Improved project organization and structure.

## [v1.5.2] - 2024-05-31

### Added
- New features and improvements for better user experience.

### Changed
- Updated documentation and project structure.

## [v1.5.1] - 2024-05-30

### Added
- Initial features and improvements.

### Changed
- Updated project structure and documentation.

## [v1.5.0] - 2024-03-18

### Added
- Initial release with core features and improvements.

### Changed
- Updated project structure and documentation.

## [1.6.0] - 2024-03-19

### Changed
- Updated GitHub Actions workflows to use artifact actions v4
- Fixed Ubuntu package dependencies for GUI applications
- Improved build process for all platforms (Windows, Mac, Linux)
- Updated Python version to 3.11
- Enhanced release automation and documentation
