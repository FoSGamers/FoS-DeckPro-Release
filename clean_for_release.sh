#!/bin/bash
# clean_for_release.sh: Remove all personal files for a clean public release
set -e

PERSONAL_FILES=(
  "FoS_DeckPro/Backups"
  "buyers.json"
  "For_Sale.json"
  "New_For_Sale.json"
  "packing_slip_summary.csv"
  "packing_slip_summary.json"
  "break_list.csv"
  "500 spot break.json"
  "50-30-15-5.json"
  "break_templates.json"
  "export_item_listing_fields_prefs.json"
  "fosbot-456712-d8da65f7bfc9.json"
  "client_secret_425804375982-49q9n1hgv592nhkmdup5egtj1eq6shq5.apps.googleusercontent.com (3).json"
  "live-7b09df55-5d0c-4dee-a698-6644a2abc082-all-slips-letter-size-168541b2.pdf"
  "Single_Shot_500.csv"
  "Whatnot Card Inventory - Template (3).csv"
  "Whatnot Card Inventory - Template (9).csv"
)

mkdir -p user_private

for f in "${PERSONAL_FILES[@]}"; do
  if [ -e "$f" ]; then
    echo "Moving $f to user_private/"
    mv "$f" user_private/ 2>/dev/null || mv "$f" user_private/ 2>/dev/null || true
  fi
  if git ls-files --error-unmatch "$f" > /dev/null 2>&1; then
    echo "Removing $f from git tracking"
    git rm --cached -r "$f" || true
  fi
done

echo "Personal files moved to user_private/ and removed from release." 