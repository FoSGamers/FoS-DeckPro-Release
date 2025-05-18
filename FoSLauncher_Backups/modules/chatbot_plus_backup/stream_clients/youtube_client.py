import os
import json
import asyncio
import websockets
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from datetime import datetime
import logging
import google_auth_oauthlib.flow
from typing import Dict, Any, Optional, List, Union, Tuple
import googleapiclient.errors
import time

logger = logging.getLogger("FoSLauncher")

class YouTubeChatClient:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.client = None
        self.credentials = None
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
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.load_config()
        
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
            
    def authenticate(self) -> bool:
        """Authenticate with YouTube using OAuth2"""
        try:
            if self.authenticated:
                return True
                
            # Get OAuth2 credentials
            client_secrets_path = os.path.join(self.base_dir, "client_secrets.json")
            if not os.path.exists(client_secrets_path):
                logger.error(f"client_secrets.json not found at {client_secrets_path}")
                logger.info("Please follow these steps to set up YouTube API credentials:")
                logger.info("1. Go to https://console.cloud.google.com/")
                logger.info("2. Create a new project")
                logger.info("3. Enable the YouTube Data API v3")
                logger.info("4. Create OAuth 2.0 credentials")
                logger.info("5. Download the credentials and save as 'client_secrets.json'")
                logger.info(f"6. Place the file at: {client_secrets_path}")
                return False
                
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_path,
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
            self.client = build("youtube", "v3", credentials=credentials)
            self.authenticated = True
            logger.info("Successfully authenticated with YouTube")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating with YouTube: {e}")
            return False
            
    def list_available_streams(self) -> Union[List[Dict[str, Any]], str]:
        """List available YouTube streams"""
        try:
            if not self.authenticated:
                if not self.authenticate():
                    return "Please authenticate with YouTube first using !youtube auth"
                    
            # Get live broadcasts
            request = self.client.liveBroadcasts().list(
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

    def check_permissions(self) -> bool:
        """Check if the user has permission to use YouTube features"""
        try:
            if not self.config.get("access"):
                logger.error("Access configuration not found")
                self.has_permission = False
                return False
                
            # Check if chatbot_plus module is unlocked and has YouTube feature enabled
            chatbot_config = self.config["access"].get("modules", {}).get("chatbot_plus", {})
            if chatbot_config.get("unlocked", False) and chatbot_config.get("features", {}).get("youtube", False):
                logger.info("YouTube features are enabled")
                self.has_permission = True
                return True
                        
            logger.warning("YouTube features are not enabled")
            self.has_permission = False
            return False
            
        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            self.has_permission = False
            return False

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

    def get_channel_id(self) -> Optional[str]:
        """Get the authenticated user's channel ID"""
        try:
            request = self.client.channels().list(
                part="id",
                mine=True
            )
            response = request.execute()
            if response['items']:
                channel_id = response['items'][0]['id']
                logger.info(f"Retrieved channel ID: {channel_id}")
                return channel_id
            logger.warning("No channel ID found")
            return None
        except Exception as e:
            logger.error(f"Error getting channel ID: {e}")
            return None

    def format_datetime(self, iso_string: str) -> str:
        """Format ISO datetime string to readable format"""
        try:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            return iso_string

    def get_live_chat_id(self) -> Optional[str]:
        """Get the live chat ID for the current live stream"""
        try:
            if not self.authenticated:
                logger.warning("Not authenticated with YouTube")
                return None
                
            # First get your channel ID
            channels_response = self.client.channels().list(
                part='id',
                mine=True
            ).execute()
            
            if not channels_response.get('items'):
                logger.warning("Could not find your channel")
                return None
                
            channel_id = channels_response['items'][0]['id']
            logger.info(f"Found your channel ID: {channel_id}")
            
            # Get active broadcasts
            broadcasts_response = self.client.liveBroadcasts().list(
                part='snippet,contentDetails,status',
                broadcastStatus='active',
                mine=True
            ).execute()
            
            if not broadcasts_response.get('items'):
                logger.warning("No active broadcasts found")
                return None
                
            # Get the first active broadcast
            broadcast = broadcasts_response['items'][0]
            if not broadcast.get('contentDetails', {}).get('boundStreamId'):
                logger.warning("No bound stream found for broadcast")
                return None
                
            # Get the stream details
            stream_response = self.client.liveStreams().list(
                part='snippet',
                id=broadcast['contentDetails']['boundStreamId']
            ).execute()
            
            if not stream_response.get('items'):
                logger.warning("No stream details found")
                return None
                
            # Get the live chat ID
            live_chat_id = stream_response['items'][0]['snippet'].get('liveChatId')
            if not live_chat_id:
                logger.warning("No live chat ID found")
                return None
                
            logger.info(f"Found live chat ID: {live_chat_id}")
            return live_chat_id
            
        except Exception as e:
            logger.error(f"Error getting live chat ID: {e}")
            return None

    async def process_chat_message(self, message: Dict[str, Any]) -> None:
        """Process a chat message from YouTube"""
        try:
            if not isinstance(message, dict):
                logger.error(f"Invalid message format: {message}")
                return
                
            if not self.ws_client:
                logger.warning("WebSocket client not connected")
                return
                
            # Extract message details
            snippet = message.get('snippet', {})
            if not snippet:
                logger.error("Message missing snippet")
                return
                
            author = snippet.get('authorChannelId', 'Unknown')
            text = snippet.get('displayMessage', '')
            if not text:
                logger.warning("Empty message received")
                return
                
            # Format the message
            formatted_message = {
                "type": "chat",
                "content": f"[YouTube] {author}: {text}"
            }
            
            # Send to WebSocket
            await self.ws_client.send(json.dumps(formatted_message))
            
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed while processing message")
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")

    def send_message(self, message: str) -> None:
        """Send a message to YouTube chat"""
        if self.live_chat_id and self.client:
            try:
                self.client.liveChatMessages().insert(
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
                ).execute()
                logger.info(f"Sent message to YouTube chat: {message}")
            except Exception as e:
                logger.error(f"Error sending message to YouTube chat: {e}")

    def is_connected(self) -> bool:
        """Check if the client is connected to a live chat"""
        return self.running and self.live_chat_id is not None and self.client is not None

    async def listen_to_chat(self) -> None:
        """Listen to the live chat and process messages"""
        while self.running:
            try:
                current_time = datetime.now()
                # Only check for streams every 30 seconds to avoid rate limiting
                if (not self.last_stream_check or 
                    (current_time - self.last_stream_check).total_seconds() > 30):
                    self.last_stream_check = current_time
                    self.live_chat_id = self.get_live_chat_id()

                if not self.live_chat_id:
                    self.retry_count += 1
                    if self.retry_count >= self.max_retries:
                        logger.warning("Max retries reached. No active stream found.")
                        logger.info("Please start a stream to continue. Will retry in 30 seconds...")
                        await asyncio.sleep(30)
                        self.retry_count = 0
                    else:
                        logger.debug(f"Retry {self.retry_count}/{self.max_retries} - No active stream found")
                        await asyncio.sleep(5)
                    continue

                # Reset retry count when we find a valid stream
                self.retry_count = 0

                try:
                    # Ensure WebSocket is connected
                    if not await self.ensure_websocket_connection():
                        logger.error("WebSocket connection lost, attempting to reconnect...")
                        await asyncio.sleep(5)
                        continue

                    # Get chat messages
                    response = self.client.liveChatMessages().list(
                        liveChatId=self.live_chat_id,
                        part='snippet,authorDetails',
                        pageToken=self.next_page_token
                    ).execute()

                    # Process messages
                    for message in response.get('items', []):
                        try:
                            await self.process_chat_message(message)
                        except Exception as e:
                            logger.error(f"Error processing individual message: {e}")
                            continue  # Continue processing other messages

                    # Get next page token and polling interval
                    self.next_page_token = response.get('nextPageToken')
                    polling_interval = response.get('pollingIntervalMillis', 5000) / 1000
                    
                    # Ensure polling interval is within reasonable bounds
                    polling_interval = max(1, min(polling_interval, 30))  # Between 1 and 30 seconds
                    
                    await asyncio.sleep(polling_interval)

                except googleapiclient.errors.HttpError as e:
                    if e.resp.status == 403:
                        logger.error("Rate limit exceeded. Waiting before retrying...")
                        await asyncio.sleep(30)
                    elif e.resp.status == 404:
                        logger.error("Live chat not found. Stream may have ended.")
                        self.live_chat_id = None
                        await asyncio.sleep(5)
                    elif e.resp.status == 401:
                        logger.error("Authentication expired. Please re-authenticate.")
                        self.running = False
                        break
                    else:
                        logger.error(f"HTTP error in chat listener: {e}")
                        await asyncio.sleep(5)
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed, attempting to reconnect...")
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Unexpected error in chat listener: {e}")
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                logger.info("Chat listener task cancelled")
                break
            except Exception as e:
                logger.error(f"Critical error in chat listener: {e}")
                await asyncio.sleep(5)

    async def start(self) -> None:
        """Start the YouTube chat client"""
        self.running = True
        
        # Load or get channel configuration
        if not self.load_config():
            logger.info("\nFirst time setup - getting your channel ID...")
            self.channel_id = self.get_channel_id()
            if self.channel_id:
                self.save_config()
                logger.info(f"✅ Channel ID saved: {self.channel_id}")
            else:
                logger.error("❌ Could not get channel ID")
                return

        await self.connect_websocket()
        await self.listen_to_chat()

    def stop(self) -> None:
        """Stop the YouTube chat client"""
        self.running = False

    def get_status(self) -> str:
        """Get detailed status information about the YouTube connection"""
        if not self.is_connected():
            return "Not connected"
            
        try:
            # Get live chat ID
            live_chat_id = self.get_live_chat_id()
            if not live_chat_id:
                return "Connected but no active stream found"
                
            # Get stream details from search API
            search_response = self.client.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video",
                maxResults=1
            ).execute()
            
            if not search_response.get("items"):
                return "Connected but no active stream found"
                
            video_id = search_response["items"][0]["id"]["videoId"]
            title = search_response["items"][0]["snippet"]["title"]
            
            # Get video details including viewer count
            video_response = self.client.videos().list(
                part="liveStreamingDetails,snippet,statistics",
                id=video_id
            ).execute()
            
            if not video_response.get("items"):
                return "Connected but stream details unavailable"
                
            video = video_response["items"][0]
            viewer_count = video.get("liveStreamingDetails", {}).get("concurrentViewers", "Unknown")
            total_viewers = video.get("statistics", {}).get("viewCount", "Unknown")
            
            # Get broadcast status
            broadcast_response = self.client.liveBroadcasts().list(
                part="status",
                id=video_id
            ).execute()
            
            status = "Unknown"
            if broadcast_response.get("items"):
                status = broadcast_response["items"][0]["status"]["lifeCycleStatus"]
                
            return f"Connected to stream: '{title}'\nStatus: {status}\nCurrent Viewers: {viewer_count}\nTotal Views: {total_viewers}"
            
        except Exception as e:
            logger.error(f"Error getting YouTube status: {e}")
            return "Error getting status information"

    def save_config(self) -> None:
        """Save configuration to config.json"""
        try:
            config = {
                'channel_id': self.channel_id
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def connect_to_stream(self, stream_id: str) -> bool:
        """Connect to a specific YouTube stream"""
        try:
            if not self.authenticated:
                if not self.authenticate():
                    return False
                    
            # Get the live chat ID for the stream
            self.live_chat_id = self.get_live_chat_id()
            if not self.live_chat_id:
                logger.error("Could not get live chat ID")
                return False
                
            # Ensure WebSocket is connected
            if not self.ws_client:
                try:
                    if not asyncio.run(self.connect_websocket()):
                        logger.error("Failed to connect WebSocket")
                        return False
                except Exception as e:
                    logger.error(f"Error connecting to WebSocket: {e}")
                    return False
                
            # Start listening to chat
            self.running = True
            try:
                self.chat_task = asyncio.create_task(self.listen_to_chat())
                logger.info(f"Connected to stream {stream_id}")
                return True
            except Exception as e:
                logger.error(f"Error creating chat task: {e}")
                self.running = False
                return False
            
        except Exception as e:
            logger.error(f"Error connecting to stream: {e}")
            self.running = False
            return False
            
    def disconnect(self) -> None:
        """Disconnect from the current stream"""
        try:
            self.running = False
            
            # Cancel chat task if it exists
            if hasattr(self, 'chat_task') and self.chat_task:
                try:
                    self.chat_task.cancel()
                    # Wait for task to complete
                    asyncio.run(asyncio.wait_for(self.chat_task, timeout=5))
                except asyncio.TimeoutError:
                    logger.warning("Chat task did not complete in time")
                except Exception as e:
                    logger.error(f"Error cancelling chat task: {e}")
                finally:
                    self.chat_task = None
            
            # Close WebSocket connection
            if self.ws_client:
                try:
                    asyncio.run(self.ws_client.close())
                except Exception as e:
                    logger.error(f"Error closing WebSocket: {e}")
                finally:
                    self.ws_client = None
            
            self.live_chat_id = None
            self.next_page_token = None
            logger.info("Disconnected from stream")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

async def main():
    client = YouTubeChatClient(os.path.dirname(__file__))
    try:
        if client.authenticate():
            await client.start()
    except KeyboardInterrupt:
        client.stop()
        print("\nStopping YouTube chat client...")

if __name__ == "__main__":
    asyncio.run(main()) 