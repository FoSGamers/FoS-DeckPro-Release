# Release Process for FoS-DeckPro

## 1. Clean Personal Files Before Release
- All personal files (backups, inventory, templates, sensitive configs, etc.) must be moved to `user_private/`.
- `user_private/` is in `.gitignore` and will never be included in a public release.
- Run the provided script before every release:

```sh
./clean_for_release.sh
```

This script will:
- Move all personal files to `user_private/` (if not already there)
- Remove any lingering personal files from tracked locations
- Verify only public files are present

## 2. Branch Management
- **Develop with personal files** on the `personal-dev` branch.
- **Release code** from the `v1.5.0-working` (or main) branch, which is always clean.
- To merge code changes:
  1. Commit your work on `personal-dev`.
  2. Switch to `v1.5.0-working`.
  3. Merge or cherry-pick code changes (not personal files).
  4. Run `./clean_for_release.sh` and verify.
  5. Build and push the release.

## 3. What Files Are Included in a Release?
- Only code, resources, and documentation needed for others to use or run the app.
- No personal data, backups, or sensitive configs.

## 4. Building and Packaging
- Use PyInstaller as described in the README to build the app for release.
- Package only the cleaned files for distribution.

## 5. Questions?
- Contact the maintainer for help with the release process or branch management. 