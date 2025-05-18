document.addEventListener('DOMContentLoaded', () => {
    console.log('Popup initialized');
    const setupModeCheckbox = document.getElementById('setupMode');
    const testButton = document.getElementById('testButton');
    const statusDiv = document.getElementById('status');
    const modeStatusDiv = document.getElementById('modeStatus');
    let ws = null;

    // Initialize WebSocket for debug logging
    function initDebugWebSocket() {
        ws = new WebSocket('ws://localhost:8000/ws/debug');
        ws.onopen = () => {
            console.log('Debug WebSocket connected');
            sendDebugLog('Popup WebSocket connected');
        };
        ws.onclose = () => {
            console.log('Debug WebSocket disconnected, retrying in 5s');
            setTimeout(initDebugWebSocket, 5000);
        };
        ws.onerror = (error) => {
            console.error('Debug WebSocket error:', error);
        };
    }
    initDebugWebSocket();

    function sendDebugLog(message) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'debug', message }));
        }
    }

    // Load saved settings
    chrome.storage.local.get(['setupMode'], (data) => {
        const isSetupMode = data.setupMode || false;
        setupModeCheckbox.checked = isSetupMode;
        updateModeStatus(isSetupMode);
        console.log('Loaded settings:', data);
        sendDebugLog(`Popup loaded settings: ${JSON.stringify(data)}`);
        updateConnectionStatus();
    });

    // Update setup mode status
    function updateModeStatus(isOn) {
        modeStatusDiv.textContent = `Setup Mode: ${isOn ? 'On' : 'Off'}`;
        modeStatusDiv.style.color = isOn ? 'green' : 'gray';
        sendDebugLog(`Setup mode updated: ${isOn ? 'On' : 'Off'}`);
    }

    // Update connection status
    function updateConnectionStatus() {
        chrome.runtime.sendMessage({ type: 'query_status' }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Status query error:', chrome.runtime.lastError);
                statusDiv.textContent = 'Error: Start the FoSBot app first!';
                statusDiv.className = 'error';
                sendDebugLog(`Status query error: ${chrome.runtime.lastError.message}`);
                setTimeout(updateConnectionStatus, 5000);
                return;
            }
            if (response && response.wsConnected) {
                statusDiv.textContent = 'Connected to FoSBot app';
                statusDiv.className = 'success';
                sendDebugLog('Connected to FoSBot app');
            } else {
                statusDiv.textContent = 'Start the FoSBot app and Whatnot service';
                statusDiv.className = 'error';
                sendDebugLog('Not connected to FoSBot app or Whatnot service');
            }
            setTimeout(updateConnectionStatus, 5000);
        });
    }

    // Toggle setup mode
    setupModeCheckbox.addEventListener('change', () => {
        const isChecked = setupModeCheckbox.checked;
        console.log('Setup Mode toggled:', isChecked);
        sendDebugLog(`Setup Mode toggled: ${isChecked}`);
        chrome.storage.local.set({ setupMode: isChecked }, () => {
            updateModeStatus(isChecked);
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (tabs[0] && tabs[0].url.match(/^https:\/\/.*\.whatnot\.com\/.*/)) {
                    console.log('Sending toggle_setup_mode to tab:', tabs[0].id);
                    sendDebugLog(`Sending toggle_setup_mode to tab ${tabs[0].id}`);
                    chrome.tabs.sendMessage(tabs[0].id, {
                        type: 'toggle_setup_mode',
                        payload: { setupMode: isChecked }
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('Message error:', chrome.runtime.lastError);
                            statusDiv.textContent = 'Error: Ensure you are on a Whatnot stream page';
                            statusDiv.className = 'error';
                            sendDebugLog(`Message error: ${chrome.runtime.lastError.message}`);
                            setupModeCheckbox.checked = false;
                            chrome.storage.local.set({ setupMode: false });
                        } else {
                            console.log('Toggle setup response:', response);
                            sendDebugLog(`Toggle setup response: ${JSON.stringify(response)}`);
                        }
                    });
                } else {
                    statusDiv.textContent = 'Error: Open a Whatnot stream page first';
                    statusDiv.className = 'error';
                    setupModeCheckbox.checked = false;
                    chrome.storage.local.set({ setupMode: false });
                    sendDebugLog('Setup mode disabled: Not on a Whatnot page');
                }
            });
        });
    });

    // Test button
    testButton.addEventListener('click', () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].url.match(/^https:\/\/.*\.whatnot\.com\/.*/)) {
                console.log('Sending test_settings to tab:', tabs[0].id);
                sendDebugLog(`Sending test_settings to tab ${tabs[0].id}`);
                chrome.tabs.sendMessage(tabs[0].id, { type: 'test_settings' }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error('Test error:', chrome.runtime.lastError);
                        statusDiv.textContent = 'Error: Reload the Whatnot page';
                        statusDiv.className = 'error';
                        sendDebugLog(`Test error: ${chrome.runtime.lastError.message}`);
                        return;
                    }
                    if (response && response.success) {
                        statusDiv.textContent = 'Setup works! Chat is ready';
                        statusDiv.className = 'success';
                        sendDebugLog('Setup test successful');
                    } else {
                        statusDiv.textContent = 'Setup failed. Try setting up again or watch the video';
                        statusDiv.className = 'error';
                        sendDebugLog('Setup test failed');
                    }
                });
            } else {
                statusDiv.textContent = 'Error: Open a Whatnot stream page first';
                statusDiv.className = 'error';
                sendDebugLog('Test settings failed: Not on a Whatnot page');
            }
        });
    });
});