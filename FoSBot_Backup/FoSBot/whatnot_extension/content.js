console.log('Content script initialized');

(function () {
    let chatInputSelector = '';
    let chatContainerSelector = '';
    let messageItemSelector = '';
    let usernameSelector = '';
    let messageTextSelector = '';
    let ws = null;
    let debugWs = null;
    let controlPanel = null;
    let currentSelectorType = null;
    let selectorIndex = 0;
    let handleMouseMove = null;
    let handleClick = null;

    const selectorTypes = [
        { id: 'chatContainer', prompt: 'where all chat messages show up' },
        { id: 'message', prompt: 'one single chat message' },
        { id: 'user', prompt: 'a username in a chat message' },
        { id: 'text', prompt: 'the text of a chat message' }
    ];
    const selectors = {
        chatContainer: '',
        message: '',
        user: '',
        text: ''
    };

    // Initialize debug WebSocket
    function initDebugWebSocket() {
        debugWs = new WebSocket('ws://localhost:8000/ws/debug');
        debugWs.onopen = () => {
            console.log('Debug WebSocket connected');
            sendDebugLog('Content script WebSocket connected');
        };
        debugWs.onclose = () => {
            console.log('Debug WebSocket disconnected, retrying in 5s');
            setTimeout(initDebugWebSocket, 5000);
        };
        debugWs.onerror = (error) => {
            console.error('Debug WebSocket error:', error);
        };
    }
    initDebugWebSocket();

    function sendDebugLog(message) {
        if (debugWs && debugWs.readyState === WebSocket.OPEN) {
            debugWs.send(JSON.stringify({ type: 'debug', message }));
        }
    }

    // Load saved selectors
    chrome.storage.local.get(['chatInputSelector', 'chatContainerSelector', 'messageSelector', 'userSelector', 'textSelector'], (result) => {
        chatInputSelector = result.chatInputSelector || '';
        chatContainerSelector = result.chatContainerSelector || '';
        messageItemSelector = result.messageSelector || '';
        usernameSelector = result.userSelector || '';
        messageTextSelector = result.textSelector || '';
        console.log('Loaded selectors:', result);
        sendDebugLog(`Loaded selectors: ${JSON.stringify(result)}`);
        initializeWebSocket();
        setupChatInput();
        if (chatContainerSelector) {
            setupMutationObserver();
        }
    });

    // Initialize WebSocket
    function initializeWebSocket() {
        if (ws) ws.close();
        ws = new WebSocket('ws://localhost:8000/ws/whatnot');
        ws.onopen = () => {
            console.log('Whatnot WebSocket connected');
            sendDebugLog('Whatnot WebSocket connected');
            queryStatus();
        };
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data);
                sendDebugLog(`WebSocket message received: ${JSON.stringify(data)}`);
                if (data.type === 'pong') {
                    console.log('Received pong from FoSBot');
                    sendDebugLog('Received pong from FoSBot');
                } else if (data.type === 'sendMessage') {
                    handlePostToWhatnot(data.data);
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
                sendDebugLog(`Error parsing WebSocket message: ${e.message}`);
            }
        };
        ws.onclose = () => {
            console.log('Whatnot WebSocket disconnected');
            sendDebugLog('Whatnot WebSocket disconnected');
            setTimeout(initializeWebSocket, 2000);
        };
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            sendDebugLog(`WebSocket error: ${error}`);
        };
    }

    // Setup chat input
    function setupChatInput() {
        if (!chatInputSelector) {
            sendDebugLog('No chat input selector configured');
            return;
        }
        const chatInput = document.querySelector(chatInputSelector);
        if (chatInput) {
            chatInput.addEventListener('focus', () => {
                console.log('Chat input area selected');
                sendDebugLog('Chat input area selected');
                sendMessageToFoSBot({ type: 'inputSelected', data: 'Chat input focused' });
            });
        } else {
            console.warn('Chat input selector not found:', chatInputSelector);
            sendDebugLog(`Chat input selector not found: ${chatInputSelector}`);
        }
    }

    // Setup MutationObserver
    function setupMutationObserver() {
        if (!chatContainerSelector) {
            sendDebugLog('No chat container selector for MutationObserver');
            return;
        }
        const chatContainer = document.querySelector(chatContainerSelector);
        if (chatContainer) {
            const observer = new MutationObserver(captureChatMessages);
            observer.observe(chatContainer, { childList: true, subtree: true });
            console.log('MutationObserver set up for:', chatContainerSelector);
            sendDebugLog(`MutationObserver set up for: ${chatContainerSelector}`);
        } else {
            console.warn('Chat container not found for MutationObserver:', chatContainerSelector);
            sendDebugLog(`Chat container not found for MutationObserver: ${chatContainerSelector}`);
        }
    }

    // Capture chat messages
    function captureChatMessages() {
        if (!chatContainerSelector || !messageItemSelector || !usernameSelector || !messageTextSelector) {
            console.warn('Missing selectors:', {
                chatContainer: chatContainerSelector,
                message: messageItemSelector,
                user: usernameSelector,
                text: messageTextSelector
            });
            sendDebugLog(`Missing selectors: chatContainer=${chatContainerSelector}, message=${messageItemSelector}, user=${usernameSelector}, text=${messageTextSelector}`);
            return false;
        }
        const chatContainer = document.querySelector(chatContainerSelector);
        if (!chatContainer) {
            console.warn('Chat container not found:', chatContainerSelector);
            sendDebugLog(`Chat container not found: ${chatContainerSelector}`);
            return false;
        }
        const messages = Array.from(chatContainer.querySelectorAll(messageItemSelector)).map(item => ({
            username: item.querySelector(usernameSelector)?.textContent.trim() || 'Unknown',
            message: item.querySelector(messageTextSelector)?.textContent.trim() || ''
        }));
        if (messages.length > 0) {
            console.log('Captured Whatnot messages:', messages);
            sendDebugLog(`Captured Whatnot messages: ${JSON.stringify(messages)}`);
            sendMessageToFoSBot({ type: 'chat_message', payload: messages, platform: 'whatnot' });
            return true;
        }
        return false;
    }

    // Handle message submission
    function handlePostToWhatnot(message) {
        if (!chatInputSelector) {
            console.warn('No chat input selector');
            sendDebugLog('No chat input selector for posting message');
            return;
        }
        const chatInput = document.querySelector(chatInputSelector);
        const submitButton = document.querySelector('button[type="submit"], [data-testid="send-message"]');
        if (chatInput && submitButton) {
            chatInput.value = message;
            submitButton.click();
            console.log('Message submitted to Whatnot:', message);
            sendDebugLog(`Message submitted to Whatnot: ${message}`);
            sendMessageToFoSBot({ type: 'messageSubmitted', data: message, platform: 'whatnot' });
        } else {
            console.warn('Chat input or submit button not found:', { chatInput, submitButton });
            sendDebugLog(`Chat input or submit button not found: input=${chatInput}, button=${submitButton}`);
        }
    }

    // Send message to FoSBot
    function sendMessageToFoSBot(message) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
            console.log('Sent message to FoSBot:', message);
            sendDebugLog(`Sent message to FoSBot: ${JSON.stringify(message)}`);
        } else {
            console.warn('WebSocket not connected:', message);
            sendDebugLog(`WebSocket not connected for message: ${JSON.stringify(message)}`);
        }
    }

    // Query status
    function queryStatus() {
        sendMessageToFoSBot({ type: 'queryStatus' });
    }

    // Create control panel
    function createControlPanel() {
        if (controlPanel) controlPanel.remove();
        if (selectorIndex >= selectorTypes.length || selectorIndex < 0) {
            console.error('Invalid selector index:', selectorIndex);
            sendDebugLog(`Invalid selector index: ${selectorIndex}`);
            selectorIndex = 0;
        }
        controlPanel = document.createElement('div');
        controlPanel.style.cssText = `
            position: fixed; top: 10px; right: 10px; width: 300px; background: white;
            border: 1px solid #ccc; padding: 15px; z-index: 100000; box-shadow: 0 0 10px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif; font-size: 14px;
        `;
        controlPanel.innerHTML = `
            <h3 style="margin: 0 0 10px;">Set Up Whatnot Chat</h3>
            <p id="instruction">Click ${selectorTypes[selectorIndex].prompt}</p>
            <div id="status" style="color: green; margin-bottom: 10px;"></div>
            <div id="error" style="color: red; margin-bottom: 10px;"></div>
            <button id="nextButton" style="padding: 8px; background: #007bff; color: white; border: none; cursor: pointer;">Next</button>
            <button id="doneButton" style="padding: 8px; margin-left: 10px; background: #28a745; color: white; border: none; cursor: pointer;">Done</button>
            <button id="cancelButton" style="padding: 8px; margin-left: 10px; background: #dc3545; color: white; border: none; cursor: pointer;">Cancel</button>
        `;
        document.body.appendChild(controlPanel);
        console.log('Control panel created for:', selectorTypes[selectorIndex].id);
        sendDebugLog(`Control panel created for: ${selectorTypes[selectorIndex].id}`);

        document.getElementById('nextButton').addEventListener('click', () => {
            if (selectors[selectorTypes[selectorIndex].id]) {
                selectorIndex++;
                if (selectorIndex < selectorTypes.length) {
                    currentSelectorType = selectorTypes[selectorIndex].id;
                    document.getElementById('instruction').textContent = `Click ${selectorTypes[selectorIndex].prompt}`;
                    document.getElementById('status').textContent = '';
                    sendDebugLog(`Advanced to next selector: ${selectorTypes[selectorIndex].id}`);
                } else {
                    document.getElementById('instruction').textContent = 'All set! Click Done to finish';
                    document.getElementById('nextButton').disabled = true;
                    sendDebugLog('All selectors set, prompting to finish');
                }
            } else {
                document.getElementById('error').textContent = 'Please click an element first';
                sendDebugLog('Next button clicked but no element selected');
            }
        });

        document.getElementById('doneButton').addEventListener('click', () => {
            saveSelectors();
            cleanup();
            sendDebugLog('Done button clicked, selectors saved');
        });

        document.getElementById('cancelButton').addEventListener('click', () => {
            cleanup();
            sendDebugLog('Cancel button clicked, setup aborted');
        });
    }

    function saveSelectors() {
        const settings = {
            chatContainerSelector: selectors.chatContainer,
            messageSelector: selectors.message,
            userSelector: selectors.user,
            textSelector: selectors.text,
            setupMode: false
        };
        chrome.storage.local.set(settings, () => {
            console.log('Selectors saved:', settings);
            sendDebugLog(`Selectors saved: ${JSON.stringify(settings)}`);
            chatContainerSelector = settings.chatContainerSelector;
            messageItemSelector = settings.messageSelector;
            usernameSelector = settings.userSelector;
            messageTextSelector = settings.textSelector;
            setupMutationObserver();
            chrome.runtime.sendMessage({ type: 'update_settings', payload: settings });
        });
    }

    function cleanup() {
        if (controlPanel) controlPanel.remove();
        document.querySelectorAll('.fosbot-overlay, .fosbot-highlight').forEach(el => el.remove());
        if (handleMouseMove) document.removeEventListener('mousemove', handleMouseMove);
        if (handleClick) document.removeEventListener('click', handleClick);
        controlPanel = null;
        currentSelectorType = null;
        selectorIndex = 0;
        handleMouseMove = null;
        handleClick = null;
        chrome.storage.local.set({ setupMode: false });
        console.log('Selector cleanup completed');
        sendDebugLog('Selector cleanup completed');
    }

    function startSetup() {
        console.log('Starting setup');
        sendDebugLog('Starting setup process');
        document.querySelectorAll('.fosbot-overlay, .fosbot-highlight').forEach(el => el.remove());

        const overlay = document.createElement('div');
        overlay.className = 'fosbot-overlay';
        overlay.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:99998;';
        document.body.appendChild(overlay);
        console.log('Overlay added');
        sendDebugLog('Overlay added');

        const highlight = document.createElement('div');
        highlight.className = 'fosbot-highlight';
        highlight.style.cssText = 'position:absolute; border:2px dashed #fff; z-index:99999; pointer-events:none;';
        document.body.appendChild(highlight);
        console.log('Highlight added');
        sendDebugLog('Highlight added');

        const getElementAtPoint = (x, y) => {
            overlay.style.pointerEvents = 'none';
            const el = document.elementFromPoint(x, y);
            overlay.style.pointerEvents = 'auto';
            return el;
        };

        handleMouseMove = (e) => {
            const el = getElementAtPoint(e.clientX, e.clientY);
            if (el) {
                console.log('Mouse over element:', el.tagName, el.className);
                sendDebugLog(`Mouse over element: ${el.tagName}, class=${el.className}`);
                const rect = el.getBoundingClientRect();
                highlight.style.left = `${rect.left}px`;
                highlight.style.top = `${rect.top}px`;
                highlight.style.width = `${rect.width}px`;
                highlight.style.height = `${rect.height}px`;
            }
        };

        handleClick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            const el = getElementAtPoint(e.clientX, e.clientY);
            if (el) {
                const selector = generateRobustSelector(el);
                console.log('Element clicked, selector:', selector);
                sendDebugLog(`Element clicked, selector: ${selector}`);
                selectors[currentSelectorType] = selector;
                document.getElementById('status').textContent = `Set: ${selectorTypes[selectorIndex].prompt}`;
                document.getElementById('error').textContent = '';
            }
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('click', handleClick);
    }

    // Selector generation
    function generateRobustSelector(el) {
        if (el.id) return `#${el.id}`;
        let path = [];
        let current = el;
        while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.body) {
            let selector = current.nodeName.toLowerCase();
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/).join('.');
                if (classes) selector += `.${classes}`;
            }
            path.unshift(selector);
            current = current.parentNode;
        }
        return path.join(' > ');
    }

    // Handle messages
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        console.log('Content script received message:', message);
        sendDebugLog(`Content script received message: ${JSON.stringify(message)}`);
        if (message.type === 'toggle_setup_mode') {
            console.log('Toggle setup mode:', message.payload.setupMode);
            sendDebugLog(`Toggle setup mode: ${message.payload.setupMode}`);
            if (message.payload.setupMode) {
                selectorIndex = 0;
                currentSelectorType = selectorTypes[0].id;
                createControlPanel();
                startSetup();
            } else {
                cleanup();
            }
            sendResponse({ success: true });
        } else if (message.type === 'query_status') {
            sendResponse({
                wsConnected: ws && ws.readyState === WebSocket.OPEN,
                selectorsValid: !!chatContainerSelector && !!messageItemSelector && !!usernameSelector && !!messageTextSelector
            });
            sendDebugLog(`Query status response: wsConnected=${ws && ws.readyState === WebSocket.OPEN}, selectorsValid=${!!chatContainerSelector && !!messageItemSelector && !!usernameSelector && !!messageTextSelector}`);
        } else if (message.type === 'update_settings') {
            console.log('Updating selectors:', message.payload);
            sendDebugLog(`Updating selectors: ${JSON.stringify(message.payload)}`);
            chatInputSelector = message.payload.chatInputSelector || '';
            chatContainerSelector = message.payload.chatContainerSelector || '';
            messageItemSelector = message.payload.messageSelector || '';
            usernameSelector = message.payload.userSelector || '';
            messageTextSelector = message.payload.textSelector || '';
            setupChatInput();
            if (chatContainerSelector) {
                setupMutationObserver();
            }
            captureChatMessages();
            sendResponse({ success: true });
        } else if (message.type === 'test_settings') {
            const success = captureChatMessages();
            sendResponse({ success });
            sendDebugLog(`Test settings result: ${success}`);
        }
        return true; // Keep channel open for async response
    });

    // Initialize on page load
    window.addEventListener('load', () => {
        console.log('Whatnot Chat Consolidator loaded');
        sendDebugLog('Whatnot Chat Consolidator loaded');
        setInterval(captureChatMessages, 2000);
    });
})();