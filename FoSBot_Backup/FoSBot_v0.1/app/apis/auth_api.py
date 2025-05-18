# --- File: app/apis/auth_api.py --- START ---
import logging
import secrets # For generating secure state tokens
from urllib.parse import urlencode
# --- CORRECTED: Add missing imports from typing ---
from typing import Dict, Optional, Any
# --- End Correction ---
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
import httpx # For making backend HTTP requests to token endpoints

# --- Configuration ---
from app.core.config import (
    TWITCH_APP_CLIENT_ID, TWITCH_APP_CLIENT_SECRET, APP_SECRET_KEY
    # Import others as needed: YOUTUBE_APP_CLIENT_ID, etc.
)

# --- Token Storage ---
# Import necessary functions from json_store
from app.core.json_store import save_tokens, clear_tokens, get_setting, update_setting, load_tokens

# --- Event Bus ---
from app.core.event_bus import event_bus
from app.events import PlatformStatusUpdate, ServiceControl # To trigger service restart after auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Constants ---
# Ensure this exactly matches what you registered on Twitch Dev Console
TWITCH_REDIRECT_URI = "http://localhost:8000/auth/twitch/callback"
TWITCH_AUTHORIZATION_BASE_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate" # To get user info
TWITCH_REVOKE_URL = "https://id.twitch.tv/oauth2/revoke"
# Define required scopes (permissions)
# See: https://dev.twitch.tv/docs/authentication/scopes/
TWITCH_SCOPES = [
    "chat:read",        # Read chat messages
    "chat:edit",        # Send chat messages
    "channel:read:subscriptions", # Example: Check subscriptions (add more as needed)
    # "user:read:email", # Example: Get user email (optional) - Removed for simplicity unless needed
]

# Simple in-memory store for the state parameter (replace with something more robust if needed)
# Key: state_token, Value: platform (e.g., 'twitch') - Cleared after use
_oauth_state_store: Dict[str, str] = {}

# --- Helper Functions ---
def generate_state() -> str:
    """Generates a secure random state token."""
    return secrets.token_urlsafe(32)

def verify_state(received_state: str, platform: str) -> bool:
    """Verifies the received state token against the store and clears it."""
    stored_platform = _oauth_state_store.pop(received_state, None)
    if stored_platform == platform:
        return True
    logger.error(f"OAuth state mismatch! Expected platform '{platform}' for state '{received_state}', but found '{stored_platform}'. Possible CSRF attack.")
    return False

