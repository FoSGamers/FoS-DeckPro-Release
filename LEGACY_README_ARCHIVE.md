# LEGACY_README_ARCHIVE.md

> **Private/Internal Archive**
> 
> This file contains all legacy, detailed, and historical documentation, rules, workflows, and notes from previous versions of the README. It is for private reference only and should not be distributed publicly. Nothing is ever lost—every rule, workflow, and detail is preserved here for your records.

---

## Table of Contents
- [How to Use](#how-to-use)
- [Beginner FAQ](#beginner-faq)
- [Troubleshooting](#troubleshooting)
- [Where to Get Help](#where-to-get-help)
- [License](#license)
- [Release Notes](#release-notes)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [Roadmap](#roadmap)
- [Use Cases](#use-cases)
- [Credits & Acknowledgments](#credits--acknowledgments)
- [Licensing & Commercial Use](#licensing--commercial-use)
- [Known Issues](#known-issues)
- [Monetization & Add-ons](#monetization--add-ons)
- [Release Status](#release-status)
- [Free vs. Paid Features](#free-vs-paid-features)
- [License Key Activation](#license-key-activation)
- [Release and Privacy Process](#release-and-privacy-process)
- [Release Hygiene & Personal Data](#release-hygiene--personal-data)
- [How to Build a Clean Release](#how-to-build-a-clean-release)
- [Build Artifact Hygiene](#build-artifact-hygiene)

---

## How to Use

### Quick Start
1. **Install requirements:**
   ```sh
   pip install -r FoS_DeckPro/requirements.txt
   ```
2. **Launch the app:**
   ```sh
   python3 FoS_DeckPro/main.py
   ```
3. **Build a Break or Process Packing Slips:**
   - Use the GUI to access the Break Builder or Packing Slip Processor from the Tools menu.
   - Follow on-screen instructions for each workflow.

### Example Workflow
- **Build a Whatnot Break:**
  1. Open the Break Builder.
  2. Filter/select cards, set rules, and preview the break.
  3. Export the break list for Whatnot.
- **Remove Sold Cards from Inventory:**
  1. Open the Packing Slip Processor.
  2. Select your Whatnot PDF(s).
  3. Review matches, resolve ambiguities, and confirm removals.

---

## Beginner FAQ
- **Q: What is FoS-DeckPro?**
  - A modular tool for managing card inventory, building Whatnot breaks, and processing packing slips.
- **Q: Do I need to know Python?**
  - No, the app is fully GUI-based for normal use.
- **Q: Where are my break templates?**
  - In the project root (e.g., `50-30-15-5.json`).
- **Q: How do I undo a removal?**
  - Use the Undo option in the File menu after processing a packing slip.

---

## Troubleshooting
- **App won't start:**
  - Ensure all requirements are installed and you are running from the correct directory.
- **GUI errors in headless environments:**
  - Use Xvfb for GUI tests or run on a local desktop.
- **Packing slip not matching cards:**
  - Check that inventory and slip data are up to date and formatted correctly.
- **Still stuck?**
  - See [Where to Get Help](#where-to-get-help).

---

## Where to Get Help
- **GitHub Issues:** [Open an issue](https://github.com/YOUR_GITHUB_REPO/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_GITHUB_REPO/discussions)
- **Email:** Thereal.FosGameres@gmail.com
- **Community Chat:** (Add Discord/Matrix/Slack link if available)

---

## License
FoS-DeckPro is released under the MIT License. See [LICENSE](LICENSE) for details.

---

## Release Notes
See [CHANGELOG.md](CHANGELOG.md) for full details. v1.5.1 is a stable, working release with all core workflows tested and documented.

---

## Contributing
We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and how to get started.

---

## Code of Conduct
All contributors and users are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Roadmap
- [ ] API integration with Whatnot (future)
- [ ] Support for packs, bundles, and accessories
- [ ] Enhanced analytics and reporting
- [ ] Multi-language support
- [ ] Community plugin system

---

## Use Cases
- **Card Sellers:** Manage inventory, build and export Whatnot breaks, and process sales efficiently.
- **Streamers:** Quickly generate break lists and overlays for live sales.
- **Shops:** Track buyers, automate packing slip processing, and maintain accurate inventory.

---

## Credits & Acknowledgments
- Project lead: [Your Name]
- Contributors: See [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Special thanks to the open source community and all testers.

## Whatnot Export Rules

- **Whatnot Price Minimum:** If a card's Whatnot price is 0, it will be exported as 1 in the Whatnot export CSV. This ensures no item is listed with a price of 0.

## Documentation Policy

- **Rule Tracking:** Any new business rule, export logic, or user-specified behavior must be documented in this README immediately upon implementation. This ensures all requirements are tracked and visible to all contributors.

## Whatnot Breaks & Autoboxes Integration Rules

- **Current State:** Only singles (individual cards) are supported for Whatnot Breaks and autoboxes. All randomization, assignment, and buyer fulfillment is handled exclusively by Whatnot's Breaks tool. No external randomizers or assignment logic are ever used.
- **Workflow:**
  1. Build a prize list of singles in the app or spreadsheet.
  2. Import/paste/upload the list into Whatnot's Breaks interface.
  3. Configure break settings and go live; Whatnot handles all assignments and tracking.
  4. After the break, export the assignment report/manifest from Whatnot for fulfillment, shipping, overlays, and recordkeeping.
  5. The Whatnot manifest is the only source of truth for fulfillment and post-break actions.
- **No External Logic:** No randomization, assignment, or fulfillment is performed outside Whatnot. The app must never implement or suggest external randomization or assignment.
- **Import/Export:** The app must always provide a clean, copy-paste or CSV workflow for importing lists into Whatnot and exporting manifests back for fulfillment.
- **Display/Overlay Tools:** Any display, overlay, or "what's left" tools must reference Whatnot's exported data, not the app's internal state.
- **Future State:** The app must be expandable to support packs, bundles, custom sets, accessories, promos, and mixed-item breaks, using the same workflow and rules. All upgrades must maintain this process and user experience.
- **Absolute Rules:**
  - Current: Singles-only support, always via Whatnot Breaks.
  - Future: Expandable to any inventory item (packs, bundles, accessories) with the same copy-paste/import/export process.
  - No randomization, assignment, or fulfillment outside Whatnot.
  - Manifest = source of truth for all post-break actions.

## Whatnot Integration Status

- **Current:** There is no direct API integration with Whatnot. All workflows are manual: users copy and paste the required Title and Description rows from the app into Whatnot's Breaks interface. No other columns are needed for breaks at this time.
- **Future:** API integration is planned. When API access and documentation are available, the app and this README will be updated to support and document direct integration, automation, and new workflows as needed.

---

## Licensing & Commercial Use

FoS-DeckPro is dual-licensed:
- **Non-commercial, personal use:** Free for evaluation and personal projects only.
- **Commercial use:** Any use by businesses, organizations, or for-profit activities requires a paid commercial license.

**You may not use, copy, modify, or distribute this software for commercial purposes without written permission.**

To obtain a commercial license or paid feature access, contact: Thereal.FosGameres@gmail.com

See [LICENSE](LICENSE) for full terms.

## Known Issues

- The only known issue in this release is that the **Customize Columns** feature does not work. This is a trivial UI bug and does not affect any core functionality or data integrity.

## Monetization & Add-ons

- The base app (inventory management and Scryfall enrichment) is free and open source.
- All other features (break builder, packing slip tools, analytics, etc.) are planned as paid add-ons/plugins in future versions. The codebase is structured to support this model without risk to the core app.

## Release Status

- This version is a stable, working release. All core features work as intended except for the minor known issue above.

## Free vs. Paid Features

### Free Features
- Inventory management (import/export from ManaBox or CSV, local database, view/edit/delete/filter/search)

### Paid Features (Require License Key)
- All Whatnot features (break builder, export listing, packing slip tools, analytics)
- Add card via Scryfall
- Scryfall enrichment (auto-fill card details/images)

## License Key Activation
- Paid features are locked by default.
- On first use of a paid feature, you will be prompted to enter a license key.
- The app checks your key online (Google Sheets) and unlocks only the features your key is valid for.
- License key is stored locally for future use.

### Subscription & Lifetime Licenses
- Each paid feature can be unlocked for a limited time (subscription) or permanently (lifetime).
- The license key generator allows you to set per-feature expiration and license type.
- When a feature's subscription expires, the app will prompt you to renew and will not unlock the feature until a new key is entered.
- Lifetime features never expire.
- All license key and expiration management is handled automatically; you never need to edit the Google Sheet manually.
- The app and key generator will always update the sheet with any new features or columns as needed.

**To request a license key for paid features, contact: Thereal.FosGameres@gmail.com**

For more details, see the in-app help or contact support at the email above.

# FoS-DeckPro License Key Generator (Private)

**This repository is private and for maintainers only. Do not share or publish these scripts.**

## Overview
This repository contains the license key generator tools for FoS-DeckPro. Use these scripts to generate, hash, and insert license keys into the Google Sheet that controls access to paid features in the public app.

- Supports per-feature subscription/lifetime licensing and expiration.
- Automatically updates the Google Sheet with any new features or columns.
- GUI and CLI tools included.

## Security Warning
- This repository contains sensitive scripts and credentials. Do **not** share or publish this code.
- Only trusted maintainers should have access.

## Usage

### 1. **Google Service Account Credentials**
- The file `fosbot-456712-d8da65f7bfc9.json` is your Google service account credentials.
- The service account must have edit access to the license Google Sheet.
- Never share this file outside trusted maintainers.

### 2. **GUI License Key Generator**
- Run the GUI tool:
  ```sh
  python3 generate_license_key_gui.py
  ```
- Fill in user info, select features, set license type (subscription/lifetime), and expiration dates as needed.
- Click "Generate License Key". The key will be hashed and added to the Google Sheet.
- Use the "Copy" button to copy the generated key for distribution.

### 3. **CLI License Key Generator**
- (If you have a CLI version, document usage here. Otherwise, remove this section.)

### 4. **Google Sheet Structure**
- The generator will automatically update the sheet header to include all required columns for features, expiration, and license type.
- No manual editing is required.

## Notes
- Only distribute license keys to users who have paid for features.
- For any questions or issues, contact the project lead.

## Whatnot Packing Slip Processing:

- **Sale Parsing:** Card name and foil/normal status are always split and normalized, even if the status is in the name (e.g., "Bribery normal").
- **Matching:** Cards are matched if at least three fields match, with collector number, foil/normal, and set code prioritized after name. Fuzzy matching and set code aliases are used for best results.
- **Ambiguity Handling:** If multiple inventory cards match except for language, and language is not specified, the user is prompted to resolve the ambiguity.
- **Undo/Restore:** Every packing slip removal can be undone from the File menu.
- **No Auto-Remove:** Cards are not removed from inventory or files moved until the user confirms.
- **Debugging:** All not-found cards are logged with detailed debug output for troubleshooting.

## Release and Privacy Process

- All personal files (backups, inventory, templates, sensitive configs, etc.) must be kept in the `user_private/` directory.
- `user_private/` is listed in `.gitignore` and will never be committed or pushed to public branches.
- Before every release, run the `clean_for_release.sh` script to ensure no personal files are present in the release branch.
- See `RELEASE.md` and `CONTRIBUTING.md` for full instructions on safe merging and release management.

## Release Hygiene & Personal Data

- **A GitHub Action will block any release or PR if personal files are present.**
- All contributors must read and follow [RELEASE.md](RELEASE.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for every release or merge.
- All personal files (backups, inventory, templates, sensitive configs) must be kept in `user_private/` (which is in `.gitignore`).
- Never commit or push personal files to the release branch.
- **Never commit build artifacts or large files. See Build Artifact Hygiene above.**
- Use the `clean_for_release.sh` script before every release to ensure no personal files are present.

## How to Build a Clean Release

1. Run `./clean_for_release.sh` to move/remove all personal files.
2. Verify only public files are present.
3. Build and package the app as described above.

See `RELEASE.md` and `CONTRIBUTING.md` for full details.

## Build Artifact Hygiene
- **Never commit build artifacts or large files (e.g., dist/, build/, *.zip, *.pkg, *.app, *.spec, *.dmg, *.exe, *.bin, *.tar.gz, *.whl, *.egg, *.pyc, __pycache__/).**
- Always add these to `.gitignore`.
- Clean them from git tracking before pushing or releasing.
- Only source code, scripts, and documentation should be versioned. 