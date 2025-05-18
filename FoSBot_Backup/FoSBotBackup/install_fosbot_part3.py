
                 event_bus.subscribe(SettingsUpdated, settings_listener)
                 logger.info(f"Waiting for YouTube settings update affecting: {relevant_keys}...")

                 try:
                     current_task = asyncio.current_task()
                     if not current_task: raise RuntimeError("Could not get current task in wait_for_settings_update (YouTube)")
                     cancel_future = asyncio.Future() # Create a future to represent cancellation
                     def cancel_callback(task): # Callback when the *current* task is done
                          if not cancel_future.done() and task.cancelled():
                               cancel_future.set_exception(asyncio.CancelledError())
                     current_task.add_done_callback(cancel_callback)

                     done, pending = await asyncio.wait(
                         [update_future, cancel_future], return_when=asyncio.FIRST_COMPLETED
                     )
                     if update_future in done: logger.debug("YouTube settings update received.")
                     elif cancel_future in done: logger.info("Wait for YouTube settings update cancelled."); raise asyncio.CancelledError
                     for future in pending: future.cancel()
                 finally:
                     event_bus.unsubscribe(SettingsUpdated, settings_listener)
                     logger.debug("Unsubscribed YouTube settings listener.")


             # --- Stop and Start Functions ---
             async def stop_youtube_service():
                 """Stops the YouTube service task gracefully."""
                 global _STATE, _run_task
                 logger.info("Stop requested for YouTube service.")
                 _STATE["running"] = False # Signal loops to stop
                 _STATE["connected"] = False # Mark as disconnected

                 # Cancel the main service task
                 current_task = _run_task
                 if current_task and not current_task.done():
                     if not current_task.cancelling():
                         logger.info("Cancelling main YouTube service task...")
                         current_task.cancel()
                         try:
                             await asyncio.wait_for(current_task, timeout=5.0)
                             logger.info("Main YouTube service task cancellation confirmed.")
                         except asyncio.CancelledError:
                             logger.info("Main YouTube service task confirmed cancelled (exception caught).")
                         except asyncio.TimeoutError:
                              logger.warning("Timeout waiting for main YouTube service task to cancel.")
                         except Exception as e:
                             logger.error(f"Error waiting for cancelled YouTube service task: {e}", exc_info=True)
                     else:
                          logger.info("Main YouTube service task already cancelling.")
                 else:
                     logger.info("No active YouTube service task found to cancel.")

                 # Clear global task reference and state
                 _run_task = None
                 _STATE["task"] = None
                 _STATE["youtube_client"] = None # Clear client reference
                 _STATE["live_chat_id"] = None
                 _STATE["next_page_token"] = None

                 # Unsubscribe handlers
                 try: event_bus.unsubscribe(SettingsUpdated, handle_settings_update_restart)
                 except ValueError: pass
                 try: event_bus.unsubscribe(BotResponseToSend, handle_youtube_response)
                 except ValueError: pass

                 logger.info("YouTube service stopped.")
                 event_bus.publish(PlatformStatusUpdate(platform='youtube', status='stopped'))

             async def handle_settings_update_restart(event: SettingsUpdated):
                 """Restarts the YouTube service if relevant settings changed."""
                 relevant_keys = {"youtube_access_token", "youtube_refresh_token"} # Add others if needed
                 if any(key in relevant_keys for key in event.keys_updated):
                     logger.info(f"Relevant YouTube settings updated ({event.keys_updated}). Triggering service restart...")
                     event_bus.publish(ServiceControl(service_name="youtube", command="restart"))

             def start_youtube_service_task() -> asyncio.Task | None:
                 """Creates and starts the background task for the YouTube service."""
                 global _STATE, _run_task
                 if _run_task and not _run_task.done():
                     logger.warning("YouTube service task is already running or starting.")
                     return _run_task

                 logger.info("Creating and starting background task for YouTube service.")
                 event_bus.subscribe(SettingsUpdated, handle_settings_update_restart)
                 event_bus.subscribe(BotResponseToSend, handle_youtube_response) # Subscribe response handler
                 _run_task = asyncio.create_task(run_youtube_service(), name="YouTubeServiceRunner")
                 _STATE["task"] = _run_task
                 return _run_task

             # --- File: app/services/youtube_service.py --- END ---
             """,
                     "app/services/x_service.py": r"""# Generated by install_fosbot.py
             # --- File: app/services/x_service.py --- START ---
             import logging
             import asyncio
             import time
             import tweepy # Use the tweepy library
             from typing import Dict, List, Optional, Any, Coroutine

             # Core imports
             from app.core.event_bus import event_bus
             from app.events import (
                 PlatformStatusUpdate, SettingsUpdated, ServiceControl, BotResponseToSend,
                 InternalChatMessage, ChatMessageReceived, BotResponse, LogMessage
             )
             from app.core.json_store import load_tokens, save_tokens, get_setting # Use get_setting for monitor query
             # Import App Owner Credentials from config
             from app.core.config import logger, X_APP_CLIENT_ID, X_APP_CLIENT_SECRET
             from datetime import datetime, timezone # Use timezone-aware datetimes

             # --- Constants ---
             # X/Twitter API v2 endpoints (tweepy handles these)
             # Define reasonable poll interval for mentions/stream
             DEFAULT_POLL_INTERVAL = 65 # Seconds (slightly above 15 requests per 15 mins limit for mentions endpoint)

             # --- Module State ---
             _STATE = {
                 "task": None,
                 "stream_task": None, # Task for the streaming client if used
                 "client": None,     # Authenticated tweepy API client
                 "running": False,
                 "connected": False, # Represents successful client init and potentially stream connection
                 "user_login": None,
                 "user_id": None,
                 "monitor_query": None # Query to monitor (e.g., #hashtag, @mention) - Not currently used by polling
             }
             _run_task: asyncio.Task | None = None

             # --- Tweepy Streaming Client (Placeholder - Future Enhancement) ---
             # class FoSBotXStreamClient(tweepy.StreamingClient):
             #     async def on_tweet(self, tweet): # Make handlers async
             #         logger.info(f"Received Tweet via stream: {tweet.id} - {tweet.text}")
             #         # Process tweet, create InternalChatMessage, publish ChatMessageReceived
             #     async def on_connect(self): # Make async
             #         logger.info("X StreamingClient connected.")
             #         _STATE["connected"] = True
             #         event_bus.publish(PlatformStatusUpdate(platform='x', status='connected', message='Stream connected'))
             #     async def on_disconnect(self): # Make async
             #         logger.warning("X StreamingClient disconnected.")
             #         _STATE["connected"] = False
             #         event_bus.publish(PlatformStatusUpdate(platform='x', status='disconnected', message='Stream disconnected'))
             #     async def on_error(self, status_code): # Make async
             #         logger.error(f"X StreamingClient error: {status_code}")
             #         event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f'Stream error: {status_code}'))
             #         if status_code == 429: await asyncio.sleep(900)
             #         # return True # Returning True might prevent auto-reconnect? Check tweepy docs.
             #     async def on_exception(self, exception): # Make async
             #         logger.exception(f"X StreamingClient exception: {exception}")
             #         event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f'Stream exception: {type(exception).__name__}'))


             # --- Helper Functions ---
             async def build_x_client(token_data: dict) -> Optional[tweepy.Client]:
                 """Builds an authenticated Tweepy API client."""
                 if not all([X_APP_CLIENT_ID, X_APP_CLIENT_SECRET, token_data.get("access_token"), token_data.get("access_token_secret")]):
                     logger.error("Cannot build X client: Missing app credentials or user tokens.")
                     return None
                 try:
                     client = tweepy.Client(
                         consumer_key=X_APP_CLIENT_ID,
                         consumer_secret=X_APP_CLIENT_SECRET,
                         access_token=token_data["access_token"],
                         access_token_secret=token_data["access_token_secret"],
                         wait_on_rate_limit=True # Let tweepy handle basic rate limit waiting
                     )
                     # Verify authentication by getting self
                     loop = asyncio.get_running_loop()
                     user_response = await loop.run_in_executor(None, lambda: client.get_me(user_fields=["id", "username"]))
                     if user_response.data:
                          _STATE["user_id"] = str(user_response.data.id)
                          _STATE["user_login"] = user_response.data.username
                          logger.info(f"X client authenticated successfully for @{_STATE['user_login']} (ID: {_STATE['user_id']})")
                          return client
                     else:
                          error_detail = f"Errors: {user_response.errors}" if hasattr(user_response, 'errors') and user_response.errors else "No data returned."
                          logger.error(f"Failed to verify X client authentication. {error_detail}")
                          event_bus.publish(PlatformStatusUpdate(platform='x', status='auth_error', message=f"Verification failed: {error_detail}"))
                          return None
                 except tweepy.errors.TweepyException as e:
                     logger.error(f"Tweepy error building client or verifying auth: {e}")
                     status_code = getattr(e, 'response', None) and getattr(e.response, 'status_code', None)
                     if status_code == 401: # Unauthorized
                          event_bus.publish(PlatformStatusUpdate(platform='x', status='auth_error', message=f"Auth failed (401): {e}"))
                          # Clear potentially invalid tokens
                          await clear_tokens("x")
                     else:
                          event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f"Client build failed: {e}"))
                     return None
                 except Exception as e:
                     logger.exception(f"Unexpected error building X client: {e}")
                     event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f"Client build exception: {type(e).__name__}"))
                     return None

             async def handle_x_response(event: BotResponseToSend):
                 """Handles sending tweets as the authenticated user."""
                 if event.response.target_platform != "x":
                     return
                 client = _STATE.get("client")
                 if not client or not _STATE.get("connected"):
                     logger.error("Cannot send tweet: X client not available or not connected.")
                     # Optionally queue the message or notify user of failure
                     return

                 text_to_send = event.response.text
                 # Twitter limits tweets to 280 characters
                 if len(text_to_send) > 280:
                      logger.warning(f"Tweet too long ({len(text_to_send)} chars), truncating to 280: {text_to_send[:50]}...")
                      text_to_send = text_to_send[:280]

                 logger.info(f"Attempting to send Tweet: {text_to_send[:100]}...")

                 try:
                     # Use asyncio.to_thread for the synchronous tweepy call
                     loop = asyncio.get_running_loop()
                     response = await loop.run_in_executor(None, lambda: client.create_tweet(text=text_to_send))

                     if response.data:
                         tweet_id = response.data.get('id')
                         logger.info(f"Successfully sent Tweet (ID: {tweet_id}): {text_to_send[:50]}...")
                     else:
                          error_detail = f"Errors: {response.errors}" if hasattr(response, 'errors') and response.errors else "No data returned."
                          logger.error(f"Failed to send Tweet. {error_detail}")
                          event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f"Send Tweet failed: {error_detail}"))

                 except tweepy.errors.TweepyException as e:
                     logger.error(f"Tweepy error sending Tweet: {e}")
                     event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f"Send Tweet Error: {e}"))
                 except Exception as e:
                     logger.exception(f"Unexpected error sending Tweet: {e}")
                     event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f"Send Tweet Exception: {type(e).__name__}"))


             # --- Mention Polling (Primary Method for Phase 1) ---
             async def poll_x_mentions(client: tweepy.Client):
                 """Polls for mentions of the authenticated user."""
                 if not _STATE.get("user_id"):
                     logger.error("Cannot poll mentions: User ID not available.")
                     return

                 logger.info(f"Starting mention polling for X user @{_STATE.get('user_login')}")
                 since_id = None
                 error_count = 0
                 MAX_ERRORS = 5
                 ERROR_BACKOFF_BASE = 15 # Seconds

                 # Fetch initial since_id from storage? Or start fresh each time? Start fresh for simplicity.
                 # Alternatively, fetch the user's latest tweet ID on start to avoid fetching old mentions?

                 while _STATE.get("running"):
                     try:
                         logger.debug(f"Polling X mentions (since_id: {since_id})...")
                         # Use asyncio.to_thread for the synchronous tweepy call
                         loop = asyncio.get_running_loop()
                         mentions_response = await loop.run_in_executor(
                              None,
                              lambda: client.get_users_mentions(
                                   id=_STATE["user_id"],
                                   since_id=since_id,
                                   expansions=["author_id"],
                                   tweet_fields=["created_at", "conversation_id", "in_reply_to_user_id"],
                                   user_fields=["username", "name"]
                              )
                         )

                         if mentions_response.errors:
                              logger.error(f"Errors received from X mentions endpoint: {mentions_response.errors}")
                              # Handle specific errors like rate limits if needed
                              if any("Rate limit exceeded" in str(err) for err in mentions_response.errors):
                                   wait_time = DEFAULT_POLL_INTERVAL * 2 # Wait longer if rate limited
                                   logger.warning(f"X Mentions rate limit likely hit, waiting {wait_time}s...")
                                   await asyncio.sleep(wait_time)
                                   continue # Skip rest of loop iteration

                         includes = mentions_response.includes or {}
                         users = {user.id: user for user in includes.get("users", [])}

                         newest_id_processed = since_id # Track the newest ID processed in this batch

                         if mentions_response.data:
                             logger.info(f"Found {len(mentions_response.data)} new mentions.")
                             # Process in chronological order (API returns reverse-chrono)
                             for tweet in reversed(mentions_response.data):
                                 author_id = tweet.author_id
                                 author = users.get(author_id)
                                 author_username = author.username if author else "unknown_user"
                                 author_display_name = author.name if author else None

                                 logger.debug(f"X Mention <@{_STATE['user_login']}> @{author_username}: {tweet.text}")
                                 timestamp_iso = tweet.created_at.isoformat() if tweet.created_at else datetime.now(timezone.utc).isoformat()

                                 internal_msg = InternalChatMessage(
                                     platform='x',
                                     channel=_STATE['user_login'], # Mentions are directed to the user
                                     user=author_username, # Use the @ handle
                                     text=tweet.text,
                                     timestamp=timestamp_iso,
                                     user_id=str(author_id),
                                     display_name=author_display_name,
                                     message_id=str(tweet.id),
                                     raw_data={'tweet': tweet.data, 'author': author.data if author else None} # Store basic tweet data
                                 )
                                 event_bus.publish(ChatMessageReceived(message=internal_msg))
                                 # Update newest_id_processed to the ID of the newest tweet processed
                                 newest_id_processed = max(newest_id_processed or 0, tweet.id)

                             # Update since_id *after* processing all tweets in the batch
                             if newest_id_processed and newest_id_processed != since_id:
                                  logger.debug(f"Updating since_id from {since_id} to {newest_id_processed}")
                                  since_id = newest_id_processed

                             error_count = 0 # Reset errors on successful poll with data
                         else:
                              logger.debug("No new X mentions found.")
                              error_count = 0 # Reset errors on successful empty poll

                         # Wait for the poll interval
                         await asyncio.sleep(DEFAULT_POLL_INTERVAL)

                     except tweepy.errors.TweepyException as e:
                          error_count += 1
                          logger.error(f"Tweepy error polling mentions (Attempt {error_count}/{MAX_ERRORS}): {e}")
                          status_code = getattr(e, 'response', None) and getattr(e.response, 'status_code', None)
                          # Handle specific HTTP errors
                          if status_code == 401: # Unauthorized
                               logger.error("X Authentication error (401) during mention poll. Tokens might be invalid.")
                               event_bus.publish(PlatformStatusUpdate(platform='x', status='auth_error', message=f"Mention Poll Auth Error (401)"))
                               # Stop polling if auth fails persistently
                               _STATE["running"] = False
                               await clear_tokens("x")
                               break
                          elif status_code == 429: # Rate limit
                               wait_time = DEFAULT_POLL_INTERVAL * 3 # Wait longer
                               logger.warning(f"X Mentions rate limit hit (429), waiting {wait_time}s...")
                               event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message="Rate limit hit"))
                               await asyncio.sleep(wait_time)
                               continue # Continue loop after waiting
                          else:
                                event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f"Mention Poll Error: {e}"))

                          if error_count >= MAX_ERRORS:
                               logger.error("Max mention poll errors reached. Stopping polling.")
                               break
                          wait_time = ERROR_BACKOFF_BASE * (2 ** (error_count - 1)) # Exponential backoff
                          await asyncio.sleep(wait_time)
                     except asyncio.CancelledError:
                         logger.info("X mention polling task cancelled.")
                         break
                     except Exception as e:
                         error_count += 1
                         logger.exception(f"Unexpected error polling X mentions (Attempt {error_count}/{MAX_ERRORS}): {e}")
                         event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message=f"Unexpected Poll Error: {type(e).__name__}"))
                         if error_count >= MAX_ERRORS:
                              logger.error("Max mention poll errors reached (unexpected). Stopping polling.")
                              break
                         wait_time = ERROR_BACKOFF_BASE * (2 ** (error_count - 1))
                         await asyncio.sleep(wait_time)

                 logger.info("X mention polling loop finished.")
                 _STATE["connected"] = False # Mark as disconnected if polling stops

             # --- Main Service Runner ---
             async def run_x_service():
                 """Main loop for the X/Twitter service."""
                 global _STATE, _run_task
                 logger.info("X service runner task started.")

                 while True: # Outer loop for re-authentication/restart
                     current_task_obj = asyncio.current_task()
                     if current_task_obj and current_task_obj.cancelled():
                         logger.info("X run loop detected cancellation request.")
                         break

                     # --- Load Auth Tokens ---
                     logger.debug("Loading X tokens...")
                     token_data = await load_tokens("x")

                     if not token_data or not token_data.get("access_token") or not token_data.get("access_token_secret"):
                         logger.warning("X service disabled: Not authenticated via OAuth. Waiting for login.")
                         event_bus.publish(PlatformStatusUpdate(platform='x', status='disabled', message='Not logged in'))
                         await wait_for_settings_update({"x_access_token"}) # Wait for login
                         continue # Re-check config

                     # --- Build Client and Start Polling ---
                     _STATE["running"] = True # Set running flag for this attempt cycle
                     x_client = await build_x_client(token_data)

                     if x_client:
                         _STATE["client"] = x_client
                         _STATE["connected"] = True # Mark as connected after successful client build & auth verify
                         event_bus.publish(PlatformStatusUpdate(platform='x', status='connected', message=f"Authenticated as @{_STATE['user_login']}"))

                         # Start the polling task
                         await poll_x_mentions(x_client)

                         # If poll_x_mentions returns, it means polling stopped due to error or cancellation
                         logger.warning("X mention polling has stopped. Will attempt to restart if service still running.")
                         _STATE["connected"] = False
                         _STATE["client"] = None
                         # Publish disconnected status if polling stopped but service wasn't explicitly stopped
                         if _STATE.get("running"):
                              event_bus.publish(PlatformStatusUpdate(platform='x', status='disconnected', message='Polling stopped'))
                              # Wait before trying to restart polling/client
                              try: await asyncio.sleep(15)
                              except asyncio.CancelledError: break
                         else:
                              break # Exit outer loop if stop was requested

                     else:
                         # Failed to build client (likely auth error)
                         logger.error("Failed to build X client. Waiting for settings update/restart.")
                         # Status already published by build_x_client on failure
                         await wait_for_settings_update({"x_access_token"}) # Wait for potential re-auth
                         continue # Retry outer loop

                 # --- Final Cleanup ---
                 logger.info("X service runner task finished.")
                 _STATE["running"] = False
                 _STATE["connected"] = False
                 _STATE["client"] = None


             async def wait_for_settings_update(relevant_keys: set):
                 """Waits for a SettingsUpdated event affecting relevant keys or task cancellation."""
                 # (Same implementation as in twitch_service, potentially move to a shared utils module)
                 update_future = asyncio.get_running_loop().create_future()
                 listener_task = None

                 async def settings_listener(event: SettingsUpdated):
                     if not update_future.done():
                         if any(key in relevant_keys for key in event.keys_updated):
                             logger.info(f"Detected relevant X settings update: {event.keys_updated}. Resuming service check.")
                             update_future.set_result(True)

                 event_bus.subscribe(SettingsUpdated, settings_listener)
                 logger.info(f"Waiting for X settings update affecting: {relevant_keys}...")

                 try:
                     current_task = asyncio.current_task()
                     if not current_task: raise RuntimeError("Could not get current task in wait_for_settings_update (X)")
                     cancel_future = asyncio.Future() # Future to represent cancellation
                     def cancel_callback(task):
                          if not cancel_future.done() and task.cancelled():
                               cancel_future.set_exception(asyncio.CancelledError())
                     current_task.add_done_callback(cancel_callback) # Link to current task's completion

                     done, pending = await asyncio.wait([update_future, cancel_future], return_when=asyncio.FIRST_COMPLETED)
                     if update_future in done: logger.debug("X Settings update received.")
                     elif cancel_future in done: logger.info("Wait for X settings update cancelled."); raise asyncio.CancelledError
                     for future in pending: future.cancel()
                 finally:
                     event_bus.unsubscribe(SettingsUpdated, settings_listener)
                     logger.debug("Unsubscribed X settings listener.")


             async def stop_x_service():
                 """Stops the X service task gracefully."""
                 global _STATE, _run_task
                 logger.info("Stop requested for X service.")
                 _STATE["running"] = False # Signal loops to stop
                 _STATE["connected"] = False

                 # Cancel the main service task
                 current_task = _run_task
                 if current_task and not current_task.done():
                     if not current_task.cancelling():
                         logger.info("Cancelling main X service task...")
                         current_task.cancel()
                         try:
                             await asyncio.wait_for(current_task, timeout=5.0)
                             logger.info("Main X service task cancellation confirmed.")
                         except asyncio.CancelledError:
                              logger.info("Main X service task confirmed cancelled (exception caught).")
                         except asyncio.TimeoutError:
                              logger.warning("Timeout waiting for main X service task to cancel.")
                         except Exception as e:
                             logger.error(f"Error waiting for cancelled X service task: {e}", exc_info=True)
                     else:
                          logger.info("Main X service task already cancelling.")
                 else:
                     logger.info("No active X service task found to cancel.")

                 # Clear global task reference and state
                 _run_task = None
                 _STATE["task"] = None
                 _STATE["client"] = None
                 _STATE["user_id"] = None
                 _STATE["user_login"] = None

                 # Unsubscribe handlers
                 try: event_bus.unsubscribe(SettingsUpdated, handle_settings_update_restart)
                 except ValueError: pass
                 try: event_bus.unsubscribe(BotResponseToSend, handle_x_response)
                 except ValueError: pass

                 logger.info("X service stopped.")
                 event_bus.publish(PlatformStatusUpdate(platform='x', status='stopped'))

             async def handle_settings_update_restart(event: SettingsUpdated):
                 """Restarts the X service if relevant settings changed."""
                 relevant_keys = {
                     "x_access_token", "x_access_token_secret", # Auth tokens
                     # App key/secret changes require full app restart
                 }
                 if any(key in relevant_keys for key in event.keys_updated):
                     logger.info(f"Relevant X settings updated ({event.keys_updated}). Triggering service restart...")
                     event_bus.publish(ServiceControl(service_name="x", command="restart"))

             def start_x_service_task() -> asyncio.Task | None:
                 """Creates and starts the background task for the X service."""
                 global _STATE, _run_task
                 if _run_task and not _run_task.done():
                     logger.warning("X service task is already running or starting.")
                     return _run_task

                 logger.info("Creating and starting background task for X service.")
                 event_bus.subscribe(SettingsUpdated, handle_settings_update_restart)
                 event_bus.subscribe(BotResponseToSend, handle_x_response)
                 _run_task = asyncio.create_task(run_x_service(), name="XServiceRunner")
                 _STATE["task"] = _run_task
                 return _run_task

             # --- File: app/services/x_service.py --- END ---
             """,
                     "app/services/whatnot_bridge.py": r"""# Generated by install_fosbot.py
             # --- File: app/services/whatnot_bridge.py --- START ---
             import logging
             import asyncio
             from fastapi import WebSocket, WebSocketDisconnect # Import WebSocket types
             from typing import Optional, Set # Use Set for connections

             from app.core.event_bus import event_bus
             from app.events import BotResponseToSend, PlatformStatusUpdate, BotResponse, ServiceControl, SettingsUpdated, LogMessage
             from app.core.config import logger, settings # Use logger from config

             # --- Module State ---
             _STATE = {
                 "websocket": None, # Holds the single active WebSocket connection from the extension
                 "task": None,      # The asyncio.Task running the keepalive/management loop
                 "running": False,  # Control flag for the service loop
                 "connected": False # Indicates if an extension WS is currently connected
             }
             _run_task: asyncio.Task | None = None # Global reference for main.py

             # --- WebSocket Management ---
             # These functions are called by the ws_endpoints handler

             def set_whatnot_websocket(websocket: WebSocket):
                 """Registers the active WebSocket connection from the extension."""
                 global _STATE
                 if _STATE.get("websocket") and _STATE["websocket"] != websocket:
                     logger.warning("New Whatnot extension connection received while another exists. Closing old one.")
                     # Try to close the old one gracefully
                     old_ws = _STATE["websocket"]
                     asyncio.create_task(old_ws.close(code=1012, reason="Service Restarting / New Connection")) # 1012 = Service Restart

                 _STATE["websocket"] = websocket
                 _STATE["connected"] = True
                 logger.info("Whatnot extension WebSocket connection registered.")
                 event_bus.publish(PlatformStatusUpdate(platform="whatnot", status="connected", message="Extension Connected"))

             def clear_whatnot_websocket():
                 """Clears the WebSocket connection reference when disconnected."""
                 global _STATE
                 if _STATE.get("websocket"):
                     _STATE["websocket"] = None
                     _STATE["connected"] = False
                     logger.info("Whatnot extension WebSocket connection cleared.")
                     # Publish disconnected only if the service is supposed to be running
                     if _STATE.get("running"):
                          event_bus.publish(PlatformStatusUpdate(platform="whatnot", status="disconnected", message="Extension Disconnected"))

             # --- Event Handlers ---
             async def handle_whatnot_response(event: BotResponseToSend):
                 """Handles sending messages FROM the bot TO the Whatnot extension."""
                 if event.response.target_platform != "whatnot":
                     return

                 websocket = _STATE.get("websocket")
                 if not websocket or not _STATE.get("connected"):
                     logger.error("Cannot send to Whatnot: No active extension WebSocket connection.")
                     # Optionally queue messages or report failure?
                     return

                 message_payload = {
                     "type": "send_message", # Action type for the extension
                     "payload": {
                         "text": event.response.text
                         # Add channel or other context if needed by extension's send logic
                     }
                 }

                 logger.info(f"Sending message to Whatnot extension: {event.response.text[:50]}...")
                 try:
                     await websocket.send_json(message_payload)
                     logger.debug("Successfully sent message payload to Whatnot extension.")
                 except Exception as e:
                     logger.error(f"Error sending message to Whatnot extension: {e}")
                     # The ws_endpoint handler will likely catch the disconnect and clear the socket

             # --- Service Runner ---
             async def run_whatnot_bridge():
                 """
                 Main task for the Whatnot Bridge service.
                 Currently, its main job is to stay alive and manage the 'running' state.
                 It also handles the subscription for sending messages *to* the extension.
                 Receiving messages *from* the extension is handled by the /ws/whatnot endpoint.
                 """
                 global _STATE
                 logger.info("Whatnot Bridge service task started.")
                 _STATE["running"] = True

                 # Subscribe to send messages when the service is running
                 event_bus.subscribe(BotResponseToSend, handle_whatnot_response)

                 try:
                     while _STATE.get("running"):
                         # Keepalive logic or periodic checks could go here if needed
                         # For now, just check connection status and wait
                         if not _STATE.get("connected"):
                              # Optionally publish a 'waiting' or 'disconnected' status periodically
                              # logger.debug("Whatnot Bridge waiting for extension connection...")
                              pass # Status is handled by set/clear functions
                         await asyncio.sleep(15) # Check state periodically

                 except asyncio.CancelledError:
                     logger.info("Whatnot Bridge service task cancelled.")
                 except Exception as e:
                     logger.exception(f"Unexpected error in Whatnot Bridge service loop: {e}")
                     event_bus.publish(PlatformStatusUpdate(platform="whatnot", status="error", message="Bridge loop error"))
                 finally:
                     logger.info("Whatnot Bridge service task stopping.")
                     _STATE["running"] = False
                     _STATE["connected"] = False # Ensure disconnected on stop
                     # Unsubscribe handlers on stop
                     try: event_bus.unsubscribe(BotResponseToSend, handle_whatnot_response)
                     except ValueError: pass
                     # Close any lingering websocket connection if stop is called externally
                     websocket = _STATE.get("websocket")
                     if websocket:
                         logger.info("Closing Whatnot extension websocket during bridge stop.")
                         await websocket.close(code=1001, reason="Server Shutting Down")
                         clear_whatnot_websocket() # Ensure state is cleared


             async def stop_whatnot_bridge():
                 """Stops the Whatnot bridge service task."""
                 global _STATE, _run_task
                 logger.info("Stop requested for Whatnot Bridge service.")
                 _STATE["running"] = False # Signal the loop to stop

                 current_task = _run_task
                 if current_task and not current_task.done():
                     if not current_task.cancelling():
                         logger.info("Cancelling Whatnot Bridge service task...")
                         current_task.cancel()
                         try:
                             await asyncio.wait_for(current_task, timeout=5.0) # Wait for cleanup in finally block
                             logger.info("Whatnot Bridge service task cancellation confirmed.")
                         except asyncio.CancelledError:
                             logger.info("Whatnot Bridge service task confirmed cancelled (exception caught).")
                         except asyncio.TimeoutError:
                              logger.warning("Timeout waiting for Whatnot Bridge service task to cancel.")
                         except Exception as e:
                             logger.error(f"Error waiting for cancelled Whatnot Bridge task: {e}", exc_info=True)
                     else:
                          logger.info("Whatnot Bridge service task already cancelling.")
                 else:
                     logger.info("No active Whatnot Bridge service task found to cancel.")

                 # Clear global task reference and state
                 _run_task = None
                 _STATE["task"] = None
                 # State regarding websocket connection is handled within run_whatnot_bridge finally block

                 # No settings handler to unsubscribe for this service currently
                 logger.info("Whatnot Bridge service stopped.")
                 event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='stopped'))


             def start_whatnot_bridge_task() -> asyncio.Task | None:
                 """Creates and starts the background task for the Whatnot Bridge."""
                 global _STATE, _run_task
                 if _run_task and not _run_task.done():
                     logger.warning("Whatnot Bridge task is already running or starting.")
                     return _run_task

                 logger.info("Creating and starting background task for Whatnot Bridge service.")
                 # No settings handler needed for this basic version
                 _run_task = asyncio.create_task(run_whatnot_bridge(), name="WhatnotBridgeRunner")
                 _STATE["task"] = _run_task
                 return _run_task

             # --- File: app/services/whatnot_bridge.py --- END ---
             """,

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
                     #settings-status, #commands-status { font-style: italic; margin-bottom: 15px; padding: 10px; border-radius: 4px; display: none; border: 1px solid transparent; }
                     #settings-status.success, #commands-status.success { color: #0f5132; background-color: #d1e7dd; border-color: #badbcc; display: block;}
                     #settings-status.error, #commands-status.error { color: #842029; background-color: #f8d7da; border-color: #f5c2c7; display: block;}

                     /* Service Control Buttons */
                     .control-buttons-container > div { margin-bottom: 10px; }
                     .control-button { margin: 0 5px 5px 0; padding: 6px 12px; font-size: 12px; }
                     .control-button[data-command="start"] { background-color: #28a745; color: white; }
                     .control-button[data-command="stop"] { background-color: #dc3545; color: white; }
                     .control-button[data-command="restart"] { background-color: #ffc107; color: #212529; }

                     /* OAuth Buttons & Status */
                     .oauth-login-button { background-color: #6441a5; color: white; padding: 10px 15px; font-size: 14px; } /* Default Twitch Purple */
                     .oauth-login-button:hover { background-color: #4a2f7c; }
                     .youtube-login-button { background-color: #ff0000; } .youtube-login-button:hover { background-color: #cc0000; }
                     .x-login-button { background-color: #1da1f2; } .x-login-button:hover { background-color: #0c85d0; }
                     .oauth-logout-button { background-color: #dc3545; color: white; padding: 6px 10px; font-size: 12px; margin-left: 10px; }
                     .auth-status { margin-left: 15px; font-style: italic; color: #6c757d; font-size: 0.9em; }
                     .auth-status strong { color: #198754; } /* Bootstrap success green */
                     .auth-status.not-logged-in { color: #dc3545; }

                     /* Commands Tab Specifics */
                     #commands-table { width: 100%; border-collapse: collapse; margin-bottom: 20px;}
                     #commands-table th, #commands-table td { border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; vertical-align: top;}
                     #commands-table th { background-color: #f8f9fa; font-weight: 600; }
                     .command-action { cursor: pointer; color: #dc3545; font-size: 0.9em; margin-left: 10px; }
                     .command-action:hover { text-decoration: underline; }
                     #add-command-form label { margin-top: 10px; }
                     #add-command-form input { width: calc(100% - 24px); } /* Adjust for padding */
                     #csv-upload label { display: inline-block; margin-right: 10px; }
                     #csv-upload input[type=file] { display: inline-block; width: auto; }

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
                             <div id="commands-status"></div>
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
                         <p id="settings-status"></p> <!-- For save confirmation/errors -->

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
                                      <button class="control-button" data-service="whatnot" data-command="start">Start</button>
                                      <button class="control-button" data-service="whatnot" data-command="stop">Stop</button>
                                      <button class="control-button" data-service="whatnot" data-command="restart">Restart</button>
                                  </div>
                              </div>
                         </div>

                         <!-- YouTube Section -->
                         <div class="settings-section">
                             <h3>YouTube Authentication & Control</h3>
                              <div id="youtube-auth-area">
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
                              <div id="twitch-auth-area">
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
                              <div id="x-auth-area">
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
                                  <!-- Save button now targets only these non-auth settings -->
                                  <button type="submit">Save App Config</button>
                              </form>
                         </div>

                     </div> <!-- End Settings Tab -->
                 </div> <!-- End Content Area -->

                 <!-- Sidebar -->
                 <div id="sidebar">
                     <h3>Status & Logs</h3>
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
                             <li>An overlay panel will appear on the Whatnot page. Carefully click the page elements it asks for (Chat Area, Message Row, Username, Message Text). Click "Next" after each selection.</li>
                             <li>When finished, click "Done" on the overlay panel.</li>
                             <li>Click the extension icon again and click "Test Setup" to verify.</li>
                             <li>**Important:** Uncheck "Turn On Setup Mode" in the popup.</li>
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
             // FoSBot Dashboard Frontend JS v0.7.3 (OAuth Flow + Commands)

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
                         lightEl.classList.add(`status-${statusClass}`);
                         textEl.textContent = statusText;
                     } else {
                         console.warn(`Could not find text/light elements for status indicator: ${statusId}`);
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
                         console.error("Timestamp format error:", e, "Input:", isoTimestamp);
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
                     const messageDiv = document.createElement('div');
                     const platformSpan = document.createElement('span');
                     const userSpan = document.createElement('span');
                     const textSpan = document.createElement('span');
                     const timeSpan = document.createElement('span');

                     const platformClass = platform ? platform.toLowerCase().replace(/[^a-z0-9]/g, '') : 'system';
                     platformSpan.className = `platform-tag ${platformClass}`;
                     platformSpan.textContent = `[${platform ? platform.toUpperCase() : 'SYS'}]`;

                     userSpan.className = 'chat-user';
                     userSpan.textContent = 'FoSBot'; // Bot identifier
                     userSpan.style.fontStyle = 'italic';
                     userSpan.style.color = '#007bff'; // Bot color

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
                     const logEntry = document.createElement('div');
                     const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                     const levelUpper = level.toUpperCase();
                     logEntry.classList.add(`log-${levelUpper.toLowerCase()}`);
                     logEntry.textContent = `[${timestamp}] [${levelUpper}] ${moduleName ? '[' + moduleName + '] ' : ''}${message}`;

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

                 function showStatusMessage(elementId, message, isError = false, duration = 5000) {
                     const statusEl = document.getElementById(elementId);
                     if (!statusEl) return;
                     statusEl.textContent = message;
                     statusEl.className = isError ? 'error' : 'success';
                     statusEl.style.display = 'block';
                     clearTimeout(statusEl.timer); // Clear existing timer if any
                     if (duration > 0) {
                         statusEl.timer = setTimeout(() => {
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
                         showStatusMessage('settings-status', `Redirecting to ${platform} for login...`, false, 0); // Indefinite
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
                      showStatusMessage('settings-status', `Logging out from ${platform}...`, false, 0); // Indefinite status

                      try {
                          const response = await fetch(`/auth/${platform}/logout`, { method: 'POST' });
                          const result = await response.json(); // Assume JSON response

                          if (response.ok) {
                              showStatusMessage('settings-status', result.message || `${platform.toUpperCase()} logout successful.`, false);
                              addLogMessage('INFO', `${platform.toUpperCase()} logout: ${result.message}`);
                          } else {
                               showStatusMessage('settings-status', `Logout Error (${response.status}): ${result.detail || response.statusText}`, true);
                               addLogMessage('ERROR', `Logout Error (${platform}, ${response.status}): ${result.detail || response.statusText}`);
                          }
                      } catch (error) {
                          console.error(`Logout Error (${platform}):`, error);
                          showStatusMessage('settings-status', `Network error during logout: ${error.message}`, true);
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
                         console.error("WS Parse Err:", err, "Data:", event.data);
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
                              // Update specific text status in Settings tab if needed (but auth status comes from /api/settings)
                              // updateSpecificPlatformStatusText(data.payload.platform, data.payload.status, data.payload.message);
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
                             console.debug("Pong received from backend."); // Debug level sufficient
                             break;
                         case 'current_settings': // Received after request_settings
                              currentSettings = data.payload || {}; // Store settings globally
                              populateAppSettingsForm(currentSettings);
                              updateAllAuthUIs(currentSettings);
                              break;
                         default:
                             console.warn("Unknown WS message type:", data.type, data);
                             addLogMessage('WARN', `Received unknown WS message type: ${data.type}`);
                     }
                 }

                 function connectWebSocket() {
                     if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
                         console.debug("WebSocket connection already open or connecting.");
                         return;
                     }
                     clearTimeout(reconnectTimer); // Clear any pending reconnect timer

                     const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                     // Use location.host which includes hostname and port
                     const wsUrl = `${wsProto}//${window.location.host}/ws/dashboard`;
                     console.info(`Connecting WebSocket: ${wsUrl}`);
                     updateStatusIndicator('ws', 'connecting', 'WebSocket: Connecting...');
                     addLogMessage('INFO', `Attempting WebSocket connection to ${wsUrl}...`);
                     generalStatus.textContent = "App Status: Connecting...";

                     socket = new WebSocket(wsUrl);

                     socket.onopen = () => {
                         console.info('WebSocket connection established.');
                         updateStatusIndicator('ws', 'connected', 'WebSocket: Online');
                         addLogMessage('INFO', 'WebSocket connected.');
                         reconnectAttempts = 0; // Reset reconnect counter on success
                         generalStatus.textContent = "App Status: Connected";
                         startPing(); // Start sending pings
                         requestSettings(); // Request initial settings upon connection
                     };

                     socket.onmessage = handleWebSocketMessage;

                     socket.onclose = (event) => {
                         console.warn(`WebSocket closed: Code=${event.code}, Reason='${event.reason}'. Attempting reconnect...`);
                         updateStatusIndicator('ws', 'disconnected', `WebSocket: Offline (Code ${event.code})`);
                         addLogMessage('WARN', `WebSocket closed (Code: ${event.code}).`);
                         generalStatus.textContent = "App Status: Disconnected";
                         socket = null; // Clear the socket object
                         stopPing(); // Stop sending pings

                         // Reconnect logic
                         if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                             reconnectAttempts++;
                             const delay = Math.min(RECONNECT_DELAY_BASE * Math.pow(1.5, reconnectAttempts - 1), 30000); // Exponential backoff up to 30s
                             console.info(`WebSocket reconnect attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay / 1000}s...`);
                             addLogMessage('INFO', `Attempting WebSocket reconnect (${reconnectAttempts})...`);
                             reconnectTimer = setTimeout(connectWebSocket, delay);
                         } else {
                             console.error("WebSocket maximum reconnect attempts reached. Please check the backend server and refresh the page.");
                             addLogMessage('ERROR', "Maximum WebSocket reconnect attempts reached. Check backend server.");
                             generalStatus.textContent = "App Status: Connection Failed (Max Retries)";
                         }
                     };

                     socket.onerror = (error) => {
                         console.error('WebSocket Error:', error);
                         updateStatusIndicator('ws', 'error', 'WebSocket: Error');
                         addLogMessage('ERROR', 'WebSocket connection error.');
                         // onclose will likely be called after onerror, triggering reconnect logic
                     };
                 }

                 function startPing() {
                     stopPing(); // Clear existing interval first
                     pingInterval = setInterval(() => {
                         if (socket && socket.readyState === WebSocket.OPEN) {
                             console.debug("Sending ping to backend.");
                             socket.send(JSON.stringify({ type: "ping" }));
                         } else {
                             console.warn("Cannot send ping, WebSocket not open.");
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
                             console.error("WS Send Err:", e);
                             addLogMessage('ERROR', `WebSocket send failed: ${e.message}`);
                             showStatusMessage('settings-status', 'Error: Could not send message. WebSocket issue.', true);
                         }
                     } else {
                         addLogMessage('ERROR', "Cannot send message: WebSocket is not connected.");
                         showStatusMessage('settings-status', 'Error: WebSocket not connected. Cannot send message.', true);
                     }
                 }
                 sendButton.addEventListener('click', sendStreamerInput);
                 streamerInput.addEventListener('keypress', (event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                           event.preventDefault(); // Prevent default newline on Enter
                           sendStreamerInput();
                      }
                 });
                 clearButton.addEventListener('click', () => {
                      chatOutput.innerHTML = '<div>Chat display cleared.</div>';
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
                           console.debug("Requesting settings from backend...");
                           // addLogMessage('DEBUG', 'Requesting current settings...'); // Too noisy?
                           socket.send(JSON.stringify({ type: "request_settings" }));
                      } else {
                           showStatusMessage('settings-status', "Cannot load settings: WebSocket closed.", true);
                           // Clear auth UIs if WS is down
                           updateAllAuthUIs({}); // Pass empty object to show logged out state
                      }
                 }

                 function populateAppSettingsForm(settings) {
                     // Populate non-auth App Config form
                     if (appSettingsForm) {
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

                 // Save App Config settings (non-auth)
                 appSettingsForm?.addEventListener('submit', async (e) => {
                     e.preventDefault();
                     const formData = new FormData(appSettingsForm);
                     const dataToSend = {
                          COMMAND_PREFIX: formData.get('COMMAND_PREFIX'),
                          LOG_LEVEL: formData.get('LOG_LEVEL'),
                          // Twitch channels are saved separately now or as part of general app settings?
                          // Include it here based on the form structure
                          TWITCH_CHANNELS: twitchChannelsInput.value.trim() // Use the specific input
                     };

                     console.debug("Saving App Config:", dataToSend);
                     showStatusMessage('settings-status', "Saving App Config...", false, 0); // Indefinite

                     try {
                         const response = await fetch('/api/settings', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify(dataToSend)
                         });
                         const result = await response.json();
                         if (response.ok) {
                             showStatusMessage('settings-status', result.message || "App Config saved!", false);
                             addLogMessage('INFO', `App Config saved: ${result.message}`);
                              // Refresh settings from backend to confirm update
                              requestSettings();
                         } else {
                              showStatusMessage('settings-status', `Error saving App Config: ${result.detail || response.statusText}`, true);
                              addLogMessage('ERROR', `Error saving App Config: ${result.detail || response.statusText}`);
                         }
                     } catch (error) {
                          console.error("Save App Config Err:", error);
                          showStatusMessage('settings-status', `Network error saving App Config: ${error.message}`, true);
                          addLogMessage('ERROR', `Network error saving App Config: ${error.message}`);
                     }
                 });

                 // --- Service Control ---
                 controlButtons.forEach(button => {
                     button.addEventListener('click', async (e) => {
                          const service = button.dataset.service;
                          const command = button.dataset.command;
                          if (!service || !command) return;

                          showStatusMessage('settings-status', `Sending '${command}' to ${service}...`, false, 0);
                          addLogMessage('INFO', `Sending control command '${command}' to service '${service}'...`);

                          try {
                              const response = await fetch(`/api/control/${service}/${command}`, { method: 'POST' });
                              const result = await response.json();
                              if (response.ok) {
                                  showStatusMessage('settings-status', result.message || `Command '${command}' sent to ${service}.`, false);
                                  addLogMessage('INFO', `Control command response for ${service}: ${result.message}`);
                              } else {
                                   showStatusMessage('settings-status', `Error controlling ${service}: ${result.detail || response.statusText}`, true);
                                   addLogMessage('ERROR', `Error controlling ${service}: ${result.detail || response.statusText}`);
                              }
                          } catch (error) {
                               console.error(`Control Error (${service} ${command}):`, error);
                               showStatusMessage('settings-status', `Network error controlling ${service}: ${error.message}`, true);
                               addLogMessage('ERROR', `Network error controlling ${service}: ${error.message}`);
                          }
                     });
                 });

                 // --- Commands Tab Logic ---
                 async function fetchCommands() {
                     try {
                         const response = await fetch('/api/commands');
                         if (!response.ok) {
                              throw new Error(`HTTP error ${response.status}`);
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
                         console.error('Error fetching commands:', error);
                         showStatusMessage('commands-status', `Error loading commands: ${error.message}`, true);
                         commandsTableBody.innerHTML = '<tr><td colspan="3"><i>Error loading commands.</i></td></tr>';
                     }
                 }

                 addCommandForm?.addEventListener('submit', async (e) => {
                     e.preventDefault();
                     const command = commandNameInput.value.trim();
                     const response = commandResponseInput.value.trim();

                     if (!command || !response) {
                         showStatusMessage('commands-status', 'Command name and response cannot be empty.', true);
                         return;
                     }

                     showStatusMessage('commands-status', `Saving command '!${command}'...`, false, 0);
                     try {
                         const res = await fetch('/api/commands', {
                             method: 'POST',
                             headers: { 'Content-Type': 'application/json' },
                             body: JSON.stringify({ command, response })
                         });
                         const result = await res.json();
                         if (res.ok) {
                             showStatusMessage('commands-status', result.message || `Command '!${command}' saved.`, false);
                             fetchCommands(); // Refresh table
                             addCommandForm.reset(); // Clear form
                         } else {
                              showStatusMessage('commands-status', `Error: ${result.detail || res.statusText}`, true);
                         }
                     } catch (error) {
                          console.error('Error adding command:', error);
                          showStatusMessage('commands-status', `Network error adding command: ${error.message}`, true);
                     }
                 });

                 async function handleDeleteCommandClick(event) {
                     const commandName = event.target.dataset.commandName;
                     if (!commandName) return;

                     if (confirm(`Are you sure you want to delete the command '!${commandName}'?`)) {
                         showStatusMessage('commands-status', `Deleting '!${commandName}'...`, false, 0);
                         try {
                             const response = await fetch(`/api/commands/${commandName}`, { method: 'DELETE' });
                             const result = await response.json();
                              if (response.ok) {
                                 showStatusMessage('commands-status', result.message || `Command '!${commandName}' deleted.`, false);
                                 fetchCommands(); // Refresh table
                              } else {
                                  showStatusMessage('commands-status', `Error deleting: ${result.detail || response.statusText}`, true);
                              }
                         } catch (error) {
                             console.error('Error deleting command:', error);
                             showStatusMessage('commands-status', `Network error deleting command: ${error.message}`, true);
                         }
                     }
                 }

                  uploadCsvButton?.addEventListener('click', async () => {
                       if (!csvFileInput.files || csvFileInput.files.length === 0) {
                            showStatusMessage('commands-status', 'Please select a CSV file first.', true);
                            return;
                       }
                       const file = csvFileInput.files[0];
                       const formData = new FormData();
                       formData.append('file', file);

                       showStatusMessage('commands-status', `Uploading ${file.name}...`, false, 0);
                       try {
                            const response = await fetch('/api/commands/upload', {
                                 method: 'POST',
                                 body: formData // Send as form data
                            });
                            const result = await response.json();
                            if (response.ok) {
                                 const summary = `Added: ${result.added}, Updated: ${result.updated}, Skipped: ${result.skipped}`;
                                 showStatusMessage('commands-status', `${result.message} ${summary}`, false, 7000);
                                 fetchCommands(); // Refresh table
                                 csvFileInput.value = ''; // Clear file input
                            } else {
                                 showStatusMessage('commands-status', `Upload Error: ${result.detail || response.statusText}`, true);
                            }
                       } catch (error) {
                            console.error('Error uploading CSV:', error);
                            showStatusMessage('commands-status', `Network error uploading CSV: ${error.message}`, true);
                       }
                  });

                 // --- Whatnot Guide Modal ---
                 window.openWhatnotGuide = () => {
                      document.getElementById('whatnot-guide-modal').style.display = 'block';
                 }
                 window.closeWhatnotGuide = () => {
                      document.getElementById('whatnot-guide-modal').style.display = 'none';
                 }
                 // Close modal if clicking outside the content
                 const modal = document.getElementById('whatnot-guide-modal');
                 modal?.addEventListener('click', (event) => {
                      if (event.target === modal) {
                           closeWhatnotGuide();
                      }
                 });


                 // --- Initial Load ---
                 addLogMessage('INFO', 'Dashboard UI Initialized.');
                 connectWebSocket(); // Start WebSocket connection
                 // Initial data fetch will happen on WebSocket connect -> requestSettings()
                 fetchCommands(); // Load commands initially

                 // --- Check for Auth Success/Error Flags in URL ---
                 function checkAuthRedirect() {
                     const urlParams = new URLSearchParams(window.location.search);
                     const successPlatform = urlParams.get('auth_success');
                     const errorPlatform = urlParams.get('auth_error');
                     const errorMessage = urlParams.get('message');

                     if (successPlatform) {
                         showStatusMessage('settings-status', `${successPlatform.charAt(0).toUpperCase() + successPlatform.slice(1)} login successful! Service restarting...`, false, 7000);
                         addLogMessage('INFO', `${successPlatform.toUpperCase()} OAuth successful.`);
                         // Clean the URL
                         window.history.replaceState({}, document.title, window.location.pathname);
                         // Switch to settings tab automatically?
                         const settingsTabButton = document.querySelector('button[data-tab="settings"]');
                         if(settingsTabButton) settingsTabButton.click();
                     } else if (errorPlatform) {
                         const platformName = errorPlatform.charAt(0).toUpperCase() + errorPlatform.slice(1);
                         const displayMessage = `OAuth Error (${platformName}): ${decodeURIComponent(errorMessage || 'Unknown error')}`;
                         showStatusMessage('settings-status', displayMessage, true, 15000); // Show error longer
                         addLogMessage('ERROR', displayMessage);
                          // Clean the URL
                         window.history.replaceState({}, document.title, window.location.pathname);
                         // Switch to settings tab automatically?
                         const settingsTabButton = document.querySelector('button[data-tab="settings"]');
                         if(settingsTabButton) settingsTabButton.click();
                     }
                 }
                 checkAuthRedirect(); // Check immediately on load

             }); // End DOMContentLoaded
             // --- File: static/main.js --- END ---
             """,

                     # === whatnot_extension/ Files ===
                     "whatnot_extension/manifest.json": r"""{
                 "manifest_version": 3,
                 "name": "FoSBot Whatnot Helper",
                 "version": "0.7.3",
                 "description": "Connects Whatnot live streams to FoSBot backend for chat reading.",
                 "permissions": [
                     "storage",
                     "activeTab",
                     "scripting"
                 ],
                 "host_permissions": [
                     "*://*.whatnot.com/*"
                 ],
                 "background": {
                     "service_worker": "background.js"
                 },
                 "content_scripts": [
                     {
                         "matches": ["*://*.whatnot.com/live/*"],
                         "js": ["content.js"],
                         "run_at": "document_idle",
                         "all_frames": false
                     }
                 ],
                 "action": {
                     "default_popup": "popup.html",
                     "default_icon": {
                         "16": "icons/icon16.png",
                         "48": "icons/icon48.png",
                         "128": "icons/icon128.png"
                     }
                 },
                 "icons": {
                     "16": "icons/icon16.png",
                     "48": "icons/icon48.png",
                     "128": "icons/icon128.png"
                 }
             }
             """,
                     "whatnot_extension/background.js": r"""# Generated by install_fosbot.py
             // FoSBot Whatnot Helper Background Script v0.7.3

             let ws = null;
             let reconnectTimer = null;
             let reconnectAttempts = 0;
             const WS_URL = 'ws://localhost:8000/ws/whatnot'; // Backend WebSocket endpoint
             const MAX_RECONNECT_ATTEMPTS = 15;
             const RECONNECT_DELAY_BASE = 3000; // 3 seconds base delay

             // --- WebSocket Connection Logic ---
             function connectWebSocket() {
                 if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
                     console.log('[FoSBot BG] WebSocket already open or connecting.');
                     return;
                 }
                 clearTimeout(reconnectTimer); // Clear any pending reconnect attempt

                 console.log(`[FoSBot BG] Attempting WebSocket connection to ${WS_URL}...`);
                 try {
                     ws = new WebSocket(WS_URL);
                 } catch (e) {
                     console.error(`[FoSBot BG] WebSocket connection failed immediately: ${e}`);
                     scheduleReconnect();
                     return;
                 }

                 ws.onopen = () => {
                     console.log('[FoSBot BG] WebSocket connected to FoSBot backend.');
                     reconnectAttempts = 0; // Reset reconnect counter on success
                     // Optionally send a ping or connection confirmation
                     ws.send(JSON.stringify({ type: 'ping', source: 'background' }));
                 };

                 ws.onclose = (event) => {
                     console.warn(`[FoSBot BG] WebSocket disconnected (Code: ${event.code}, Reason: ${event.reason || 'N/A'}).`);
                     ws = null; // Clear the socket object
                     scheduleReconnect();
                 };

                 ws.onerror = (error) => {
                     // Log the error object itself for more details if available
                     console.error('[FoSBot BG] WebSocket error:', error);
                     // scheduleReconnect will be called by onclose which usually follows onerror
                 };

                 ws.onmessage = (event) => {
                     try {
                         const data = JSON.parse(event.data);
                         console.log('[FoSBot BG] Received message from backend:', data);
                         if (data.type === 'pong') {
                             console.debug('[FoSBot BG] Pong received.');
                         } else if (data.type === 'send_message') {
                              // Forward message to content script to be posted
                              forwardMessageToContentScript(data);
                         }
                         // Handle other message types from backend if needed
                     } catch (e) {
                         console.error('[FoSBot BG] Error parsing WebSocket message:', e, "Data:", event.data);
                     }
                 };
             }

             function scheduleReconnect() {
                 if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                     reconnectAttempts++;
                     const delay = Math.min(RECONNECT_DELAY_BASE * Math.pow(1.5, reconnectAttempts - 1), 60000); // Exponential backoff up to 60s
                     console.info(`[FoSBot BG] WebSocket reconnect attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay / 1000}s...`);
                     clearTimeout(reconnectTimer); // Clear previous timer just in case
                     reconnectTimer = setTimeout(connectWebSocket, delay);
                 } else {
                     console.error("[FoSBot BG] Maximum WebSocket reconnect attempts reached. Stopping attempts.");
                     // Consider notifying the user via popup or badge?
                 }
             }

             function forwardMessageToContentScript(messageData) {
                 chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                     const activeTab = tabs.find(t => t.url && t.url.includes('whatnot.com/live/'));
                     if (activeTab && activeTab.id) {
                          console.debug(`[FoSBot BG] Forwarding message to content script in tab ${activeTab.id}:`, messageData);
                          chrome.tabs.sendMessage(activeTab.id, messageData, (response) => {
                              if (chrome.runtime.lastError) {
                                   console.error(`[FoSBot BG] Error sending message to content script: ${chrome.runtime.lastError.message}`);
                              } else {
                                   console.debug("[FoSBot BG] Content script acknowledged message:", response);
                              }
                          });
                     } else {
                          console.warn("[FoSBot BG] No active Whatnot live tab found to forward message.");
                     }
                });
             }

             // --- Message Listener for Content Script ---
             chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
                 console.debug('[FoSBot BG] Received message:', request, 'from sender:', sender);

                 if (request.type === 'chat_message') {
                     // Forward chat message from content script to backend WebSocket
                     if (ws && ws.readyState === WebSocket.OPEN) {
                         console.debug('[FoSBot BG] Forwarding chat message to backend.');
                         ws.send(JSON.stringify(request)); // Send the whole message object
                         sendResponse({ success: true, message: "Sent to backend" });
                     } else {
                         console.warn('[FoSBot BG] Cannot forward chat message: WebSocket not connected.');
                         sendResponse({ success: false, message: "WebSocket not connected" });
                     }
                 } else if (request.type === 'query_status') {
                      // Respond to popup/content script asking for connection status
                      sendResponse({
                           wsConnected: ws && ws.readyState === WebSocket.OPEN,
                           // Add other status info if needed
                      });
                 } else if (request.type === 'debug') {
                      // Forward debug messages from content script/popup to backend debug WS (if needed)
                      console.log(`[FoSBot BG Debug from ${request.source || 'unknown'}]: ${request.message}`);
                      // Optionally forward to a debug websocket endpoint if implemented backend-side
                 } else {
                      console.warn(`[FoSBot BG] Unhandled message type: ${request.type}`);
                      sendResponse({ success: false, message: "Unknown message type" });
                 }

                 // Return true to indicate you wish to send a response asynchronously
                 // (although most responses here are synchronous)
                 return true;
             });

             // --- Initial Connection ---
             connectWebSocket(); // Start connection attempt when background script loads

             // --- Keep Alive for Service Worker ---
             // Simple periodic alarm to keep the service worker alive (MV3 requirement)
             const KEEPALIVE_ALARM_NAME = 'fosbotKeepalive';
             chrome.alarms.get(KEEPALIVE_ALARM_NAME, (alarm) => {
                  if (!alarm) {
                       chrome.alarms.create(KEEPALIVE_ALARM_NAME, { periodInMinutes: 0.5 }); // Check every 30 seconds
                       console.log('[FoSBot BG] Keepalive alarm created.');
                  }
             });

             chrome.alarms.onAlarm.addListener((alarm) => {
                  if (alarm.name === KEEPALIVE_ALARM_NAME) {
                       console.debug('[FoSBot BG] Keepalive alarm triggered.');
                       // Optionally check WebSocket connection status here
                       if (!ws || ws.readyState === WebSocket.CLOSED) {
                            console.warn('[FoSBot BG] Keepalive found WebSocket closed. Attempting reconnect.');
                            connectWebSocket();
                       }
                  }
             });

             console.log('[FoSBot BG] Background script loaded and initialized.');
             """,
                     "whatnot_extension/popup.html": r"""<!-- Generated by install_fosbot.py -->
             <!DOCTYPE html>
             <html>
             <head>
                 <title>FoSBot Whatnot Helper</title>
                 <style>
                     body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; width: 350px; padding: 15px; font-size: 14px; }
                     h3 { margin: 0 0 10px; font-size: 1.1em; color: #333; }
                     label { display: block; margin: 12px 0 5px; font-weight: bold; font-size: 0.9em; }
                     button { width: 100%; padding: 9px 15px; margin-bottom: 10px; box-sizing: border-box; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background-color 0.2s ease; }
                     button:hover { background: #0056b3; }
                     button:disabled { background: #aaa; cursor: not-allowed; }
                     #status, #modeStatus { font-size: 0.9em; margin: 10px 0; padding: 8px; border-radius: 3px; text-align: center; }
                     #status.success { color: #155724; background-color: #d4edda; border: 1px solid #c3e6cb; }
                     #status.error { color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; }
                     #status.info { color: #0c5460; background-color: #d1ecf1; border: 1px solid #bee5eb; }
                     #modeStatus { font-weight: bold; border: 1px solid transparent; } /* Remove default border */
                     #modeStatus.on { color: #155724; background-color: #d4edda; border-color: #c3e6cb; }
                     #modeStatus.off { color: #6c757d; background-color: #e9ecef; border-color: #dee2e6; }
                     .instructions { font-size: 12px; margin-bottom: 10px; background-color: #f8f9fa; padding: 10px; border-radius: 3px; border: 1px solid #eee; line-height: 1.4; }
                     .instructions ol { margin: 5px 0 0 0; padding-left: 20px; }
                     a { color: #007bff; text-decoration: none; }
                     a:hover { text-decoration: underline; }
                     .setup-toggle { display: flex; align-items: center; margin-bottom: 10px; }
                     .setup-toggle input { width: auto; margin-right: 8px; }
                 </style>
             </head>
             <body>
                 <h3>FoSBot Whatnot Helper</h3>
                 <div id="modeStatus">Setup Mode: Checking...</div>
                 <div id="status">Checking connection...</div>
                 <div class="setup-toggle">
                     <input type="checkbox" id="setupMode">
                     <label for="setupMode" style="margin: 0; font-weight: normal;">Turn On Setup Mode (on Whatnot page)</label>
                 </div>
                 <div class="instructions">
                     <p><strong>How to set up:</strong></p>
                     <ol>
                         <li>Start the FoSBot app in Terminal.</li>
                         <li>Open a Whatnot stream page.</li>
                         <li>Check "Turn On Setup Mode" above.</li>
                         <li>Follow the floating box on the page to click chat parts.</li>
                         <li>Click "Test Setup" below when done.</li>
                         <li>Uncheck setup mode when finished.</li>
                     </ol>
                 </div>
                 <button id="testButton">Test Setup</button>
                 <!-- <p><a href="https://patreon.com/yourvideo" target="_blank">Watch Setup Video</a></p> -->
                 <script src="popup.js"></script>
             </body>
             </html>
             """,
                     "whatnot_extension/popup.js": r"""// Generated by install_fosbot.py
             // FoSBot Whatnot Helper Popup Script v0.7.3

             document.addEventListener('DOMContentLoaded', () => {
                 console.log('[FoSBot Popup] Initializing...');
                 const setupModeCheckbox = document.getElementById('setupMode');
                 const testButton = document.getElementById('testButton');
                 const statusDiv = document.getElementById('status');
                 const modeStatusDiv = document.getElementById('modeStatus');

                 // --- Helper Functions ---
                 function setStatus(message, type = 'info') {
                     statusDiv.textContent = message;
                     statusDiv.className = type; // 'success', 'error', 'info'
                     console.log(`[FoSBot Popup] Status: ${type} - ${message}`);
                 }

                 function updateModeStatus(isOn) {
                     modeStatusDiv.textContent = `Setup Mode: ${isOn ? 'On' : 'Off'}`;
                     modeStatusDiv.className = isOn ? 'on' : 'off';
                     console.log(`[FoSBot Popup] Mode Status Updated: ${isOn ? 'On' : 'Off'}`);
                 }

                 function queryContentScript(action, payload = {}, callback = null) {
                     chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                          // Ensure it's a whatnot page
                          if (tabs[0] && tabs[0].id && tabs[0].url && tabs[0].url.includes('whatnot.com/live/')) {
                              console.debug(`[FoSBot Popup] Sending message to tab ${tabs[0].id}:`, { type: action, payload });
                              chrome.tabs.sendMessage(tabs[0].id, { type: action, payload: payload }, (response) => {
                                  if (chrome.runtime.lastError) {
                                       console.error(`[FoSBot Popup] Error sending message '${action}': ${chrome.runtime.lastError.message}`);
                                       setStatus(`Error communicating with page. Reload Whatnot page? (${chrome.runtime.lastError.message})`, 'error');
                                       if (action === 'toggle_setup_mode') { // Revert checkbox if toggle failed
                                           setupModeCheckbox.checked = !payload.setupMode;
                                           updateModeStatus(!payload.setupMode);
                                       }
                                       if(callback) callback({ success: false, error: chrome.runtime.lastError.message });
                                  } else {
                                       console.debug(`[FoSBot Popup] Response for '${action}':`, response);
                                       if(callback) callback(response);
                                  }
                              });
                          } else {
                               console.warn(`[FoSBot Popup] Cannot send '${action}': Not on an active Whatnot live page.`);
                               setStatus('Error: Open a Whatnot live stream page first.', 'error');
                               if (action === 'toggle_setup_mode') { // Revert checkbox
                                   setupModeCheckbox.checked = !payload.setupMode;
                                   updateModeStatus(!payload.setupMode);
                               }
                              if(callback) callback({ success: false, error: "Not on Whatnot live page" });
                          }
                     });
                 }

                 // --- Initialization ---

                 // Load initial setupMode state
                 chrome.storage.local.get(['setupMode'], (data) => {
                     const isSetupMode = data.setupMode || false;
                     setupModeCheckbox.checked = isSetupMode;
                     updateModeStatus(isSetupMode);
                     console.log('[FoSBot Popup] Initial setupMode loaded:', isSetupMode);
                 });

                 // Check initial connection status with backend via background script
                 chrome.runtime.sendMessage({ type: 'query_status' }, (response) => {
                     if (chrome.runtime.lastError) {
                         console.error('[FoSBot Popup] Initial Status query error:', chrome.runtime.lastError);
                         setStatus('Error: Cannot reach background script.', 'error');
                         return;
                     }
                     if (response && response.wsConnected) {
                         setStatus('Connected to FoSBot Backend', 'success');
                     } else {
                         setStatus('Error: FoSBot backend not running or WS disconnected.', 'error');
                     }
                 });

                 // --- Event Listeners ---

                 // Toggle setup mode
                 setupModeCheckbox.addEventListener('change', () => {
                     const isChecked = setupModeCheckbox.checked;
                     console.log('[FoSBot Popup] Setup Mode toggled:', isChecked);
                     updateModeStatus(isChecked); // Update UI immediately
                     // Save state and notify content script
                     chrome.storage.local.set({ setupMode: isChecked }, () => {
                          queryContentScript('toggle_setup_mode', { setupMode: isChecked }, (response)=>{
                               if(!response || !response.success){
                                    // Revert UI if content script communication failed
                                    setupModeCheckbox.checked = !isChecked;
                                    updateModeStatus(!isChecked);
                                    // Status already set by queryContentScript on error
                               }
                          });
                     });
                 });

                 // Test button
                 testButton.addEventListener('click', () => {
                     setStatus('Testing setup...', 'info');
                     queryContentScript('test_settings', {}, (response) => {
                          if (response && response.success) {
                               setStatus(`Setup Test OK! (Found ${response.messagesFound || 0} messages)`, 'success');
                          } else {
                               setStatus(`Setup Test FAILED. Error: ${response?.error || 'Unknown. Redo setup?'}.`, 'error');
                          }
                     });
                 });

                 console.log('[FoSBot Popup] Initialization complete.');
             });
             """,
                     "whatnot_extension/content.js": r"""// Generated by install_fosbot.py
             // FoSBot Whatnot Helper Content Script v0.7.3

             // --- Start IIFE (Immediately Invoked Function Expression) to encapsulate scope ---
             (function () {
                 console.log('[FoSBot CS] Content script initializing...');

                 // --- State Variables ---
                 let settings = {
                     chatContainerSelector: null,
                     messageSelector: null,
                     userSelector: null,
                     textSelector: null,
                     chatInputSelector: null, // Added for sending messages
                     // setupMode is read dynamically from storage
                 };
                 let isSetupMode = false; // Current state of setup mode
                 let observer = null;
                 let controlPanel = null; // Reference to the setup UI panel
                 let highlightElement = null; // Reference to the mouseover highlight element
                 let currentSelectorType = null; // Which selector is being configured ('chatContainer', 'message', etc.)
                 let selectorIndex = 0;
                 const selectorTypes = [ // Define the steps for setup UI
                     { id: 'chatContainer', prompt: 'the MAIN CHAT AREA (where all messages appear)' },
                     { id: 'message', prompt: 'a SINGLE MESSAGE ROW inside the chat area' },
                     { id: 'user', prompt: 'the USERNAME text within that single message row' },
                     { id: 'text', prompt: 'the MESSAGE TEXT within that same single message row' },
                     // Add chat input selector setup
                     { id: 'chatInput', prompt: 'the TEXT INPUT field where you type chat messages' }
                 ];
                 let tempSelectors = {}; // Store selectors during setup process
                 let lastProcessedMessages = new Set(); // Keep track of processed message texts to avoid duplicates short-term
                 const MAX_PROCESSED_MEMORY = 200; // Limit memory of processed messages

                 // --- Helper Functions ---
                 function sendDebugLog(message) {
                     // console.debug(`[FoSBot CS Debug] ${message}`); // Local console log
                     // Send to background script which might forward to a debug websocket
                     chrome.runtime.sendMessage({ type: 'debug', source: 'content_script', message: message });
                 }

                 function sendMessageToBackground(message) {
                     sendDebugLog(`Sending message to background: ${JSON.stringify(message).substring(0, 100)}...`);
                     chrome.runtime.sendMessage(message, (response) => {
                         if (chrome.runtime.lastError) {
                             sendDebugLog(`Error sending message to background: ${chrome.runtime.lastError.message}`);
                         } else {
                             sendDebugLog(`Background response: ${JSON.stringify(response)}`);
                         }
                     });
                 }

                 function debounce(func, wait) {
                     let timeout;
                     return function executedFunction(...args) {
                         const later = () => {
                             clearTimeout(timeout);
                             func(...args);
                         };
                         clearTimeout(timeout);
                         timeout = setTimeout(later, wait);
                     };
                 }

                 // --- Core Logic ---

                 // Load saved selectors from chrome.storage.local
                 function loadSelectors() {
                     chrome.storage.local.get([
                         'chatContainerSelector', 'messageSelector', 'userSelector', 'textSelector', 'chatInputSelector'
                     ], (result) => {
                         settings.chatContainerSelector = result.chatContainerSelector || null;
                         settings.messageSelector = result.messageSelector || null;
                         settings.userSelector = result.userSelector || null;
                         settings.textSelector = result.textSelector || null;
                         settings.chatInputSelector = result.chatInputSelector || null; // Load input selector
                         sendDebugLog(`Selectors loaded from storage: ${JSON.stringify(settings)}`);
                         // Start observer only if essential selectors are present
                         if (areReadSelectorsValid()) {
                             setupMutationObserver();
                         } else {
                              sendDebugLog("Read selectors not valid, observer not started.");
                         }
                     });
                 }

                 function areReadSelectorsValid() {
                     return settings.chatContainerSelector && settings.messageSelector && settings.userSelector && settings.textSelector;
                 }
                 function areWriteSelectorsValid() {
                      return !!settings.chatInputSelector; // Only need input for now
                 }

                 // Setup MutationObserver to watch for new chat messages
                 function setupMutationObserver() {
                     if (!settings.chatContainerSelector) {
                         sendDebugLog('Cannot setup observer: Chat container selector is missing.');
                         return;
                     }
                     if (observer) {
                         observer.disconnect(); // Disconnect previous observer if any
                         sendDebugLog('Disconnected previous observer.');
                     }

                     const chatContainer = document.querySelector(settings.chatContainerSelector);
                     if (!chatContainer) {
                         sendDebugLog(`Chat container element not found with selector: ${settings.chatContainerSelector}. Observer not started.`);
                         // Maybe schedule a retry?
                         return;
                     }

                     observer = new MutationObserver(handleMutations);
                     observer.observe(chatContainer, { childList: true, subtree: true });
                     sendDebugLog(`MutationObserver started on: ${settings.chatContainerSelector}`);
                     // Process existing messages on initial observe
                     processExistingMessages(chatContainer);
                 }

                 const handleMutations = debounce((mutationsList) => {
                     sendDebugLog(`Mutation detected (${mutationsList.length} records). Processing added nodes...`);
                     let processed = false;
                     for (const mutation of mutationsList) {
                         if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                             mutation.addedNodes.forEach(node => {
                                 // Check if the added node itself is a message item or contains message items
                                 if (node.nodeType === Node.ELEMENT_NODE) {
                                     if (settings.messageSelector && node.matches(settings.messageSelector)) {
                                         parseAndSendMessage(node);
                                         processed = true;
                                     } else if (settings.messageSelector) {
                                         // Check descendants only if the node itself isn't the message item
                                         node.querySelectorAll(settings.messageSelector).forEach(parseAndSendMessage);
                                         processed = true; // Assume processed if we querySelectorAll
                                     }
                                 }
                             });
                         }
                     }
                      if(!processed) sendDebugLog("No relevant message nodes found in mutation.");
                 }, 250); // Debounce mutations slightly to handle rapid additions

                 function processExistingMessages(container) {
                      if (!container || !settings.messageSelector) return;
                      sendDebugLog("Processing existing messages on observer start...");
                      container.querySelectorAll(settings.messageSelector).forEach(parseAndSendMessage);
                      sendDebugLog("Finished processing existing messages.");
                 }

                 // Parse a message element and send it to the background script
                 function parseAndSendMessage(messageElement) {
                     if (!messageElement || !settings.userSelector || !settings.textSelector) return;

                     const userElement = messageElement.querySelector(settings.userSelector);
                     const textElement = messageElement.querySelector(settings.textSelector);

                     const username = userElement?.textContent?.trim();
                     const messageText = textElement?.textContent?.trim();

                     if (username && messageText) {
                          // Crude check to avoid immediate duplicates often caused by re-renders
                          const messageKey = `${username}:${messageText}`;
                          if (lastProcessedMessages.has(messageKey)) {
                               // sendDebugLog(`Skipping likely duplicate message: ${messageKey}`);
                               return;
                          }
                          lastProcessedMessages.add(messageKey);
                          // Limit the size of the duplicate check set
                          if (lastProcessedMessages.size > MAX_PROCESSED_MEMORY) {
                               const oldestKey = lastProcessedMessages.values().next().value;
                               lastProcessedMessages.delete(oldestKey);
                          }

                         sendDebugLog(`Parsed message - User: ${username}, Text: ${messageText.substring(0, 30)}...`);
                         sendMessageToBackground({
                             type: 'chat_message',
                             payload: {
                                 platform: 'whatnot',
                                 channel: 'live', // Assuming live stream chat, maybe extract later?
                                 user: username,
                                 text: messageText,
                                 timestamp: new Date().toISOString() // Use current time as Whatnot doesn't expose timestamps easily
                             }
                         });
                     } else {
                          sendDebugLog(`Failed to parse user or text from message element using selectors: U='${settings.userSelector}', T='${settings.textSelector}'`);
                     }
                 }

                 // --- Setup Mode UI and Logic ---

                 function startSetupMode() {
                     if (controlPanel) return; // Already in setup mode
                     isSetupMode = true;
                     selectorIndex = 0;
                     tempSelectors = {}; // Reset temporary selectors
                     currentSelectorType = selectorTypes[selectorIndex].id;
                     createControlPanel();
                     addHighlightOverlay();
                     document.addEventListener('mousemove', handleMouseMove);
                     document.addEventListener('click', handleClickCapture, true); // Use capture phase
                     sendDebugLog("Setup Mode Started.");
                 }

                 function stopSetupMode(save = false) {
                     if (!isSetupMode) return; // Prevent multiple calls
                     isSetupMode = false;
                     removeControlPanel();
                     removeHighlightOverlay();
                     if (handleMouseMove) document.removeEventListener('mousemove', handleMouseMove);
                     if (handleClickCapture) document.removeEventListener('click', handleClickCapture, true);
                     handleMouseMove = null;
                     handleClickCapture = null;

                     if (save) {
                         saveFinalSelectors();
                     } else {
                         tempSelectors = {}; // Discard temp selectors
                     }
                     sendDebugLog(`Setup Mode Stopped. ${save ? 'Selectors Saved.' : 'Cancelled.'}`);
                 }

                 function createControlPanel() {
                     removeControlPanel(); // Ensure only one exists
                     controlPanel = document.createElement('div');
                     controlPanel.style.cssText = `
                         position: fixed; top: 10px; right: 10px; width: 300px; background: rgba(255, 255, 255, 0.95);
                         border: 1px solid #aaa; padding: 15px; z-index: 100001; box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                         font-family: Arial, sans-serif; font-size: 14px; border-radius: 5px; color: #333;
                     `;
                     controlPanel.innerHTML = `
                         <h3 style="margin: 0 0 10px; font-size: 1.1em;">FoSBot Setup (Step <span id="fosbot-step-num">1</span>/${selectorTypes.length})</h3>
                         <p id="fosbot-instruction" style="margin: 5px 0 10px;">Click the element representing: <strong>${selectorTypes[selectorIndex].prompt}</strong></p>
                         <div id="fosbot-status" style="min-height: 1.5em; font-style: italic; color: green; margin-bottom: 10px; font-size: 0.9em;"></div>
                         <div id="fosbot-selector-preview" style="font-family: monospace; font-size: 0.8em; background: #eee; padding: 3px 5px; border-radius: 3px; margin-bottom: 10px; word-wrap: break-word;">Selector: (click element)</div>
                         <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                             <button id="fosbot-cancelButton" style="padding: 6px 12px; background: #dc3545; color: white; border: none; cursor: pointer; border-radius: 3px;">Cancel</button>
                             <button id="fosbot-nextButton" style="padding: 6px 12px; background: #007bff; color: white; border: none; cursor: pointer; border-radius: 3px;" disabled>Next</button>
                             <button id="fosbot-doneButton" style="padding: 6px 12px; background: #28a745; color: white; border: none; cursor: pointer; border-radius: 3px; display: none;">Done</button>
                         </div>
                     `;
                     document.body.appendChild(controlPanel);
                     updateControlPanelUI(); // Set initial state

                     // Add event listeners using IDs
                     controlPanel.querySelector('#fosbot-nextButton').addEventListener('click', handleNextButtonClick);
                     controlPanel.querySelector('#fosbot-doneButton').addEventListener('click', () => stopSetupMode(true));
                     controlPanel.querySelector('#fosbot-cancelButton').addEventListener('click', () => stopSetupMode(false));
                 }

                 function removeControlPanel() {
                     if (controlPanel) {
                         controlPanel.remove();
                         controlPanel = null;
                     }
                 }

                  function updateControlPanelUI() {
                       if (!controlPanel) return;
                       const stepNumEl = controlPanel.querySelector('#fosbot-step-num');
                       const instructionEl = controlPanel.querySelector('#fosbot-instruction strong');
                       const statusEl = controlPanel.querySelector('#fosbot-status');
                       const previewEl = controlPanel.querySelector('#fosbot-selector-preview');
                       const nextButton = controlPanel.querySelector('#fosbot-nextButton');
                       const doneButton = controlPanel.querySelector('#fosbot-doneButton');

                       stepNumEl.textContent = selectorIndex + 1;
                       instructionEl.textContent = selectorTypes[selectorIndex].prompt;
                       statusEl.textContent = ""; // Clear status on step change

                       const currentTypeId = selectorTypes[selectorIndex].id;
                       const currentSelector = tempSelectors[currentTypeId];
                       previewEl.textContent = currentSelector ? `Selector: ${currentSelector}` : 'Selector: (click element)';
                       nextButton.disabled = !currentSelector; // Enable Next only if a selector is set for the current step

                       // Show Done button only on the last step if all selectors are set
                       const allSet = selectorTypes.every(st => !!tempSelectors[st.id]);
                       if (selectorIndex === selectorTypes.length - 1 && allSet) {
                           nextButton.style.display = 'none';
                           doneButton.style.display = 'inline-block';
                       } else {
                           nextButton.style.display = 'inline-block';
                           doneButton.style.display = 'none';
                       }
                  }


                 function addHighlightOverlay() {
                     removeHighlightOverlay(); // Remove existing first
                     highlightElement = document.createElement('div');
                     highlightElement.style.cssText = `
                         position: absolute; border: 2px dashed #007bff; background: rgba(0, 123, 255, 0.1);
                         z-index: 100000; pointer-events: none; transition: all 0.05s linear;
                         box-sizing: border-box; border-radius: 3px;
                     `;
                     document.body.appendChild(highlightElement);
                 }

                 function removeHighlightOverlay() {
                     if (highlightElement) {
                         highlightElement.remove();
                         highlightElement = null;
                     }
                 }

                 handleMouseMove = (e) => {
                     if (!isSetupMode || !highlightElement) return;
                     // Hide highlight briefly to get element underneath
                     highlightElement.style.display = 'none';
                     const el = document.elementFromPoint(e.clientX, e.clientY);
                     highlightElement.style.display = 'block'; // Show highlight again

                     // Avoid highlighting the control panel itself or the highlight element
                     if (!el || el === controlPanel || controlPanel?.contains(el) || el === highlightElement) {
                         highlightElement.style.width = '0'; // Hide if not over valid element
                         highlightElement.style.height = '0';
                         return;
                     }

                     const rect = el.getBoundingClientRect();
                     highlightElement.style.left = `${window.scrollX + rect.left}px`;
                     highlightElement.style.top = `${window.scrollY + rect.top}px`;
                     highlightElement.style.width = `${rect.width}px`;
                     highlightElement.style.height = `${rect.height}px`;
                 };

                 handleClickCapture = (e) => {
                     if (!isSetupMode || !controlPanel) return;

                     // Allow clicks inside the control panel
                     if (controlPanel.contains(e.target)) {
                         return;
                     }