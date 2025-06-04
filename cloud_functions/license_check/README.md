# License Check Google Cloud Function

This function provides secure license key validation for FoS-DeckPro using Google Sheets as the backend.

## Features
- Accepts POST requests with a license key, feature name, and machine ID.
- Checks the Google Sheet for license validity and returns a JSON response.
- Keeps your Google credentials secure (never distributed to users).

## Deployment (Google Cloud Functions)

### 1. Prepare
- Place your Google service account JSON in the function directory (e.g., `service_account.json`).
- Set the following environment variables when deploying:
  - `GOOGLE_APPLICATION_CREDENTIALS=service_account.json`
  - `SHEET_ID=your_google_sheet_id`
  - `WORKSHEET_NAME=Sheet1` (or your worksheet name)

### 2. Deploy (using gcloud CLI)

```
gcloud functions deploy license_check \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point license_check \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=service_account.json,SHEET_ID=your_google_sheet_id,WORKSHEET_NAME=Sheet1
```

- Replace `your_google_sheet_id` with your actual sheet ID.
- Adjust `WORKSHEET_NAME` if needed.

### 3. Test

Send a POST request:

```
curl -X POST https://REGION-PROJECT.cloudfunctions.net/license_check \
  -H "Content-Type: application/json" \
  -d '{"key": "LICENSE-KEY-HERE", "feature": "break_builder", "machine_id": "optional-machine-id"}'
```

## Usage in FoS-DeckPro
- Update your app to POST to this endpoint for license checks instead of accessing the Google Sheet directly.

## Security
- Never distribute your service account JSON to users.
- Restrict the service account's permissions to only the required Google Sheet. 