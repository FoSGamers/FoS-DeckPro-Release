# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Full integration of all Scryfall price fields (usd, usd_foil, usd_etched, eur, eur_foil, eur_etched, tix)
- Full integration of all Scryfall purchase URIs (TCGplayer, Cardmarket, Cardhoarder)
- All price fields are now visible, filterable, and exportable in all card UIs
- Numeric filtering support for all price fields with range operators (>, <, >=, <=, -)

## [v1.5.0] - 2024-05-30

### Major Enhancements
- **Advanced Break/Autobox Builder:**
  - Modular, rule-based, and curated break list generation.
  - Dynamic filtering, live preview, cost calculation, and export.
  - Save/load rule sets, batch inventory operations, and undo support.
- **Whatnot Packing Slip Processing (in progress):**
  - Scan a folder of Whatnot packing slip PDFs and update inventory automatically (requires `pdfplumber`).
  - Buyer analytics and robust error handling.
- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.
- **Full test coverage and CI integration.**
- **Requirements and Documentation:**
  - All dependencies are now listed in `requirements.txt` for easy setup on any computer.
  - README updated with clear Quick Start, usage, and requirements.

### Status
- This is a stable, working release on branch `v1.5.0-working` and tag `v1.5.0`.
- The Whatnot packing slip PDF feature is under active development.

## [v1.4.0] - 2024-05-20

### Major Enhancements
- **Advanced Break/Autobox Builder:**
  - Modular, rule-based, and curated break list generation.
  - Dynamic filtering, live preview, cost calculation, and export.
  - Save/load rule sets, batch inventory operations, and undo support.
- **Whatnot Packing Slip Processing (in progress):**
  - Scan a folder of Whatnot packing slip PDFs and update inventory automatically (requires `pdfplumber`).
  - Buyer analytics and robust error handling.
- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.
- **Full test coverage and CI integration.**
- **Requirements and Documentation:**
  - All dependencies are now listed in `requirements.txt` for easy setup on any computer.
  - README updated with clear Quick Start, usage, and requirements.

### Status
- This is a stable, working release on branch `v1.4.0-working` and tag `v1.4.0`.
- The Whatnot packing slip PDF feature is under active development.

## [v1.3.0] - 2024-05-10

### Major Enhancements
- **Advanced Break/Autobox Builder:**
  - Modular, rule-based, and curated break list generation.
  - Dynamic filtering, live preview, cost calculation, and export.
  - Save/load rule sets, batch inventory operations, and undo support.
- **Whatnot Packing Slip Processing (in progress):**
  - Scan a folder of Whatnot packing slip PDFs and update inventory automatically (requires `pdfplumber`).
  - Buyer analytics and robust error handling.
- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.
- **Full test coverage and CI integration.**
- **Requirements and Documentation:**
  - All dependencies are now listed in `requirements.txt` for easy setup on any computer.
  - README updated with clear Quick Start, usage, and requirements.

### Status
- This is a stable, working release on branch `v1.3.0-working` and tag `v1.3.0`.
- The Whatnot packing slip PDF feature is under active development.

## [v1.2.0] - 2024-04-30

### Major Enhancements
- **Advanced Break/Autobox Builder:**
  - Modular, rule-based, and curated break list generation.
  - Dynamic filtering, live preview, cost calculation, and export.
  - Save/load rule sets, batch inventory operations, and undo support.
- **Whatnot Packing Slip Processing (in progress):**
  - Scan a folder of Whatnot packing slip PDFs and update inventory automatically (requires `pdfplumber`).
  - Buyer analytics and robust error handling.
- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.
- **Full test coverage and CI integration.**
- **Requirements and Documentation:**
  - All dependencies are now listed in `requirements.txt` for easy setup on any computer.
  - README updated with clear Quick Start, usage, and requirements.

### Status
- This is a stable, working release on branch `v1.2.0-working` and tag `v1.2.0`.
- The Whatnot packing slip PDF feature is under active development.

## [v1.1.0] - 2024-04-20

### Major Enhancements
- **Advanced Break/Autobox Builder:**
  - Modular, rule-based, and curated break list generation.
  - Dynamic filtering, live preview, cost calculation, and export.
  - Save/load rule sets, batch inventory operations, and undo support.
- **Whatnot Packing Slip Processing (in progress):**
  - Scan a folder of Whatnot packing slip PDFs and update inventory automatically (requires `pdfplumber`).
  - Buyer analytics and robust error handling.
- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.
- **Full test coverage and CI integration.**
- **Requirements and Documentation:**
  - All dependencies are now listed in `requirements.txt` for easy setup on any computer.
  - README updated with clear Quick Start, usage, and requirements.

### Status
- This is a stable, working release on branch `v1.1.0-working` and tag `v1.1.0`.
- The Whatnot packing slip PDF feature is under active development.

## [v1.0.0] - 2024-04-10

### Major Enhancements
- **Advanced Break/Autobox Builder:**
  - Modular, rule-based, and curated break list generation.
  - Dynamic filtering, live preview, cost calculation, and export.
  - Save/load rule sets, batch inventory operations, and undo support.
- **Whatnot Packing Slip Processing (in progress):**
  - Scan a folder of Whatnot packing slip PDFs and update inventory automatically (requires `pdfplumber`).
  - Buyer analytics and robust error handling.
- **Buyers Database & Analytics:**
  - Tracks buyers, purchase history, and analytics for future CRM features.
- **Full test coverage and CI integration.**
- **Requirements and Documentation:**
  - All dependencies are now listed in `requirements.txt` for easy setup on any computer.
  - README updated with clear Quick Start, usage, and requirements.

### Status
- This is a stable, working release on branch `v1.0.0-working` and tag `v1.0.0`.
- The Whatnot packing slip PDF feature is under active development.

## [v1.5.1] - 2024-06-XX

### Major Enhancements
- **Robust Sale Parsing:**
  - Card name and foil/normal status are now always split and normalized, even if the status is in the name (e.g., "Bribery normal").
  - Parsing logic is fully regression-tested for all known edge cases.
- **Improved Matching Logic:**
  - Cards are matched using name, set code, collector number, foil/normal, and language.
  - Fuzzy matching and set code aliases are used for best results.
  - Collector number is always compared as an exact string.
- **Ambiguity Handling:**
  - If multiple inventory cards match except for language, the user is prompted to resolve the ambiguity.
- **Undo/Restore:**
  - Every packing slip removal can be undone from the File menu.
- **No Auto-Remove:**
  - Cards are not removed from inventory or files moved until the user confirms.
- **Debugging:**
  - All not-found cards are logged with detailed debug output for troubleshooting.
- **Full Test Coverage:**
  - All core logic is covered by regression and edge-case tests.
  - Sale parsing and matching logic are tested for all known edge cases.
- **Documentation:**
  - README.md and this changelog are fully updated for all changes, with clear instructions for users and AI contributors.

### Status
- This is a stable, working release on branch `v1.5.1-working` and tag `v1.5.1`.
- All features are fully documented and regression-tested.
