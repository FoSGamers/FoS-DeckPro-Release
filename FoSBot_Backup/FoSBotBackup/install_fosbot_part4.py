
                     // Prevent default behavior and stop propagation for clicks outside panel
                     e.preventDefault();
                     e.stopPropagation();

                     // Hide highlight briefly
                     if(highlightElement) highlightElement.style.display = 'none';
                     const targetElement = document.elementFromPoint(e.clientX, e.clientY);
                     if(highlightElement) highlightElement.style.display = 'block';

                     if (targetElement && targetElement !== controlPanel && !controlPanel.contains(targetElement)) {
                         const selector = generateRobustSelector(targetElement);
                         sendDebugLog(`Element clicked: ${targetElement.tagName}, Generated Selector: ${selector}`);

                         if(selector){
                              const currentTypeId = selectorTypes[selectorIndex].id;
                              tempSelectors[currentTypeId] = selector;
                              controlPanel.querySelector('#fosbot-status').textContent = `Set: ${selectorTypes[selectorIndex].prompt}`;
                              controlPanel.querySelector('#fosbot-status').style.color = 'green';
                              controlPanel.querySelector('#fosbot-selector-preview').textContent = `Selector: ${selector}`;
                              controlPanel.querySelector('#fosbot-nextButton').disabled = false;
                              // If on last step, enable Done button immediately
                              if (selectorIndex === selectorTypes.length - 1) {
                                  controlPanel.querySelector('#fosbot-doneButton').disabled = false;
                              }
                              updateControlPanelUI(); // Refresh button states
                         } else {
                              controlPanel.querySelector('#fosbot-status').textContent = `Could not generate selector for clicked element. Try a different part.`;
                              controlPanel.querySelector('#fosbot-status').style.color = 'red';
                              controlPanel.querySelector('#fosbot-nextButton').disabled = true;
                         }
                     }
                 };

                 function handleNextButtonClick() {
                      if (selectorIndex < selectorTypes.length - 1) {
                          selectorIndex++;
                          currentSelectorType = selectorTypes[selectorIndex].id;
                          updateControlPanelUI();
                          sendDebugLog(`Advanced to next selector: ${currentSelectorType}`);
                      } else {
                           // Should ideally show Done button now if all selectors are filled
                           updateControlPanelUI(); // Refresh to show Done if applicable
                      }
                 }

                 function saveFinalSelectors() {
                     const settingsToSave = {
                         chatContainerSelector: tempSelectors.chatContainer || null,
                         messageSelector: tempSelectors.message || null,
                         userSelector: tempSelectors.user || null,
                         textSelector: tempSelectors.text || null,
                         chatInputSelector: tempSelectors.chatInput || null, // Save input selector
                         setupMode: false // Ensure setup mode is off after saving
                     };

                     // Basic validation - ensure read selectors are present
                     if (!settingsToSave.chatContainerSelector || !settingsToSave.messageSelector || !settingsToSave.userSelector || !settingsToSave.textSelector) {
                          alert("Setup Error: Core chat reading selectors are missing. Please restart setup.");
                          sendDebugLog("Setup save failed: Missing core read selectors.");
                          return; // Don't save incomplete core set
                     }

                     chrome.storage.local.set(settingsToSave, () => {
                         console.log('[FoSBot CS] Final selectors saved:', settingsToSave);
                         sendDebugLog(`Final selectors saved: ${JSON.stringify(settingsToSave)}`);
                         // Update local settings state immediately
                         settings = { ...settings, ...settingsToSave };
                         // Restart observer with new settings
                         setupMutationObserver();
                         // Notify background/popup if needed
                         // sendMessageToBackground({ type: 'update_settings', payload: settingsToSave });
                         alert("FoSBot selectors saved successfully!");
                     });
                 }


                 // --- Selector Generation (Improved) ---
                 function generateRobustSelector(el) {
                     if (!el || typeof el.getAttribute !== 'function') return null;
                     // Prioritize data-testid or specific data attributes if available
                     for (const attr of ['data-testid', 'data-test-id', 'data-cy']) {
                          const value = el.getAttribute(attr);
                          if (value) {
                               const selector = `${el.tagName.toLowerCase()}[${attr}="${CSS.escape(value)}"]`;
                               try { if (document.querySelectorAll(selector).length === 1) return selector; } catch (e) {}
                          }
                     }
                     // Try ID if unique
                     if (el.id) {
                         const idSelector = `#${CSS.escape(el.id)}`;
                          try { if (document.querySelectorAll(idSelector).length === 1) return idSelector; } catch (e) {}
                     }
                     // Try combination of tag + significant classes
                     if (el.classList.length > 0) {
                          const significantClasses = Array.from(el.classList)
                               .filter(c => !/^(?:js-|is-|has-|active|focus|hover|animating|ng-|css-)/.test(c) && !/\d/.test(c) && c.length > 2) // Filter common/dynamic classes
                               .map(c => CSS.escape(c))
                               .sort(); // Consistent order
                          if (significantClasses.length > 0) {
                               const classSelector = `${el.tagName.toLowerCase()}.${significantClasses.join('.')}`;
                               try { if (document.querySelectorAll(classSelector).length === 1) return classSelector; } catch (e) {}
                          }
                     }
                     // Fallback to simple tag name (least reliable) - maybe add nth-child? Too complex for now.
                     // console.warn("Falling back to simple tag name selector for element:", el);
                     // return el.tagName.toLowerCase();
                     // Fallback: Construct path if simple methods fail
                     let path = [];
                     let current = el;
                     while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.body) {
                         let selector = current.nodeName.toLowerCase();
                         const parent = current.parentNode;
                         if (parent) {
                              const siblings = Array.from(parent.children).filter(child => child.nodeName === current.nodeName);
                              if (siblings.length > 1) {
                                   const index = siblings.indexOf(current) + 1;
                                   selector += `:nth-of-type(${index})`;
                              }
                         }
                         path.unshift(selector);
                         current = parent;
                     }
                     return path.join(' > ');
                 }


                 // --- Message Handling from Background/Popup ---
                 chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
                     sendDebugLog(`Content script received message: ${JSON.stringify(message)}`);
                     if (message.type === 'toggle_setup_mode') {
                         if (message.payload.setupMode) {
                             startSetupMode();
                         } else {
                             stopSetupMode(false); // Stop without saving on toggle off
                         }
                         sendResponse({ success: true });
                     } else if (message.type === 'test_settings') {
                         const validRead = areReadSelectorsValid();
                         const foundMessages = validRead ? captureChatMessages() : false; // Try capturing
                         sendResponse({ success: validRead && foundMessages, messagesFound: foundMessages ? "Some" : 0, error: validRead ? null : "Read selectors invalid" });
                     } else if (message.type === 'send_message'){
                          // Handle request from background to send message
                          handlePostToWhatnot(message.payload.text);
                          sendResponse({success: true}); // Acknowledge receipt
                     }
                     return true; // Indicate potential async response
                 });

                 // --- Initial Load ---
                 loadSelectors(); // Load settings when script injected
                 console.log('[FoSBot CS] Content script loaded and listener set up.');
                 sendDebugLog('Content script loaded.');

             // --- End IIFE ---
             })();
             """,

                     # === data/ Files (Empty Placeholders) ===
                     "data/settings.json": r"""{}""",
                     "data/checkins.json": r"""{}""",
                     "data/counters.json": r"""{}""",
                     "data/commands.json": r"""{}""",
                     # Removed tokens.json and oauth_states.json as they seem unused/superseded

                     # === static/ Files ===
                     "static/index.html": r"""<!-- Generated by install_fosbot.py -->
             <!DOCTYPE html>
             <html lang="en">
             <head>
                 <meta charset="UTF-8">
                 <meta name="viewport" content="width=device-width, initial-scale=1.0">
                 <title>FoSBot Dashboard</title>
                 <style>
                     /* Basic Reset & Font */
                     *, *::before, *::after { box-sizing: border-box; }
                     body {
                         font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
                         margin: 0; display: flex; flex-direction: column; height: 100vh;
                         background-color: #f0f2f5; font-size: 14px; color: #333;
                     }
                     button { cursor: pointer; padding: 8px 15px; border: none; border-radius: 4px; font-weight: 600; transition: background-color .2s ease; font-size: 13px; line-height: 1.5; }
                     button:disabled { cursor: not-allowed; opacity: 0.6; }
                     input[type=text], input[type=password], input[type=url], select {
                         padding: 9px 12px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;
                         width: 100%; margin-bottom: 10px; background-color: #fff;
                         box-shadow: inset 0 1px 2px rgba(0,0,0,.075); box-sizing: border-box; /* Ensure padding doesn't break width */
                     }
                     label { display: block; margin-bottom: 4px; font-weight: 600; font-size: .85em; color: #555; }
                     a { color: #007bff; text-decoration: none; }
                     a:hover { text-decoration: underline; }

                     /* Header */
                     #header { background-color: #343a40; color: #f8f9fa; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,.15); position: sticky; top: 0; z-index: 100;}
                     #header h1 { margin: 0; font-size: 1.5em; font-weight: 600; }
                     #status-indicators { display: flex; flex-wrap: wrap; gap: 10px 15px; font-size: .8em; }
                     #status-indicators span { display: flex; align-items: center; background-color: rgba(255,255,255,0.1); padding: 3px 8px; border-radius: 10px; white-space: nowrap;}
                     .status-light { width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; border: 1px solid rgba(0,0,0,.2); flex-shrink: 0;}
                     .status-text { color: #adb5bd; }
                     /* Status Colors */
                     .status-disconnected, .status-disabled, .status-stopped, .status-logged_out { background-color: #6c757d; } /* Grey */
                     .status-connected { background-color: #28a745; box-shadow: 0 0 5px #28a745; } /* Green */
                     .status-connecting { background-color: #ffc107; animation: pulseConnect 1.5s infinite ease-in-out; } /* Yellow */
                     .status-error, .status-crashed, .status-auth_error { background-color: #dc3545; animation: pulseError 1s infinite ease-in-out; } /* Red */
                     .status-disconnecting { background-color: #fd7e14; } /* Orange */
                     .status-waiting { background-color: #0dcaf0; } /* Teal/Info */

                     /* Keyframes */
                     @keyframes pulseConnect { 0%, 100% { opacity: .6; } 50% { opacity: 1; } }
                     @keyframes pulseError { 0% { transform: scale(.9); box-shadow: 0 0 3px #dc3545;} 50% { transform: scale(1.1); box-shadow: 0 0 8px #dc3545;} 100% { transform: scale(.9); box-shadow: 0 0 3px #dc3545;} }

                     /* Main Layout */
                     #main-container { display: flex; flex: 1; overflow: hidden; flex-direction: column;}
                     #tab-buttons { background-color: #e9ecef; padding: 5px 15px; border-bottom: 1px solid #dee2e6; flex-shrink: 0; }
                     #tab-buttons button { background: none; border: none; padding: 10px 15px; cursor: pointer; font-size: 1em; color: #495057; border-bottom: 3px solid transparent; margin-right: 5px; font-weight: 500; }
                     #tab-buttons button.active { border-bottom-color: #007bff; font-weight: 700; color: #0056b3; }
                     #content-area { flex: 1; display: flex; overflow: hidden; }

                     /* Tab Content Panes */
                     .tab-content { display: none; height: 100%; width: 100%; overflow: hidden; flex-direction: row; } /* Default flex direction row */
                     .tab-content.active { display: flex; }

                     /* Chat Area (within content-area) */
                     #chat-tab-container { flex: 3; display: flex; flex-direction: column; border-right: 1px solid #dee2e6; }
                     #chat-output { flex: 1; overflow-y: scroll; padding: 10px 15px; background-color: #fff; line-height: 1.6; }
                     #chat-output div { margin-bottom: 6px; word-wrap: break-word; padding: 2px 0; font-size: 13px; }
                     #chat-output .platform-tag { font-weight: 700; margin-right: 5px; display: inline-block; min-width: 40px; text-align: right; border-radius: 3px; padding: 0 4px; font-size: 0.8em; vertical-align: baseline; color: white; }
                     .twitch { background-color: #9146ff; } .youtube { background-color: #ff0000; } .x { background-color: #1da1f2; } .whatnot { background-color: #ff6b00; }
                     .dashboard { background-color: #fd7e14; } .system { background-color: #6c757d; font-style: italic; }
                     .chat-user { font-weight: bold; margin: 0 3px; }
                     /* Style bot messages differently */
                     .bot-response .chat-user { font-style: italic; color: #0056b3; } /* Italicize bot name */
                     .streamer-msg { background-color: #fff3cd; padding: 4px 8px; border-left: 3px solid #ffeeba; border-radius: 3px; margin: 2px -8px; }
                     .timestamp { font-size: .75em; color: #6c757d; margin-left: 8px; float: right; opacity: .8; }

                     /* Input Area (within chat-tab-container) */
                     #input-area { display: flex; padding: 12px; border-top: 1px solid #dee2e6; background-color: #e9ecef; align-items: center; flex-shrink: 0;}
                     #streamerInput { flex: 1; margin-right: 8px; }
                     #sendButton { background-color: #28a745; color: #fff; }
                     #sendButton:hover { background-color: #218838; }
                     #clearButton { background-color: #ffc107; color: #212529; margin-left: 5px; }
                     #clearButton:hover { background-color: #e0a800; }

                     /* Settings & Commands Area (Common styling for tab contents) */
                     #settings-container, #commands-container { padding: 25px; overflow-y: auto; background-color: #fff; flex: 1; }
                     .settings-section, .commands-section { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #e9ecef; }
                     .settings-section:last-of-type, .commands-section:last-of-type { border-bottom: none; }
                     .settings-section h3, .commands-section h3 { margin-top: 0; margin-bottom: 15px; color: #495057; font-size: 1.2em; font-weight: 600; }
                     .settings-section button[type=submit], .commands-section button[type=submit] { background-color: #007bff; color: #fff; margin-top: 15px; min-width: 120px;}
                     .settings-section button[type=submit]:hover, .commands-section button[type=submit]:hover { background-color: #0056b3; }
                     .form-group { margin-bottom: 15px; }
                     #settings-status, #commands-status { font-style: italic; margin-bottom: 15px; padding: 10px; border-radius: 4px; display: none; border: 1px solid transparent; font-size: 0.9em; }
                     #settings-status.success, #commands-status.success { color: #0f5132; background-color: #d1e7dd; border-color: #badbcc; display: block;}
                     #settings-status.error, #commands-status.error { color: #842029; background-color: #f8d7da; border-color: #f5c2c7; display: block;}
                     #settings-status.info, #commands-status.info { color: #0c5460; background-color: #d1ecf1; border-color: #bee5eb; display: block;}

                     /* Service Control Buttons */
                     .control-buttons-container { margin-top: 15px; }
                     .control-buttons-container > div { margin-bottom: 10px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
                     .control-button { margin: 0; padding: 6px 12px; font-size: 12px; flex-shrink: 0; }
                     .control-button[data-command="start"] { background-color: #198754; color: white; } /* Bootstrap green */
                     .control-button[data-command="stop"] { background-color: #dc3545; color: white; } /* Bootstrap red */
                     .control-button[data-command="restart"] { background-color: #ffc107; color: #212529; } /* Bootstrap yellow */

                     /* OAuth Buttons & Status */
                     .auth-area { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
                     .oauth-login-button { background-color: #6441a5; color: white; padding: 8px 12px; font-size: 13px; } /* Default Twitch Purple */
                     .oauth-login-button:hover { background-color: #4a2f7c; }
                     .youtube-login-button { background-color: #ff0000; } .youtube-login-button:hover { background-color: #cc0000; }
                     .x-login-button { background-color: #1da1f2; } .x-login-button:hover { background-color: #0c85d0; }
                     .oauth-logout-button { background-color: #dc3545; color: white; padding: 5px 10px; font-size: 11px; }
                     .auth-status { font-style: italic; color: #6c757d; font-size: 0.9em; }
                     .auth-status strong { color: #198754; font-weight: 600;} /* Bootstrap success green */
                     .auth-status.not-logged-in { color: #dc3545; font-weight: 600;}

                     /* Commands Tab Specifics */
                     #commands-table { width: 100%; border-collapse: collapse; margin-bottom: 20px;}
                     #commands-table th, #commands-table td { border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; vertical-align: top;}
                     #commands-table th { background-color: #f8f9fa; font-weight: 600; }
                     .command-action { cursor: pointer; color: #dc3545; font-size: 0.9em; margin-left: 10px; font-weight: bold; }
                     .command-action:hover { text-decoration: underline; }
                     #add-command-form label { margin-top: 10px; }
                     #add-command-form input { width: 100%; }
                     #csv-upload label { display: block; margin-bottom: 5px; }
                     #csv-upload input[type=file] { display: inline-block; width: auto; margin-right: 10px;}
                     #csv-upload button { display: inline-block; width: auto; vertical-align: middle;}

                     /* Sidebar */
                     #sidebar { flex: 1; padding: 15px; background-color: #f8f9fa; border-left: 1px solid #dee2e6; overflow-y: auto; font-size: 12px; min-width: 280px; max-width: 400px;}
                     #sidebar h3 { margin-top: 0; margin-bottom: 10px; color: #495057; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 1.1em; }
                     #general-status { margin-bottom: 15px; font-weight: 500;}
                     #log-output { height: 300px; overflow-y: scroll; border: 1px solid #e0e0e0; padding: 8px; margin-top: 10px; font-family: Menlo, Monaco, Consolas, 'Courier New', monospace; background-color: #fff; border-radius: 3px; margin-bottom: 15px; line-height: 1.4; font-size: 11px;}
                     .log-CRITICAL, .log-ERROR { color: #dc3545; font-weight: bold; }
                     .log-WARNING { color: #fd7e14; }
                     .log-INFO { color: #0d6efd; }
                     .log-DEBUG { color: #6c757d; }

                     /* Whatnot Guide Modal */
                     .modal { display: none; position: fixed; z-index: 1050; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.5); }
                     .modal-content { background-color: #fefefe; margin: 10% auto; padding: 25px; border: 1px solid #888; width: 80%; max-width: 600px; border-radius: 5px; position: relative; }
                     .modal-close { color: #aaa; float: right; font-size: 28px; font-weight: bold; position: absolute; top: 10px; right: 15px; cursor: pointer; }
                     .modal-close:hover, .modal-close:focus { color: black; text-decoration: none; }
                     .modal-content h3 { margin-top: 0; }
                     .modal-content ol { line-height: 1.6; }
                     .modal-content button { margin-top: 15px; }
                     .download-link { display: inline-block; padding: 10px 15px; background-color: #0d6efd; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; font-size: 14px; }
                     .download-link:hover { background-color: #0b5ed7; }

                 </style>
             </head>
             <body>
                 <div id="header">
                     <h1>FoSBot Dashboard</h1>
                     <div id="status-indicators">
                         <span id="status-ws">WS: <span class="status-light status-disconnected"></span><span class="status-text">Offline</span></span>
                         <span id="status-twitch">Twitch: <span class="status-light status-disabled"></span><span class="status-text">Off</span></span>
                         <span id="status-youtube">YouTube: <span class="status-light status-disabled"></span><span class="status-text">Off</span></span>
                         <span id="status-x">X: <span class="status-light status-disabled"></span><span class="status-text">Off</span></span>
                         <span id="status-whatnot">Whatnot: <span class="status-light status-disabled"></span><span class="status-text">Ext Off</span></span>
                     </div>
                 </div>

                 <div id="tab-buttons">
                     <button class="tab-button active" data-tab="chat">Chat</button>
                     <button class="tab-button" data-tab="commands">Commands</button>
                     <button class="tab-button" data-tab="settings">Settings</button>
                 </div>

                 <div id="content-area">
                     <!-- Chat Tab -->
                     <div id="chat-tab-container" class="tab-content active" data-tab-content="chat">
                         <div id="chat-output">
                             <div>Welcome to FoSBot! Connecting to backend...</div>
                         </div>
                         <div id="input-area">
                             <input type="text" id="streamerInput" placeholder="Type message or command (e.g., !ping) to send...">
                             <button id="sendButton" title="Send message/command to connected platforms">Send</button>
                             <button id="clearButton" title="Clear chat display only">Clear Display</button>
                         </div>
                     </div>

                     <!-- Commands Tab -->
                     <div id="commands-container" class="tab-content" data-tab-content="commands">
                         <div class="commands-section">
                             <h3>Manage Custom Commands</h3>
                             <p>Create simple text commands. Use <code>{user}</code> to mention the user.</p>
                             <div id="commands-status"></div> <!-- Status specific to commands tab -->
                             <table id="commands-table">
                                 <thead>
                                     <tr>
                                         <th>Command (e.g. "lurk")</th>
                                         <th>Response</th>
                                         <th>Actions</th>
                                     </tr>
                                 </thead>
                                 <tbody>
                                     <!-- Rows added dynamically by JS -->
                                     <tr><td colspan="3"><i>Loading commands...</i></td></tr>
                                 </tbody>
                             </table>
                         </div>
                         <div class="commands-section">
                             <h3>Add/Update Command</h3>
                             <form id="add-command-form">
                                 <div class="form-group">
                                     <label for="command-name">Command Name (without prefix)</label>
                                     <input type="text" id="command-name" placeholder="e.g., welcome" required>
                                 </div>
                                 <div class="form-group">
                                     <label for="command-response">Bot Response</label>
                                     <input type="text" id="command-response" placeholder="e.g., Welcome to the stream, {user}!" required>
                                 </div>
                                 <button type="submit">Save Command</button>
                             </form>
                         </div>
                          <div class="commands-section">
                              <h3>Upload Commands via CSV</h3>
                              <div id="csv-upload">
                                  <label for="csv-file">Upload CSV (Format: command,response)</label>
                                  <input type="file" id="csv-file" accept=".csv">
                                  <button id="upload-csv-button">Upload File</button>
                              </div>
                         </div>
                     </div> <!-- End Commands Tab -->

                     <!-- Settings Tab -->
                     <div id="settings-container" class="tab-content" data-tab-content="settings">
                         <h2>Application Settings</h2>
                         <p id="settings-status"></p> <!-- Status specific to settings tab -->

                         <!-- Whatnot Section -->
                         <div class="settings-section">
                             <h3>Whatnot Integration</h3>
                             <div id="whatnot-status-area">
                                 <span class="auth-status">Status: Requires Chrome Extension Setup</span>
                             </div>
                             <p>
                                 <a href="/whatnot_extension.zip" class="download-link" download>Download Extension</a>
                                 <button class="control-button" style="background-color:#6c757d; color:white;" onclick="openWhatnotGuide()">Show Setup Guide</button>
                             </p>
                              <div class="control-buttons-container">
                                  <div>
                                      Whatnot Service:
                                      <button class="control-button" data-service="whatnot" data-command="start">Start Bridge</button>
                                      <button class="control-button" data-service="whatnot" data-command="stop">Stop Bridge</button>
                                      <button class="control-button" data-service="whatnot" data-command="restart">Restart Bridge</button>
                                  </div>
                              </div>
                         </div>

                         <!-- YouTube Section -->
                         <div class="settings-section">
                             <h3>YouTube Authentication & Control</h3>
                              <div class="auth-area" id="youtube-auth-area">
                                  <span class="auth-status">Loading...</span>
                                  <!-- Login/Logout buttons added dynamically by JS -->
                              </div>
                              <div class="control-buttons-container">
                                  <div>
                                      YouTube Service:
                                      <button class="control-button" data-service="youtube" data-command="start">Start</button>
                                      <button class="control-button" data-service="youtube" data-command="stop">Stop</button>
                                      <button class="control-button" data-service="youtube" data-command="restart">Restart</button>
                                  </div>
                              </div>
                         </div>

                         <!-- Twitch Section -->
                         <div class="settings-section">
                             <h3>Twitch Authentication & Control</h3>
                              <div class="auth-area" id="twitch-auth-area">
                                  <span class="auth-status">Loading...</span>
                                  <!-- Login/Logout buttons added dynamically by JS -->
                              </div>
                              <div class="form-group">
                                  <label for="twitch-channels">Channel(s) to Join (comma-separated, optional)</label>
                                  <input type="text" id="twitch-channels" name="TWITCH_CHANNELS" placeholder="Defaults to authenticated user's channel">
                              </div>
                              <div class="control-buttons-container">
                                  <div>
                                      Twitch Service:
                                      <button class="control-button" data-service="twitch" data-command="start">Start</button>
                                      <button class="control-button" data-service="twitch" data-command="stop">Stop</button>
                                      <button class="control-button" data-service="twitch" data-command="restart">Restart</button>
                                  </div>
                              </div>
                         </div>

                         <!-- X Section -->
                         <div class="settings-section">
                             <h3>X (Twitter) Authentication & Control</h3>
                              <div class="auth-area" id="x-auth-area">
                                  <span class="auth-status">Loading...</span>
                                  <!-- Login/Logout buttons added dynamically by JS -->
                              </div>
                              <div class="control-buttons-container">
                                  <div>
                                      X Service:
                                      <button class="control-button" data-service="x" data-command="start">Start</button>
                                      <button class="control-button" data-service="x" data-command="stop">Stop</button>
                                      <button class="control-button" data-service="x" data-command="restart">Restart</button>
                                  </div>
                              </div>
                         </div>

                          <!-- App Config Section -->
                          <div class="settings-section">
                              <h3>App Configuration</h3>
                              <form id="app-settings-form">
                                  <div class="form-group">
                                     <label for="app-command-prefix">Command Prefix</label>
                                     <input type="text" id="app-command-prefix" name="COMMAND_PREFIX" style="width: 60px;" maxlength="5">
                                 </div>
                                  <div class="form-group">
                                      <label for="app-log-level">Log Level</label>
                                      <select id="app-log-level" name="LOG_LEVEL">
                                         <option value="DEBUG">DEBUG</option>
                                         <option value="INFO">INFO</option>
                                         <option value="WARNING">WARNING</option>
                                         <option value="ERROR">ERROR</option>
                                         <option value="CRITICAL">CRITICAL</option>
                                     </select>
                                  </div>
                                  <!-- Note: Twitch Channels input moved to Twitch section -->
                                  <button type="submit">Save App Config</button>
                              </form>
                         </div>

                     </div> <!-- End Settings Tab -->
                 </div> <!-- End Content Area -->

                 <!-- Sidebar -->
                 <div id="sidebar">
                     <h3>Status</h3>
                     <div id="general-status">App Status: Initializing...</div>
                     <h3>Logs</h3>
                     <div id="log-output"></div>
                     <!-- Future: User Lists, Game Info etc. -->
                 </div>

                 <!-- Whatnot Setup Modal -->
                 <div id="whatnot-guide-modal" class="modal">
                     <div class="modal-content">
                         <span class="modal-close" onclick="closeWhatnotGuide()">&times;</span>
                         <h3>Whatnot Extension Setup Guide</h3>
                         <ol>
                             <li>Click the "Download Extension" link on the Settings tab.</li>
                             <li>Unzip the downloaded `whatnot_extension.zip` file somewhere memorable.</li>
                             <li>Open Chrome and navigate to `chrome://extensions/`.</li>
                             <li>Enable "Developer mode" (toggle usually in the top-right corner).</li>
                             <li>Click the "Load unpacked" button.</li>
                             <li>Select the folder where you unzipped the extension files.</li>
                             <li>Go to an active Whatnot stream page (e.g., `whatnot.com/live/...`).</li>
                             <li>Click the FoSBot puzzle piece icon in your Chrome extensions toolbar.</li>
                             <li>In the popup, check the "Turn On Setup Mode" box.</li>
                             <li>An overlay panel will appear on the Whatnot page. Carefully click the page elements it asks for (Chat Area, Message Row, Username, Message Text, Chat Input). Click "Next" after each selection.</li>
                             <li>When finished, click "Done" on the overlay panel. The panel will disappear.</li>
                             <li>Click the extension icon again and click "Test Setup" to verify. A success message means it found chat messages.</li>
                             <li>**Important:** Uncheck "Turn On Setup Mode" in the popup when finished.</li>
                         </ol>
                         <p><em>If Whatnot chat stops working later, repeat steps 7-13 as the website structure might have changed.</em></p>
                         <button onclick="closeWhatnotGuide()">Close Guide</button>
                     </div>
                 </div>

                 <script src="main.js"></script>
             </body>
             </html>
             """,
                     "static/main.js": r"""// Generated by install_fosbot.py
             // --- File: static/main.js --- START ---
             // FoSBot Dashboard Frontend JS v0.7.3 (OAuth Flow + Commands + Refinements)

             document.addEventListener('DOMContentLoaded', () => {
                 // --- DOM Elements ---
                 const chatOutput = document.getElementById('chat-output');
                 const streamerInput = document.getElementById('streamerInput');
                 const sendButton = document.getElementById('sendButton');
                 const clearButton = document.getElementById('clearButton');
                 const wsStatusElement = document.getElementById('status-ws').querySelector('.status-text');
                 const wsLightElement = document.getElementById('status-ws').querySelector('.status-light');
                 const platformStatusIndicators = { // Spans containing light and text
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
                 const commandsStatus = document.getElementById('commands-status'); // Added
                 // Settings Forms
                 const appSettingsForm = document.getElementById('app-settings-form');
                 const twitchChannelsInput = document.getElementById('twitch-channels'); // Specific input for Twitch channels
                 // Auth Areas
                 const twitchAuthArea = document.getElementById('twitch-auth-area');
                 const youtubeAuthArea = document.getElementById('youtube-auth-area');
                 const xAuthArea = document.getElementById('x-auth-area');
                 const whatnotStatusArea = document.getElementById('whatnot-status-area'); // For Whatnot status text
                 // Service Control Buttons
                 const controlButtons = document.querySelectorAll('.control-button[data-service]');
                 // Commands Tab Elements
                 const commandsTableBody = document.querySelector('#commands-table tbody');
                 const addCommandForm = document.getElementById('add-command-form');
                 const commandNameInput = document.getElementById('command-name');
                 const commandResponseInput = document.getElementById('command-response');
                 const csvFileInput = document.getElementById('csv-file');
                 const uploadCsvButton = document.getElementById('upload-csv-button');
                 // Logger
                 const logger = {
                      debug: (message, ...optionalParams) => console.debug(`[FoSBot UI DEBUG] ${message}`, ...optionalParams),
                      info: (message, ...optionalParams) => console.info(`[FoSBot UI INFO] ${message}`, ...optionalParams),
                      warn: (message, ...optionalParams) => console.warn(`[FoSBot UI WARN] ${message}`, ...optionalParams),
                      error: (message, ...optionalParams) => console.error(`[FoSBot UI ERROR] ${message}`, ...optionalParams),
                 };


                 // --- WebSocket State ---
                 let socket = null;
                 let reconnectTimer = null;
                 let reconnectAttempts = 0;
                 const MAX_RECONNECT_ATTEMPTS = 15; // Increased attempts
                 const RECONNECT_DELAY_BASE = 3000; // 3 seconds base delay
                 let pingInterval = null;
                 const PING_INTERVAL_MS = 30000; // Send ping every 30 seconds

                 // --- State ---
                 let currentSettings = {}; // Store loaded non-sensitive settings + auth status

                 // --- Helper Functions ---
                 function updateStatusIndicator(statusId, statusClass = 'disabled', statusText = 'Unknown') {
                     const indicatorSpan = platformStatusIndicators[statusId] || (statusId === 'ws' ? document.getElementById('status-ws') : null);
                     if (!indicatorSpan) return;

                     const textEl = indicatorSpan.querySelector('.status-text');
                     const lightEl = indicatorSpan.querySelector('.status-light');
                     if (textEl && lightEl) {
                         lightEl.className = 'status-light'; // Reset classes
                         lightEl.classList.add(`status-${statusClass.toLowerCase().replace(/[^a-z0-9_]/g, '_')}`); // Sanitize class name
                         textEl.textContent = statusText;
                     } else {
                         logger.warn(`Could not find text/light elements for status indicator: ${statusId}`);
                     }
                 }

                 function formatTimestamp(isoTimestamp) {
                     if (!isoTimestamp) return '';
                     try {
                         // Attempt to parse ISO string, handle potential 'Z'
                         const date = new Date(isoTimestamp.endsWith('Z') ? isoTimestamp : isoTimestamp + 'Z');
                         if (isNaN(date.getTime())) return ''; // Invalid date
                         return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                     } catch (e) {
                         logger.error("Timestamp format error:", e, "Input:", isoTimestamp);
                         return '';
                     }
                 }

                 function escapeHtml(unsafe) {
                     if (typeof unsafe !== 'string') return unsafe;
                     return unsafe
                          .replace(/&/g, "&amp;")
                          .replace(/</g, "&lt;")
                          .replace(/>/g, "&gt;")
                          .replace(/"/g, "&quot;")
                          .replace(/'/g, "&#039;");
                 }

                 function linkify(text) {
                     // Simple URL linkification
                     const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
                     return text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
                 }

                 function addChatMessage(platform, user, display_name, text, timestamp = null) {
                     const chatOutput = document.getElementById('chat-output');
                     if (!chatOutput) return;
                     const messageDiv = document.createElement('div');
                     const platformSpan = document.createElement('span');
                     const userSpan = document.createElement('span');
                     const textSpan = document.createElement('span');
                     const timeSpan = document.createElement('span');

                     const platformClass = platform ? platform.toLowerCase().replace(/[^a-z0-9]/g, '') : 'system';
                     platformSpan.className = `platform-tag ${platformClass}`;
                     platformSpan.textContent = `[${platform ? platform.toUpperCase() : 'SYS'}]`;

                     userSpan.className = 'chat-user';
                     userSpan.textContent = display_name || user || 'Unknown'; // Use display name, fallback to user

                     textSpan.innerHTML = linkify(escapeHtml(text)); // Linkify after escaping

                     timeSpan.className = 'timestamp';
                     timeSpan.textContent = formatTimestamp(timestamp);

                     messageDiv.appendChild(timeSpan); // Timestamp first (floats right)
                     messageDiv.appendChild(platformSpan);
                     messageDiv.appendChild(userSpan);
                     messageDiv.appendChild(document.createTextNode(': ')); // Separator
                     messageDiv.appendChild(textSpan);

                     if (user && user.toLowerCase() === 'streamer') { // Highlight streamer messages
                         messageDiv.classList.add('streamer-msg');
                     }

                     // Auto-scroll logic
                     const shouldScroll = chatOutput.scrollTop + chatOutput.clientHeight >= chatOutput.scrollHeight - 30;
                     chatOutput.appendChild(messageDiv);
                     if (shouldScroll) {
                         chatOutput.scrollTop = chatOutput.scrollHeight;
                     }
                 }
                  function addBotResponseMessage(platform, channel, text, timestamp = null) {
                     const chatOutput = document.getElementById('chat-output');
                      if (!chatOutput) return;
                     const messageDiv = document.createElement('div');
                     messageDiv.classList.add("bot-response"); // Add class to style bot messages
                     const platformSpan = document.createElement('span');
                     const userSpan = document.createElement('span');
                     const textSpan = document.createElement('span');
                     const timeSpan = document.createElement('span');

                     const platformClass = platform ? platform.toLowerCase().replace(/[^a-z0-9]/g, '') : 'system';
                     platformSpan.className = `platform-tag ${platformClass}`;
                     platformSpan.textContent = `[${platform ? platform.toUpperCase() : 'SYS'}]`;

                     userSpan.className = 'chat-user';
                     userSpan.textContent = 'FoSBot'; // Bot identifier
                     // Style applied via CSS using .bot-response .chat-user

                     textSpan.innerHTML = linkify(escapeHtml(text)); // Linkify after escaping

                     timeSpan.className = 'timestamp';
                     timeSpan.textContent = formatTimestamp(timestamp || new Date().toISOString());

                     messageDiv.appendChild(timeSpan);
                     messageDiv.appendChild(platformSpan);
                     messageDiv.appendChild(userSpan);
                     messageDiv.appendChild(document.createTextNode(': '));
                     messageDiv.appendChild(textSpan);

                     // Auto-scroll logic
                     const shouldScroll = chatOutput.scrollTop + chatOutput.clientHeight >= chatOutput.scrollHeight - 30;
                     chatOutput.appendChild(messageDiv);
                     if (shouldScroll) {
                         chatOutput.scrollTop = chatOutput.scrollHeight;
                     }
                 }


                 function addLogMessage(level, message, moduleName = '') {
                     const logOutput = document.getElementById('log-output');
                     if (!logOutput) return;
                     const logEntry = document.createElement('div');
                     const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                     const levelUpper = level.toUpperCase();
                     logEntry.classList.add(`log-${levelUpper.toLowerCase()}`);
                     logEntry.textContent = `[${timestamp}] [${levelUpper}] ${moduleName ? '[' + escapeHtml(moduleName) + '] ' : ''}${escapeHtml(message)}`;

                     // Auto-scroll logic for logs
                     const shouldScroll = logOutput.scrollTop + logOutput.clientHeight >= logOutput.scrollHeight - 10;
                     logOutput.appendChild(logEntry);
                     // Keep log trimmed
                     const MAX_LOG_LINES = 200;
                     while (logOutput.children.length > MAX_LOG_LINES) {
                         logOutput.removeChild(logOutput.firstChild);
                     }
                     if (shouldScroll) {
                         logOutput.scrollTop = logOutput.scrollHeight;
                     }
                 }

                 function showStatusMessage(elementId, message, type = 'info', duration = 5000) {
                     const statusEl = document.getElementById(elementId);
                     if (!statusEl) return;
                     statusEl.textContent = message;
                     statusEl.className = type; // 'success', 'error', 'info'
                     statusEl.style.display = 'block';
                     // Clear previous timer associated with this specific element
                     clearTimeout(statusEl.timerId);
                     if (duration > 0) {
                         statusEl.timerId = setTimeout(() => {
                             statusEl.textContent = '';
                             statusEl.style.display = 'none';
                             statusEl.className = '';
                         }, duration);
                     }
                 }

                 // --- OAuth UI Update ---
                 function updateAuthUI(platform, authData) {
                     const authArea = document.getElementById(`${platform}-auth-area`);
                     if (!authArea) return;

                     authArea.innerHTML = ''; // Clear previous content

                     const statusSpan = document.createElement('span');
                     statusSpan.className = 'auth-status';

                     const loginButton = document.createElement('button');
                     loginButton.className = `control-button oauth-login-button ${platform}-login-button`; // Add platform specific class
                     loginButton.textContent = `Login with ${platform.charAt(0).toUpperCase() + platform.slice(1)}`;
                     loginButton.dataset.platform = platform;
                     loginButton.dataset.action = 'login'; // Consistent action data attribute
                     loginButton.addEventListener('click', handleAuthButtonClick);

                     const logoutButton = document.createElement('button');
                     logoutButton.className = 'control-button oauth-logout-button';
                     logoutButton.textContent = 'Logout';
                     logoutButton.dataset.platform = platform;
                     logoutButton.dataset.action = 'logout'; // Consistent action data attribute
                     logoutButton.addEventListener('click', handleAuthButtonClick);

                     if (authData && authData.logged_in) {
                         // Logged In State
                         statusSpan.innerHTML = `Logged in as: <strong>${escapeHtml(authData.user_login || 'Unknown User')}</strong>`;
                         loginButton.disabled = true;
                         logoutButton.disabled = false;
                         authArea.appendChild(statusSpan);
                         authArea.appendChild(logoutButton);
                     } else {
                         // Logged Out State
                         statusSpan.textContent = 'Not Logged In';
                         statusSpan.classList.add('not-logged-in');
                         loginButton.disabled = false;
                         logoutButton.disabled = true;
                         authArea.appendChild(loginButton);
                         authArea.appendChild(statusSpan);
                     }
                 }

                 function handleAuthButtonClick(event) {
                     const button = event.target;
                     const platform = button.dataset.platform;
                     const action = button.dataset.action;
                     if (!platform || !action) return;

                     if (action === 'login') {
                         addLogMessage('INFO', `Initiating login flow for ${platform}...`);
                         showStatusMessage('settings-status', `Redirecting to ${platform} for login...`, 'info', 0); // Indefinite
                         // Redirect the browser to the backend login endpoint
                         window.location.href = `/auth/${platform}/login`;
                     } else if (action === 'logout') {
                         if (!confirm(`Are you sure you want to logout from ${platform.toUpperCase()}? This will stop and clear related service data.`)) {
                             return;
                         }
                         logoutPlatform(platform); // Call async logout function
                     }
                 }

                 async function logoutPlatform(platform) {
                      addLogMessage('INFO', `Initiating logout for ${platform}...`);
                      showStatusMessage('settings-status', `Logging out from ${platform}...`, 'info', 0); // Indefinite status

                      try {
                          const response = await fetch(`/api/auth/${platform}/logout`, { method: 'POST' }); // Corrected path based on auth_api.py prefix
                          const result = await response.json(); // Assume JSON response

                          if (response.ok) {
                              showStatusMessage('settings-status', result.message || `${platform.toUpperCase()} logout successful.`, 'success');
                              addLogMessage('INFO', `${platform.toUpperCase()} logout: ${result.message}`);
                          } else {
                               showStatusMessage('settings-status', `Logout Error (${response.status}): ${result.detail || response.statusText}`, 'error');
                               addLogMessage('ERROR', `Logout Error (${platform}, ${response.status}): ${result.detail || response.statusText}`);
                          }
                      } catch (error) {
                          logger.error(`Logout Error (${platform}):`, error);
                          showStatusMessage('settings-status', `Network error during logout: ${error.message}`, 'error');
                          addLogMessage('ERROR', `Network error during ${platform} logout: ${error.message}`);
                      } finally {
                           // Refresh settings/auth status from backend regardless of revoke success/fail
                           requestSettings();
                      }
                 }


                 // --- WebSocket Handling ---
                 function handleWebSocketMessage(event) {
                     let data;
                     try {
                         data = JSON.parse(event.data);
                     } catch (err) {
                         logger.error("WS Parse Err:", err, "Data:", event.data);
                         addLogMessage("ERROR", "Received invalid JSON message from backend.");
                         return;
                     }

                     logger.debug("Received WS message:", data); // Log parsed data at debug

                     switch (data.type) {
                         case 'chat_message':
                             addChatMessage(data.payload.platform, data.payload.user, data.payload.display_name, data.payload.text, data.payload.timestamp);
                             break;
                         case 'bot_response': // Handle displaying bot's own messages
                              addBotResponseMessage(data.payload.platform, data.payload.channel, data.payload.text, new Date().toISOString());
                              break;
                         case 'status_update':
                              updatePlatformStatus(data.payload); // Update header indicators
                              addLogMessage('INFO', `Platform [${data.payload.platform.toUpperCase()}]: ${data.payload.status} ${data.payload.message ? '- ' + data.payload.message : ''}`);
                              break;
                         case 'log_message':
                              addLogMessage(data.payload.level, data.payload.message, data.payload.module);
                              break;
                         case 'status': // General backend status
                             addLogMessage('INFO', `Backend Status: ${data.message}`);
                             generalStatus.textContent = `App Status: ${data.message}`;
                             break;
                         case 'error': // General backend error for UI display
                             addLogMessage('ERROR', `Backend Error: ${data.message}`);
                             generalStatus.textContent = `App Status: Error - ${data.message}`;
                             break;
                         case 'pong':
                             logger.debug("Pong received from backend."); // Debug level sufficient
                             break;
                         case 'current_settings': // Received after request_settings
                              currentSettings = data.payload || {}; // Store settings globally
                              populateAppSettingsForm(currentSettings);
                              updateAllAuthUIs(currentSettings);
                              break;
                         default:
                             logger.warn("Unknown WS message type:", data.type, data);
                             addLogMessage('WARN', `Received unknown WS message type: ${data.type}`);
                     }
                 }

                 function connectWebSocket() {
                     if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
                         logger.debug("WebSocket connection already open or connecting.");
                         return;
                     }
                     clearTimeout(reconnectTimer); // Clear any pending reconnect timer

                     const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                     // Use location.host which includes hostname and port
                     const wsUrl = `${wsProto}//${window.location.host}/ws/dashboard`;
                     logger.info(`Connecting WebSocket: ${wsUrl}`);
                     updateStatusIndicator('ws', 'connecting', 'WebSocket: Connecting...');
                     addLogMessage('INFO', `Attempting WebSocket connection to ${wsUrl}...`);
                     generalStatus.textContent = "App Status: Connecting...";

                     socket = new WebSocket(wsUrl);

                     socket.onopen = () => {
                         logger.info('WebSocket connection established.');
                         updateStatusIndicator('ws', 'connected', 'WebSocket: Online');
                         addLogMessage('INFO', 'WebSocket connected.');
                         reconnectAttempts = 0; // Reset reconnect counter on success
                         generalStatus.textContent = "App Status: Connected";
                         startPing(); // Start sending pings
                         requestSettings(); // Request initial settings upon connection
                     };

                     socket.onmessage = handleWebSocketMessage;

                     socket.onclose = (event) => {
                         logger.warn(`WebSocket closed: Code=${event.code}, Reason='${event.reason}'. Attempting reconnect...`);
                         updateStatusIndicator('ws', 'disconnected', `WebSocket: Offline (Code ${event.code})`);
                         addLogMessage('WARN', `WebSocket closed (Code: ${event.code}).`);
                         generalStatus.textContent = "App Status: Disconnected";
                         socket = null; // Clear the socket object
                         stopPing(); // Stop sending pings

                         // Reconnect logic
                         if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                             reconnectAttempts++;
                             const delay = Math.min(RECONNECT_DELAY_BASE * Math.pow(1.5, reconnectAttempts - 1), 30000); // Exponential backoff up to 30s
                             logger.info(`WebSocket reconnect attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay / 1000}s...`);
                             addLogMessage('INFO', `Attempting WebSocket reconnect (${reconnectAttempts})...`);
                             reconnectTimer = setTimeout(connectWebSocket, delay);
                         } else {
                             logger.error("WebSocket maximum reconnect attempts reached. Please check the backend server and refresh the page.");
                             addLogMessage('ERROR', "Maximum WebSocket reconnect attempts reached. Check backend server.");
                             generalStatus.textContent = "App Status: Connection Failed (Max Retries)";
                         }
                     };

                     socket.onerror = (error) => {
                         logger.error('WebSocket Error:', error);
                         updateStatusIndicator('ws', 'error', 'WebSocket: Error');
                         addLogMessage('ERROR', 'WebSocket connection error.');
                         // onclose will likely be called after onerror, triggering reconnect logic
                     };
                 }

                 function startPing() {
                     stopPing(); // Clear existing interval first
                     pingInterval = setInterval(() => {
                         if (socket && socket.readyState === WebSocket.OPEN) {
                             logger.debug("Sending ping to backend.");
                             socket.send(JSON.stringify({ type: "ping" }));
                         } else {
                             logger.warn("Cannot send ping, WebSocket not open.");
                             stopPing(); // Stop pinging if connection is lost
                         }
                     }, PING_INTERVAL_MS);
                 }

                 function stopPing() {
                     clearInterval(pingInterval);
                     pingInterval = null;
                 }

                 // --- Input Handling ---
                 function sendStreamerInput() {
                     const text = streamerInput.value.trim();
                     if (!text) return;
                     if (socket && socket.readyState === WebSocket.OPEN) {
                         const message = { type: "streamer_input", payload: { text: text } };
                         try {
                             socket.send(JSON.stringify(message));
                             streamerInput.value = ''; // Clear input on successful send
                             addLogMessage('DEBUG', `Sent streamer input: "${text.substring(0, 50)}..."`);
                         } catch (e) {
                             logger.error("WS Send Err:", e);
                             addLogMessage('ERROR', `WebSocket send failed: ${e.message}`);
                             showStatusMessage('settings-status', 'Error: Could not send message. WebSocket issue.', 'error');
                         }
                     } else {
                         addLogMessage('ERROR', "Cannot send message: WebSocket is not connected.");
                         showStatusMessage('settings-status', 'Error: WebSocket not connected. Cannot send message.', 'error');
                     }
                 }
                 sendButton?.addEventListener('click', sendStreamerInput);
                 streamerInput?.addEventListener('keypress', (event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                           event.preventDefault(); // Prevent default newline on Enter
                           sendStreamerInput();
                      }
                 });
                 clearButton?.addEventListener('click', () => {
                      if(chatOutput) chatOutput.innerHTML = '<div>Chat display cleared.</div>';
                      addLogMessage('INFO', "Chat display cleared manually.");
                 });

                 // --- Tab Switching ---
                 tabButtons.forEach(button => {
                     button.addEventListener('click', () => {
                         const activeTab = document.querySelector('.tab-button.active');
                         const activeContent = document.querySelector('.tab-content.active');
                         if(activeTab) activeTab.classList.remove('active');
                         if(activeContent) activeContent.classList.remove('active');

                         button.classList.add('active');
                         const tabName = button.getAttribute('data-tab');
                         const newContent = document.querySelector(`.tab-content[data-tab-content="${tabName}"]`);
                         if(newContent) newContent.classList.add('active');

                         // Refresh relevant data when switching to tabs
                         if (tabName === 'settings') {
                             requestSettings(); // Refresh settings & auth status
                         } else if (tabName === 'commands') {
                             fetchCommands(); // Refresh command list
                         }
                     });
                 });

                 // --- Settings Handling ---
                 function requestSettings() {
                      if (socket && socket.readyState === WebSocket.OPEN) {
                           logger.debug("Requesting settings from backend...");
                           // addLogMessage('DEBUG', 'Requesting current settings...'); // Too noisy?
                           socket.send(JSON.stringify({ type: "request_settings" }));
                      } else {
                           showStatusMessage('settings-status', "Cannot load settings: WebSocket closed.", 'error');
                           // Clear auth UIs if WS is down
                           updateAllAuthUIs({}); // Pass empty object to show logged out state
                      }
                 }

                 function populateAppSettingsForm(settings) {
                     // Populate non-auth App Config form
                     if (appSettingsForm) {
                          // Use currentSettings which includes auth status
                         appSettingsForm.elements['COMMAND_PREFIX'].value = settings.COMMAND_PREFIX || '!';
                         appSettingsForm.elements['LOG_LEVEL'].value = settings.LOG_LEVEL || 'INFO';
                     }
                     // Populate Twitch channels input specifically
                     if (twitchChannelsInput) {
                         twitchChannelsInput.value = settings.TWITCH_CHANNELS || '';
                     }
                     logger.debug("Populated App Config form fields.");
                 }

                 function updateAllAuthUIs(settingsData){
                      // Update auth UI based on the *_auth_status fields
                      updateAuthUI('twitch', settingsData.twitch_auth_status);
                      updateAuthUI('youtube', settingsData.youtube_auth_status);
                      updateAuthUI('x', settingsData.x_auth_status);
                      // Update Whatnot status display
                      const whatnotStatusSpan = whatnotStatusArea?.querySelector('.auth-status');
                      if(whatnotStatusSpan){
                           whatnotStatusSpan.textContent = settingsData.whatnot_auth_status?.user_login || "Status: Unknown";
                           whatnotStatusSpan.className = settingsData.whatnot_auth_status?.logged_in ? 'auth-status' : 'auth-status not-logged-in';
                      }

                 }

                 // Save App Config settings (non-auth) and Twitch Channels
                 appSettingsForm?.addEventListener('submit', async (e) => {
                     e.preventDefault();
                     const formData = new FormData(appSettingsForm);
                     // Include Twitch channels from its specific input
                     const dataToSend = {
                          COMMAND_PREFIX: formData.get('COMMAND_PREFIX'),
                          LOG_LEVEL: formData.get('LOG_LEVEL'),
                          TWITCH_CHANNELS: twitchChannelsInput.value.trim() // Use the specific input
                     };

                     logger.debug("Saving App Config:", dataToSend);
                     showStatusMessage('settings-status', "Saving App Config...", 'info', 0); // Indefinite

                     try {
                         const response = await fetch('/api/settings', { // Correct endpoint
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify(dataToSend)
                         });
                         const result = await response.json();
                         if (response.ok) {
                             showStatusMessage('settings-status', result.message || "App Config saved!", 'success');
                             addLogMessage('INFO', `App Config saved: ${result.message}`);
                              // Refresh settings from backend to confirm update
                              requestSettings();
                         } else {
                              showStatusMessage('settings-status', `Error saving App Config: ${result.detail || response.statusText}`, 'error');
                              addLogMessage('ERROR', `Error saving App Config: ${result.detail || response.statusText}`);
                         }
                     } catch (error) {
                          logger.error("Save App Config Err:", error);
                          showStatusMessage('settings-status', `Network error saving App Config: ${error.message}`, 'error');
                          addLogMessage('ERROR', `Network error saving App Config: ${error.message}`);
                     }
                 });

                  // Save Twitch Channels specifically when its input changes (optional, or rely on main save button)
                  // twitchChannelsInput?.addEventListener('change', async (e) => { ... }); // Could add specific save logic here


                 // --- Service Control ---
                 controlButtons.forEach(button => {
                     button.addEventListener('click', async (e) => {
                          const service = button.dataset.service;
                          const command = button.dataset.command;
                          if (!service || !command) return;

                          showStatusMessage('settings-status', `Sending '${command}' to ${service}...`, 'info', 0);
                          addLogMessage('INFO', `Sending control command '${command}' to service '${service}'...`);

                          try {
                              const response = await fetch(`/api/control/${service}/${command}`, { method: 'POST' }); // Correct endpoint
                              const result = await response.json();
                              if (response.ok) {
                                  showStatusMessage('settings-status', result.message || `Command '${command}' sent to ${service}.`, 'success');
                                  addLogMessage('INFO', `Control command response for ${service}: ${result.message}`);
                                  // Request settings again to update status indicators based on expected service state change
                                  setTimeout(requestSettings, 1500); // Delay slightly
                              } else {
                                   showStatusMessage('settings-status', `Error controlling ${service}: ${result.detail || response.statusText}`, 'error');
                                   addLogMessage('ERROR', `Error controlling ${service}: ${result.detail || response.statusText}`);
                              }
                          } catch (error) {
                               logger.error(`Control Error (${service} ${command}):`, error);
                               showStatusMessage('settings-status', `Network error controlling ${service}: ${error.message}`, 'error');
                               addLogMessage('ERROR', `Network error controlling ${service}: ${error.message}`);
                          }
                     });
                 });

                 // --- Commands Tab Logic ---
                 async function fetchCommands() {
                     try {
                         const response = await fetch('/api/commands'); // Correct endpoint
                         if (!response.ok) {
                              const errorData = await response.json();
                              throw new Error(`HTTP error ${response.status}: ${errorData.detail || response.statusText}`);
                         }
                         const commands = await response.json();
                         commandsTableBody.innerHTML = ''; // Clear existing rows
                         if (Object.keys(commands).length === 0) {
                              commandsTableBody.innerHTML = '<tr><td colspan="3"><i>No custom commands defined yet.</i></td></tr>';
                         } else {
                              // Sort commands alphabetically for display
                              const sortedCommands = Object.entries(commands).sort((a, b) => a[0].localeCompare(b[0]));
                              sortedCommands.forEach(([name, responseText]) => {
                                   const row = commandsTableBody.insertRow();
                                   row.innerHTML = `
                                        <td>!${escapeHtml(name)}</td>
                                        <td>${escapeHtml(responseText)}</td>
                                        <td>
                                            <span class="command-action" data-command-name="${escapeHtml(name)}">Delete</span>
                                        </td>
                                   `;
                                   // Add event listener directly to the delete span
                                   row.querySelector('.command-action').addEventListener('click', handleDeleteCommandClick);
                              });
                         }
                     } catch (error) {
                         logger.error('Error fetching commands:', error);
                         showStatusMessage('commands-status', `Error loading commands: ${error.message}`, 'error');
                         commandsTableBody.innerHTML = '<tr><td colspan="3"><i>Error loading commands.</i></td></tr>';
                     }
                 }

                 add
                 "app/services/dashboard_service.py": r"""# Generated by install_fosbot.py
             # --- File: app/services/dashboard_service.py --- START ---
             import logging
             import json
             import asyncio
             from fastapi import WebSocket, WebSocketDisconnect
             from typing import Set # Use Set for active connections

             # Core imports
             from app.core.event_bus import event_bus
             from app.events import (
                 InternalChatMessage, ChatMessageReceived, PlatformStatusUpdate, LogMessage,
                 StreamerInputReceived, BotResponseToSend, BroadcastStreamerMessage, BotResponse # Added BotResponse
             )
             # Use json_store for loading tokens to determine platforms to broadcast to
             from app.core.json_store import load_tokens, load_settings # Load settings for masking

             logger = logging.getLogger(__name__)

             # --- Connection Management ---
             class ConnectionManager:
                 """Manages active WebSocket connections for the dashboard."""
                 def __init__(self):
                     self.active_connections: Set[WebSocket] = set()
                     logger.info("Dashboard Connection Manager initialized.")

                 async def connect(self, websocket: WebSocket):
                     """Accepts a new WebSocket connection and adds it to the set."""
                     await websocket.accept()
                     self.active_connections.add(websocket)
                     client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown"
                     logger.info(f"Dashboard client connected: {client_id} (Total: {len(self.active_connections)})")
                     # Send initial status or welcome message
                     try:
                         await self.send_personal_message(json.dumps({"type":"status", "message":"Connected to FoSBot backend!"}), websocket)
                     except Exception as e:
                          logger.warning(f"Failed to send initial welcome to {client_id}: {e}")

                 def disconnect(self, websocket: WebSocket):
                     """Removes a WebSocket connection from the set."""
                     client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown"
                     if websocket in self.active_connections:
                         self.active_connections.remove(websocket)
                         logger.info(f"Dashboard client disconnected: {client_id} (Total: {len(self.active_connections)})")
                     else:
                          logger.debug(f"Attempted to disconnect already removed client: {client_id}")

                 async def send_personal_message(self, message: str, websocket: WebSocket) -> bool:
                     """Sends a message to a single specific WebSocket connection. Returns True on success, False on failure."""
                     if websocket in self.active_connections:
                         try:
                             await websocket.send_text(message)
                             return True # Indicate success
                         except Exception as e:
                              # Common errors: WebSocketStateError if closed during send, ConnectionClosedOK
                              client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown"
                              # Log less severely for expected disconnects
                              if isinstance(e, (WebSocketDisconnect, ConnectionResetError, RuntimeError)):
                                   logger.info(f"WebSocket closed for client {client_id} during send.")
                              else:
                                   logger.warning(f"Failed to send personal message to client {client_id}: {e}. Disconnecting.")
                              # Disconnect on send error to clean up list
                              self.disconnect(websocket)
                              return False # Indicate failure
                     return False # Not connected

                 async def broadcast(self, data: dict):
                     """Sends JSON data to all active WebSocket connections."""
                     if not self.active_connections: return # Skip if no clients
                     logger.debug(f"Broadcasting message type '{data.get('type')}' to {len(self.active_connections)} dashboard clients.")

                     message_string = json.dumps(data) # Prepare message once
                     # Use asyncio.gather for concurrent sending
                     # Iterate over a copy of the set in case disconnect modifies it during broadcast
                     tasks = [self.send_personal_message(message_string, ws) for ws in list(self.active_connections)]
                     if tasks:
                         results = await asyncio.gather(*tasks, return_exceptions=True)
                         # Log any errors that occurred during broadcast (send_personal_message already handles logging/disconnecting failed ones)
                         error_count = sum(1 for result in results if isinstance(result, Exception) or result is False)
                         if error_count > 0:
                              logger.warning(f"Broadcast finished with {error_count} send errors/failures.")

             # Create a single instance of the manager
             manager = ConnectionManager()

             # --- WebSocket Handling Logic ---
             async def handle_dashboard_websocket(websocket: WebSocket):
                 """Handles the lifecycle of a single dashboard WebSocket connection."""
                 await manager.connect(websocket)
                 client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown"
                 try:
                     while True:
                         # Set a timeout for receive to detect dead connections sooner?
                         # Or rely on ping/pong from frontend? Let's rely on frontend ping for now.
                         data = await websocket.receive_text()
                         logger.debug(f"Received from dashboard client {client_id}: {data}")
                         try:
                             message_data = json.loads(data)
                             msg_type = message_data.get("type")
                             payload = message_data.get("payload", {}) # Use payload consistently

                             if msg_type == "streamer_input":
                                 text = payload.get("text", "").strip() # Get text from payload
                                 if text:
                                     # Publish for backend processing (chat_processor handles command/broadcast logic)
                                     event_bus.publish(StreamerInputReceived(text=text))
                                     # Confirmation not strictly needed, relies on seeing message appear/action happen
                                     # await manager.send_personal_message(json.dumps({"type": "status", "message": "Input received."}), websocket)
                                 else:
                                     logger.warning(f"Received empty streamer_input from {client_id}")
                                     await manager.send_personal_message(json.dumps({"type": "error", "message": "Cannot send empty input."}), websocket)

                             elif msg_type == "ping":
                                 # Respond to keepalive pings from frontend
                                 await manager.send_personal_message(json.dumps({"type":"pong"}), websocket)
                                 logger.debug(f"Sent pong to dashboard client {client_id}")

                             elif msg_type == "request_settings":
                                  # Send current non-sensitive settings + auth status
                                  logger.debug(f"Processing request_settings from {client_id}")
                                  # Fetch settings via API handler logic for consistency
                                  from app.apis.settings_api import get_current_settings
                                  current_display_settings = await get_current_settings()
                                  await manager.send_personal_message(json.dumps({"type": "current_settings", "payload": current_display_settings}), websocket)

                             else:
                                  logger.warning(f"Received unknown message type from dashboard {client_id}: {msg_type}")
                                  await manager.send_personal_message(json.dumps({"type": "error", "message": f"Unknown message type: {msg_type}"}), websocket)

                         except json.JSONDecodeError:
                             logger.warning(f"Received non-JSON message from dashboard {client_id}: {data}")
                             await manager.send_personal_message(json.dumps({"type": "error", "message": "Invalid JSON format."}), websocket)
                         except Exception as e:
                              logger.exception(f"Error processing message from dashboard client {client_id}: {e}")
                              try: await manager.send_personal_message(json.dumps({"type": "error", "message": "Backend error processing request."}), websocket)
                              except: pass # Avoid error loops

                 except WebSocketDisconnect as e:
                     logger.info(f"Dashboard client {client_id} disconnected cleanly (Code: {e.code}).")
                 except Exception as e:
                     # Handle other potential exceptions during receive_text or connection handling
                     logger.error(f"Dashboard client {client_id} unexpected error: {e}", exc_info=True)
                 finally:
                     manager.disconnect(websocket)


             # --- Event Handlers (Subscribed by setup_dashboard_service_listeners) ---

             async def forward_chat_to_dashboard(event: ChatMessageReceived):
                 """Formats and broadcasts chat messages to all connected dashboards."""
                 if not isinstance(event, ChatMessageReceived): return
                 msg = event.message
                 # Prepare payload matching frontend expectations
                 payload_data = {
                     "platform": msg.platform,
                     "channel": msg.channel,
                     "user": msg.user, # Use the primary username
                     "display_name": msg.display_name or msg.user, # Fallback display name
                     "text": msg.text,
                     "timestamp": msg.timestamp # Already ISO string from InternalChatMessage
                 }
                 await manager.broadcast({"type": "chat_message", "payload": payload_data})

             async def forward_status_to_dashboard(event: PlatformStatusUpdate):
                 """Broadcasts platform connection status updates to dashboards."""
                 if not isinstance(event, PlatformStatusUpdate): return
                 payload_data = {
                     "platform": event.platform,
                     "status": event.status.lower(), # Ensure consistent casing
                     "message": event.message or ""
                 }
                 await manager.broadcast({"type": "status_update", "payload": payload_data})

             async def forward_log_to_dashboard(event: LogMessage):
                 """Broadcasts important log messages (Info/Warning/Error/Critical) to dashboards."""
                 if not isinstance(event, LogMessage): return
                 # Only forward levels likely relevant to the user interface
                 log_level_numeric = getattr(logging, event.level.upper(), logging.INFO)
                 if log_level_numeric >= logging.INFO: # Send INFO and above
                      payload_data = {
                          "level": event.level.upper(),
                          "message": event.message,
                          "module": event.module or "Unknown" # Indicate source if available
                      }
                      await manager.broadcast({"type": "log_message", "payload": payload_data})

             async def forward_bot_response_to_dashboard(event: BotResponseToSend):
                 """Shows messages the bot sends in the dashboard chat for context."""
                 if not isinstance(event, BotResponseToSend): return
                 response = event.response
                 # Mimic the chat message format but indicate it's from the bot
                 payload_data = {
                     "platform": response.target_platform,
                     "channel": response.target_channel,
                     "user": "FoSBot", # Clear bot identifier
                     "display_name": "FoSBot",
                     "text": response.text,
                     "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                 }
                 await manager.broadcast({"type": "bot_response", "payload": payload_data}) # Use distinct type


             async def handle_broadcast_request(event: BroadcastStreamerMessage):
                 """
                 Receives a request to broadcast a message and publishes BotResponseToSend
                 events for each connected/authenticated platform.
                 """
                 if not isinstance(event, BroadcastStreamerMessage): return
                 logger.info(f"Received request to broadcast: '{event.text[:50]}...'")
                 platforms_to_try = ["twitch", "youtube", "x"] # Whatnot handled via extension response
                 # Get user login names for channel context if available
                 tokens = {p: await load_tokens(p) for p in platforms_to_try}

                 for platform in platforms_to_try:
                     platform_tokens = tokens.get(platform)
                     if platform_tokens and platform_tokens.get("access_token"):
                          # Determine target channel (use user_login or a default)
                          target_channel = platform_tokens.get("user_login", f"{platform}_default_channel")
                          # For Twitch, use the *first* configured channel if available, else user_login
                          if platform == 'twitch':
                               channels_str = await get_setting("TWITCH_CHANNELS", "")
                               channels_list = [ch.strip().lower() for ch in channels_str.split(',') if ch.strip()]
                               target_channel = channels_list[0] if channels_list else platform_tokens.get("user_login")

                          if not target_channel:
                               logger.warning(f"Cannot determine target channel for broadcast on {platform}.")
                               continue

                          response = BotResponse(
                               target_platform=platform,
                               target_channel=target_channel,
                               text=f"[Broadcast] {event.text}" # Prefix to indicate it's a broadcast
                          )
                          event_bus.publish(BotResponseToSend(response=response))
                          logger.debug(f"Published broadcast message for {platform} to channel {target_channel}")
                     else:
                          logger.debug(f"Skipping broadcast for {platform}: Not authenticated.")


             # --- Setup Function ---
             def setup_dashboard_service_listeners():
                 """Subscribes the necessary handlers to the event bus."""
                 logger.info("Setting up Dashboard Service event listeners...")
                 event_bus.subscribe(ChatMessageReceived, forward_chat_to_dashboard)
                 event_bus.subscribe(PlatformStatusUpdate, forward_status_to_dashboard)
                 event_bus.subscribe(LogMessage, forward_log_to_dashboard)
                 # Subscribe to see bot's own messages in dashboard
                 event_bus.subscribe(BotResponseToSend, forward_bot_response_to_dashboard)
                 # Subscribe to handle broadcast requests coming from streamer input handler
                 event_bus.subscribe(BroadcastStreamerMessage, handle_broadcast_request)
                 logger.info("Dashboard Service listeners subscribed.")

             # --- File: app/services/dashboard_service.py --- END ---
             """,
                     "app/services/streamer_command_handler.py": r"""# Generated by install_fosbot.py
             # --- File: app/services/streamer_command_handler.py --- START ---
             import logging
             import datetime
             from app.core.event_bus import event_bus
             from app.events import StreamerInputReceived, CommandDetected, BroadcastStreamerMessage, InternalChatMessage # Use specific events
             from app.core.config import logger, settings # Use settings dict

             async def handle_streamer_input(event: StreamerInputReceived):
                 """Handles raw text input from the streamer dashboard."""
                 text = event.text.strip()
                 if not text:
                     logger.debug("Ignoring empty streamer input.")
                     return

                 prefix = settings.get('COMMAND_PREFIX', '!') # Get current command prefix
                 logger.info(f"Processing streamer input: '{text[:100]}...'")

                 if text.startswith(prefix):
                     # Treat as a command to be processed by the main chat processor
                     logger.info("Streamer input detected as command.")
                     # Create a standard message object, marking it as from the dashboard admin
                     now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                     streamer_msg = InternalChatMessage(
                         platform='dashboard',      # Special identifier for source
                         user='STREAMER',           # Fixed admin username
                         text=text,                 # The raw command string
                         channel='admin_console',   # Arbitrary channel name/identifier
                         timestamp=now_iso,         # Timestamp
                         raw_data={'is_admin_command': True} # Metadata flag
                     )
                     # Publish ChatMessageReceived so chat_processor handles it
                     # Allows admin commands to use the same command registry & bypass cooldowns
                     event_bus.publish(ChatMessageReceived(message=streamer_msg))
                 else:
                     # Treat as a broadcast message request
                     logger.info("Streamer input detected as broadcast message.")
                     # Publish event for dashboard service to handle actual broadcasting
                     event_bus.publish(BroadcastStreamerMessage(text=text))

             def setup_streamer_command_handler():
                 """Subscribes the handler to the event bus."""
                 logger.info("Setting up Streamer Command/Input Handler...")
                 # Listen for raw input from the dashboard WebSocket handler
                 event_bus.subscribe(StreamerInputReceived, handle_streamer_input)
                 logger.info("Streamer Command/Input Handler subscribed to StreamerInputReceived.")

             # Note: Actual command execution logic (like !announce) should reside
             # in the chat_processor's command handlers, triggered when it receives
             # the ChatMessageReceived event with platform='dashboard'.

             # --- File: app/services/streamer_command_handler.py --- END ---
             """,
                     "app/services/twitch_service.py": r"""# Generated by install_fosbot.py
             # --- File: app/services/twitch_service.py --- START ---
             import logging
             import asyncio
             import time
             import traceback
             from twitchio.ext import commands
             from twitchio import Client, Chatter, Channel, Message # Use specific twitchio types
             from twitchio.errors import AuthenticationError, TwitchIOException # Use specific errors
             import httpx
             from collections import defaultdict
             import datetime
             from typing import Dict, List, Optional, Coroutine, Any # Added imports

             # Core imports
             from app.core.json_store import load_tokens, save_tokens, get_setting, clear_tokens # Use get_setting for TWITCH_CHANNELS
             # Import App Owner Credentials from config
             from app.core.config import logger, TWITCH_APP_CLIENT_ID, TWITCH_APP_CLIENT_SECRET
             from app.core.event_bus import event_bus
             from app.events import (
                 InternalChatMessage, ChatMessageReceived,
                 BotResponseToSend, BotResponse,
                 PlatformStatusUpdate, SettingsUpdated, ServiceControl, LogMessage
             )

             # --- Constants ---
             TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
             DEFAULT_SEND_DELAY = 1.6 # Seconds between messages to avoid rate limits

             # --- Module State ---
             _STATE = {
                 "task": None,       # The asyncio.Task running the main service loop
                 "instance": None,   # The active TwitchBot instance
                 "running": False,   # Control flag for the main run loop (set by start/stop)
                 "connected": False, # Actual connection status flag
                 "user_login": None, # Store the login name associated with the token
                 "user_id": None,    # Store the user ID associated with the token
             }
             # Global reference to the task for cancellation from main.py
             _run_task: asyncio.Task | None = None

             # --- Twitch Bot Class ---
             class TwitchBot(commands.Bot):
                 """Custom Bot class extending twitchio.ext.commands.Bot"""
                 def __init__(self, token: str, nick: str, client_id: str, channels: List[str]):
                     self.initial_channels_list = [ch.strip().lower() for ch in channels if ch.strip()]
                     if not self.initial_channels_list:
                         logger.warning("TwitchBot initialized with an empty channel list.")

                     # Ensure token starts with oauth:, handle None token gracefully
                     valid_token = token if token and token.startswith('oauth:') else (f'oauth:{token}' if token else None)
                     if not valid_token:
                          logger.error("CRITICAL: TwitchBot initialized without a valid token.")
                          raise ValueError("Cannot initialize TwitchBot without a valid OAuth token.")

                     if not nick:
                          logger.error("CRITICAL: TwitchBot initialized without a 'nick' (username).")
                          raise ValueError("Cannot initialize TwitchBot without a 'nick'.")
                     if not client_id:
                          logger.error("CRITICAL: TwitchBot initialized without a 'client_id'.")
                          raise ValueError("Cannot initialize TwitchBot without a 'client_id'.")

                     super().__init__(
                         token=valid_token,
                         client_id=client_id,
                         nick=nick.lower(), # Ensure nick is lowercase
                         prefix=None, # We handle commands via event bus, not twitchio's prefix system
                         initial_channels=self.initial_channels_list
                     )
                     self._closing = False
                     self._response_queue: asyncio.Queue[BotResponse] = asyncio.Queue(maxsize=100) # Queue for outgoing messages
                     self._sender_task: asyncio.Task | None = None
                     logger.info(f"TwitchBot instance created for nick '{self.nick}'. Attempting to join: {self.initial_channels_list}")

                 async def event_ready(self):
                     """Called once the bot connects to Twitch successfully."""
                     global _STATE
                     _STATE["connected"] = True
                     self._closing = False
                     # Store actual user ID and nick confirmed by Twitch
                     _STATE["user_id"] = self.user_id
                     _STATE["user_login"] = self.nick
                     logger.info(f"Twitch Bot Ready! Logged in as: {self.nick} (ID: {self.user_id})")
                     if self.connected_channels:
                         channel_names = ', '.join(ch.name for ch in self.connected_channels)
                         logger.info(f"Successfully joined channels: {channel_names}")
                         event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connected', message=f"Joined: {channel_names}"))
                     else:
                         logger.warning(f"Twitch Bot connected but failed to join specified channels: {self.initial_channels_list}")
                         event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message="Connected but failed to join channels"))

                     # Start the message sender task only when ready
                     if self._sender_task is None or self._sender_task.done():
                         self._sender_task = asyncio.create_task(self._message_sender(), name=f"TwitchSender_{self.nick}")
                         logger.info("Twitch message sender task started.")

                     # Subscribe to BotResponseToSend events *after* ready and sender is running
                     event_bus.subscribe(BotResponseToSend, self.handle_bot_response_event)

                 async def event_message(self, message: Message):
                     """Processes incoming chat messages from joined channels."""
                     # Ignore messages from the bot itself or if shutting down
                     if message.echo or self._closing or not message.author or not message.channel:
                         return

                     logger.debug(f"Twitch <#{message.channel.name}> {message.author.name}: {message.content}")

                     # Convert timestamp to UTC ISO format string
                     timestamp_iso = message.timestamp.replace(tzinfo=datetime.timezone.utc).isoformat() if message.timestamp else datetime.datetime.now(datetime.timezone.utc).isoformat()

                     # Create the standardized internal message format
                     internal_msg = InternalChatMessage(
                         platform='twitch',
                         channel=message.channel.name,
                         user=message.author.name, # Use name for general display
                         text=message.content,
                         timestamp=timestamp_iso,
                         # Include additional useful info
                         user_id=str(message.author.id),
                         display_name=message.author.display_name,
                         message_id=message.id,
                         raw_data={ # Store tags and other potentially useful raw data
                             'tags': message.tags or {},
                             'is_mod': message.author.is_mod,
                             'is_subscriber': message.author.is_subscriber,
                             'bits': getattr(message, 'bits', 0) # Include bits if available
                         }
                     )
                     # Publish the internal message onto the event bus
                     event_bus.publish(ChatMessageReceived(message=internal_msg))

                 async def event_join(self, channel: Channel, user: Chatter):
                     """Logs when a user (or the bot) joins a channel."""
                     # Log joins unless it's the bot itself joining
                     if user.name and self.nick and user.name.lower() != self.nick.lower():
                         logger.debug(f"User '{user.name}' joined #{channel.name}")

                 async def event_part(self, channel: Channel, user: Chatter):
                     """Logs when a user (or the bot) leaves a channel."""
                      if user.name and self.nick and user.name.lower() != self.nick.lower():
                         logger.debug(f"User '{user.name}' left #{channel.name}")

                 async def event_error(self, error: Exception, data: str = None):
                     """Handles errors reported by the twitchio library."""
                     global _STATE
                     error_name = type(error).__name__
                     logger.error(f"Twitch Bot event_error: {error_name} - {error}", exc_info=logger.isEnabledFor(logging.DEBUG))

                     # Specific handling for authentication failures
                     if isinstance(error, AuthenticationError) or 'Login authentication failed' in str(error):
                         logger.critical("Twitch login failed - Invalid token or nick. Check settings. Disabling service.")
                         event_bus.publish(PlatformStatusUpdate(platform='twitch', status='auth_error', message='Login failed - Check Credentials'))
                         _STATE["running"] = False # Signal the main run loop to stop retrying this config
                         # Optionally clear the bad token here
                         await clear_tokens("twitch")
                     elif isinstance(error, TwitchIOException):
                          logger.error(f"Twitch IO Error: {error}. May indicate connection issue.")
                          # Let the main loop handle reconnection for IO errors
                          event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=f"IO Error: {error_name}"))
                     else:
                         # General error reporting
                         event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=f"Internal Error: {error_name}"))

                 async def event_close(self):
                     """Called when the underlying connection is closed."""
                     global _STATE
                     logger.warning(f"Twitch Bot WebSocket connection closed (Instance ID: {id(self)}).")
                     _STATE["connected"] = False
                     # Stop the sender task if it's running
                     if self._sender_task and not self._sender_task.done():
                          logger.debug("Cancelling sender task due to connection close.")
                          self._sender_task.cancel()
                     # Unsubscribe from BotResponseToSend to prevent queueing messages while disconnected
                     # Check if method exists before unsubscribing (handle potential race conditions)
                     if hasattr(self, 'handle_bot_response_event'):
                          try:
                               event_bus.unsubscribe(BotResponseToSend, self.handle_bot_response_event)
                          except ValueError:
                               pass # Already unsubscribed

                     # Publish disconnected status only if not initiated by our own shutdown
                     if not self._closing:
                         event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disconnected', message="Connection closed unexpectedly"))
                         # Reconnection is handled by the run_twitch_service loop

                 async def handle_bot_response_event(self, event: BotResponseToSend):
                     """Event bus subscriber method to queue outgoing messages."""
                     # Check if this response is for Twitch and if we are connected
                     if event.response.target_platform == 'twitch' and _STATE.get("connected") and not self._closing:
                         logger.debug(f"Queueing Twitch response for channel {event.response.target_channel}: {event.response.text[:50]}...")
                         try:
                             self._response_queue.put_nowait(event.response)
                         except asyncio.QueueFull:
                             logger.error("Twitch response queue FULL! Discarding message.")
                     # Silently ignore messages for other platforms or when disconnected/closing

                 async def _message_sender(self):
                     """Task that pulls messages from the queue and sends them with rate limiting."""
                     global _STATE
                     logger.info("Twitch message sender task running.")
                     while _STATE.get("connected") and not self._closing:
                         try:
                             # Wait for a message with a timeout to allow checking the running state
                             response: BotResponse = await asyncio.wait_for(self._response_queue.get(), timeout=1.0)

                             target_channel_name = response.target_channel
                             if not target_channel_name:
                                 logger.warning("Skipping Twitch send: No target channel specified.")
                                 self._response_queue.task_done()
                                 continue

                             # Get the channel object (case-insensitive check)
                             channel = self.get_channel(target_channel_name.lower())
                             if not channel:
                                 # Attempt to join the channel if not currently joined
                                 logger.warning(f"Not in channel '{target_channel_name}'. Attempting to join...")
                                 try:
                                      await self.join_channels([target_channel_name.lower()])
                                      # Give twitchio a moment to process the join
                                      await asyncio.sleep(1.0)
                                      channel = self.get_channel(target_channel_name.lower())
                                      if not channel:
                                           logger.error(f"Failed to join channel '{target_channel_name}' for sending.")
                                           self._response_queue.task_done()
                                           continue
                                      else:
                                           logger.info(f"Successfully joined '{target_channel_name}' for sending.")
                                 except Exception as join_err:
                                      logger.error(f"Error joining channel '{target_channel_name}': {join_err}")
                                      self._response_queue.task_done()
                                      continue

                             # Format message (e.g., add reply mention)
                             text_to_send = response.text
                             if response.reply_to_user:
                                 clean_user = response.reply_to_user.lstrip('@')
                                 text_to_send = f"@{clean_user}, {text_to_send}"

                             # Send the message
                             try:
                                 # Truncate if necessary (Twitch limit is 500 chars)
                                 if len(text_to_send) > 500:
                                      logger.warning(f"Truncating message to 500 chars for Twitch: {text_to_send[:50]}...")
                                      text_to_send = text_to_send[:500]

                                 logger.info(f"Sending Twitch to #{target_channel_name}: {text_to_send[:100]}...")
                                 await channel.send(text_to_send)
                                 self._response_queue.task_done()
                                 # Wait *after* sending to respect rate limits
                                 await asyncio.sleep(DEFAULT_SEND_DELAY)
                             except ConnectionResetError:
                                 logger.error(f"Connection reset while sending to #{target_channel_name}. Stopping sender.")
                                 self._response_queue.task_done()
                                 break # Exit sender loop, main loop will handle reconnect
                             except TwitchIOException as tio_e:
                                 logger.error(f"TwitchIO Error during send: {tio_e}. Message likely not sent.")
                                 self._response_queue.task_done()
                                 await asyncio.sleep(DEFAULT_SEND_DELAY) # Still wait to avoid spamming on transient errors
                             except Exception as send_e:
                                 logger.error(f"Unexpected error sending to #{target_channel_name}: {send_e}", exc_info=True)
                                 self._response_queue.task_done()
                                 await asyncio.sleep(DEFAULT_SEND_DELAY) # Wait even on error

                         except asyncio.TimeoutError:
                             # No message in queue, loop continues to check connected/closing state
                             continue
                         except asyncio.CancelledError:
                             logger.info("Twitch message sender task cancelled.")
                             break # Exit loop
                         except Exception as e:
                             logger.exception(f"Critical error in Twitch sender loop: {e}")
                             await asyncio.sleep(5) # Pause before potentially retrying loop

                     logger.warning("Twitch message sender task stopped.")
                     # Ensure any remaining tasks in queue are marked done if loop exits unexpectedly
                     while not self._response_queue.empty():
                         try: self._response_queue.get_nowait(); self._response_queue.task_done()
                         except asyncio.QueueEmpty: break

                 async def custom_shutdown(self):
                     """Initiates a graceful shutdown of this bot instance."""
                     global _STATE
                     if self._closing: return # Prevent double shutdown
                     instance_id = id(self)
                     logger.info(f"Initiating shutdown for TwitchBot instance {instance_id}...")
                     self._closing = True
                     _STATE["connected"] = False # Mark as disconnected immediately

                     # Unsubscribe from events first
                     if hasattr(self, 'handle_bot_response_event'):
                          try: event_bus.unsubscribe(BotResponseToSend, self.handle_bot_response_event)
                          except ValueError: pass

                     event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disconnecting'))

                     # Cancel and await the sender task
                     if self._sender_task and not self._sender_task.done():
                         if not self._sender_task.cancelling():
                             logger.debug(f"Cancelling sender task for instance {instance_id}...")
                             self._sender_task.cancel()
                         try:
                             await asyncio.wait_for(self._sender_task, timeout=5.0)
                             logger.debug(f"Sender task for instance {instance_id} finished.")
                         except asyncio.CancelledError:
                             logger.debug(f"Sender task for instance {instance_id} confirmed cancelled.")
                         except asyncio.TimeoutError:
                              logger.warning(f"Timeout waiting for sender task of instance {instance_id} to cancel.")
                         except Exception as e:
                             logger.error(f"Error awaiting cancelled sender task for instance {instance_id}: {e}")
                     self._sender_task = None

                     # Clear the response queue *before* closing the connection
                     logger.debug(f"Clearing response queue for instance {instance_id}...")
                     while not self._response_queue.empty():
                         try: self._response_queue.get_nowait(); self._response_queue.task_done()
                         except asyncio.QueueEmpty: break
                     logger.debug(f"Response queue cleared for instance {instance_id}.")

                     # Close the twitchio connection
                     logger.debug(f"Closing Twitch connection for instance {instance_id}...")
                     try:
                         # Use twitchio's close method
                         await self.close()
                     except Exception as e:
                         logger.error(f"Error during twitchio bot close for instance {instance_id}: {e}", exc_info=True)
                     logger.info(f"Twitch bot instance {instance_id} shutdown process complete.")


             # --- Token Refresh ---
             async def refresh_twitch_token(refresh_token: str) -> Optional[Dict[str, Any]]:
                 """Refreshes the Twitch OAuth token."""
                 if not refresh_token:
                     logger.error("Cannot refresh Twitch token: No refresh token provided.")
                     return None
                 if not TWITCH_APP_CLIENT_ID or not TWITCH_APP_CLIENT_SECRET:
                     logger.error("Cannot refresh Twitch token: App credentials missing.")
                     return None

                 logger.info("Attempting to refresh Twitch OAuth token...")
                 token_params = {
                     "grant_type": "refresh_token",
                     "refresh_token": refresh_token,
                     "client_id": TWITCH_APP_CLIENT_ID,
                     "client_secret": TWITCH_APP_CLIENT_SECRET
                 }
                 async with httpx.AsyncClient(timeout=15.0) as client:
                     try:
                         response = await client.post(TWITCH_TOKEN_URL, data=token_params)
                         response.raise_for_status()
                         token_data = response.json()
                         logger.info("Twitch token refreshed successfully.")
                         # Prepare data structure consistent with save_tokens expectations
                         return {
                             "access_token": token_data.get("access_token"),
                             "refresh_token": token_data.get("refresh_token"), # Usually gets a new refresh token too
                             "expires_in": token_data.get("expires_in"),
                             "scope": token_data.get("scope", []), # Scope might be a list here
                         }
                     except httpx.TimeoutException:
                         logger.error("Timeout refreshing Twitch token.")
                         return None
                     except httpx.HTTPStatusError as e:
                         logger.error(f"HTTP error refreshing Twitch token: {e.response.status_code} - {e.response.text}")
                         if e.response.status_code in [400, 401]: # Bad request or unauthorized often means bad refresh token
                              logger.error("Refresh token may be invalid or revoked.")
                              # Consider clearing the invalid token here? Or let auth flow handle it.
                         return None
                     except Exception as e:
                         logger.exception(f"Unexpected error refreshing Twitch token: {e}")
                         return None

             # --- Service Runner & Control ---
             async def run_twitch_service():
                 """Main loop for the Twitch service: handles loading config, connecting, and reconnecting."""
                 global _STATE, _run_task
                 logger.info("Twitch service runner task started.")

                 while True: # Outer loop allows reloading settings if needed
                     # --- Cancellation Check ---
                     # Use current_task() instead of relying on _run_task which might be None briefly
                     current_task_obj = asyncio.current_task()
                     if current_task_obj and current_task_obj.cancelled():
                          logger.info("Twitch run loop detected cancellation request.")
                          break

                     # --- Load Configuration ---
                     logger.debug("Loading Twitch tokens and settings...")
                     token_data = await load_tokens("twitch")
                     # Load channels specifically using get_setting with a default
                     channels_str = await get_setting("TWITCH_CHANNELS", "")
                     channels_list = [ch.strip().lower() for ch in channels_str.split(',') if ch.strip()]

                     # --- Configuration Validation ---
                     if not token_data or not token_data.get("access_token") or not token_data.get("user_login"):
                         logger.warning("Twitch service disabled: Not authenticated via OAuth. Waiting for login.")
                         event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disabled', message='Not logged in'))
                         await wait_for_settings_update({"twitch_access_token"}) # Wait for login event essentially
                         continue # Re-check config after settings update

                     if not TWITCH_APP_CLIENT_ID: # App Client ID is needed by twitchio
                          logger.error("Twitch service disabled: TWITCH_APP_CLIENT_ID missing in config.")
                          event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disabled', message='App Client ID Missing'))
                          # This is an admin config issue, likely won't be fixed by user settings update
                          await asyncio.sleep(300) # Wait a long time
                          continue

                     if not channels_list:
                         # Default to the authenticated user's own channel if none specified
                         own_channel = token_data["user_login"].lower()
                         logger.warning(f"No TWITCH_CHANNELS configured. Defaulting to bot's own channel: {own_channel}")
                         channels_list = [own_channel]
                         # Optionally save this default back? For now, just use it.
                         # await update_setting("TWITCH_CHANNELS", own_channel)

                     # --- Token Refresh Check ---
                     expires_at = token_data.get("expires_at")
                     if expires_at and expires_at < time.time() + 300: # 5 min buffer
                         logger.info("Twitch token expired or expiring soon. Attempting refresh...")
                         refreshed_data = await refresh_twitch_token(token_data.get("refresh_token"))
                         if refreshed_data:
                              # Need user_id and user_login which aren't returned by refresh
                              refreshed_data['user_id'] = token_data.get('user_id')
                              refreshed_data['user_login'] = token_data.get('user_login')
                              if await save_tokens("twitch", refreshed_data):
                                   token_data = await load_tokens("twitch") # Reload updated tokens
                                   logger.info("Twitch token refreshed and saved successfully.")
                              else:
                                   logger.error("Failed to save refreshed Twitch token. Stopping service.")
                                   event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message='Token refresh save failed'))
                                   _STATE["running"] = False # Stop trying until manual intervention
                                   break # Exit outer loop
                         else:
                             logger.error("Twitch token refresh failed. Requires manual re-authentication.")
                             event_bus.publish(PlatformStatusUpdate(platform='twitch', status='auth_error', message='Token refresh failed'))
                             # Clear potentially invalid token to force re-auth
                             await clear_tokens("twitch")
                             await wait_for_settings_update({"twitch_access_token"}) # Wait for new login
                             continue # Restart outer loop

                     # --- Connection Loop ---
                     _STATE["running"] = True # Set running flag for this configuration attempt
                     attempt = 0
                     MAX_CONNECT_ATTEMPTS = 5
                     bot_instance = None

                     while _STATE.get("running") and attempt < MAX_CONNECT_ATTEMPTS:
                         attempt += 1
                         try:
                             logger.info(f"Attempting Twitch connection (Attempt {attempt}/{MAX_CONNECT_ATTEMPTS})...")
                             event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connecting'))

                             # --- Create and Start Bot Instance ---
                             bot_instance = TwitchBot(
                                 token=token_data["access_token"],
                                 nick=token_data["user_login"],
                                 client_id=TWITCH_APP_CLIENT_ID,
                                 channels=channels_list
                             )
                             _STATE["instance"] = bot_instance # Store current instance

                             # Start the bot. This runs until disconnected or closed.
                             await bot_instance.start()

                             # If start() returns without error, it means connection closed normally/unexpectedly
                             logger.warning("Twitch bot's start() method returned. Connection likely closed.")
                             # Reset attempt count if we were connected and just got disconnected normally
                             if _STATE["connected"]: # If we were previously connected, maybe reset attempts?
                                  # Or just let the loop handle retries as configured below
                                  pass

                         except asyncio.CancelledError:
                             logger.info("Twitch connection attempt cancelled by task.")
                             _STATE["running"] = False # Ensure outer loop exits
                             break # Exit inner connection loop
                         except AuthenticationError as auth_err:
                              logger.critical(f"Twitch Authentication Error on connect (Attempt {attempt}): {auth_err}. Disabling service.")
                              event_bus.publish(PlatformStatusUpdate(platform='twitch', status='auth_error', message="Authentication Failed"))
                              _STATE["running"] = False # Stop retrying with bad credentials
                              await clear_tokens("twitch") # Clear bad tokens
                              break # Exit inner loop
                         except ValueError as val_err: # Catch init errors
                              logger.critical(f"Twitch Bot Initialization Error: {val_err}. Check config/tokens. Disabling.")
                              event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=f"Init Error: {val_err}"))
                              _STATE["running"] = False
                              break # Exit inner loop
                         except Exception as e:
                             logger.error(f"Error during Twitch connection/run (Attempt {attempt}): {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
                             event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=f"Connect/Run Error: {type(e).__name__}"))
                         finally:
                             # --- Cleanup After Each Attempt ---
                             # Ensure bot instance is shut down properly, even if start() failed
                             if bot_instance:
                                 logger.debug(f"Cleaning up bot instance {id(bot_instance)} after connection attempt {attempt}...")
                                 await bot_instance.custom_shutdown()
                             # Clear state references ONLY IF this instance is the one in state
                             if _STATE.get("instance") == bot_instance:
                                  _STATE["instance"] = None
                                  _STATE["connected"] = False
                             bot_instance = None # Clear local var

                         # --- Retry Logic ---
                         if not _STATE.get("running"):
                             logger.info("Twitch running flag turned false, exiting connection loop.")
                             break # Exit inner loop if stop was requested

                         if attempt >= MAX_CONNECT_ATTEMPTS:
                             logger.error("Maximum Twitch connection attempts reached. Disabling until restart/settings change.")
                             event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message='Max connection attempts'))
                             _STATE["running"] = False # Stop trying
                             break # Exit inner loop

                         # Calculate wait time with exponential backoff
                         wait_time = min(5 * (2 ** (attempt - 1)), 60) # e.g., 5s, 10s, 20s, 40s, 60s
                         logger.info(f"Waiting {wait_time}s before Twitch retry (Attempt {attempt + 1})...")
                         try:
                             await asyncio.sleep(wait_time)
                         except asyncio.CancelledError:
                             logger.info("Twitch retry sleep cancelled.")
                             _STATE["running"] = False # Ensure outer loop exits
                             break # Exit inner loop

                     # --- After Inner Connection Loop ---
                     if not _STATE.get("running"):
                         logger.info("Twitch service runner stopping as requested.")
                         break # Exit outer loop

                     # If max attempts were reached and we weren't stopped, wait for settings update
                     if attempt >= MAX_CONNECT_ATTEMPTS:
                          logger.warning("Max attempts reached. Waiting for relevant settings update to retry.")
                          await wait_for_settings_update({
                              "twitch_access_token", "twitch_refresh_token", "TWITCH_CHANNELS"
                          })
                          # Continue outer loop to reload settings and retry connection

                 logger.info("Twitch service runner task finished.")


             async def wait_for_settings_update(relevant_keys: set):
                 """Waits for a SettingsUpdated event affecting relevant keys or task cancellation."""
                 # Create a future that will be resolved when the relevant setting is updated
                 update_future = asyncio.get_running_loop().create_future()
                 listener_task = None

                 async def settings_listener(event: SettingsUpdated):
                     # nonlocal update_future # Not needed with instance/class approach, but needed here
                     if not update_future.done():
                         if any(key in relevant_keys for key in event.keys_updated):
                             logger.info(f"Detected relevant settings update: {event.keys_updated}. Resuming service check.")
                             update_future.set_result(True)

                 # Subscribe the listener
                 event_bus.subscribe(SettingsUpdated, settings_listener)
                 logger.info(f"Waiting for settings update affecting: {relevant_keys}...")

                 try:
                     # Wait for either the settings update or the main task being cancelled
                     # Get the current task (the one running run_twitch_service)
                     current_task = asyncio.current_task()
                     if not current_task: raise RuntimeError("Could not get current task in wait_for_settings_update")

                     # Create a future representing the cancellation of the current task
                     cancel_future = asyncio.Future() # Future to represent cancellation
                     def cancel_callback(task): # Callback when the *current* task is done
                          if not cancel_future.done() and task.cancelled():
                               cancel_future.set_exception(asyncio.CancelledError())
                     current_task.add_done_callback(cancel_callback) # Link to current task's completion

                     done, pending = await asyncio.wait(
                         [update_future, cancel_future], return_when=asyncio.FIRST_COMPLETED
                     )
                     if update_future in done: logger.debug("Settings update received.")
                     elif cancel_future in done: logger.info("Wait for settings update cancelled."); raise asyncio.CancelledError
                     for future in pending: future.cancel()
                 finally:
                     # CRITICAL: Always unsubscribe the listener to prevent leaks
                     event_bus.unsubscribe(SettingsUpdated, settings_listener)
                     logger.debug("Unsubscribed settings listener.")

             # Ensure stop function uses the global _run_task
             async def stop_twitch_service():
                 """Stops the Twitch service task gracefully."""
                 global _STATE, _run_task
                 logger.info("Stop requested for Twitch service.")
                 _STATE["running"] = False # Signal the run loop and bot tasks to stop

                 # Shutdown the bot instance first
                 bot_instance = _STATE.get("instance")
                 if bot_instance:
                     logger.info("Requesting shutdown of active TwitchBot instance...")
                     await bot_instance.custom_shutdown() # Call the graceful shutdown
                     if _STATE.get("instance") == bot_instance: # Check if it wasn't replaced meanwhile
                          _STATE["instance"] = None # Clear instance ref after shutdown

                 # Cancel the main service task using the global reference
                 current_task = _run_task
                 if current_task and not current_task.done():
                     if not current_task.cancelling():
                         logger.info("Cancelling main Twitch service task...")
                         current_task.cancel()
                         try:
                             # Wait for the task cancellation to complete
                             await asyncio.wait_for(current_task, timeout=5.0)
                             logger.info("Main Twitch service task cancellation confirmed.")
                         except asyncio.CancelledError:
                             logger.info("Main Twitch service task confirmed cancelled (exception caught).")
                         except asyncio.TimeoutError:
                              logger.warning("Timeout waiting for main Twitch service task to cancel.")
                         except Exception as e:
                             logger.error(f"Error waiting for cancelled Twitch service task: {e}", exc_info=True)
                     else:
                         logger.info("Main Twitch service task already cancelling.")
                 else:
                     logger.info("No active Twitch service task found to cancel.")

                 # Clear global task reference
                 _run_task = None
                 _STATE["task"] = None # Also clear state's task reference
                 _STATE["connected"] = False # Ensure connected state is false

                 # Unsubscribe settings handler *after* ensuring task is stopped
                 # Ensure the specific handler function is referenced
                 try:
                     event_bus.unsubscribe(SettingsUpdated, handle_settings_update_restart)
                 except ValueError:
                     logger.debug("Settings handler already unsubscribed or never subscribed.")

                 logger.info("Twitch service stopped.")
                 event_bus.publish(PlatformStatusUpdate(platform='twitch', status='stopped')) # Publish final stopped status

             async def handle_settings_update_restart(event: SettingsUpdated):
                 """Restarts the Twitch service if relevant settings changed."""
                 # Define keys that necessitate a restart
                 relevant_keys = {
                     "twitch_access_token", "twitch_refresh_token", # Auth tokens
                     "twitch_user_login", "twitch_user_id",         # User identity
                     "TWITCH_CHANNELS"                              # Channels to join
                     # App Client ID/Secret changes require full app restart, not handled here.
                 }
                 # Check if any updated key is relevant
                 if any(key in relevant_keys for key in event.keys_updated):
                     logger.info(f"Relevant Twitch settings updated ({event.keys_updated}). Triggering service restart...")
                     # Publish a control event for main.py's handler to manage the restart
                     event_bus.publish(ServiceControl(service_name="twitch", command="restart"))

             def start_twitch_service_task() -> asyncio.Task | None:
                 """Creates and starts the background task for the Twitch service."""
                 global _STATE, _run_task
                 # Prevent starting if already running
                 if _run_task and not _run_task.done():
                     logger.warning("Twitch service task is already running or starting.")
                     return _run_task

                 logger.info("Creating and starting background task for Twitch service.")
                 # Subscribe to settings updates *before* starting the task
                 event_bus.subscribe(SettingsUpdated, handle_settings_update_restart)
                 # Create the task
                 _run_task = asyncio.create_task(run_twitch_service(), name="TwitchServiceRunner")
                 _STATE["task"] = _run_task # Store task reference in state as well

                 return _run_task

             # --- File: app/services/twitch_service.py --- END ---
             """,
                     "app/services/youtube_service.py": r"""# Generated by install_fosbot.py
             # --- File: app/services/youtube_service.py --- START ---
             import logging
             import asyncio
             import time
             from google.oauth2.credentials import Credentials
             from google.auth.transport.requests import Request as GoogleAuthRequest # Standard transport
             from google_auth_oauthlib.flow import InstalledAppFlow # If needed for manual auth, but web flow preferred
             from googleapiclient.discovery import build, Resource # For type hinting
             from googleapiclient.errors import HttpError
             import httpx # Use httpx for refresh
             from datetime import datetime, timezone, timedelta # Use timezone-aware datetimes
             from typing import Dict, List, Optional, Any, Coroutine

             # Core imports
             from app.core.event_bus import event_bus
             from app.events import (
                 PlatformStatusUpdate, SettingsUpdated, ServiceControl, BotResponseToSend,
                 InternalChatMessage, ChatMessageReceived, BotResponse, LogMessage
             )
             from app.core.json_store import load_tokens, save_tokens, get_setting, clear_tokens
             # Import App Owner Credentials from config
             from app.core.config import logger, YOUTUBE_APP_CLIENT_ID, YOUTUBE_APP_CLIENT_SECRET

             # --- Constants ---
             YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
             YOUTUBE_API_SERVICE_NAME = "youtube"
             YOUTUBE_API_VERSION = "v3"
             # Scopes required for reading chat and potentially posting
             YOUTUBE_SCOPES = [
                 "https://www.googleapis.com/auth/youtube.readonly", # Needed to list broadcasts/chats
                 "https://www.googleapis.com/auth/youtube.force-ssl", # Often needed for chat operations
                 "https://www.googleapis.com/auth/youtube" # Needed to insert chat messages
             ]

             # --- Module State ---
             _STATE = {
                 "task": None,
                 "running": False,
                 "connected": False, # Represents connection to a specific live chat
                 "live_chat_id": None,
                 "youtube_client": None, # Stores the authorized googleapiclient resource
                 "user_login": None,
                 "user_id": None,
                 "last_poll_time": 0.0,
                 "next_page_token": None
             }
             _run_task: asyncio.Task | None = None

             # --- Helper Functions ---
             async def refresh_youtube_token(refresh_token: str) -> Optional[Dict[str, Any]]:
                 """Refreshes the YouTube OAuth token using httpx."""
                 if not refresh_token:
                     logger.error("Cannot refresh YouTube token: No refresh token provided.")
                     return None
                 if not YOUTUBE_APP_CLIENT_ID or not YOUTUBE_APP_CLIENT_SECRET:
                     logger.error("Cannot refresh YouTube token: App credentials missing.")
                     return None

                 logger.info("Attempting to refresh YouTube OAuth token...")
                 token_params = {
                     "grant_type": "refresh_token",
                     "refresh_token": refresh_token,
                     "client_id": YOUTUBE_APP_CLIENT_ID,
                     "client_secret": YOUTUBE_APP_CLIENT_SECRET
                 }
                 async with httpx.AsyncClient(timeout=15.0) as client:
                     try:
                         response = await client.post(YOUTUBE_TOKEN_URL, data=token_params)
                         response.raise_for_status()
                         token_data = response.json()
                         logger.info("YouTube token refreshed successfully.")
                         # Prepare data for save_tokens
                         return {
                             "access_token": token_data.get("access_token"),
                             "refresh_token": refresh_token, # Refresh token usually doesn't change unless revoked
                             "expires_in": token_data.get("expires_in"),
                             "scope": token_data.get("scope", "").split(),
                         }
                     except httpx.TimeoutException:
                          logger.error("Timeout refreshing YouTube token.")
                          return None
                     except httpx.HTTPStatusError as e:
                         logger.error(f"HTTP error refreshing YouTube token: {e.response.status_code} - {e.response.text}")
                         if e.response.status_code in [400, 401]:
                              logger.error("Refresh token may be invalid or revoked.")
                              # Consider clearing the token?
                         return None
                     except Exception as e:
                         logger.exception(f"Unexpected error refreshing YouTube token: {e}")
                         return None

             async def build_youtube_client_async(credentials: Credentials) -> Optional[Resource]:
                  """Builds the YouTube API client resource asynchronously using run_in_executor."""
                  loop = asyncio.get_running_loop()
                  try:
                       # googleapiclient.discovery.build is synchronous/blocking
                       youtube = await loop.run_in_executor(
                            None, # Use default thread pool executor
                            lambda: build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
                       )
                       logger.info("YouTube API client built successfully.")
                       return youtube
                  except Exception as e:
                       logger.error(f"Failed to build YouTube API client: {e}", exc_info=True)
                       return None

             async def get_active_live_chat_id(youtube: Resource) -> Optional[str]:
                 """Finds the liveChatId for the channel's active broadcast asynchronously."""
                 if not youtube:
                     logger.error("Cannot get live chat ID: YouTube client is not available.")
                     return None
                 try:
                     logger.debug("Fetching active live broadcasts...")
                     loop = asyncio.get_running_loop()
                     request = youtube.liveBroadcasts().list(
                         part="snippet",
                         broadcastStatus="active",
                         broadcastType="all",
                         mine=True,
                         maxResults=1
                     )
                     response = await loop.run_in_executor(None, request.execute)

                     if not response or not response.get("items"):
                         logger.info("No active YouTube live broadcasts found for this account.")
                         return None

                     live_broadcast = response["items"][0]
                     snippet = live_broadcast.get("snippet", {})
                     live_chat_id = snippet.get("liveChatId")
                     title = snippet.get("title", "Unknown Broadcast")

                     if live_chat_id:
                         logger.info(f"Found active liveChatId: {live_chat_id} for broadcast '{title}'")
                         return live_chat_id
                     else:
                         # This can happen if the stream is active but chat is disabled or not yet fully initialized
                         logger.warning(f"Active broadcast found ('{title}'), but it has no liveChatId yet.")
                         return None

                 except HttpError as e:
                     logger.error(f"YouTube API error fetching broadcasts/chat ID: {e.resp.status} - {e.content}")
                     if e.resp.status == 403:
                          logger.error("Permission denied fetching YouTube broadcasts. Check API scopes/enablement.")
                     return None
                 except Exception as e:
                     logger.exception(f"Unexpected error fetching YouTube live chat ID: {e}")
                     return None

             async def poll_youtube_chat(youtube: Resource, live_chat_id: str):
                 """Polls the specified YouTube live chat for new messages."""
                 global _STATE # Need to access/modify state like next_page_token
                 logger.info(f"Starting polling for YouTube liveChatId: {live_chat_id}")
                 error_count = 0
                 MAX_ERRORS = 5
                 ERROR_BACKOFF_BASE = 5 # Seconds

                 while _STATE.get("running") and _STATE.get("live_chat_id") == live_chat_id:
                     try:
                         loop = asyncio.get_running_loop()
                         request = youtube.liveChatMessages().list(
                             liveChatId=live_chat_id,
                             part="id,snippet,authorDetails",
                             maxResults=200,
                             pageToken=_STATE.get("next_page_token") # Use state's token
                         )
                         # response = await loop.run_in_executor(None, request.execute)
                         response = request.execute() # Blocking call

                         if response:
                              items = response.get("items", [])
                              if items:
                                   logger.debug(f"Received {len(items)} YouTube chat messages.")
                                   for item in items:
                                        snippet = item.get("snippet", {})
                                        author = item.get("authorDetails", {})
                                        msg_text = snippet.get("displayMessage")
                                        published_at_str = snippet.get("publishedAt")

                                        if msg_text:
                                             timestamp_iso = published_at_str or datetime.now(timezone.utc).isoformat()
                                             internal_msg = InternalChatMessage(
                                                  platform="youtube",
                                                  channel=author.get("channelId", live_chat_id),
                                                  user=author.get("displayName", "Unknown User"),
                                                  text=msg_text,
                                                  timestamp=timestamp_iso,
                                                  user_id=author.get("channelId"),
                                                  display_name=author.get("displayName"),
                                                  message_id=item.get("id"),
                                                  raw_data={'authorDetails': author, 'snippet': snippet}
                                             )
                                             event_bus.publish(ChatMessageReceived(message=internal_msg))
                                             logger.debug(f"YouTube <{live_chat_id}> {author.get('displayName')}: {msg_text}")

                              _STATE["next_page_token"] = response.get("nextPageToken")
                              polling_interval_ms = response.get("pollingIntervalMillis", 5000)
                              wait_seconds = max(polling_interval_ms / 1000.0, 2.0)

                              logger.debug(f"YouTube poll successful. Waiting {wait_seconds}s. Next page: {'Yes' if _STATE['next_page_token'] else 'No'}")
                              error_count = 0 # Reset error count
                              await asyncio.sleep(wait_seconds)
                         else:
                              logger.warning("YouTube chat poll returned empty/invalid response.")
                              await asyncio.sleep(10)

                     except HttpError as e:
                         error_count += 1
                         logger.error(f"YouTube API error during chat polling (Attempt {error_count}/{MAX_ERRORS}): {e.resp.status} - {e.content}")
                         event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message=f"Chat poll failed: {e.resp.status}"))

                         if e.resp.status in [403, 404]: # Forbidden or Not Found often means chat ended
                             logger.warning(f"YouTube chat polling failed ({e.resp.status}). Chat likely ended or permissions lost.")
                             _STATE["connected"] = False
                             _STATE["live_chat_id"] = None
                             event_bus.publish(PlatformStatusUpdate(platform='youtube', status='disconnected', message=f"Chat ended/unavailable ({e.resp.status})"))
                             break # Exit polling loop for this chat_id

                         if error_count >= MAX_ERRORS:
                              logger.error("Max YouTube polling errors reached. Stopping polling.")
                              _STATE["connected"] = False
                              event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message="Max polling errors"))
                              break # Exit polling loop

                         wait_time = ERROR_BACKOFF_BASE * (2 ** (error_count - 1)) # Exponential backoff
                         logger.info(f"Waiting {wait_time}s before retrying YouTube poll...")
                         await asyncio.sleep(wait_time)

                     except asyncio.CancelledError:
                          logger.info("YouTube chat polling task cancelled.")
                          break # Exit loop
                     except Exception as e:
                         error_count += 1
                         logger.exception(f"Unexpected error polling YouTube chat (Attempt {error_count}/{MAX_ERRORS}): {e}")
                         event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message=f"Unexpected Poll Error: {type(e).__name__}"))
                         if error_count >= MAX_ERRORS:
                              logger.error("Max YouTube polling errors reached (unexpected). Stopping polling.")
                              break
                         wait_time = ERROR_BACKOFF_BASE * (2 ** (error_count - 1))
                         await asyncio.sleep(wait_time)

                 logger.info("YouTube chat polling loop finished.")
                 _STATE["connected"] = False # Ensure state reflects polling stopped

             async def handle_youtube_response(event: BotResponseToSend):
                 """Handles sending messages to YouTube live chat."""
                 if event.response.target_platform != "youtube":
                     return

                 youtube_client = _STATE.get("youtube_client")
                 live_chat_id = _STATE.get("live_chat_id")
                 if not youtube_client or not live_chat_id or not _STATE.get("connected"):
                     logger.error(f"Cannot send YouTube response: Client/ChatID not available or not connected. State: {_STATE}")
                     return

                 logger.info(f"Attempting to send YouTube message to {live_chat_id}: {event.response.text[:50]}...")
                 try:
                     loop = asyncio.get_running_loop()
                     request = youtube_client.liveChatMessages().insert(
                         part="snippet",
                         body={
                             "snippet": {
                                 "liveChatId": live_chat_id,
                                 "type": "textMessageEvent",
                                 "textMessageDetails": {"messageText": event.response.text}
                             }
                         }
                     )
                     # await loop.run_in_executor(None, request.execute)
                     request.execute() # Blocking call
                     logger.info(f"Successfully sent YouTube message to {live_chat_id}.")

                 except HttpError as e:
                     logger.error(f"Error sending YouTube live chat message: {e.resp.status} - {e.content}")
                     event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message=f"Send failed: {e.resp.status}"))
                     if e.resp.status == 403: # Forbidden might mean chat ended or bot banned/timed out
                          logger.warning("YouTube send failed (403) - Chat possibly ended or bot lacks permission.")
                          # Consider stopping polling if sends consistently fail with 403
                          # stop_youtube_service() # Maybe too aggressive?
                 except Exception as e:
                     logger.exception(f"Unexpected error sending YouTube message: {e}")
                     event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message=f"Send Exception: {type(e).__name__}"))


             # --- Main Service Runner ---
             async def run_youtube_service():
                 """Main loop for the YouTube service."""
                 global _STATE, _run_task
                 logger.info("YouTube service runner task started.")

                 while True: # Outer loop for re-checking auth/broadcast state
                     current_task_obj = asyncio.current_task()
                     if current_task_obj and current_task_obj.cancelled():
                         logger.info("YouTube run loop detected cancellation request.")
                         break

                     # --- Load Auth Tokens ---
                     logger.debug("Loading YouTube tokens...")
                     token_data = await load_tokens("youtube")

                     if not token_data or not token_data.get("access_token") or not token_data.get("user_id"):
                         logger.warning("YouTube service disabled: Not authenticated. Waiting for login.")
                         event_bus.publish(PlatformStatusUpdate(platform='youtube', status='disabled', message='Not logged in'))
                         await wait_for_settings_update({"youtube_access_token"})
                         continue # Re-check config

                     _STATE["user_id"] = token_data["user_id"]
                     _STATE["user_login"] = token_data.get("user_login", "Unknown YT User")

                     # --- Token Refresh Check ---
                     expires_at = token_data.get("expires_at")
                     if expires_at and expires_at < time.time() + 300:
                         logger.info("YouTube token expired or expiring soon. Attempting refresh...")
                         refreshed_data = await refresh_youtube_token(token_data.get("refresh_token"))
                         if refreshed_data:
                              # Merge user info back into refreshed data before saving
                              refreshed_data['user_id'] = _STATE["user_id"]
                              refreshed_data['user_login'] = _STATE["user_login"]
                              if await save_tokens("youtube", refreshed_data):
                                   token_data = await load_tokens("youtube") # Reload
                                   logger.info("YouTube token refreshed and saved successfully.")
                              else:
                                   logger.error("Failed to save refreshed YouTube token. Disabling service.")
                                   event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message='Token refresh save failed'))
                                   _STATE["running"] = False; break # Stop trying
                         else:
                             logger.error("YouTube token refresh failed. Requires manual re-authentication.")
                             event_bus.publish(PlatformStatusUpdate(platform='youtube', status='auth_error', message='Token refresh failed'))
                             await clear_tokens("youtube") # Clear bad tokens
                             await wait_for_settings_update({"youtube_access_token"}) # Wait for new login
                             continue # Restart outer loop

                     # --- Build API Client ---
                     credentials = Credentials(
                         token=token_data["access_token"],
                         refresh_token=token_data.get("refresh_token"),
                         token_uri=YOUTUBE_TOKEN_URL,
                         client_id=YOUTUBE_APP_CLIENT_ID,
                         client_secret=YOUTUBE_APP_CLIENT_SECRET,
                         scopes=token_data.get("scopes", YOUTUBE_SCOPES) # Use stored scopes if available
                     )
                     # Ensure credentials are valid/refreshed before building client (optional but good practice)
                     try:
                          # credentials.refresh(GoogleAuthRequest()) # Synchronous refresh if needed immediately
                          pass # Assume token is valid or refresh handled above/by google client lib implicitly
                     except Exception as cred_err:
                          logger.error(f"Error validating/refreshing credentials before build: {cred_err}")
                          # Handle potential token invalidation
                          event_bus.publish(PlatformStatusUpdate(platform='youtube', status='auth_error', message='Credential validation failed'))
                          await clear_tokens("youtube")
                          await wait_for_settings_update({"youtube_access_token"})
                          continue

                     youtube_client = await build_youtube_client_async(credentials)
                     if not youtube_client:
                          logger.error("Failed to build YouTube client. Disabling service temporarily.")
                          event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message='Client build failed'))
                          await asyncio.sleep(60); continue # Wait and retry outer loop

                     _STATE["youtube_client"] = youtube_client
                     _STATE["running"] = True # Set running flag for this attempt cycle
                     _STATE["live_chat_id"] = None # Reset live chat ID
                     _STATE["connected"] = False