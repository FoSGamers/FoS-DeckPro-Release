import json
import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import time

logger = logging.getLogger("FoSLauncher")

class StatusManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.status = {
            "youtube": {
                "enabled": False,
                "connected": False,
                "streaming": False,
                "viewer_count": 0,
                "last_check": None
            },
            "twitch": {
                "enabled": False,
                "connected": False,
                "streaming": False,
                "viewer_count": 0,
                "last_check": None
            },
            "twitter": {
                "enabled": False,
                "connected": False,
                "streaming": False,
                "viewer_count": 0,
                "last_check": None
            },
            "whatnot": {
                "enabled": False,
                "connected": False,
                "streaming": False,
                "viewer_count": 0,
                "last_check": None
            }
        }
        self.config = self.load_config()
        self.running = False
        self.check_thread = None
        self.youtube_client = None

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        try:
            # Try to load from main config first
            main_config_path = os.path.join(self.base_dir, "config.json")
            module_config_path = os.path.join(os.path.dirname(self.base_dir), "config.json")
            access_config_path = os.path.join(os.path.dirname(self.base_dir), "access.json")
            
            config = {}
            
            # Load main config
            if os.path.exists(main_config_path):
                with open(main_config_path, "r") as f:
                    config.update(json.load(f))
            
            # Load module config
            if os.path.exists(module_config_path):
                with open(module_config_path, "r") as f:
                    config.update(json.load(f))
            
            # Load access config
            if os.path.exists(access_config_path):
                with open(access_config_path, "r") as f:
                    access_config = json.load(f)
                    config["access"] = access_config
                    
            logger.info("Successfully loaded configuration")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def update_status(self, platform: str, status_data: Dict[str, Any]) -> None:
        """Update the status for a specific platform"""
        if platform in self.status:
            self.status[platform].update(status_data)
            self.status[platform]["last_check"] = datetime.now().isoformat()
            logger.debug(f"Updated {platform} status: {status_data}")

    def get_status(self, platform: str = None) -> Dict[str, Any]:
        """Get the status for a specific platform or all platforms"""
        if platform:
            return self.status.get(platform, {})
        return self.status

    def format_status_message(self) -> str:
        """Format the status information into a readable message"""
        message = "Stream Status:\n"
        for platform, status in self.status.items():
            if status["enabled"]:
                message += f"\n{platform.title()}:\n"
                message += f"  Connected: {'Yes' if status['connected'] else 'No'}\n"
                message += f"  Streaming: {'Yes' if status['streaming'] else 'No'}\n"
                if status["viewer_count"] > 0:
                    message += f"  Viewers: {status['viewer_count']}\n"
                if status["last_check"]:
                    last_check = datetime.fromisoformat(status["last_check"])
                    message += f"  Last Check: {last_check.strftime('%H:%M:%S')}\n"
        return message

    def check_youtube_status(self, youtube_client=None) -> None:
        """Check the status of YouTube streaming"""
        try:
            # Check if YouTube is enabled in config
            youtube_enabled = self.config.get("access", {}).get("modules", {}).get("chatbot_plus", {}).get("features", {}).get("youtube", False)
            
            if not youtube_enabled:
                self.update_status("youtube", {
                    "enabled": False,
                    "connected": False,
                    "streaming": False,
                    "viewer_count": 0
                })
                return

            # Check if client is initialized and authenticated
            if not youtube_client or not youtube_client.authenticated:
                self.update_status("youtube", {
                    "enabled": True,
                    "connected": False,
                    "streaming": False,
                    "viewer_count": 0
                })
                return

            # Check if streaming
            live_chat_id = youtube_client.get_live_chat_id()
            if live_chat_id:
                # Get viewer count
                viewer_count = 0
                try:
                    # Get live stream details
                    streams = youtube_client.list_available_streams()
                    if isinstance(streams, list) and streams:
                        # Get the first stream's statistics
                        stream_id = streams[0]["id"]
                        stream_response = youtube_client.client.videos().list(
                            part="statistics",
                            id=stream_id
                        ).execute()
                        
                        if stream_response.get("items"):
                            viewer_count = int(stream_response["items"][0]["statistics"].get("viewCount", 0))
                except Exception as e:
                    logger.error(f"Error getting viewer count: {e}")
                
                self.update_status("youtube", {
                    "enabled": True,
                    "connected": True,
                    "streaming": True,
                    "viewer_count": viewer_count
                })
            else:
                self.update_status("youtube", {
                    "enabled": True,
                    "connected": True,
                    "streaming": False,
                    "viewer_count": 0
                })

        except Exception as e:
            logger.error(f"Error checking YouTube status: {e}")
            self.update_status("youtube", {
                "enabled": True,
                "connected": False,
                "streaming": False,
                "viewer_count": 0
            })

    def start_status_checks(self) -> None:
        """Start the periodic status checks"""
        if self.running:
            return

        self.running = True
        self.check_thread = threading.Thread(target=self._status_check_loop)
        self.check_thread.daemon = True
        self.check_thread.start()

    def _status_check_loop(self) -> None:
        """Main loop for checking platform statuses"""
        while self.running:
            try:
                # Get the YouTube client from the main module
                from .main import youtube_client
                self.check_youtube_status(youtube_client)
                # TODO: Add checks for other platforms
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in status check loop: {e}")
                if self.running:  # Only sleep if we're still running
                    time.sleep(30)  # Wait before retrying

    def stop_status_checks(self) -> None:
        """Stop the periodic status checks"""
        self.running = False
        if self.check_thread:
            try:
                self.check_thread.join(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping status check thread: {e}")
            finally:
                self.check_thread = None

    def set_youtube_client(self, client) -> None:
        """Set the YouTube client for status checks"""
        self.youtube_client = client

    def cleanup(self) -> None:
        """Clean up resources"""
        self.stop_status_checks()
        self.youtube_client = None 