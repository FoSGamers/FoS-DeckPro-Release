#!/bin/bash
# start_feature.sh: Start a new feature branch from personal-dev
set -e

echo "Enter feature name (use-dashes-not-spaces):"
read FEATURE
if [ -z "$FEATURE" ]; then
  echo "No feature name provided. Exiting."
  exit 1
fi
BRANCH="feature/$FEATURE"
git checkout personal-dev
if git rev-parse --verify $BRANCH >/dev/null 2>&1; then
  echo "Branch $BRANCH already exists. Switching to it."
  git checkout $BRANCH
else
  git checkout -b $BRANCH
fi
echo "Now on branch: $(git branch --show-current)" 