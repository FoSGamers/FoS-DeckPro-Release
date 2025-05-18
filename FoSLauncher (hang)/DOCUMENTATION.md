# FoSLauncher Documentation

## Overview
FoSLauncher is a modular application launcher with integrated YouTube chat functionality. It provides a secure, user-friendly interface for managing and launching various modules.

## Project Structure
```
FoSLauncher/
├── foslauncher_cli.py          # Main application entry point
├── config.json                 # Main configuration file
├── logs/                       # Log files directory
├── backup/                     # Backup files directory
└── modules/                    # Module directory
    ├── logger.py               # Centralized logging system
    ├── access.json             # Access control configuration
    ├── manifest.json           # Module manifest
    ├── command_manager_gui.py  # GUI command management
    ├── chatbot_plus_module.py  # Chatbot+ module definition
    ├── gui/                    # GUI module
    │   ├── main.py            # GUI implementation
    │   └── config.json        # GUI configuration
    ├── chatbot_plus/          # Chatbot+ module
    │   ├── main.py            # Main module implementation
    │   ├── unified_chat.py    # Unified chat handling
    │   ├── command_manager.py # Command management
    │   ├── status_manager.py  # Status management
    │   ├── commands.json      # Command definitions
    │   ├── requirements.txt   # Module dependencies
    │   └── stream_clients/    # Stream client implementations
    │       ├── youtube_client.py  # YouTube client
    │       └── config.json    # Stream client configuration
    └── chatsplitter/          # Chat splitter module
        └── main.py            # Chat splitter implementation
```

## Core Components

### 1. Main Launcher (`foslauncher_cli.py`)
- Entry point for the application
- Handles configuration loading and access verification
- Initializes the GUI and manages the main application loop
- Key functions:
  - `load_config()`: Loads configuration from config.json
  - `verify_access_code()`: Handles access code verification
  - `main()`: Application entry point
  - `setup_logging()`: Configures logging system

### 2. GUI Module (`modules/gui/main.py`)
- CustomTkinter-based graphical interface
- Features:
  - Module discovery and display
  - Access code verification
  - YouTube integration
  - Module launching
  - Status monitoring
- Key classes:
  - `FoSLauncherGUI`: Main GUI class
  - `AccessCodeDialog`: Handles access code input
  - `ModuleFrame`: Individual module display
- Configuration:
  - Theme settings
  - Module display preferences
  - Access control settings

### 3. Chatbot+ Module (`modules/chatbot_plus/`)
- Core chat management system
- Components:
  - `main.py`: Module entry point and WebSocket server
    - Initializes YouTube client and chat interface
    - Runs FastAPI server for WebSocket communication
    - Manages global state and message routing
    - Handles cleanup and shutdown
  - `unified_chat.py`: Unified chat message handling
    - Provides GUI interface for chat
    - Connects to FastAPI server via WebSocket
    - Uses shared YouTube client instance
    - Handles chat commands and message display
  - `command_manager.py`: Command processing system
  - `status_manager.py`: Stream status monitoring
  - `stream_clients/`: Platform-specific implementations
- Component Interaction Flow:
  1. `main.py` initializes YouTube client and chat interface
  2. FastAPI server starts in a non-daemon thread
  3. Chat interface connects to WebSocket server
  4. Messages flow:
     - User input → chat interface → WebSocket server → YouTube client → YouTube
     - YouTube messages → YouTube client → WebSocket server → chat interface → GUI
- Features:
  - Multi-platform chat support
  - Command processing
  - Status monitoring
  - WebSocket integration
  - Proper thread management
  - Clean shutdown handling

### 4. YouTube Client (`modules/chatbot_plus/stream_clients/youtube_client.py`)
- Handles YouTube API integration
- Features:
  - OAuth2 authentication via browser
  - Live stream monitoring
  - Chat message handling
  - Stream status tracking
  - WebSocket integration for real-time chat
  - Automatic reconnection handling
  - Rate limit management
- Key methods:
  - `authenticate()`: Handles YouTube authentication
  - `list_available_streams()`: Lists active streams
  - `send_message()`: Sends messages to YouTube chat
  - `listen_to_chat()`: Monitors chat messages
  - `process_chat_message()`: Processes incoming chat messages
  - `connect_websocket()`: Connects to local WebSocket server
  - `get_status()`: Retrieves detailed stream status
  - `stop()`: Clean shutdown of client
