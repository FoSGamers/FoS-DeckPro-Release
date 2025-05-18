# Version History: 0.7.2 -> 0.7.3
#!/bin/bash

mkdir -p app/core app/services app/apis static whatnot_extension data
touch app/__init__.py app/main.py app/events.py
touch app/core/__init__.py app/core/config.py app/core/event_bus.py app/core/json_store.py
touch app/services/__init__.py app/services/chat_processor.py app/services/dashboard_service.py
touch app/services/streamer_command_handler.py app/services/twitch_service.py
touch app/services/youtube_service.py app/services/x_service.py app/services/whatnot_bridge.py
touch app/apis/__init__.py app/apis/auth_api.py app/apis/settings_api.py
touch app/apis/ws_endpoints.py app/apis/commands_api.py
touch static/index.html static/main.js
touch whatnot_extension/manifest.json whatnot_extension/background.js
touch whatnot_extension/popup.html whatnot_extension/popup.js whatnot_extension/content.js
touch data/oauth_states.json data/settings.json data/commands.json data/tokens.json
touch requirements.txt README.md combine_files.py create_fosbot_files.sh .env .gitignore
