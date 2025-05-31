# FoS-DeckPro Release Notes

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
- The only known issue in this release is that the **Customize Columns** feature does not work. This is a trivial UI bug and does not affect any core functionality or data integrity.

### Upgrade Instructions
- Install requirements from `FoS_DeckPro/requirements.txt`.
- Run the app from `FoS_DeckPro/main.py`.
- Move any custom break templates to the project root if needed.

## Monetization & Add-ons

- The base app (inventory management and Scryfall enrichment) is free and open source.
- All other features (break builder, packing slip tools, analytics, etc.) are planned as paid add-ons/plugins in future versions. The codebase is structured to support this model without risk to the core app.

## Release Status

- This version is a stable, working release. All core features work as intended except for the minor known issue above.

See [CHANGELOG.md](CHANGELOG.md) for full details.

## Free vs. Paid Features

### Free Features
- Inventory management (import/export from ManaBox or CSV, local database, view/edit/delete/filter/search)

### Paid Features (Require License Key)
- All Whatnot features (break builder, export listing, packing slip tools, analytics)
- Add card via Scryfall
- Scryfall enrichment (auto-fill card details/images)

## License Key System
- Paid features are locked by default.
- On first use of a paid feature, you will be prompted to enter a license key.
- The app checks your key online (Google Sheets) and unlocks only the features your key is valid for.
- License key is stored locally for future use.

**To request a license key for paid features, contact: Thereal.FosGameres@gmail.com**

This is the recommended model for future releases. 