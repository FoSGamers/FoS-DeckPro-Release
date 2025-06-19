#!/bin/bash

# APTPT Phase 1: Setup
echo "[APTPT] Setting up test environment..."
python -m pip install -r requirements.txt

# APTPT Phase 2: Run Tests
echo "[APTPT] Running tests..."
pytest tests/ -v --cov=. --cov-report=term-missing

# APTPT Phase 3: Check Coverage
COVERAGE_THRESHOLD=80
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')

if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
    echo "[APTPT] Warning: Test coverage ($COVERAGE%) is below threshold ($COVERAGE_THRESHOLD%)"
    exit 1
else
    echo "[APTPT] Test coverage ($COVERAGE%) is above threshold ($COVERAGE_THRESHOLD%)"
fi

# APTPT Phase 4: Cleanup
echo "[APTPT] Cleaning up..."
rm -rf .coverage
rm -rf htmlcov 