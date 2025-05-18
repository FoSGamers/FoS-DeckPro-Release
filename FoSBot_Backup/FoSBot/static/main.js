// Main dashboard script
document.addEventListener('DOMContentLoaded', () => {
    const statusIndicators = {
        twitch: document.getElementById('twitch-status'),
        youtube: document.getElementById('youtube-status'),
        x: document.getElementById('x-status'),
        whatnot: document.getElementById('whatnot-status')
    };

    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');
    ws.onopen = () => {
        console.log('Dashboard WebSocket connected');
    };
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'status_update') {
                const { platform, status } = data.payload;
                const indicator = statusIndicators[platform];
                if (indicator) {
                    indicator.style.backgroundColor = status === 'connected' ? 'green' : 'red';
                    console.log(`Status update: ${platform} is ${status}`);
                }
            }
        } catch (e) {
            console.error('Error parsing dashboard WebSocket message:', e);
        }
    };
    ws.onclose = () => {
        console.log('Dashboard WebSocket disconnected, retrying in 5s');
        setTimeout(() => {
            location.reload();
        }, 5000);
    };

    // Fetch initial settings and commands
    fetch('/api/settings').then(res => res.json()).then(data => {
        document.getElementById('command-prefix').value = data.COMMAND_PREFIX;
        document.getElementById('log-level').value = data.LOG_LEVEL;
        document.getElementById('twitch-channels').value = data.TWITCH_CHANNELS;
        updateAuthStatus(data.twitch_auth_status, 'twitch');
        updateAuthStatus(data.youtube_auth_status, 'youtube');
        updateAuthStatus(data.x_auth_status, 'x');
    });

    fetch('/api/commands').then(res => res.json()).then(commands => {
        const commandList = document.getElementById('command-list');
        Object.entries(commands).forEach(([name, response]) => {
            const li = document.createElement('li');
            li.textContent = `!${name}: ${response}`;
            commandList.appendChild(li);
        });
    });

    function updateAuthStatus(auth, platform) {
        const statusEl = document.getElementById(`${platform}-auth-status`);
        if (auth.logged_in) {
            statusEl.textContent = `Logged in as ${auth.user_login}`;
            statusEl.style.color = 'green';
        } else {
            statusEl.textContent = 'Not logged in';
            statusEl.style.color = 'red';
        }
    }

    // Control buttons
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const [platform, action] = btn.id.split('-');
            fetch(`/api/control/${platform}/${action}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => console.log(`${platform} ${action}:`, data))
                .catch(err => console.error('Control error:', err));
        });
    });
});