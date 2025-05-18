import os
import sys
import json
import logging
import asyncio
import threading
import time
from typing import Dict, Any, List
import unittest
from unittest.mock import patch, MagicMock
import websockets
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import websocket

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import all modules we want to test
from modules.logger import FoSLogger
from modules.chatbot_plus.main import initialize_components, run_fastapi, cleanup
from modules.youtube_login.youtube_client import YouTubeClient
from modules.chatbot_plus.unified_chat import UnifiedChatInterface
from modules.chatbot_plus.command_manager import CommandManager
from modules.chatbot_plus.status_manager import StatusManager
from modules.chatsplitter.main import FoSGamersChatSplitter
from modules.gui.main import FoSLauncherGUI
from foslauncher_cli import FoSLauncher
from modules.websocket_server import WebSocketServer

class TestFoSLauncher(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(os.path.join(self.base_dir, "logs")):
            os.makedirs(os.path.join(self.base_dir, "logs"))
        self.logger = FoSLogger()
        self.launcher = FoSLauncher()

    def tearDown(self):
        """Clean up test environment"""
        self.logger.cleanup()

    def test_01_logger_initialization(self):
        """Test logger initialization"""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(self.base_dir, "logs")
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)

            # Initialize logger
            logger = FoSLogger()

            # Test singleton behavior
            logger2 = FoSLogger()
            self.assertEqual(logger, logger2)

            # Test log file creation
            log_file = os.path.join(logs_dir, "foslauncher.log")
            self.assertTrue(os.path.exists(log_file))

            # Test logging levels
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")

            # Verify log content
            with open(log_file, 'r') as f:
                content = f.read()
                self.assertIn("Test info message", content)
                self.assertIn("Test warning message", content)
                self.assertIn("Test error message", content)

            print("✅ Logger initialization test passed")
        except Exception as e:
            print(f"❌ Logger initialization test failed: {e}")
            raise

    def test_05_youtube_client(self):
        """Test YouTube client functionality"""
        try:
            # Initialize YouTube client with base directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            client = YouTubeClient(base_dir)
            self.assertIsNotNone(client)
            
            # Test configuration loading
            self.assertIsInstance(client.config, dict)
            self.assertFalse(client.authenticated)
            self.assertIsNone(client.live_chat_id)
            
            # Mock authentication
            with patch.object(client, 'authenticate') as mock_auth:
                mock_auth.return_value = True
                self.assertTrue(client.authenticate())
            
            # Test stream listing
            with patch.object(client, 'list_available_streams') as mock_list:
                mock_list.return_value = [{"id": "test_stream", "title": "Test Stream"}]
                streams = client.list_available_streams()
                self.assertIsInstance(streams, list)
                self.assertEqual(len(streams), 1)
                self.assertEqual(streams[0]["id"], "test_stream")
            
            # Test connection
            with patch.object(client, 'connect_to_stream') as mock_connect:
                mock_connect.return_value = True
                self.assertTrue(client.connect_to_stream("test_stream"))
            
            # Test message processing
            test_message = {
                "snippet": {
                    "authorChannelId": "test_author",
                    "displayMessage": "test message"
                }
            }
            asyncio.run(client.process_chat_message(test_message))
            
            # Cleanup
            client.disconnect()
            print("✅ YouTube client test passed")
        except Exception as e:
            print(f"✗ YouTube client test failed: {str(e)}")
            raise

    def test_06_unified_chat(self):
        """Test unified chat interface"""
        try:
            # Initialize components
            base_dir = os.path.dirname(os.path.abspath(__file__))
            youtube_client = YouTubeClient(base_dir)
            chat = UnifiedChatInterface(base_dir, youtube_client=youtube_client)

            # Test message sending
            test_message = "Test message"
            chat.send_message(test_message)

            # Test YouTube command handling
            response = chat.handle_youtube_command("auth", [])
            self.assertIsInstance(response, str)

            # Test message display
            chat.display_message("Test display message")

            # Test permission checking
            self.assertFalse(chat.has_permission("master"))
            self.assertFalse(chat.has_permission("premium"))

            # Test command handling
            asyncio.run(chat.handle_command("!test"))

            # Test cleanup
            chat.cleanup()

            print("✅ Unified chat test passed")
        except Exception as e:
            print(f"❌ Unified chat test failed: {e}")
            raise

    def test_07_gui(self):
        """Test GUI operations"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.title("FoSLauncher")  # Set the title before creating the GUI
            root.withdraw()  # Hide the window during tests
            gui = FoSLauncherGUI(root, base_dir=os.path.dirname(os.path.abspath(__file__)))
            
            # Test frame creation
            self.assertIsNotNone(gui)
            self.assertEqual(gui.root.title(), "FoSLauncher")
            
            # Test module discovery
            gui.discover_modules()
            self.assertIsInstance(gui.modules, list)
            
            # Test widget creation
            gui.create_widgets()
            self.assertIsNotNone(gui.main_container)
            self.assertIsNotNone(gui.module_frame)
            
            # Cleanup
            root.destroy()
            print("✅ GUI test passed")
        except Exception as e:
            print(f"✗ GUI test failed: {str(e)}")
            raise

    def test_09_component_initialization(self):
        """Test component initialization order and dependencies"""
        try:
            # Initialize components in correct order
            base_dir = os.path.dirname(os.path.abspath(__file__))
            launcher = FoSLauncher()
            config = launcher.load_config()
            access = launcher.load_access_control()
            
            # Initialize YouTube client
            youtube_client = YouTubeClient(base_dir)
            self.assertIsNotNone(youtube_client)
            
            # Initialize chat interface
            chat_interface = UnifiedChatInterface(base_dir, youtube_client=youtube_client)
            self.assertIsNotNone(chat_interface)
            
            # Initialize status manager
            status_manager = StatusManager()
            self.assertIsNotNone(status_manager)
            
            # Test component dependencies
            self.assertTrue(hasattr(youtube_client, 'config'))
            self.assertTrue(hasattr(chat_interface, 'youtube_client'))
            self.assertTrue(hasattr(status_manager, 'youtube_client'))
            
            # Test component communication
            test_message = "Test message"
            chat_interface.send_message(test_message)
            status = status_manager.get_status()
            self.assertIn("youtube", status)
            
            # Cleanup
            youtube_client.disconnect()
            chat_interface.stop()
            status_manager.cleanup()
            print("✅ Component initialization test passed")
        except Exception as e:
            print(f"✗ Component initialization test failed: {str(e)}")
            raise

    def test_08_websocket_server(self):
        """Test WebSocket server functionality"""
        try:
            # Initialize WebSocket server
            server = WebSocketServer()
            self.assertIsNotNone(server)
            
            # Start server in a separate thread
            server_thread = threading.Thread(target=server.start)
            server_thread.daemon = True
            server_thread.start()
            
            # Wait for server to start
            time.sleep(1)
            
            # Test server status
            self.assertTrue(server.is_running())
            
            # Test client connection
            ws = websocket.WebSocket()
            ws.connect("ws://localhost:8765")
            self.assertTrue(ws.connected)
            
            # Test message handling
            test_message = "Test message"
            ws.send(test_message)
            response = ws.recv()
            self.assertEqual(response, test_message)
            
            # Cleanup
            ws.close()
            server.stop()
            server_thread.join(timeout=5)
            print("✅ WebSocket server test passed")
        except Exception as e:
            print(f"✗ WebSocket server test failed: {str(e)}")
            raise

    def test_10_access_control(self):
        """Test access control functionality"""
        try:
            # Load access control configuration
            config = self.launcher.load_access_control()
            self.assertIsInstance(config, dict)
            self.assertIn("modules", config)
            self.assertIn("chatbot_plus", config["modules"])

            print("✅ Access control test passed")
        except Exception as e:
            print(f"❌ Access control test failed: {e}")
            raise

    def test_11_config_manager(self):
        """Test configuration manager functionality"""
        try:
            # Load configuration
            config = self.launcher.load_config()
            self.assertIsInstance(config, dict)
            self.assertIn("settings", config)
            self.assertIn("modules", config)
            self.assertIn("youtube", config)
            self.assertTrue(config["modules"]["chatbot_plus"]["enabled"])

            # Test manifest loading
            manifest = self.launcher.load_manifest()
            self.assertIsInstance(manifest, list)
            self.assertTrue(len(manifest) > 0)
            self.assertIn("Name", manifest[0])
            self.assertIn("ID", manifest[0])
            self.assertIn("Entry", manifest[0])
            self.assertIn("Status", manifest[0])

            print("✅ Config manager test passed")
        except Exception as e:
            print(f"❌ Config manager test failed: {e}")
            raise

    def test_12_integration(self):
        """Test integration between components"""
        try:
            # Initialize components
            launcher = FoSLauncher()
            config = launcher.load_config()
            access = launcher.load_access_control()

            self.assertIsNotNone(config)
            self.assertIsNotNone(access)
            self.assertIn("modules", access)
            self.assertIn("chatbot_plus", access["modules"])

            # Initialize chat components
            base_dir = os.path.dirname(os.path.abspath(__file__))
            youtube_client = YouTubeClient(base_dir)
            chat_interface = UnifiedChatInterface(base_dir, youtube_client=youtube_client)

            # Test message flow
            test_message = "Test integration message"
            chat_interface.send_message(test_message)

            # Test command handling
            response = chat_interface.handle_youtube_command("auth", [])
            self.assertIsInstance(response, str)

            # Test status updates
            status_manager = StatusManager()
            status_manager.update_status("youtube", {"enabled": True, "connected": True})
            status = status_manager.get_status("youtube")
            self.assertTrue(status["enabled"])
            self.assertTrue(status["connected"])

            # Clean up
            chat_interface.cleanup()
            status_manager.cleanup()
            youtube_client.disconnect()

            print("✅ Integration test passed")
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            raise

    def test_04_status_manager(self):
        """Test status manager functionality"""
        try:
            # Initialize status manager
            status_manager = StatusManager()
            
            # Test initial state
            self.assertFalse(status_manager.status["youtube"]["enabled"])
            self.assertFalse(status_manager.status["youtube"]["connected"])
            self.assertFalse(status_manager.status["youtube"]["streaming"])
            self.assertEqual(status_manager.status["youtube"]["viewer_count"], 0)
            self.assertIsNone(status_manager.status["youtube"]["last_check"])
            
            # Test status update
            status_manager.update_status("youtube", {"enabled": True})
            self.assertTrue(status_manager.status["youtube"]["enabled"])
            
            # Test status message formatting
            status_message = status_manager.format_status_message()
            self.assertIn("Youtube", status_message)
            self.assertIn("Connected: No", status_message)
            self.assertIn("Streaming: No", status_message)
            
            # Test status checks
            status_manager.start_status_checks()
            self.assertTrue(status_manager.running)
            self.assertIsNotNone(status_manager.check_thread)
            
            # Test cleanup
            status_manager.cleanup()
            self.assertFalse(status_manager.running)
            self.assertIsNone(status_manager.check_thread)
            self.assertIsNone(status_manager.youtube_client)
            
            print("✓ Status manager test passed")
        except Exception as e:
            print(f"✗ Status manager test failed: {str(e)}")
            raise

if __name__ == '__main__':
    unittest.main()