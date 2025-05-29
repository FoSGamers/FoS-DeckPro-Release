# ManaBox Enhancer

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

## Branching and Release Workflow (Best Practices)

- The `main` branch always contains the best working, stable, and production-ready code.
- All new features, bugfixes, or experimental work should be done in separate branches (e.g., `feature/xyz`, `experiment/v1.4.0-semi-working`).
- Only merge a feature or experiment branch into `main` after it is fully tested and confirmed to work as intended.
- Use tags (e.g., `v1.4.0`) to mark stable releases on the `main` branch.
- Avoid tagging experimental or semi-working versions as official releases unless needed for reference.
- Never push untested or unstable code directly to `main`.
- Always ensure `main` is deployable and represents the best working state.

This workflow ensures stability, traceability, and safe collaboration for all contributors. 