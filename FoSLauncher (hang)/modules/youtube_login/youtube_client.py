import os
import json
import pickle
import asyncio
import logging
import webbrowser
from typing import Dict, Any, Optional, List, Union, Tuple
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from modules.logger import FoSLogger

class YouTubeClient:
    def __init__(self, client_secrets_path: str, logger: FoSLogger):
        self.client_secrets_path = client_secrets_path
        self.logger = logger
        self.yt_logger = self.logger.get_logger("youtube")
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.token_path = os.path.join(self.base_dir, "config", "modules", "youtube_login", "token.pickle")
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
        self.logger.log_info("youtube", "YouTube client initialized")
        self.logger.log_debug("youtube", f"Token path: {self.token_path}")

    def show_error(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an error message in the main thread"""
        if root and isinstance(root, (tk.Tk, tk.Toplevel, ctk.CTk, ctk.CTkToplevel)):
            root.after(0, lambda: messagebox.showerror("Error", message))
        else:
            self.logger.log_error(self.yt_logger, message)

    def show_info(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an info message in the main thread"""
        if root and isinstance(root, (tk.Tk, tk.Toplevel, ctk.CTk, ctk.CTkToplevel)):
            root.after(0, lambda: messagebox.showinfo("Information", message))
        else:
            self.logger.log_info(self.yt_logger, message)

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
                self.logger.log_info(self.yt_logger, instructions)
                return False

        except Exception as e:
            self.show_error(root, f"Error during setup: {str(e)}")
            return False

    async def authenticate(self) -> bool:
        """Authenticate with YouTube API"""
        try:
            self.logger.log_info("youtube", "Starting YouTube authentication")

            if os.path.exists(self.token_path):
                self.logger.log_debug("youtube", "Loading existing credentials")
                with open(self.token_path, 'rb') as token:
                    self.credentials = pickle.load(token)

            if not self.credentials or not self.credentials.valid:
                self.logger.log_debug("youtube", "Checking credentials validity")
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.logger.log_info("youtube", "Refreshing expired credentials")
                    self.credentials.refresh(Request())
                else:
                    self.logger.log_info("youtube", "Starting OAuth2 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        os.path.join(self.base_dir, "config", "modules", "youtube_login", "client_secrets.json"),
                        ['https://www.googleapis.com/auth/youtube.force-ssl']
                    )
                    self.credentials = flow.run_local_server(port=8001)

                self.logger.log_info("youtube", "Saving credentials")
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)

            self.service = build("youtube", "v3", credentials=self.credentials)
            self.authenticated = True

            # Verify the credentials work by making a test API call
            try:
                self.logger.log_debug("youtube", "Verifying credentials with test API call")
                self.get_channel_info()
                self.logger.log_info("youtube", "Successfully authenticated with YouTube!")
                self.show_info(None, "Successfully authenticated with YouTube!")
                return True
            except Exception as e:
                self.logger.log_exception(self.yt_logger, "Error verifying credentials", e)
                self.show_error(None, f"Failed to verify YouTube API access: {str(e)}")
                return False

        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Authentication error", e)
            self.show_error(None, f"Authentication error: {str(e)}")
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
            self.logger.log_exception(self.yt_logger, "Error getting channel info", e)
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
                self.logger.log_info(self.yt_logger, "No active streams found")
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
                    self.logger.log_warning(self.yt_logger, f"Error processing stream data: {e}")
                    continue

            if not streams:
                self.logger.log_info(self.yt_logger, "No valid streams found after processing")
                return []

            return streams

        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error listing streams", e)
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
            self.logger.log_info(self.yt_logger, "Connected to local WebSocket server")
            return True
        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Failed to connect to WebSocket", e)
            self.ws_client = None
            return False

    async def ensure_websocket_connection(self) -> bool:
        """Ensure WebSocket connection is active"""
        try:
            if not self.ws_client:
                return await self.connect_websocket()
            return True
        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error ensuring WebSocket connection", e)
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
                self.logger.log_info(self.yt_logger, "No active broadcast found")
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
                        self.logger.log_info(self.yt_logger, f"Found live chat ID: {self.live_chat_id}")
                        return self.live_chat_id

            self.logger.log_warning(self.yt_logger, "Could not find live chat ID")
            return None

        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error getting live chat ID", e)
            return None

    async def process_chat_message(self, message: Dict[str, Any]) -> None:
        """Process a chat message and relay it through WebSocket"""
        try:
            if not await self.ensure_websocket_connection():
                self.logger.log_error(self.yt_logger, "Failed to establish WebSocket connection")
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
            self.logger.log_exception(self.yt_logger, "Error processing chat message", e)

    async def connect_to_live_chat(self) -> bool:
        """Connect to YouTube live chat"""
        try:
            self.logger.log_info(self.yt_logger, "Connecting to live chat")

            if not self.service:
                self.logger.log_warning(self.yt_logger, "YouTube client not initialized")
                if not await self.authenticate():
                    return False

            self.logger.log_debug(self.yt_logger, "Getting live broadcast")
            broadcasts = self.service.liveBroadcasts().list(
                part='snippet',
                broadcastStatus='active'
            ).execute()

            if not broadcasts.get('items'):
                self.logger.log_warning(self.yt_logger, "No active broadcast found")
                return False

            broadcast = broadcasts['items'][0]
            self.live_chat_id = broadcast['snippet']['liveChatId']
            self.logger.log_info(self.yt_logger, f"Connected to live chat: {self.live_chat_id}")
            return True

        except HttpError as e:
            self.logger.log_exception(self.yt_logger, "YouTube API error during live chat connection", e)
            return False
        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error connecting to live chat", e)
            return False

    async def send_message(self, message: str) -> bool:
        """Send a message to the live chat"""
        try:
            if not self.authenticated:
                self.logger.log_warning(self.yt_logger, "Not authenticated")
                if not await self.authenticate():
                    return False

            self.logger.log_debug(self.yt_logger, f"Sending message: {message}")
            self.service.liveChatMessages().insert(
                part='snippet',
                body={
                    'snippet': {
                        'liveChatId': self.live_chat_id,
                        'type': 'textMessageEvent',
                        'textMessageDetails': {
                            'messageText': message
                        }
                    }
                }
            ).execute()

            self.logger.log_info(self.yt_logger, "Message sent successfully")
            return True

        except HttpError as e:
            self.logger.log_exception(self.yt_logger, "YouTube API error sending message", e)
            return False
        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error sending message", e)
            return False

    async def get_chat_messages(self) -> Optional[Dict[str, Any]]:
        """Get messages from the live chat"""
        try:
            if not self.authenticated:
                self.logger.log_warning(self.yt_logger, "Not authenticated")
                if not await self.authenticate():
                    return None

            self.logger.log_debug(self.yt_logger, "Fetching chat messages")
            response = self.service.liveChatMessages().list(
                liveChatId=self.live_chat_id,
                part='snippet,authorDetails'
            ).execute()

            messages = []
            for item in response.get('items', []):
                message = {
                    'author': item['authorDetails']['displayName'],
                    'message': item['snippet']['displayMessage'],
                    'timestamp': item['snippet']['publishedAt']
                }
                messages.append(message)

            self.logger.log_debug(self.yt_logger, f"Retrieved {len(messages)} messages")
            return {'messages': messages}

        except HttpError as e:
            self.logger.log_exception(self.yt_logger, "YouTube API error getting messages", e)
            return None
        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error getting messages", e)
            return None

    async def disconnect(self) -> None:
        """Disconnect from YouTube live chat"""
        try:
            self.logger.log_info(self.yt_logger, "Disconnecting from live chat")
            self.authenticated = False
            self.live_chat_id = None
            self.logger.log_info(self.yt_logger, "Successfully disconnected")
        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error during disconnect", e)

    def is_rate_limited(self) -> bool:
        """Check if we're rate limited"""
        try:
            time_since_last = datetime.now() - self.last_stream_check
            is_limited = time_since_last < timedelta(seconds=1)
            if is_limited:
                self.logger.log_debug(self.yt_logger, f"Rate limited, {time_since_last.total_seconds()}s since last stream check")
            return is_limited
        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error checking rate limit", e)
            return True

    async def listen_to_chat(self) -> None:
        """Listen to the live chat messages"""
        try:
            if not self.authenticated:
                self.logger.log_error(self.yt_logger, "Not authenticated")
                return

            if not self.live_chat_id:
                if not self.get_live_chat_id():
                    self.logger.log_error(self.yt_logger, "Could not get live chat ID")
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
                    self.logger.log_exception(self.yt_logger, "Error in chat listener", e)
                    await asyncio.sleep(5)  # Wait before retrying

        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error in chat listener", e)
        finally:
            self.running = False

    async def start(self) -> None:
        """Start the YouTube client"""
        try:
            if not self.authenticated:
                self.logger.log_error(self.yt_logger, "Not authenticated")
                return

            if not self.live_chat_id:
                if not self.get_live_chat_id():
                    self.logger.log_error(self.yt_logger, "Could not get live chat ID")
                    return

            await self.listen_to_chat()

        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error starting YouTube client", e)

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
                self.logger.log_error(self.yt_logger, "Not authenticated")
                return False

            # Get the live stream details
            request = self.service.liveStreams().list(
                part="snippet,cdn",
                id=stream_id
            )
            response = request.execute()

            if not response.get("items"):
                self.logger.log_error(self.yt_logger, "Stream not found")
                return False

            stream = response["items"][0]
            if "snippet" in stream and "liveChatId" in stream["snippet"]:
                self.live_chat_id = stream["snippet"]["liveChatId"]
                self.logger.log_info(self.yt_logger, f"Connected to stream with chat ID: {self.live_chat_id}")
                return True

            self.logger.log_error(self.yt_logger, "Could not find live chat ID for stream")
            return False

        except Exception as e:
            self.logger.log_exception(self.yt_logger, "Error connecting to stream", e)
            return False

    def disconnect(self) -> None:
        """Disconnect from the current stream"""
        self.live_chat_id = None
        self.next_page_token = None
        self.running = False
        if self.ws_client:
            asyncio.create_task(self.ws_client.close())
            self.ws_client = None