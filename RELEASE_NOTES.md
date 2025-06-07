# 🚀 FoS-DeckPro v1.6.0

> **Release Date:** 2024-06-05  
> **Maintainer:** [@FoSGamers](https://github.com/FoSGamers)

---

## ✨ What's New in v1.6.0

- **Unified License & Trial System**
  All paid features now use a single, user-friendly dialog: start a free trial or enter a license key at any time.
  Secure backend (Google Cloud Function) manages all license/trial logic—no backend credentials ever shipped to users.

- **Modern, Modular Codebase**
  Every feature is independently enable/disable-able.
  Centralized configuration and robust error handling throughout.
  All code is modular, maintainable, and extensible for future features.

  - Every feature is independently enable/disable-able.
  - Centralized configuration and robust error handling throughout.
  - All code is modular, maintainable, and extensible for future features.

- **Documentation & Workflow**
  - All documentation, ignore files, and workflow scripts are up to date.
  - CHANGELOG, README, and onboarding docs are current and explicit for public release.

- **Admin Tool (Private)**
  - Powerful admin dashboard for license/trial management (never included in public releases).
  - Full documentation and onboarding for maintainers.

---

## 🛠️ Major Features

- **Break Builder**: Build and export Whatnot breaks with advanced filtering, curation, and rule-based workflows.
- **Packing Slip Processor**: Scan Whatnot packing slip PDFs, extract singles sold, and remove them from inventory with best-match logic.
- **Buyers Database & Analytics**: Track all buyers, purchase history, and analytics in a modular, extensible database.
- **Undo/Restore**: Instantly undo packing slip removals for safety and flexibility.
- **Scryfall Enrichment**: Instantly auto-fill card details and images using Scryfall for any card in your inventory or break.
- **Product Listing Export**: Export your inventory or break as a CSV for easy copy/paste into product listings (Whatnot, Shopify, TCGplayer, eBay, etc.).
- **Modern UI/UX**: Clean, resizable, and user-friendly interface throughout the app.
- **Full Test Coverage**: All core logic is fully tested for reliability.

---

## 🚦 How to Get Started

1. **Install requirements:**
   ```sh
   pip install -r FoS_DeckPro/requirements.txt
   ```
2. **Launch the app:**
   ```sh
   python3 FoS_DeckPro/main.py
   ```
3. **Access paid features:**
   - When prompted, start a free trial or enter a license key.

---

## 💡 Free vs. Paid Features

**Free Features:**
- Inventory management (import/export, local database, view/edit/delete/filter/search)

**Paid Features (Require License Key):**
- All Whatnot features (break builder, export listing, packing slip tools, analytics)
- Add card via Scryfall
- Scryfall enrichment (auto-fill card details/images)

---

## 🔑 License Key System
- Paid features are locked by default.
- On first use of a paid feature, you will be prompted to enter a license key or start a free trial.
- The app checks your key online and unlocks only the features your key is valid for.
- License key is stored locally for future use.
- Each paid feature can be unlocked for a limited time (subscription) or permanently (lifetime).
- All license key and expiration management is handled automatically.

**To request a license key for paid features, contact:** Thereal.FosGameres@gmail.com

---

## 🛣️ Roadmap & Future Directions
- **Upcoming Integrations:**
  - Direct export and integration with Shopify, TCGplayer, and eBay for seamless product listing management (planned).
- **Deckbuilding Features:**
  - Future versions will include a full-featured deckbuilder, allowing users to build, save, and analyze decks like a pro (FoS-DeckPro).

---

## 📝 Full Changelog
See [CHANGELOG.md](https://github.com/FoSGamers/FoS-DeckPro/blob/main/CHANGELOG.md) for detailed history.

---

## 💬 Support & Feedback
- [Open an Issue](https://github.com/FoSGamers/FoS-DeckPro/issues)
- [Read the Docs](https://github.com/FoSGamers/FoS-DeckPro#readme)
- [Contact Maintainer](mailto:Thereal.FosGameres@gmail.com)

---

**Thank you for using FoS-DeckPro!**

## Overview
This release focuses on improving code quality, documentation, and security measures.

## Changes
- Updated all Standards files to use generic private directory references
- Improved git hooks for better security
- Enhanced documentation for debugging and release processes
- Archived v1.5.0-working branch

## Security
- Enhanced git hooks to better protect private content
- Improved documentation for security practices
- Added more comprehensive debugging guides

## Documentation
- Updated Standards files with clearer guidelines
- Enhanced debugging documentation
- Improved release process documentation

## Technical Details
- Updated git hooks for better pattern matching
- Improved error handling in security checks
- Enhanced documentation structure

## Known Issues
None

## Future Plans
- Continue improving security measures
- Enhance documentation further
- Implement additional debugging tools

## Support
For support, please refer to SUPPORT.md or create an issue in the repository. 