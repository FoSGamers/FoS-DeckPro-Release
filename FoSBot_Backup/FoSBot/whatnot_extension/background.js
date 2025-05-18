let ws = null;
let debugWs = null;

function connectWebSocket() {
    console.log('Attempting WebSocket connection to FoSBot');
    ws = new WebSocket('ws://localhost:8000/ws/whatnot');
    ws.onopen = () => {
        console.log('WebSocket connected to FoSBot');
        sendDebugLog('Background WebSocket connected to FoSBot');
        ws.send(JSON.stringify({ type: 'ping' }));
    };
    ws.onclose = () => {
        console.log('WebSocket disconnected, retrying in 5 seconds');
        sendDebugLog('Background WebSocket disconnected, retrying in 5s');
        setTimeout(connectWebSocket, 5000);
    };
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        sendDebugLog(`Background WebSocket error: ${error}`);
    };
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);
            sendDebugLog(`Background received message: ${JSON.stringify(data)}`);
            if (data.type === 'pong') {
                console.log('Received pong from FoSBot');
                sendDebugLog('Background received pong from FoSBot');
            }
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
            sendDebugLog(`Background error parsing WebSocket message: ${e.message}`);
        }
    };
}

function initDebugWebSocket() {
    debugWs = new WebSocket('ws://localhost:8000/ws/debug');
    debugWs.onopen = () => {
        console.log('Background Debug WebSocket connected');
        sendDebugLog('Background Debug WebSocket connected');
    };
    debugWs.onclose = () => {
        console.log('Background Debug WebSocket disconnected, retrying in 5s');
        setTimeout(initDebugWebSocket, 5000);
    };
    debugWs.onerror = (error) => {
        console.error('Background Debug WebSocket error:', error);
    };
}
initDebugWebSocket();

function sendDebugLog(message) {
    if (debugWs && debugWs.readyState === WebSocket.OPEN) {
        debugWs.send(JSON.stringify({ type: 'debug', message }));
    }
}

connectWebSocket();

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request);
    sendDebugLog(`Background received message: ${JSON.stringify(request)}`);
    if (request.type === 'chat_message' && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'chat_message',
            payload: request.payload
        }));
        sendResponse({ success: true });
        sendDebugLog('Background sent chat message to FoSBot');
    } else if (request.type === 'query_status') {
        sendResponse({
            wsConnected: ws && ws.readyState === WebSocket.OPEN,
            selectorsValid: true // Handled by content.js
        });
        sendDebugLog(`Background query status: wsConnected=${ws && ws.readyState === WebSocket.OPEN}`);
    } else {
        sendResponse({ success: false });
        sendDebugLog('Background message not handled');
    }
    return true; // Keep channel open
});