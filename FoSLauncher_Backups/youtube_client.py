import os
import json
import logging
import webbrowser
import asyncio
import websockets
from typing import Dict, Any, Optional, List, Union, Tuple
import tkinter as tk
import customtkinter as ctk
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
        self.authenticated = False
        self.live_chat_id = None
        self.next_page_token = None
        self.running = False
        self.ws_client = None
        self.ws_uri = "ws://127.0.0.1:8001/ws"
        self.channel_id = None
        self.retry_count = 0
        self.max_retries = 5
        self.last_stream_check = None
        self.has_permission = False
        self.config: Dict[str, Any] = {}
        
    def show_error(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an error message in the main thread"""
        if root and isinstance(root, (tk.Tk, tk.Toplevel, ctk.CTk, ctk.CTkToplevel)):
            root.after(0, lambda: messagebox.showerror("Error", message))
        else:
            logger.error(message)
            
    def show_info(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an info message in the main thread"""
        if root and isinstance(root, (tk.Tk, tk.Toplevel, ctk.CTk, ctk.CTkToplevel)):
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
                "7. Place it in the modules/youtube_login directory\n\n"
                "Would you like to open the Google Cloud Console now?"
            )
            
            if root:
                response = messagebox.askyesno("YouTube Setup", instructions)
                if response:
                    webbrowser.open("https://console.cloud.google.com")
                    # Wait for user to complete setup
                    messagebox.showinfo(
                        "Setup Complete",
                        "Please place the downloaded credentials file in the modules/youtube_login directory and click OK."
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
                            [
                                "https://www.googleapis.com/auth/youtube.force-ssl",
                                "https://www.googleapis.com/auth/youtube.readonly",
                                "https://www.googleapis.com/auth/youtube"
                            ]
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
            self.authenticated = True
            
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
                self.channel_id = response["items"][0]["id"]
                return response["items"][0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None

    def list_available_streams(self) -> Union[List[Dict[str, Any]], str]:
        """List available YouTube streams"""
        try:
            if not self.authenticated:
                return "Please authenticate with YouTube first"
                    
            # Get live broadcasts
            request = self.service.liveBroadcasts().list(
                part="snippet,contentDetails,status",
                broadcastStatus="active",
                maxResults=50
            )
            response = request.execute()
            
            if not response.get("items"):
                logger.info("No active streams found")
                return []
                
            streams = []
            for item in response["items"]:
                try:
                    stream = {
                        "id": item["id"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "status": item["status"]["lifeCycleStatus"]
                    }
                    streams.append(stream)
                except KeyError as e:
                    logger.warning(f"Error processing stream data: {e}")
                    continue
                    
            if not streams:
                logger.info("No valid streams found after processing")
                return []
                
            return streams
            
        except Exception as e:
            logger.error(f"Error listing streams: {e}")
            return f"Error listing streams: {str(e)}"

    async def connect_websocket(self) -> bool:
        """Connect to our WebSocket server to relay messages"""
        try:
            if self.ws_client:
                try:
                    await self.ws_client.close()
                except Exception:
                    pass
                self.ws_client = None
                    
            self.ws_client = await websockets.connect(self.ws_uri, ping_interval=30, ping_timeout=10)
            logger.info("Connected to local WebSocket server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.ws_client = None
            return False
            
    async def ensure_websocket_connection(self) -> bool:
        """Ensure WebSocket connection is active"""
        try:
            if not self.ws_client:
                return await self.connect_websocket()
            return True
        except Exception as e:
            logger.error(f"Error ensuring WebSocket connection: {e}")
            return False

    def get_live_chat_id(self) -> Optional[str]:
        """Get the live chat ID for the current stream"""
        try:
            if not self.authenticated:
                return None
                
            # Get active broadcasts
            request = self.service.liveBroadcasts().list(
                part="snippet,contentDetails,status",
                broadcastStatus="active",
                maxResults=1
            )
            response = request.execute()
            
            if not response.get("items"):
                logger.info("No active broadcast found")
                return None
                
            # Get the live chat ID from the broadcast
            broadcast = response["items"][0]
            if "contentDetails" in broadcast and "boundStreamId" in broadcast["contentDetails"]:
                stream_id = broadcast["contentDetails"]["boundStreamId"]
                
                # Get the live stream details
                stream_request = self.service.liveStreams().list(
                    part="snippet,cdn",
                    id=stream_id
                )
                stream_response = stream_request.execute()
                
                if stream_response.get("items"):
                    stream = stream_response["items"][0]
                    if "snippet" in stream and "liveChatId" in stream["snippet"]:
                        self.live_chat_id = stream["snippet"]["liveChatId"]
                        logger.info(f"Found live chat ID: {self.live_chat_id}")
                        return self.live_chat_id
                        
            logger.warning("Could not find live chat ID")
            return None
            
        except Exception as e:
            logger.error(f"Error getting live chat ID: {e}")
            return None

    async def process_chat_message(self, message: Dict[str, Any]) -> None:
        """Process a chat message and relay it through WebSocket"""
        try:
            if not await self.ensure_websocket_connection():
                logger.error("Failed to establish WebSocket connection")
                return
                
            # Format the message
            formatted_message = {
                "type": "youtube_chat",
                "data": {
                    "author": message["authorDetails"]["displayName"],
                    "message": message["snippet"]["displayMessage"],
                    "timestamp": message["snippet"]["publishedAt"]
                }
            }
            
            # Send through WebSocket
            await self.ws_client.send(json.dumps(formatted_message))
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")

    def send_message(self, message: str) -> None:
        """Send a message to the live chat"""
        try:
            if not self.authenticated or not self.live_chat_id:
                logger.error("Not authenticated or no live chat ID")
                return
                
            request = self.service.liveChatMessages().insert(
                part="snippet",
                body={
                    "snippet": {
                        "liveChatId": self.live_chat_id,
                        "type": "textMessageEvent",
                        "textMessageDetails": {
                            "messageText": message
                        }
                    }
                }
            )
            request.execute()
            logger.info("Message sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def is_connected(self) -> bool:
        """Check if the client is connected to YouTube"""
        return self.authenticated and self.service is not None

    async def listen_to_chat(self) -> None:
        """Listen to the live chat messages"""
        try:
            if not self.authenticated:
                logger.error("Not authenticated")
                return
                
            if not self.live_chat_id:
                if not self.get_live_chat_id():
                    logger.error("Could not get live chat ID")
                    return
                    
            self.running = True
            while self.running:
                try:
                    request = self.service.liveChatMessages().list(
                        liveChatId=self.live_chat_id,
                        part="snippet,authorDetails",
                        pageToken=self.next_page_token
                    )
                    response = request.execute()
                    
                    if "items" in response:
                        for message in response["items"]:
                            await self.process_chat_message(message)
                            
                    self.next_page_token = response.get("nextPageToken")
                    
                    # Wait for the polling interval
                    polling_interval = response.get("pollingIntervalMillis", 5000)
                    await asyncio.sleep(polling_interval / 1000)
                    
                except Exception as e:
                    logger.error(f"Error in chat listener: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
                    
        except Exception as e:
            logger.error(f"Error in chat listener: {e}")
        finally:
            self.running = False

    async def start(self) -> None:
        """Start the YouTube client"""
        try:
            if not self.authenticated:
                logger.error("Not authenticated")
                return
                
            if not self.live_chat_id:
                if not self.get_live_chat_id():
                    logger.error("Could not get live chat ID")
                    return
                    
            await self.listen_to_chat()
            
        except Exception as e:
            logger.error(f"Error starting YouTube client: {e}")

    def stop(self) -> None:
        """Stop the YouTube client"""
        self.running = False
        if self.ws_client:
            asyncio.create_task(self.ws_client.close())
            self.ws_client = None

    def get_status(self) -> str:
        """Get the current status of the YouTube client"""
        if not self.authenticated:
            return "Not authenticated"
        if not self.live_chat_id:
            return "No live chat ID"
        if not self.running:
            return "Not running"
        return "Connected and listening"

    def connect_to_stream(self, stream_id: str) -> bool:
        """Connect to a specific YouTube stream"""
        try:
            if not self.authenticated:
                logger.error("Not authenticated")
                return False
                
            # Get the live stream details
            request = self.service.liveStreams().list(
                part="snippet,cdn",
                id=stream_id
            )
            response = request.execute()
            
            if not response.get("items"):
                logger.error("Stream not found")
                return False
                
            stream = response["items"][0]
            if "snippet" in stream and "liveChatId" in stream["snippet"]:
                self.live_chat_id = stream["snippet"]["liveChatId"]
                logger.info(f"Connected to stream with chat ID: {self.live_chat_id}")
                return True
                
            logger.error("Could not find live chat ID for stream")
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to stream: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the current stream"""
        self.live_chat_id = None
        self.next_page_token = None
        self.running = False
        if self.ws_client:
            asyncio.create_task(self.ws_client.close())
            self.ws_client = None 