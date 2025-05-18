import os
import json
import pickle
import asyncio
import logging
import webbrowser
import ssl
import certifi
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
import google_auth_oauthlib.flow
import websockets
from datetime import datetime
import time
import googleapiclient.errors

logger = logging.getLogger("FoSLauncher")

class WebSocketServer:
    def __init__(self, port: int = 8001):
        self.port = port
        self.clients = set()
        self.message_callback = None
        self.server = None
        self.logger = logging.getLogger("websocket_server")

    async def register(self, websocket):
        self.clients.add(websocket)
        self.logger.info(f"New client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        self.logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, message: str):
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients]
            )

    async def handler(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                if self.message_callback:
                    await self.message_callback(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def start(self):
        self.server = await websockets.serve(self.handler, "localhost", self.port)
        self.logger.info(f"WebSocket server started on port {self.port}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")

class YouTubeClient:
    def __init__(self, client_secrets_path: str, token_path: str):
        self.logger = logging.getLogger("youtube_client")
        self.logger.info("YouTube client initialized")
        self.client_secrets_path = client_secrets_path
        self.token_path = token_path
        self.authenticated = False
        self.credentials = None
        self.youtube = None
        self.live_chat_id = None
        self.websocket = None
        self.websocket_task = None
        self.message_queue = asyncio.Queue()
        self.running = False
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.next_page_token = None
        self.ws_client = None
        self.ws_server = WebSocketServer()
        self.ws_server.message_callback = self.handle_websocket_message
        self.channel_id = None
        self.retry_count = 0
        self.max_retries = 5
        self.last_stream_check = None
        self.has_permission = False
        self.config: Dict[str, Any] = {}
        self.message_callback = None
        self.connection_callback = None
        self.current_chat_id = None
        self.current_stream_id = None
        self.connected = False
        self.last_message_time = 0
        self.message_cooldown = 1.0  # 1 second cooldown between messages
        self.message_history = set()  # Track sent messages to prevent duplicates
        self.message_history_max_size = 100  # Maximum number of messages to track
        self.own_channel_id = None  # Store our own channel ID
        self.processed_messages = set()  # Track processed messages globally
        
        # Configure SSL context with modern settings
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        self.ssl_context.check_hostname = True
        self.ssl_context.load_default_certs()
        self.ssl_context.set_ciphers('DEFAULT@SECLEVEL=2')
        
        # Try to load credentials immediately
        self.load_credentials()
        self.load_config()

        # Add quota management
        self.quota_reset_time = None
        self.quota_retry_delay = 60  # seconds to wait when quota exceeded
        self.stream_cache = {}
        self.stream_cache_timeout = 300  # 5 minutes cache timeout
        self.last_stream_list_time = None

    def show_error(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an error message in the main thread"""
        if root and isinstance(root, (tk.Tk, tk.Toplevel, ctk.CTk, ctk.CTkToplevel)) and root.winfo_exists():
            root.after(0, lambda: messagebox.showerror("Error", message))
        else:
            self.logger.error(message)

    def show_info(self, root: Optional[tk.Tk], message: str) -> None:
        """Show an info message in the main thread"""
        if root and isinstance(root, (tk.Tk, tk.Toplevel, ctk.CTk, ctk.CTkToplevel)) and root.winfo_exists():
            root.after(0, lambda: messagebox.showinfo("Information", message))
        else:
            self.logger.info(message)

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
                self.logger.info(instructions)
                return False

        except Exception as e:
            self.show_error(root, f"Error during setup: {str(e)}")
            return False

    def load_config(self) -> None:
        """Load configuration from config.json"""
        try:
            # Try to load from main config first
            main_config_path = os.path.join(self.base_dir, "config.json")
            module_config_path = os.path.join(self.base_dir, "modules", "config.json")
            access_config_path = os.path.join(self.base_dir, "modules", "access.json")
            
            self.config = {}
            
            # Load main config
            if os.path.exists(main_config_path):
                with open(main_config_path, "r") as f:
                    self.config.update(json.load(f))
                    logger.info("Loaded main configuration")
            
            # Load module config
            if os.path.exists(module_config_path):
                with open(module_config_path, "r") as f:
                    self.config.update(json.load(f))
                    logger.info("Loaded module configuration")
            
            # Load access config
            if os.path.exists(access_config_path):
                with open(access_config_path, "r") as f:
                    access_config = json.load(f)
                    self.config["access"] = access_config
                    logger.info("Loaded access configuration")
                    
            logger.info("Successfully loaded all configurations")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}

    async def authenticate(self) -> bool:
        """Authenticate with YouTube using OAuth2"""
        try:
            if self.authenticated:
                return True
                
            # Get OAuth2 credentials
            if not os.path.exists(self.client_secrets_path):
                logger.error(f"client_secrets.json not found at {self.client_secrets_path}")
                logger.info("Please follow these steps to set up YouTube API credentials:")
                logger.info("1. Go to https://console.cloud.google.com/")
                logger.info("2. Create a new project")
                logger.info("3. Enable the YouTube Data API v3")
                logger.info("4. Create OAuth 2.0 credentials")
                logger.info("5. Download the credentials and save as 'client_secrets.json'")
                logger.info(f"6. Place the file at: {self.client_secrets_path}")
                return False

            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_path,
                scopes=[
                    "https://www.googleapis.com/auth/youtube.readonly",
                    "https://www.googleapis.com/auth/youtube.force-ssl",
                    "https://www.googleapis.com/auth/youtube"
                ]
            )
            
            # Start local server for OAuth2 callback
            port = 8001
            success = False
            max_retries = 3
            retry_count = 0
            
            while not success and retry_count < max_retries:
                try:
                    flow.redirect_uri = f"http://localhost:{port}/oauth2callback"
                    credentials = flow.run_local_server(port=port)
                    success = True
                except OSError as e:
                    logger.warning(f"Port {port} in use, trying next port")
                    port += 1
                    if port >= 8010:
                        port = 8001
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.info(f"Retrying authentication (attempt {retry_count + 1}/{max_retries})")
                            time.sleep(1)  # Wait before retrying
                    
            if not success:
                logger.error("Could not find available port for OAuth2 callback after multiple attempts")
                return False
                
            # Build YouTube client
            self.youtube = build("youtube", "v3", credentials=credentials)
            self.authenticated = True
            
            # Get our own channel ID
            try:
                request = self.youtube.channels().list(
                    part="id",
                    mine=True
                )
                response = request.execute()
                if response.get("items"):
                    self.own_channel_id = response["items"][0]["id"]
                    logger.info(f"Found own channel ID: {self.own_channel_id}")
            except Exception as e:
                logger.error(f"Error getting own channel ID: {str(e)}")
            
            logger.info("Successfully authenticated with YouTube")
            return True

        except Exception as e:
            logger.error(f"Error authenticating with YouTube: {str(e)}")
            return False

    def load_credentials(self) -> bool:
        """Load credentials from token file"""
        try:
            if os.path.exists(self.token_path):
                self.logger.info(f"Loading credentials from {self.token_path}")
                with open(self.token_path, 'rb') as token:
                    self.credentials = pickle.load(token)
                    
                # Check if credentials are expired
                if self.credentials and self.credentials.expired:
                    self.logger.info("Credentials expired, attempting to refresh")
                    if self.credentials.refresh_token:
                        self.credentials.refresh(Request())
                        # Save refreshed credentials
                        with open(self.token_path, 'wb') as token:
                            pickle.dump(self.credentials, token)
                        self.logger.info("Credentials refreshed successfully")
                    else:
                        self.logger.info("No refresh token available")
                        return False
                        
                # Build YouTube service
                if self.credentials and not self.credentials.expired:
                    self.youtube = build('youtube', 'v3', credentials=self.credentials)
                    self.authenticated = True
                    self.logger.info("Successfully loaded credentials and built YouTube service")
                    return True
                    
            self.logger.info("No credentials found or credentials invalid")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {str(e)}")
            return False

    def get_channel_info(self) -> dict:
        """Get information about the authenticated channel"""
        try:
            if not self.youtube:
                raise Exception("Not authenticated")
                
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                return response['items'][0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get channel info: {str(e)}")
            return None
            
    def list_available_streams(self) -> Union[List[Dict[str, Any]], str]:
        """List available YouTube streams"""
        try:
            if not self.authenticated:
                return "Please authenticate with YouTube first"

            # Check cache first
            current_time = time.time()
            if (self.last_stream_list_time and 
                current_time - self.last_stream_list_time < self.stream_cache_timeout and 
                self.stream_cache):
                self.logger.info("Using cached stream list")
                return list(self.stream_cache.values())

            streams = []
            
            # Get active broadcasts (including private ones)
            try:
                active_request = self.youtube.liveBroadcasts().list(
                    part="snippet,contentDetails,status",
                    broadcastStatus="active",
                    broadcastType="all",
                    maxResults=50
                )
                active_response = active_request.execute()
                
                # Process active streams
                for item in active_response.get("items", []):
                    try:
                        privacy_status = item.get("status", {}).get("privacyStatus", "unknown")
                        stream = {
                            "id": item["id"],
                            "title": item["snippet"]["title"],
                            "description": item["snippet"]["description"],
                            "status": "LIVE",
                            "privacy": privacy_status,
                            "scheduled_start_time": item["snippet"].get("scheduledStartTime", ""),
                            "actual_start_time": item["snippet"].get("actualStartTime", "")
                        }
                        streams.append(stream)
                        self.stream_cache[stream["id"]] = stream
                    except KeyError as e:
                        self.logger.warning(f"Error processing active stream data: {e}")
                        continue
            except HttpError as e:
                if 'quotaExceeded' in str(e):
                    self.logger.warning("YouTube API quota exceeded. Will retry later.")
                    self.quota_reset_time = time.time() + self.quota_retry_delay
                    return "YouTube API quota exceeded. Please try again later."
                raise

            # Get upcoming broadcasts (including private ones)
            try:
                upcoming_request = self.youtube.liveBroadcasts().list(
                    part="snippet,contentDetails,status",
                    broadcastStatus="upcoming",
                    broadcastType="all",
                    maxResults=50
                )
                upcoming_response = upcoming_request.execute()

                # Process upcoming streams
                for item in upcoming_response.get("items", []):
                    try:
                        privacy_status = item.get("status", {}).get("privacyStatus", "unknown")
                        stream = {
                            "id": item["id"],
                            "title": item["snippet"]["title"],
                            "description": item["snippet"]["description"],
                            "status": "SCHEDULED",
                            "privacy": privacy_status,
                            "scheduled_start_time": item["snippet"].get("scheduledStartTime", ""),
                            "actual_start_time": item["snippet"].get("actualStartTime", "")
                        }
                        streams.append(stream)
                        self.stream_cache[stream["id"]] = stream
                    except KeyError as e:
                        self.logger.warning(f"Error processing upcoming stream data: {e}")
                        continue
            except HttpError as e:
                if 'quotaExceeded' in str(e):
                    self.logger.warning("YouTube API quota exceeded. Will retry later.")
                    self.quota_reset_time = time.time() + self.quota_retry_delay
                    return "YouTube API quota exceeded. Please try again later."
                raise

            if not streams:
                self.logger.info("No streams found")
                return []
            
            # Sort streams by scheduled start time
            streams.sort(key=lambda x: x["scheduled_start_time"] if x["status"] == "SCHEDULED" else x["actual_start_time"])
            
            # Update cache timestamp
            self.last_stream_list_time = current_time
            
            return streams

        except Exception as e:
            self.logger.error(f"Error listing streams: {str(e)}")
            return f"Error listing streams: {str(e)}"

    def _notify_connection_change(self, connected: bool, stream_id: str = None):
        """Notify listeners of connection state changes"""
        self.connected = connected
        self.current_stream_id = stream_id
        if self.connection_callback:
            self.connection_callback(connected, stream_id)

    async def select_stream(self, stream_id: str) -> bool:
        """Select a stream to connect to"""
        try:
            if not self.authenticated:
                self.logger.error("Not authenticated")
                return False
                
            self.logger.info(f"Attempting to connect to stream ID: {stream_id}")
            
            # Check cache first
            if stream_id in self.stream_cache:
                self.logger.info("Using cached stream data")
                stream_data = self.stream_cache[stream_id]
                if stream_data["privacy"] == "private":
                    self.logger.info("Stream is private, will need to fetch live chat ID")
                else:
                    self.current_chat_id = stream_data.get("liveChatId")
                    if self.current_chat_id:
                        self.current_stream_id = stream_id
                        self.connected = True
                        if self.connection_callback:
                            self.connection_callback(True, stream_id)
                        return True
            
            # Get broadcast details
            try:
                broadcast = self.youtube.liveBroadcasts().list(
                    part="snippet,contentDetails,status,id",
                    id=stream_id
                ).execute()
                
                if not broadcast.get('items'):
                    self.logger.error(f"No broadcast found with ID: {stream_id}")
                    return False
                    
                broadcast = broadcast['items'][0]
                self.logger.info(f"Found broadcast: {broadcast['snippet']['title']} (Privacy: {broadcast['status']['privacyStatus']})")
                
                # Get bound stream ID
                if 'contentDetails' in broadcast and 'boundStreamId' in broadcast['contentDetails']:
                    bound_stream_id = broadcast['contentDetails']['boundStreamId']
                    self.logger.info(f"Found bound stream ID: {bound_stream_id}")
                    
                    # Get live chat ID
                    try:
                        if broadcast['status']['privacyStatus'] == 'private':
                            self.logger.info("Attempting to get live chat ID for private stream...")
                            video = self.youtube.videos().list(
                                part="liveStreamingDetails",
                                id=stream_id
                            ).execute()
                            
                            if not video.get('items'):
                                self.logger.error("Could not find video details")
                                return False
                                
                            live_chat_id = video['items'][0]['liveStreamingDetails']['activeLiveChatId']
                        else:
                            live_chat_id = broadcast['snippet']['liveChatId']
                            
                        self.current_chat_id = live_chat_id
                        self.current_stream_id = stream_id
                        self.connected = True
                        
                        # Update cache
                        if stream_id in self.stream_cache:
                            self.stream_cache[stream_id]["liveChatId"] = live_chat_id
                        
                        if self.connection_callback:
                            self.connection_callback(True, stream_id)
                            
                        self.logger.info(f"Successfully connected to stream {stream_id}")
                        return True
                    except HttpError as e:
                        if 'quotaExceeded' in str(e):
                            self.logger.warning("YouTube API quota exceeded. Will retry in 1 minute.")
                            self.quota_reset_time = time.time() + self.quota_retry_delay
                            await asyncio.sleep(self.quota_retry_delay)
                            return await self.select_stream(stream_id)
                        self.logger.error(f"Error getting live chat ID: {str(e)}")
                        return False
                else:
                    self.logger.error("No bound stream ID found")
                    return False
                    
            except HttpError as e:
                if 'quotaExceeded' in str(e):
                    self.logger.warning("YouTube API quota exceeded. Will retry in 1 minute.")
                    self.quota_reset_time = time.time() + self.quota_retry_delay
                    await asyncio.sleep(self.quota_retry_delay)
                    return await self.select_stream(stream_id)
                self.logger.error(f"Error selecting stream: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in select_stream: {str(e)}")
            return False

    def close(self):
        """Close any open connections"""
        try:
            if self.youtube:
                self.youtube.close()
            self.youtube = None
            self.credentials = None
            self.authenticated = False
        except Exception as e:
            self.logger.debug(f"Non-critical error closing client: {str(e)}")

    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the authenticated channel"""
        try:
            if not self.youtube:
                return None

            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()

            if response["items"]:
                self.channel_id = response["items"][0]["id"]
                return response["items"][0]
            return None

        except Exception as e:
            self.logger.error(f"Error getting channel info: {str(e)}")
            return None

    async def connect_websocket(self) -> bool:
        """Connect to our WebSocket server to relay messages"""
        try:
            if self.ws_client:
                try:
                    await self.ws_client.close()
                except Exception:
                    pass
                self.ws_client = None

            # Try different ports if 8001 fails
            ports = [8001, 8002, 8003, 8004, 8005]
            for port in ports:
                try:
                    self.ws_uri = f"ws://127.0.0.1:{port}/ws"
                    self.ws_client = await websockets.connect(
                        self.ws_uri,
                        ping_interval=30,
                        ping_timeout=10,
                        ssl=None  # Remove SSL context for ws:// connections
                    )
                    self.logger.info(f"Connected to local WebSocket server on port {port}")
                    return True
                except Exception as e:
                    self.logger.warning(f"Failed to connect to WebSocket on port {port}: {str(e)}")
                    continue

            self.logger.error("Failed to connect to WebSocket on any port")
            self.ws_client = None
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket: {str(e)}")
            self.ws_client = None
            return False

    async def ensure_websocket_connection(self) -> bool:
        """Ensure WebSocket connection is active"""
        try:
            if not self.ws_client:
                return await self.connect_websocket()
            return True
        except Exception as e:
            self.logger.error(f"Error ensuring WebSocket connection: {str(e)}")
            return False

    def get_live_chat_id(self) -> Optional[str]:
        """Get the live chat ID for the current stream"""
        try:
            if not self.authenticated:
                return None

            # Get active broadcasts
            request = self.youtube.liveBroadcasts().list(
                part="snippet,contentDetails,status",
                broadcastStatus="active",
                maxResults=1
            )
            response = request.execute()

            if not response.get("items"):
                self.logger.info("No active broadcast found")
                return None

            # Get the live chat ID from the broadcast
            broadcast = response["items"][0]
            if "contentDetails" in broadcast and "boundStreamId" in broadcast["contentDetails"]:
                stream_id = broadcast["contentDetails"]["boundStreamId"]

                # Get the live stream details
                stream_request = self.youtube.liveStreams().list(
                    part="snippet,cdn",
                    id=stream_id
                )
                stream_response = stream_request.execute()

                if stream_response.get("items"):
                    stream = stream_response["items"][0]
                    if "snippet" in stream and "liveChatId" in stream["snippet"]:
                        self.live_chat_id = stream["snippet"]["liveChatId"]
                        self.logger.info(f"Found live chat ID: {self.live_chat_id}")
                        return self.live_chat_id

            self.logger.warning("Could not find live chat ID")
            return None

        except Exception as e:
            self.logger.error(f"Error getting live chat ID: {str(e)}")
            return None

    async def handle_websocket_message(self, message: Dict[str, Any]):
        """Handle messages received from WebSocket clients"""
        try:
            if self.message_callback:
                await self.message_callback(message)
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {str(e)}")

    async def process_chat_message(self, message: Dict[str, Any]) -> None:
        """Process a chat message and relay it through WebSocket"""
        try:
            # Get message details
            author = message["authorDetails"]["displayName"]
            content = message["snippet"]["displayMessage"]
            timestamp = message["snippet"]["publishedAt"]
            message_id = message.get("id")

            # Log the message for debugging
            self.logger.info(f"Received message from {author}: {content}")

            # Process the message directly through the callback
            if self.message_callback:
                # Check if it's a command
                if content.startswith('!'):
                    # Process the command and get the response
                    response = await self.message_callback(message)
                    if response:
                        # Send the response back to YouTube chat
                        await self.send_message(response)
                else:
                    # Just show regular messages
                    await self.message_callback(message)

        except Exception as e:
            self.logger.error(f"Error processing chat message: {str(e)}")

    async def connect_to_live_chat(self) -> bool:
        """Connect to YouTube live chat"""
        try:
            self.logger.info("Connecting to live chat")

            if not self.youtube:
                self.logger.warning("YouTube client not initialized")
                if not await self.authenticate():
                    return False

            self.logger.debug("Getting live broadcast")
            broadcasts = self.youtube.liveBroadcasts().list(
                part='snippet',
                broadcastStatus='active'
            ).execute()

            if not broadcasts.get('items'):
                self.logger.warning("No active broadcast found")
                return False

            broadcast = broadcasts['items'][0]
            self.live_chat_id = broadcast['snippet']['liveChatId']
            self.logger.info(f"Connected to live chat: {self.live_chat_id}")
            return True

        except HttpError as e:
            self.logger.error(f"YouTube API error during live chat connection: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error connecting to live chat: {str(e)}")
            return False

    async def send_message(self, message: str) -> bool:
        """Send a message to the live chat"""
        try:
            if not self.authenticated or not self.youtube or not self.current_chat_id:
                self.logger.error("Not connected to a live chat")
                return False

            # Check message cooldown
            current_time = time.time()
            if current_time - self.last_message_time < self.message_cooldown:
                self.logger.warning("Message cooldown active, waiting...")
                await asyncio.sleep(self.message_cooldown - (current_time - self.last_message_time))

            # Check for duplicate message
            message_hash = hash(message)
            if message_hash in self.message_history:
                self.logger.warning("Duplicate message detected, skipping")
                return True

            # Create the message body with the correct format
            message_body = {
                "snippet": {
                    "liveChatId": self.current_chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": message
                    }
                }
            }
            
            # Send the message
            try:
                response = self.youtube.liveChatMessages().insert(
                    part="snippet",
                    body=message_body
                ).execute()

                if response and "snippet" in response:
                    self.last_message_time = time.time()
                    self.message_history.add(message_hash)
                    # Clean up old message history if needed
                    if len(self.message_history) > self.message_history_max_size:
                        self.message_history.clear()
                    self.logger.info(f"Message sent successfully: {message}")
                    return True
            except HttpError as e:
                error_details = json.loads(e.content).get('error', {}).get('errors', [{}])[0]
                error_reason = error_details.get('reason')
                error_message = error_details.get('message')
                self.logger.error(f"HTTP Error sending message: {error_reason} - {error_message}")
                # Try to refresh credentials if token expired
                if error_reason == "authError":
                    self.logger.info("Attempting to refresh credentials...")
                    if self.credentials and self.credentials.refresh_token:
                        self.credentials.refresh(Request())
                        # Save refreshed credentials
                        with open(self.token_path, 'wb') as token:
                            pickle.dump(self.credentials, token)
                        self.logger.info("Credentials refreshed successfully")
                        # Try sending again
                        response = self.youtube.liveChatMessages().insert(
                            part="snippet",
                            body=message_body
                        ).execute()
                        if response and "snippet" in response:
                            self.last_message_time = time.time()
                            self.message_history.add(message_hash)
                            self.logger.info(f"Message sent successfully after refresh: {message}")
                            return True
                return False
            except Exception as e:
                self.logger.error(f"Error sending message: {str(e)}")
                return False
                
            return False

        except Exception as e:
            self.logger.error(f"Error in send_message: {str(e)}")
            return False

    async def get_chat_messages(self) -> Optional[Dict[str, Any]]:
        """Get messages from the live chat"""
        try:
            if not self.authenticated:
                self.logger.warning("Not authenticated")
                if not await self.authenticate():
                    return None

            self.logger.debug("Fetching chat messages")
            response = self.youtube.liveChatMessages().list(
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

            self.logger.debug(f"Retrieved {len(messages)} messages")
            return {'messages': messages}

        except HttpError as e:
            self.logger.error(f"YouTube API error getting messages: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting messages: {str(e)}")
            return None

    async def disconnect(self) -> None:
        """Disconnect from YouTube live chat"""
        try:
            self.logger.info("Disconnecting from live chat")
            self.authenticated = False
            self.live_chat_id = None
            self.logger.info("Successfully disconnected")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")

    def is_rate_limited(self) -> bool:
        """Check if we're rate limited"""
        try:
            time_since_last = datetime.now() - self.last_stream_check
            is_limited = time_since_last < timedelta(seconds=1)
            if is_limited:
                self.logger.debug(f"Rate limited, {time_since_last.total_seconds()}s since last stream check")
            return is_limited
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {str(e)}")
            return True

    async def listen_to_chat(self) -> None:
        """Listen to the live chat messages"""
        try:
            if not self.authenticated:
                self.logger.error("Not authenticated")
                return

            if not self.current_chat_id:
                self.logger.error("No active chat ID")
                return

            self.running = True
            self.logger.info("Starting chat listener")
            
            while self.running:
                try:
                    request = self.youtube.liveChatMessages().list(
                        liveChatId=self.current_chat_id,
                        part="snippet,authorDetails",
                        pageToken=self.next_page_token
                    )
                    response = request.execute()

                    if "items" in response:
                        for message in response["items"]:
                            # Create a unique identifier for the message
                            message_id = message.get("id")
                            if not message_id:
                                continue
                                
                            # Skip if we've already processed this message
                            if message_id in self.processed_messages:
                                continue
                                
                            # Get the author's channel ID
                            author_id = message.get("authorDetails", {}).get("channelId")
                            
                            # Skip our own messages
                            if author_id == self.own_channel_id:
                                continue
                                
                            # Add to processed messages
                            self.processed_messages.add(message_id)
                            
                            # Clean up old processed messages if needed
                            if len(self.processed_messages) > 1000:
                                self.processed_messages.clear()
                            
                            # Process the message
                            await self.process_chat_message(message)

                    self.next_page_token = response.get("nextPageToken")

                    # Wait for the polling interval
                    polling_interval = response.get("pollingIntervalMillis", 5000)
                    await asyncio.sleep(polling_interval / 1000)

                except Exception as e:
                    self.logger.error(f"Error in chat listener: {str(e)}")
                    await asyncio.sleep(5)  # Wait before retrying
                    continue

        except Exception as e:
            self.logger.error(f"Error in chat listener: {str(e)}")
        finally:
            self.running = False
            self._notify_connection_change(False)

    async def start(self) -> None:
        """Start the YouTube client and WebSocket server"""
        try:
            if not self.authenticated:
                self.logger.error("Not authenticated")
                return

            # Start WebSocket server
            await self.ws_server.start()

            if not self.live_chat_id:
                if not self.get_live_chat_id():
                    self.logger.error("Could not get live chat ID")
                    return

            await self.listen_to_chat()

        except Exception as e:
            self.logger.error(f"Error starting YouTube client: {str(e)}")

    def stop(self) -> None:
        """Stop the YouTube client and WebSocket server"""
        self.running = False
        if self.ws_client:
            try:
                asyncio.create_task(self.ws_client.close())
            except Exception as e:
                self.logger.error(f"Error closing WebSocket: {str(e)}")
            self.ws_client = None
        if self.ws_server:
            asyncio.create_task(self.ws_server.stop())
        self.logger.info("YouTube client stopped")

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
                self.logger.log_error("Not authenticated")
                return False

            # Get the live stream details
            request = self.youtube.liveStreams().list(
                part="snippet,cdn",
                id=stream_id
            )
            response = request.execute()

            if not response.get("items"):
                self.logger.log_error("Stream not found")
                return False

            stream = response["items"][0]
            if "snippet" in stream and "liveChatId" in stream["snippet"]:
                self.live_chat_id = stream["snippet"]["liveChatId"]
                self.logger.log_info(f"Connected to stream with chat ID: {self.live_chat_id}")
                return True

            self.logger.log_error("Could not find live chat ID for stream")
            return False

        except Exception as e:
            self.logger.log_exception("Error connecting to stream", e)
            return False

    def disconnect(self) -> None:
        """Disconnect from the current stream"""
        self.live_chat_id = None
        self.next_page_token = None
        self.running = False
        if self.ws_client:
            asyncio.create_task(self.ws_client.close())
            self.ws_client = None

    def _build_client(self):
        """Build the YouTube API client with proper SSL configuration"""
        try:
            self.youtube = build('youtube', 'v3', 
                               credentials=self.credentials,
                               cache_discovery=False,
                               static_discovery=False)
            self.logger.info("YouTube client built successfully")
        except Exception as e:
            self.logger.error(f"Error building YouTube client: {e}")
            self.youtube = None
            self.authenticated = False