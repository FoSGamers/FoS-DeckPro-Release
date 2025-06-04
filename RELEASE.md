# Release Process Guide

## Keeping Personal Files Private
- All personal files (backups, inventory, templates, sensitive configs, etc.) must be kept in the `user_private/` directory.
- `user_private/` is listed in `.gitignore` and will never be committed or pushed to public branches.
- Only code, resources, and documentation needed for others to use or run the app should be present in the release branch.

## Automated Cleaning Script
- Use the `clean_for_release.sh` script before every release to remove or move personal files.
- The script will:
  - Move all personal files to `user_private/`.
  - Ensure only public files are present in the release branch.
- Run the script with:
  ```sh
  ./clean_for_release.sh
  ```

## Merging Code Changes Safely
- Do all development (including with personal files) on the `personal-dev` branch.
- When ready to release:
  1. Run `git checkout v1.5.0-working` to switch to the release branch.
  2. Merge or cherry-pick code changes from `personal-dev` (avoid merging personal files).
  3. Run `./clean_for_release.sh` to ensure the release is clean.
  4. Commit and push the release branch.
- Never merge `user_private/` or personal files into the release branch.

## Checklist for Every Release
- [ ] All personal files are in `user_private/`.
- [ ] `./clean_for_release.sh` has been run.
- [ ] Only public files are present in the release branch.
- [ ] Code changes have been merged/cherry-picked from `personal-dev`.
- [ ] All tests pass and documentation is up to date.
- [ ] Commit and push the release branch. 