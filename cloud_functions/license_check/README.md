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

## Service Account Credentials (Critical!)

- You **must** have your Google service account JSON file (with Sheets access) in this directory as `service_account.json` **before deploying**.
- To verify:
  1. Check that `service_account.json` is present in `cloud_functions/license_check/`.
  2. Run `ls -l service_account.json` and ensure the file is not empty and readable.
  3. The file **must** be listed in the output of `ls` before you run `./deploy_license_check.sh`.
  4. The file **must not** be in `.gitignore` for deployment, but should be in `.gcloudignore` to avoid accidental upload elsewhere.

### After Deployment
- If you see `FileNotFoundError: [Errno 2] No such file or directory: 'service_account.json'` in Cloud Function logs, the file was not included in the deployment package.
- To fix: Copy the file to this directory and redeploy.
- You can check the deployed files in the Cloud Console under Cloud Functions > license_check > Source.

### Troubleshooting
- Always redeploy after changing or adding `service_account.json`.
- If you rotate credentials, update the file and redeploy.
- If you see any credential or permission errors, check the file path, permissions, and that the service account has Editor access to the target Google Sheet.

> **NOTE:**
> - The `.gitignore` and `.gcloudignore` files in this directory are configured to ensure `service_account.json` is always included in Cloud Function deployments, but never committed to public repositories. See comments in those files and this README for details.
> - This is enforced for security and workflow compliance. Always follow the steps below for deployment and troubleshooting. 