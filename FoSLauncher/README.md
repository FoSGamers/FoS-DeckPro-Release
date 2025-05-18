# FoSLauncher

A modular application launcher for FoS tools and utilities.

## Features

- ChatSplitter: Split and organize chat conversations
- ChatBot Plus: Advanced chatbot with YouTube integration
- Command Manager: Manage and execute custom commands
- YouTube Login: Handle YouTube authentication

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/FoSLauncher.git
cd FoSLauncher
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up YouTube API credentials:
   - Create a project in the Google Cloud Console
   - Enable the YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download the client secrets file and place it in `modules/youtube_login/client_secrets.json`

## Usage

1. Start the launcher:
```bash
python FoSLauncher/foslauncher_gui.py
```

2. Use the buttons in the launcher to start individual modules.

## Module Descriptions

### ChatSplitter
Splits chat conversations into manageable files and organizes them with timestamps.

### ChatBot Plus
Advanced chatbot with YouTube integration for chat management and moderation.

### Command Manager
GUI for managing and executing custom commands and scripts.

### YouTube Login
Handles YouTube authentication and API access.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 