- Thread Safety:
  - Single instance shared between components
  - Proper cleanup on shutdown
  - Thread-safe message handling

### 5. Chat Splitter Module (`modules/chatsplitter/main.py`)
- Handles chat message splitting and formatting
- Features:
  - Message length management
  - Formatting options
  - Character limit handling
  - Multi-platform support

### 6. Configuration System
- Multiple configuration files:
  - `config.json`: Main application configuration
  - `modules/config.json`: Module-specific settings
  - `modules/access.json`: Access control settings
  - `modules/chatbot_plus/config.json`: Chatbot+ settings
  - `modules/chatbot_plus/commands.json`: Command definitions
  - `modules/gui/config.json`: GUI settings
- Configuration hierarchy:
  1. Main config (global settings)
  2. Module config (module-specific settings)
  3. Access config (permission settings)

### 7. Command System
- Centralized command management
- Features:
  - Command registration
  - Permission checking
  - Command execution
  - Response handling
- Command types:
  - YouTube commands
  - System commands
  - Module-specific commands
- Command format:
  - Prefix: '!'
  - Structure: `!command [args]`
  - Examples: `!youtube auth`, `!status`

### 8. Logging System (`modules/logger.py`)
- Centralized logging implementation
- Features:
  - Multiple log levels
  - Rotating file handler
  - Console output
  - Error tracking
- Log levels:
  - DEBUG: Detailed information
  - INFO: General information
  - WARNING: Potential issues
  - ERROR: Error conditions
  - CRITICAL: Fatal errors
- Log file management:
  - Daily rotation
  - Size-based rotation
  - Backup retention

## Access Control
- Three access levels:
  1. Master: Full access to all features
  2. Premium: Access to premium modules
  3. Basic: Access to basic modules
- Access codes stored in config.json
- Verification required at startup
- Access level persists for session
- Module-specific access control
- Command-level permissions

## Module System
- Modules discovered automatically
- Each module requires:
  - main.py file
  - Configuration in config.json
  - Access level requirements
- Module types:
  - Core modules (required)
  - Optional modules
  - Platform-specific modules
- Module lifecycle:
  1. Discovery
  2. Configuration loading
  3. Access verification
  4. Initialization
  5. Execution
  6. Cleanup

## YouTube Integration
- Browser-based OAuth2 authentication
- Features:
  - Live stream monitoring
  - Chat message handling
  - Stream status tracking
  - Real-time chat processing
  - Command handling
  - Automatic reconnection
- Requirements:
  - Google Cloud project
  - YouTube Data API enabled
  - OAuth2 credentials
  - WebSocket server running on port 8001
- Authentication flow:
  1. User clicks "Connect to YouTube"
  2. Browser opens for OAuth2
  3. User authorizes application
  4. Token stored securely
  5. Connection established

## Security
- Access code verification
- Secure credential storage
- Permission-based module access
- OAuth2 for YouTube integration
- WebSocket communication for chat
- Rate limiting
- Error handling
- Secure token storage

## Usage
1. Start the launcher: `python3 foslauncher_cli.py`
2. Enter access code when prompted
3. Click "Connect to YouTube" to authenticate
4. Launch desired modules
5. For YouTube chat:
   - Start a live stream
   - Chat messages will be processed automatically
   - Commands starting with '!' will be processed
6. Monitor status:
   - Use !status command
   - Check GUI status panel
   - Review logs if needed

## Troubleshooting
1. Access Issues:
   - Verify access code in config.json
   - Check module permissions
   - Restart launcher if access level changes
   - Review access.json configuration
2. YouTube Integration:
   - Ensure client_secrets.json is present in project root
   - Verify OAuth2 credentials
   - Check API quota limits
   - Ensure WebSocket server is running
   - Check token.pickle file
3. Module Launching:
   - Verify module configuration
   - Check access level requirements
   - Review logs for errors
   - Check module dependencies
4. Chat Issues:
   - Verify stream is live
   - Check WebSocket connection
   - Review chat permissions
   - Monitor rate limits
   - Check command processing
5. General Issues:
   - Check log files
   - Verify configuration files
   - Restart application
   - Clear cached tokens if needed 