# Version History: 0.7.2 -> 0.7.3
# FoSBot: Your Epic Stream Chat Adventure

Welcome, brave streamer, to **FoSBot**—the ultimate companion for your Magic: The Gathering and Dungeons & Dragons live streams! This bot unites Whatnot, YouTube, Twitch, and X chats into one magical dashboard, letting you engage your party with commands like `!checkin`, `!ping`, and `!roll`. Roll for initiative and let's get started!

## Your Quest: Setup (Level 1 - Easy)

### Prerequisites
- **Python 3.13**: Your trusty spellbook. Install it from [python.org](https://www.python.org/downloads/) or via Homebrew (`brew install python@3.13`).
- **Chrome Browser**: Your enchanted portal to the dashboard.

### Step 1: Unpack the Treasure
1. **Grab the Loot**:
   - Download `fosbot.zip` from our Patreon ([insert your Patreon link]).
   - Unzip it to a folder, like `~/FoSBot`:
     ```bash
     unzip fosbot.zip -d ~/FoSBot
     ```

### Step 2: Cast the Setup Spell
1. **Enter the Dungeon**:
   - Open Terminal (Mac: Spotlight > "Terminal").
   - Navigate to your folder:
     ```bash
     cd ~/FoSBot
     ```
2. **Prepare Your Magic**:
   - Create a virtual environment and install dependencies:
     ```bash
     /opt/homebrew/bin/python3.13 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
3. **Launch the Portal**:
   - Run the app:
     ```bash
     uvicorn app.main:app --host localhost --port 8000
     ```
     - If you see “Application startup complete,” you’re ready!

### Step 3: Enter the Dashboard
1. **Open the Gate**:
   - In Chrome, go to http://localhost:8000.
2. **Join the Party**:
   - Go to the **Settings** tab.
   - Click “Login with YouTube,” “Login with Twitch,” and “Login with X.” Sign in to each—no developer portals needed, just your account!
3. **Whatnot Enchantment**:
   - In Settings, click “Guided Setup” for step-by-step help or download `whatnot_extension.zip`.
   - Unzip to a folder (e.g., `~/FoSBot_Whatnot`).
   - In Chrome, go to `chrome://extensions/`, enable “Developer mode,” click “Load unpacked,” and select the folder.
   - On a Whatnot stream, click the extension icon (puzzle piece), enable “Select Mode,” click chat elements, and save.
   - **Need Help?** Watch our 1-minute setup video on Patreon ([insert your video link]).

### Step 4: Wield Your Powers
- **Chat Tab**:
  - See all platform chats in real-time.
  - Send messages or commands (e.g., `!ping` for “Pong!”).
- **Commands Tab**:
  - Click “Add Command” to create new ones (e.g., `!roll` for “Rolled a 15!”).
  - Upload a CSV (`command,response`) to add multiple commands.
  - Edit or delete as needed.
- **Settings Tab**:
  - Manage logins, Twitch channels, and services (start/stop/restart).
- **Commands to Try**:
  - `!checkin`: Marks your presence in the tavern.
  - `!ping`: Tests the bot’s reflexes.
  - `!roll`: Rolls a die (e.g., `!roll d20`).
  - Add your own in the Commands tab!

## The Playbook: Tips for Glory
- **Engage Your Guild**:
  - Use `!roll` for D&D flair (add via Commands tab).
  - Broadcast messages to all platforms from the Chat tab.
- **Troubleshooting**:
  - **Login Issues?** Ensure you’re signed into the right account. Check the video if stuck.
  - **Whatnot Not Working?** Verify selectors in the extension popup.
  - **App Won’t Run?** Confirm Python 3.13 and re-run `pip install -r requirements.txt`.
- **Need a Bard?** Post on our Patreon for help!

## Epic Loot (Future Quests)
- Add more commands like `!quest` for community challenges.
- Share feedback on Patreon to shape FoSBot’s saga!

**Roll a natural 20 and stream on!**

*Created by [Your Name] for the MTG & D&D crew. No OAuth setup needed—log in and play!*
