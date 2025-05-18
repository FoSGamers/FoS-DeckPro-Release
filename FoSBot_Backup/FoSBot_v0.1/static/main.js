// --- File: static/main.js --- START ---
// FoSBot Dashboard Frontend JS v0.6 (OAuth Flow)

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const chatOutput = document.getElementById('chat-output');
    const streamerInput = document.getElementById('streamerInput');
    const sendButton = document.getElementById('sendButton');
    const clearButton = document.getElementById('clearButton');
    const wsStatusElement = document.getElementById('status-ws').querySelector('.status-text');
    const wsLightElement = document.getElementById('status-ws').querySelector('.status-light');
    const platformStatusIndicators = {
        twitch: document.getElementById('status-twitch'),
        youtube: document.getElementById('status-youtube'),
        x: document.getElementById('status-x'),
        whatnot: document.getElementById('status-whatnot')
    };
    const generalStatus = document.getElementById('general-status');
    const logOutput = document.getElementById('log-output');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const settingsStatus = document.getElementById('settings-status');
    // Settings Forms (Non-Auth)
    const manualSettingsForms = document.querySelectorAll('#settings-container form:not(#twitch-settings-form-manual)'); // Exclude manual twitch form initially
    const appSettingsForm = document.getElementById('app-settings-form'); // Keep separate ref if needed
    // Auth Areas
    const twitchAuthArea = document.getElementById('twitch-auth-area');
    // Service Control Buttons
    const controlButtons = document.querySelectorAll('.control-button');

    // --- WebSocket State ---
    let socket = null;
    let reconnectTimer = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 15;
    const RECONNECT_DELAY_BASE = 3000;

    // --- State ---
    let currentSettings = {}; // Store loaded settings

    // --- Helper Functions ---
    function updateStatusIndicator(statusId, statusClass, statusText = '') {
        const indicator = platformStatusIndicators[statusId];
        const defaultText = statusClass ? statusClass.charAt(0).toUpperCase() + statusClass.slice(1) : 'Unknown';
        const textToShow = statusText || defaultText;
        if (indicator) {
            const textEl = indicator.querySelector('.status-text');
            const lightEl = indicator.querySelector('.status-light');
            if(textEl && lightEl){
                lightEl.className = 'status-light'; // Reset
                lightEl.classList.add(`status-${statusClass}`);
                textEl.textContent = textToShow;
            }
        } else if (statusId === 'ws') {
            wsLightElement.className = 'status-light'; // Reset
            wsLightElement.classList.add(`status-${statusClass}`);
            wsStatusElement.textContent = textToShow;
        }
    }

    function formatTimestamp(isoTimestamp) { /* ... (keep unchanged) ... */ }
    function escapeHtml(unsafe) { /* ... (keep unchanged) ... */ }
    function linkify(text) { /* ... (keep unchanged) ... */ }
    function addChatMessage(platform, user, text, timestamp = null) { /* ... (keep unchanged) ... */ }
    function addLogMessage(level, message, moduleName = '') { /* ... (keep unchanged) ... */ }

    function showSettingsStatus(message, isError = false, duration = 5000) {
        if (!settingsStatus) return;
        settingsStatus.textContent = message;
        settingsStatus.className = isError ? 'error' : 'success';
        settingsStatus.style.display = 'block';
        clearTimeout(settingsStatus.timer);
        if (duration > 0) {
            settingsStatus.timer = setTimeout(() => {
                settingsStatus.textContent = '';
                settingsStatus.style.display = 'none';
                settingsStatus.className = '';
            }, duration);
        }
    }

    // --- OAuth UI Update ---
    function updateAuthUI(platform, authData) {
        const authArea = document.getElementById(`${platform}-auth-area`);
        if (!authArea) return;

        authArea.innerHTML = ''; // Clear previous content

        if (authData && authData.user_login) {
            // Logged In State
            const statusSpan = document.createElement('span');
            statusSpan.className = 'auth-status';
            statusSpan.innerHTML = `Logged in as: <strong>${escapeHtml(authData.user_login)}</strong>`;

            const logoutButton = document.createElement('button');
            logoutButton.className = 'oauth-logout-button';
            logoutButton.textContent = 'Logout';
            logoutButton.dataset.platform = platform; // Store platform for handler
            logoutButton.addEventListener('click', handleLogoutClick);

            authArea.appendChild(statusSpan);
            authArea.appendChild(logoutButton);
            updateStatusIndicator(platform, 'connected', `Logged in as ${authData.user_login}`); // Update header status too

        } else {
            // Logged Out State
            const loginButton = document.createElement('button');
            loginButton.className = 'oauth-login-button';
            loginButton.textContent = `Login with ${platform.charAt(0).toUpperCase() + platform.slice(1)}`;
            loginButton.dataset.platform = platform; // Store platform for handler
            loginButton.addEventListener('click', handleLoginClick);

            const statusSpan = document.createElement('span');
            statusSpan.className = 'auth-status not-logged-in';
            statusSpan.textContent = 'Not Logged In';

            authArea.appendChild(loginButton);
            authArea.appendChild(statusSpan);
            updateStatusIndicator(platform, 'logged_out', 'Logged Out'); // Update header status
        }
    }

    function handleLoginClick(event) {
        const platform = event.target.dataset.platform;
        if (!platform) return;
        addLogMessage('INFO', `Initiating login flow for ${platform}...`);
        // Redirect the browser to the backend login endpoint
        window.location.href = `/auth/${platform}/login`;
    }

    async function handleLogoutClick(event) {
        const platform = event.target.dataset.platform;
        if (!platform) return;

        if (!confirm(`Are you sure you want to logout from ${platform.toUpperCase()}? This will disconnect the service.`)) {
            return;
        }

        addLogMessage('INFO', `Initiating logout for ${platform}...`);
        showSettingsStatus(`Logging out from ${platform}...`, false, 0); // Indefinite status

        try {
            const response = await fetch(`/auth/${platform}/logout`, { method: 'POST' });
            const result = await response.json(); // Assume JSON response

            if (response.ok) {
                showSettingsStatus(result.message || `${platform.toUpperCase()} logout successful.`, false);
                addLogMessage('INFO', `${platform.toUpperCase()} logout: ${result.message}`);
                // Refresh settings/auth status after logout
                requestSettings();
            } else {
                 showSettingsStatus(`Logout Error: ${result.detail || response.statusText}`, true);
                 addLogMessage('ERROR', `Logout Error (${platform}): ${result.detail || response.statusText}`);
            }
        } catch (error) {
            console.error(`Logout Error (${platform}):`, error);
            showSettingsStatus(`Network error during logout: ${error.message}`, true);
            addLogMessage('ERROR', `Network error during ${platform} logout: ${error.message}`);
        }
    }


    // --- WebSocket Handling ---
    function handleWebSocketMessage(data) {
        switch (data.type) {
            case 'chat': addChatMessage(data.platform, data.user, data.text, data.timestamp); break;
            case 'platform_status':
                 // Don't override logged-in status from manual status updates unless it's disconnected/error
                 const isLoggedIn = currentSettings[`${data.platform}_user_login`];
                 if (!isLoggedIn || (isLoggedIn && ['disconnected', 'error', 'auth_error', 'stopped'].includes(data.status.toLowerCase()))) {
                     updateStatusIndicator(data.platform, data.status.toLowerCase(), data.message || data.status);
                 } else {
                     // If logged in, just maybe update the light color based on connection status?
                     updateStatusIndicator(data.platform, data.status.toLowerCase(), `Logged in as ${isLoggedIn}`);
                 }
                 addLogMessage('INFO', `Platform [${data.platform.toUpperCase()}]: ${data.status} ${data.message ? '- ' + data.message : ''}`);
                 break;
            case 'log': addLogMessage(data.level, data.message, data.module); break;
            case 'status': addLogMessage('INFO', `Backend: ${data.message}`); generalStatus.textContent = `App Status: ${data.message}`; break;
            case 'error': addLogMessage('ERROR', `Backend Err: ${data.message}`); generalStatus.textContent = `App Status: Error - ${data.message}`; break;
            case 'pong': console.log("Pong received."); break;
            case 'current_settings':
                 currentSettings = data.payload || {}; // Store settings globally
                 populateSettingsForm(currentSettings);
                 updateAuthUI('twitch', { user_login: currentSettings.twitch_user_login }); // Update Twitch Auth UI
                 // Update other auth UIs if/when implemented
                 // updateAuthUI('youtube', { user_login: currentSettings.youtube_user_login });
                 // updateAuthUI('x', { user_login: currentSettings.x_user_login });
                 break;
            default: console.warn("Unknown WS type:", data.type, data); addLogMessage('WARN', `Unknown WS message type: ${data.type}`);
        }
    }

    function connectWebSocket() { /* ... (keep unchanged from previous correct version) ... */ }

    // --- Input Handling ---
    function sendStreamerInput() { /* ... (keep unchanged) ... */ }
    sendButton.addEventListener('click', sendStreamerInput);
    streamerInput.addEventListener('keypress', (event) => { /* ... */ });
    clearButton.addEventListener('click', () => { /* ... */ });

    // --- Tab Switching ---
    tabButtons.forEach(button => { button.addEventListener('click', () => { /* ... (keep unchanged, requestSettings is still good) ... */ }); });

    // --- Settings Handling ---
    function requestSettings() { if (socket && socket.readyState === WebSocket.OPEN) { console.log("Requesting settings..."); addLogMessage('DEBUG', 'Requesting settings...'); socket.send(JSON.stringify({ type: "request_settings" })); } else { showSettingsStatus("Cannot load settings: WS closed.", true); updateAuthUI('twitch', null); /* Clear auth UI if WS down */ } }

    function populateSettingsForm(settings) {
        console.log("Populating settings:", settings);
        addLogMessage('DEBUG', 'Populating non-auth settings form fields.');

        // Populate non-auth forms (YouTube Manual, X Manual, App Config)
        manualSettingsForms.forEach(form => {
            for (const element of form.elements) {
                if (element.name && settings.hasOwnProperty(element.name)) {
                     // Only populate non-token fields here
                     if (element.type !== 'password' && !element.name.includes('_token') && !element.name.includes('_secret')) {
                        element.value = settings[element.name] || '';
                    } else if (element.type === 'password') {
                        // Standard password handling (masked if value exists)
                        element.placeholder = settings[element.name] ? '******** (Saved)' : 'Enter Secret/Token';
                        element.value = '';
                    }
                } else if (element.type === 'password' && element.name) {
                     element.placeholder = 'Enter Secret/Token'; // Default placeholder
                     element.value = '';
                }
            }
        });
        showSettingsStatus("Settings loaded.", false, 3000); // Short confirmation
    }

    async function saveSettings(formEl) {
        const formData = new FormData(formEl);
        const dataToSend = {};
        let hasChanges = false;

        // Check against currentSettings state to see if values *actually* changed
        formData.forEach((value, key) => {
            const inputEl = formEl.elements[key];
            if (!inputEl) return;
            const isSecret = (inputEl.type === 'password');
            const existingValue = currentSettings[key];

            // Determine if we should send the value:
            // 1. It's a non-secret field and its value is different from the currently stored setting.
            // 2. It IS a secret field, and the user has typed something into it (value is not empty).
            let shouldSend = false;
            if (!isSecret) {
                if (value !== (existingValue || '')) { // Compare with existing or empty string
                     shouldSend = true;
                 }
            } else { // Is a secret field
                if (value !== '') { // Only send if user typed something new
                     shouldSend = true;
                 }
            }

            if (shouldSend) {
                 dataToSend[key] = value;
                 hasChanges = true;
            }
        });

        if (!hasChanges) {
             showSettingsStatus("No actual changes detected to save.", false);
             return;
        }

        const formId = formEl.id.split('-')[0]; // e.g., 'youtube', 'x', 'app'
        console.log(`Saving ${formId} settings:`, Object.keys(dataToSend));
        showSettingsStatus(`Saving ${formId} settings...`, false, 0);

        try {
            const response = await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataToSend) });
            const result = await response.json();
            if (response.ok) {
                showSettingsStatus(result.message || "Settings saved!", false);
                // Request settings again to update UI and currentSettings state
                requestSettings();
            } else { showSettingsStatus(`Error: ${result.detail || response.statusText}`, true); }
        } catch (error) { console.error(`Save ${formId} Err:`, error); showSettingsStatus(`Network error: ${error.message}`, true); }
    }

    // Attach submit listener ONLY to non-auth forms
    manualSettingsForms.forEach(form => { form.addEventListener('submit', (e) => { e.preventDefault(); saveSettings(e.target); }); });

    // --- Service Control ---
    controlButtons.forEach(button => { button.addEventListener('click', async (e) => { /* ... (keep unchanged) ... */ }); });

    // --- Check for Auth Success Flag ---
    function checkAuthSuccess() {
        const urlParams = new URLSearchParams(window.location.search);
        const authSuccess = urlParams.get('auth_success');
        if (authSuccess) {
            showSettingsStatus(`${authSuccess.charAt(0).toUpperCase() + authSuccess.slice(1)} login successful!`, false, 7000);
            addLogMessage('INFO', `${authSuccess.toUpperCase()} OAuth successful.`);
            // Clean the URL (optional)
            window.history.replaceState({}, document.title, window.location.pathname); // Remove query params
            // Switch to settings tab automatically?
            const settingsTabButton = document.querySelector('button[data-tab="settings"]');
            if(settingsTabButton) settingsTabButton.click();
        }
    }

    // --- Initial Load ---
    addLogMessage('INFO', 'Dashboard UI Initialized.');
    checkAuthSuccess(); // Check immediately on load
    connectWebSocket(); // Start WebSocket connection

}); // End DOMContentLoaded
// --- File: static/main.js --- END ---