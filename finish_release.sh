#!/bin/bash
# finish_release.sh: Clean, merge, tag, and publish a new release
set -e

./clean_for_release.sh

echo "Enter new version tag (e.g., v1.5.4):"
read TAG
if [ -z "$TAG" ]; then
  echo "No tag provided. Exiting."
  exit 1
fi

git add .
git commit -am "chore: Prepare release $TAG" || true

git checkout v1.5.0-working
git merge --no-ff -m "Merge feature branch for $TAG" -X theirs -X patience -s recursive $(git branch --show-current)
git tag -a $TAG -m "Release $TAG"
git push && git push --tags

git checkout main
git merge --no-ff v1.5.0-working -m "Release $TAG to main"
git push

echo "Deleting old release branches (except v1.5.0-working and main)..."
for b in $(git branch | grep -E 'feature/|release/' | grep -v v1.5.0-working | grep -v main); do
  git branch -d $b || true
done

echo "Release $TAG published. Only the latest version is available in main."
echo "Next: Upload the new build to GitHub Releases and update the README badge if needed." 