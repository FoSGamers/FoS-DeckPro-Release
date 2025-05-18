# FoSBot - Multi-Platform Stream Chatbot (Webapp Config Version)

Handles chat aggregation and bot commands. API keys and settings are configured via the web UI after launching. Data is stored in JSON files in the `./data` directory.

## Setup

1.  Run the setup script: `./setup_fosbot.sh`
2.  Follow prompts (may require sudo for Homebrew/Xcode tools).
3.  Follow the final manual steps printed by the script (Load browser extension, configure its selectors).

## Running

1.  Activate the virtual environment: `source venv/bin/activate`
2.  Start the backend server: `uvicorn app.main:app --reload --host localhost`
3.  Open the dashboard in your browser (usually `http://localhost:8000`).
4.  Navigate to the **Settings** tab in the dashboard.
5.  Enter your API keys, tokens, bot/channel names, etc., and click "Save" for each section.
6.  Use the "Service Control" buttons (e.g., "Start Twitch") on the Settings tab to activate the platform connections.
7.  Configure the Whatnot extension selectors via its popup while on a Whatnot page.