async def get_twitch_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Gets user ID and login using a validated access token."""
    # Ensure Client ID is available, as it's required for validate endpoint header
    if not TWITCH_APP_CLIENT_ID:
        logger.error("Cannot validate Twitch token: TWITCH_APP_CLIENT_ID is not configured.")
        return None

    headers = {
        "Authorization": f"OAuth {access_token}",
        # Twitch Validate endpoint requires Client-ID in header now (unlike older methods)
        "Client-ID": TWITCH_APP_CLIENT_ID
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(TWITCH_VALIDATE_URL, headers=headers)
            response.raise_for_status() # Raise exception for 4xx/5xx status
            data = response.json()

            # Validate response structure and ensure token belongs to our app
            if (data.get("user_id") and data.get("login") and
                data.get("client_id") == TWITCH_APP_CLIENT_ID):
                logger.info(f"Token validated successfully for user {data['login']} ({data['user_id']})")
                # Return only the necessary info for storage/use
                return {
                    "user_id": data["user_id"],
                    "user_login": data["login"],
                    "scopes": data.get("scopes", []) # Include granted scopes
                 }
            else:
                logger.error(f"Twitch validation response missing data or client_id mismatch: {data}")
                return None
        except httpx.RequestError as e:
            logger.error(f"HTTP request error validating Twitch token: {e}")
            return None
        except httpx.HTTPStatusError as e:
            # Handle specific errors like 401 Unauthorized (invalid token)
            if e.response.status_code == 401:
                 logger.warning(f"Twitch token validation failed (401 Unauthorized): {e.response.text}")
            else:
                 logger.error(f"HTTP status error validating Twitch token: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error validating Twitch token: {e}")
            return None

# --- Twitch Auth Endpoints ---

@router.get("/twitch/login")
async def twitch_login():
    """
    Initiates the Twitch OAuth flow by redirecting the user to Twitch.
    """
    if not TWITCH_APP_CLIENT_ID:
        logger.critical("Cannot initiate Twitch login: TWITCH_APP_CLIENT_ID is not configured in .env")
        raise HTTPException(status_code=500, detail="Twitch application credentials not configured on server.")

    state = generate_state()
    _oauth_state_store[state] = "twitch" # Store state with platform identifier
    logger.debug(f"Generated Twitch OAuth state: {state}")

    params = {
        "client_id": TWITCH_APP_CLIENT_ID,
        "redirect_uri": TWITCH_REDIRECT_URI,
        "response_type": "code", # Request authorization code
        "scope": " ".join(TWITCH_SCOPES), # Space-separated scopes
        "state": state,
        # "force_verify": "true", # Optional: Usually leave false for better UX
    }
    auth_url = f"{TWITCH_AUTHORIZATION_BASE_URL}?{urlencode(params)}"
    logger.info(f"Redirecting user to Twitch authorization URL...")
    return RedirectResponse(url=auth_url, status_code=307) # Use 307 Temporary Redirect

@router.get("/twitch/callback")
async def twitch_callback(code: Optional[str] = Query(None), state: Optional[str] = Query(None), scope: Optional[str] = Query(None), error: Optional[str] = Query(None), error_description: Optional[str] = Query(None)):
    """
    Handles the redirect back from Twitch after user authorization.
    Exchanges the code for tokens and stores them.
    """
    logger.info(f"Received Twitch callback. State: {state}, Code: {'***' if code else 'N/A'}, Error: {error}")

    # --- Verify State First ---
    if not state or not verify_state(state, "twitch"):
        raise HTTPException(status_code=400, detail="Invalid or missing OAuth state parameter. Potential CSRF attack.")

    if error:
        logger.error(f"Twitch OAuth error on callback: {error} - {error_description}")
        # Redirect back to dashboard with error message? Maybe store error in session?
        # For now, raise exception shown to user.
        raise HTTPException(status_code=400, detail=f"Twitch Auth Error: {error_description or error}")

    if not code:
         raise HTTPException(status_code=400, detail="Missing authorization code from Twitch.")

    if not TWITCH_APP_CLIENT_ID or not TWITCH_APP_CLIENT_SECRET:
        logger.critical("Cannot exchange code: Twitch App credentials missing on backend.")
        raise HTTPException(status_code=500, detail="Twitch application credentials not configured on server.")

    # --- Exchange code for tokens ---
    token_params = {
        "client_id": TWITCH_APP_CLIENT_ID,
        "client_secret": TWITCH_APP_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": TWITCH_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.debug("Requesting access token from Twitch...")
            response = await client.post(TWITCH_TOKEN_URL, data=token_params)
            response.raise_for_status() # Check for HTTP errors
            token_data = response.json()
            logger.info("Successfully received tokens from Twitch.")
            # Expected keys: 'access_token', 'refresh_token', 'expires_in', 'scope', 'token_type'

            # --- Get User Info (using the new token) ---
            user_info = await get_twitch_user_info(token_data['access_token'])
            if user_info:
                 # Add user_id, user_login, and validated scopes to token data before saving
                 token_data['user_id'] = user_info['user_id']
                 token_data['user_login'] = user_info['user_login']
                 token_data['scope'] = user_info['scopes'] # Use scopes confirmed by validation
                 logger.info(f"Validated token for Twitch user: {user_info['user_login']} ({user_info['user_id']})")

                 # Update the bot's Nick setting to match the logged-in user
                 # This assumes the user logging in IS the bot account
                 if await update_setting("TWITCH_NICK", user_info['user_login']):
                     logger.info(f"Updated TWITCH_NICK setting to: {user_info['user_login']}")
                 else:
                     logger.error("Failed to update TWITCH_NICK setting.")

            else:
                 logger.error("Failed to validate token and get user info after successful token exchange.")
                 # Proceed with saving tokens, but log the validation failure. User might need to retry.
                 # You could raise an exception here to prevent saving unvalidated tokens if preferred.

            # --- Save Tokens ---
            if await save_tokens("twitch", token_data):
                logger.info("Twitch tokens saved successfully.")
                # Publish status update and trigger service restart via event
                event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connected', message=f"Authenticated as {token_data.get('user_login', 'Unknown')}"))
                event_bus.publish(ServiceControl(service_name="twitch", command="restart"))
            else:
                logger.error("Failed to save Twitch tokens to storage.")
                raise HTTPException(status_code=500, detail="Failed to save authentication tokens.")

        except httpx.RequestError as e:
            logger.error(f"HTTP request error exchanging Twitch code: {e}")
            raise HTTPException(status_code=503, detail=f"Error contacting Twitch token endpoint: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error exchanging Twitch code: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Error from Twitch token endpoint: {e.response.text}")
        except Exception as e:
            logger.exception(f"Unexpected error during Twitch token exchange or saving: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error during authentication.")

    # Redirect back to the main dashboard page upon success
    return RedirectResponse(url="/?auth_success=twitch", status_code=303) # Use 303 See Other for POST-redirect-GET pattern

@router.post("/twitch/logout", status_code=200) # Use POST for logout action
async def twitch_logout():
    """ Clears Twitch tokens and attempts to revoke them. """
    logger.info("Processing Twitch logout request.")
    tokens = await load_tokens("twitch")
    access_token = tokens.get("access_token") if tokens else None

    # Always clear local tokens
    cleared_local = await clear_tokens("twitch")
    if not cleared_local:
        logger.error("Failed to clear local Twitch tokens from storage.")
        # Continue with revocation attempt anyway, but maybe return a different status?

    # Attempt to revoke token on Twitch side
    if access_token and TWITCH_APP_CLIENT_ID:
        revoke_params = {
            "client_id": TWITCH_APP_CLIENT_ID,
            "token": access_token
        }
        async with httpx.AsyncClient() as client:
            try:
                logger.debug("Attempting to revoke Twitch token...")
                response = await client.post(TWITCH_REVOKE_URL, data=revoke_params)
                if 200 <= response.status_code < 300:
                    logger.info("Successfully revoked Twitch token.")
                else:
                     # Log warning but don't necessarily fail the whole logout if revoke fails
                     logger.warning(f"Failed to revoke Twitch token. Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                 logger.error(f"Error during Twitch token revocation request: {e}")
    else:
        logger.info("Skipping Twitch token revocation (no access token or client ID found).")

    # Publish status update and trigger service stop via event
    event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disconnected', message="Logged out"))
    event_bus.publish(ServiceControl(service_name="twitch", command="stop"))

    # Return success even if revocation failed, as local tokens are cleared
    return {"message": "Twitch logout processed. Local tokens cleared."}


# --- Add Placeholders for YouTube and X ---

@router.get("/{platform}/login", status_code=501)
async def platform_login_nyi(platform: str):
    if platform in ["youtube", "x"]:
         raise HTTPException(status_code=501, detail=f"{platform.capitalize()} OAuth login not implemented yet.")
    else:
         raise HTTPException(status_code=404, detail="Unknown platform.")

@router.get("/{platform}/callback", status_code=501)
async def platform_callback_nyi(platform: str):
     if platform in ["youtube", "x"]:
          raise HTTPException(status_code=501, detail=f"{platform.capitalize()} OAuth callback not implemented yet.")
     else:
          raise HTTPException(status_code=404, detail="Unknown platform.")

@router.post("/{platform}/logout", status_code=501)
async def platform_logout_nyi(platform: str):
    if platform in ["youtube", "x"]:
         raise HTTPException(status_code=501, detail=f"{platform.capitalize()} OAuth logout not implemented yet.")
    else:
         raise HTTPException(status_code=404, detail="Unknown platform.")

# --- File: app/apis/auth_api.py --- END ---