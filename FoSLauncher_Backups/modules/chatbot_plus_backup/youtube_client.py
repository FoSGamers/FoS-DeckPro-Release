import os
import json
import logging
import webbrowser
from typing import Dict, Any, Optional
import tkinter as tk
from tkinter import messagebox, simpledialog
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from modules.logger import logger

class YouTubeClient:
    def __init__(self, client_secrets_path: str):
        self.client_secrets_path = client_secrets_path
        self.credentials = None
        self.service = None
        
    def show_error(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an error message in the main thread"""
        if root:
            root.after(0, lambda: messagebox.showerror("Error", message))
        else:
            logger.error(message)
            
    def show_info(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an info message in the main thread"""
        if root:
            root.after(0, lambda: messagebox.showinfo("Information", message))
        else:
            logger.info(message)
            
    def setup_credentials(self, root: Optional[tk.Tk] = None) -> bool:
        """Guide user through setting up YouTube API credentials"""
        try:
            # Create credentials directory if it doesn't exist
            creds_dir = os.path.dirname(self.client_secrets_path)
            os.makedirs(creds_dir, exist_ok=True)
            
            # Check if credentials already exist
            if os.path.exists(self.client_secrets_path):
                return True
                
            # Show setup instructions
            instructions = (
                "To use YouTube features, you need to set up API credentials:\n\n"
                "1. Go to https://console.cloud.google.com\n"
                "2. Create a new project or select an existing one\n"
                "3. Enable the YouTube Data API v3\n"
                "4. Create OAuth 2.0 credentials\n"
                "5. Download the credentials file\n"
                "6. Rename it to 'client_secrets.json'\n"
                "7. Place it in the modules/chatbot_plus directory\n\n"
                "Would you like to open the Google Cloud Console now?"
            )
            
            if root:
                response = messagebox.askyesno("YouTube Setup", instructions)
                if response:
                    webbrowser.open("https://console.cloud.google.com")
                    # Wait for user to complete setup
                    messagebox.showinfo(
                        "Setup Complete",
                        "Please place the downloaded credentials file in the modules/chatbot_plus directory and click OK."
                    )
                    return os.path.exists(self.client_secrets_path)
            else:
                logger.info(instructions)
                return False
                
        except Exception as e:
            self.show_error(root, f"Error during setup: {str(e)}")
            return False
            
    def authenticate(self, root: Optional[tk.Tk] = None) -> bool:
        """Authenticate with YouTube API"""
        try:
            logger.info("Starting YouTube authentication process")
            
            # Check if credentials exist, if not guide user through setup
            logger.debug(f"Looking for credentials at: {self.client_secrets_path}")
            if not os.path.exists(self.client_secrets_path):
                logger.error(f"Credentials file not found at: {self.client_secrets_path}")
                if not self.setup_credentials(root):
                    logger.error("Failed to set up credentials")
                    return False
                    
            # Load or create credentials
            creds = None
            token_path = os.path.join(os.path.dirname(self.client_secrets_path), "token.json")
            logger.debug(f"Token path: {token_path}")
            
            if os.path.exists(token_path):
                logger.debug("Found existing token file")
                try:
                    creds = Credentials.from_authorized_user_file(token_path)
                    logger.debug("Successfully loaded credentials from token file")
                except Exception as e:
                    logger.error(f"Error loading credentials from token file: {e}")
                    # If token file is invalid, remove it
                    os.remove(token_path)
                    creds = None
                
            if not creds or not creds.valid:
                logger.debug("No valid credentials found, starting OAuth flow")
                if creds and creds.expired and creds.refresh_token:
                    logger.debug("Refreshing expired credentials")
                    try:
                        creds.refresh(Request())
                        logger.debug("Successfully refreshed credentials")
                    except Exception as e:
                        logger.error(f"Error refreshing credentials: {e}")
                        creds = None
                else:
                    # Show authentication in browser
                    logger.debug("Starting new OAuth flow")
                    try:
                        # Load client secrets
                        logger.debug("Loading client secrets file")
                        with open(self.client_secrets_path, 'r') as f:
                            client_secrets = json.load(f)
                        
                        # Update redirect URIs to include port-specific URIs
                        if 'installed' in client_secrets:
                            redirect_uris = client_secrets['installed'].get('redirect_uris', [])
                            logger.debug(f"Current redirect URIs: {redirect_uris}")
                            
                            for port in range(8001, 8004):
                                uri = f"http://localhost:{port}/oauth2callback"
                                if uri not in redirect_uris:
                                    redirect_uris.append(uri)
                            client_secrets['installed']['redirect_uris'] = redirect_uris
                            logger.debug(f"Updated redirect URIs: {redirect_uris}")
                            
                            # Save updated client secrets
                            with open(self.client_secrets_path, 'w') as f:
                                json.dump(client_secrets, f)
                            logger.debug("Saved updated client secrets")
                        
                        logger.debug("Creating OAuth flow")
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.client_secrets_path,
                            ["https://www.googleapis.com/auth/youtube.force-ssl"]
                        )
                        logger.debug("Starting local server for OAuth flow")
                        creds = flow.run_local_server(
                            port=0,
                            success_message="Authentication successful! You can close this window.",
                            open_browser=True
                        )
                        logger.debug("Successfully completed OAuth flow")
                    except Exception as e:
                        logger.error(f"Error during OAuth flow: {e}", exc_info=True)
                        self.show_error(root, f"Authentication failed: {str(e)}")
                        return False
                    
                # Save credentials
                try:
                    logger.debug("Saving credentials to token file")
                    with open(token_path, "w") as token:
                        token.write(creds.to_json())
                    logger.debug("Successfully saved credentials to token file")
                except Exception as e:
                    logger.error(f"Error saving credentials: {e}")
                    self.show_error(root, f"Failed to save credentials: {str(e)}")
                    return False
                    
            self.credentials = creds
            logger.debug("Building YouTube service")
            self.service = build("youtube", "v3", credentials=creds)
            
            # Verify the credentials work by making a test API call
            try:
                logger.debug("Verifying credentials with test API call")
                self.get_channel_info()
                logger.info("Successfully authenticated with YouTube!")
                self.show_info(root, "Successfully authenticated with YouTube!")
                return True
            except Exception as e:
                logger.error(f"Error verifying credentials: {e}", exc_info=True)
                self.show_error(root, f"Failed to verify YouTube API access: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            self.show_error(root, f"Authentication error: {str(e)}")
            return False
            
    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the authenticated channel"""
        try:
            if not self.service:
                return None
                
            request = self.service.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            
            if response["items"]:
                return response["items"][0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None 