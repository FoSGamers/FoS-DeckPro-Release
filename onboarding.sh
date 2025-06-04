#!/bin/bash
# onboarding.sh: Print repo status and next steps
set -e

BRANCH=$(git branch --show-current)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")

echo "\n=== FoS-DeckPro Onboarding ==="
echo "Current branch: $BRANCH"
echo "Last release tag: $LAST_TAG"
echo ""
echo "Common next steps:"
echo "- To start a new feature: ./start_feature.sh"
echo "- To finish and release: ./finish_release.sh"
echo "- To clean personal files: ./clean_for_release.sh"
echo "- To see release process: cat RELEASE.md"
echo "- To see contributor guide: cat CONTRIBUTING.md"
echo "- To see latest release: git tag --sort=-creatordate | head -n 1"
echo "- To check for personal files: ./clean_for_release.sh --check"
echo ""
echo "Always work on a feature branch or personal-dev, never directly on main or v1.5.0-working!"
echo "==============================\n" 