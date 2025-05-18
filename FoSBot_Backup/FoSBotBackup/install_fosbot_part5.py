                     _STATE["next_page_token"] = None # Reset page token

                     # --- Find Active Chat and Poll ---
                     while _STATE.get("running"): # Inner loop: Find chat -> Poll -> Repeat if chat ends
                         if asyncio.current_task().cancelled(): break

                         live_chat_id = await get_active_live_chat_id(youtube_client)
                         if live_chat_id:
                              _STATE["live_chat_id"] = live_chat_id
                              _STATE["connected"] = True
                              event_bus.publish(PlatformStatusUpdate(platform='youtube', status='connected', message=f"Polling chat {live_chat_id}"))
                              # Start polling - this will run until the chat ends, an error occurs, or stop is requested
                              await poll_youtube_chat(youtube_client, live_chat_id)
                              # If poll_youtube_chat returns, it means chat ended or error occurred
                              logger.info("Polling finished or stopped. Will check for new active chat.")
                              _STATE["connected"] = False # Mark as disconnected from *this* chat
                              _STATE["live_chat_id"] = None
                              _STATE["next_page_token"] = None # Reset page token
                              # Publish disconnected status after polling stops for a specific chat
                              event_bus.publish(PlatformStatusUpdate(platform='youtube', status='disconnected', message='Polling stopped/ended'))
                              # Optional: Add a small delay before checking for a new stream
                              await asyncio.sleep(10)
                         else:
                              # No active chat found
                              logger.info("No active YouTube chat found. Waiting before checking again.")
                              event_bus.publish(PlatformStatusUpdate(platform='youtube', status='waiting', message='No active stream found'))
                              # Wait for a while before checking for a new live stream
                              try: await asyncio.sleep(60)
                              except asyncio.CancelledError: break # Exit if cancelled during wait

                     # --- Cleanup after inner loop (if stop was requested) ---
                     if not _STATE.get("running"):
                         logger.info("YouTube service runner stopping as requested.")
                         break # Exit outer loop

                 # --- Final Cleanup ---
                 logger.info("YouTube service runner task finished.")
                 _STATE["running"] = False
                 _STATE["connected"] = False
                 _STATE["live_chat_id"] = None
                 _STATE["youtube_client"] = None


             # --- Wait Function ---
             async def wait_for_settings_update(relevant_keys: set):
                 """Waits for a SettingsUpdated event affecting relevant keys or task cancellation."""
                 # (Same implementation as in twitch_service)
                 update_future = asyncio.get_running_loop().create_future()
                 listener_task = None

                 async def settings_listener(event: SettingsUpdated):
                     if not update_future.done():
                         if any(key in relevant_keys for key in event.keys_updated):
                             logger.info(f"Detected relevant YouTube settings update: {event.keys_updated}. Resuming service check.")
                             update_future.set_result(True)

                 event_bus.subscribe(SettingsUpdated, settings_listener)
                 logger.info(f"Waiting for YouTube settings update affecting: {relevant_keys}...")

                 try:
                     current_task = asyncio.current_task()
                     if not current_task: raise RuntimeError("Could not get current task in wait_for_settings_update (YouTube)")
                     cancel_future = asyncio.Future() # Future to represent cancellation
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
                     try:
                         event_bus.unsubscribe(SettingsUpdated, settings_listener)
                         logger.debug("Unsubscribed YouTube settings listener.")
                     except ValueError:
                          logger.debug("YouTube settings listener already unsubscribed.")


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
             from app.core.json_store import load_tokens, save_tokens, get_setting, clear_tokens # Use get_setting for monitor query
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
                     try:
                         event_bus.unsubscribe(SettingsUpdated, settings_listener)
                         logger.debug("Unsubscribed X settings listener.")
                     except ValueError:
                          logger.debug("X settings listener already unsubscribed.")


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
                 Its primary role is to manage the 'running' state and subscribe the
                 response handler. The actual WebSocket server logic is now implicitly
                 handled by FastAPI/Uvicorn via the /ws/whatnot endpoint.
                 This task mainly keeps the service "alive" in the service map.
                 """
                 global _STATE
                 logger.info("Whatnot Bridge service task started.")
                 _STATE["running"] = True

                 # Subscribe to send messages when the service is running
                 event_bus.subscribe(BotResponseToSend, handle_whatnot_response)

                 try:
                     while _STATE.get("running"):
                         # This loop now primarily exists to keep the service alive
                         # and potentially perform periodic checks if needed in the future.
                         # The connection status is managed by set/clear_whatnot_websocket.
                         await asyncio.sleep(60) # Sleep for a longer interval

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
                     # The WebSocket connection itself is managed by the endpoint handler,
                     # but we ensure the state reflects it's no longer managed by this service.
                     clear_whatnot_websocket()


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
                             await asyncio.wait_for(current_task, timeout=2.0) # Wait for cleanup in finally block
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
                 # Connection state handled by run_whatnot_bridge finally block

                 logger.info("Whatnot Bridge service stopped.")
                 event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='stopped'))


             def start_whatnot_bridge_task() -> asyncio.Task | None:
                 """Creates and starts the background task for the Whatnot Bridge."""
                 global _STATE, _run_task
                 if _run_task and not _run_task.done():
                     logger.warning("Whatnot Bridge task is already running or starting.")
                     return _run_task

                 logger.info("Creating and starting background task for Whatnot Bridge service.")
                 # No specific settings needed to start the bridge itself, just the WS endpoint needs to run
                 _run_task = asyncio.create_task(run_whatnot_bridge(), name="WhatnotBridgeRunner")
                 _STATE["task"] = _run_task
                 return _run_task

             # --- File: app/services/whatnot_bridge.py --- END ---
             """
                 }
                 # <<< END OF FILE_CONTENTS DICTIONARY >>>

                 # --- Start Setup Process ---
                 check_environment()
                 backup_existing()
                 create_project_structure()
                 create_project_files()
                 install_macos_dependencies()
                 setup_python_venv()
                 generate_icons()
                 create_extension_zip()
                 print_final_instructions()

             if __name__ == "__main__":
                 main()

             ```

             **How to Use:**

             1.  **Save:** Save the entire Python code block above as a file named `install_fosbot.py`.
             2.  **Navigate:** Open your Terminal and navigate to the directory where you *want* the `FoSBot` project folder to be created (e.g., your Desktop or a development folder). **Do not** `cd` into an existing `FoSBot` folder if one exists.
             3.  **Run:** Execute the script using the correct Python 3.13 interpreter:
                 ```bash
                 python3.13 install_fosbot.py
                 ```
                 *(Adjust `python3.13` if your executable has a different name or path).*
             4.  **Interact:**
                 *   Click "Install" if the Xcode tools dialog appears.
                 *   Enter your macOS password in the terminal if the Homebrew installer prompts for it.
             5.  **Wait:** The script will perform all the steps, including installing dependencies via `brew` and `pip`, which can take some time depending on your internet speed and system state.
             6.  **Follow Final Instructions:** Once the script finishes successfully, it will print the "Next Steps". **Crucially**, follow step 1 to create and populate your `.env` file with your unique credentials. Then follow the subsequent steps to run the application.

             This script automates the entire setup based on our reconciled understanding, leaving only the essential manual configuration of secrets for the user.