# ManaBox Enhancer Release Notes

## v1.5.1 (2024-06-XX)

### Highlights
- Fully working, stable, and modular release.
- All core workflows (break builder, Whatnot packing slip processing, inventory management, buyers database, analytics) are robust and tested.
- All break templates and configuration files are present and referenced.
- Legacy and backup files are isolated in the `legacy/` folder.
- Documentation, changelog, and contributor guides are up to date.

### New Features
- End-to-end Whatnot packing slip PDF processing and inventory removal.
- Modular break builder with rule-based and curated workflows.
- Buyers database and analytics.
- Undo/restore for packing slip removals.
- Full test coverage for all core logic.

### Improvements
- Modern, modular UI/UX throughout the app.
- Robust error handling and user feedback.
- All configuration and templates centralized.

### Bug Fixes
- Fixed break builder indentation and UI bugs.
- Improved test reliability and CI integration.

### Known Issues
- Some GUI tests require a display environment (see README for headless testing instructions).
- No direct Whatnot API integration yet (planned for future).

### Upgrade Instructions
- Install requirements from `ManaBox_Enhancer/requirements.txt`.
- Run the app from `ManaBox_Enhancer/main.py`.
- Move any custom break templates to the project root if needed.

See [CHANGELOG.md](CHANGELOG.md) for full details. 