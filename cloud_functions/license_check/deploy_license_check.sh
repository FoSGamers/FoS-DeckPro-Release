#!/bin/bash

# FoS-DeckPro License Check Cloud Function Deployment Script
# --------------------------------------------------------
# This script automates the deployment of the license_check Google Cloud Function.
# It checks for gcloud CLI, prompts for authentication and project selection if needed,
# and deploys the function with all required environment variables.
#
# Usage: ./deploy_license_check.sh
#
# Requirements:
# - gcloud CLI installed (https://cloud.google.com/sdk/docs/install)
# - You must have a Google Cloud project and billing enabled
# - service_account.json must be present in this directory
#
# This script is idempotent and safe to run multiple times.

set -e

# Configurable variables
FUNCTION_NAME="license_check"
RUNTIME="python310"
ENTRY_POINT="license_check"
TRIGGER="--trigger-http"
ALLOW_UNAUTH="--allow-unauthenticated"
SERVICE_ACCOUNT_JSON="service_account.json"
SHEET_ID="1hvOb_2fADbCs3DSLg0CMOdCAOVAy2Is_ok0JIvqAZEY"
WORKSHEET_NAME="Sheet1"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "[ERROR] gcloud CLI not found. Please install it first: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check for service account JSON
if [ ! -f "$SERVICE_ACCOUNT_JSON" ]; then
    echo "[ERROR] $SERVICE_ACCOUNT_JSON not found in $(pwd). Please add your Google service account credentials."
    exit 1
fi

# Authenticate if needed
if ! gcloud auth list --format="value(account)" | grep -q "@"; then
    echo "[INFO] No active gcloud account. Launching login..."
    gcloud auth login
fi

# Set project if not set
if [ -z "$(gcloud config get-value project 2>/dev/null)" ]; then
    echo "[INFO] No active gcloud project. Launching project selector..."
    gcloud projects list
    echo "Enter your Google Cloud project ID: "
    read PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

# Deploy the function
echo "[INFO] Deploying $FUNCTION_NAME to Google Cloud Functions..."
gcloud functions deploy "$FUNCTION_NAME" \
  --runtime "$RUNTIME" \
  $TRIGGER \
  $ALLOW_UNAUTH \
  --entry-point "$ENTRY_POINT" \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=$SERVICE_ACCOUNT_JSON,SHEET_ID=$SHEET_ID,WORKSHEET_NAME=$WORKSHEET_NAME

# Print the deployed function URL
echo "[INFO] Deployment complete. Your function URL is:"
gcloud functions describe "$FUNCTION_NAME" --format='value(httpsTrigger.url)'

echo "[INFO] Update LICENSE_API_URL in your app with the above URL." 