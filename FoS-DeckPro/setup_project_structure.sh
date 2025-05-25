#!/bin/bash
# setup_project_structure.sh
# Idempotently create the directory structure and empty files for ManaBox Enhancer modular PySide6 project

set -e

mkdir -p ManaBox_Enhancer/models
mkdir -p ManaBox_Enhancer/logic
mkdir -p ManaBox_Enhancer/ui/dialogs
mkdir -p ManaBox_Enhancer/utils
mkdir -p ManaBox_Enhancer/resources
mkdir -p ManaBox_Enhancer/tests
mkdir -p ManaBox_Enhancer/docs

# Top-level files
for f in main.py README.md CONTRIBUTING.md CHANGELOG.md; do
  touch ManaBox_Enhancer/$f
done

# models
for f in __init__.py card.py inventory.py filters.py scryfall_api.py; do
  touch ManaBox_Enhancer/models/$f
done

# logic
for f in __init__.py merge.py price.py export.py backup.py; do
  touch ManaBox_Enhancer/logic/$f
done

# ui
for f in __init__.py main_window.py card_table.py filter_row.py image_preview.py; do
  touch ManaBox_Enhancer/ui/$f
done

# ui/dialogs
for f in __init__.py column_customization.py listing.py advanced_filter.py; do
  touch ManaBox_Enhancer/ui/dialogs/$f
done

# utils
for f in __init__.py config.py logging.py; do
  touch ManaBox_Enhancer/utils/$f
done

# tests
for f in __init__.py test_inventory.py test_merge.py; do
  touch ManaBox_Enhancer/tests/$f
done

# docs
for f in ui-style-guide.md architecture.md; do
  touch ManaBox_Enhancer/docs/$f
done 