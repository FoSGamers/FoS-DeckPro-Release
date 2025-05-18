import os
import sys
import subprocess
import time
import re
import json
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import logging

# Settings
BATCH_SIZE = 10  # Process 10 videos at a time
BATCH_DELAY = 1  # 1 second delay between batches
MERGED_CAPTIONS_FILE = "merged_captions.txt"
FAILURES_FILE = "failures.txt"
COOKIES_FILE = "yt_cookies.txt"
CAPTIONS_FOLDER = "captions"

def clear_terminal():
    subprocess.run("clear", shell=True)

def ensure_directories():
    os.makedirs(CAPTIONS_FOLDER, exist_ok=True)

def find_cookies():
    chrome_cookies_path = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome/Default/Cookies"
    )
    if os.path.exists(chrome_cookies_path):
        return chrome_cookies_path
    elif os.path.exists(COOKIES_FILE):
        return COOKIES_FILE
    else:
        return None

def create_ydl_instance():
    print("Initializing YouTube downloader...")
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,  # Focus on auto-generated captions
        "subtitlesformat": "vtt",
        "subtitleslangs": ["en"],
        "cookiesfrombrowser": ("chrome",),
        "outtmpl": "%(id)s.%(ext)s",
    }
    
    cookies_path = find_cookies()
    if cookies_path and cookies_path.endswith(".txt"):
        ydl_opts["cookiefile"] = cookies_path
    
    try:
        ydl = YoutubeDL(ydl_opts)
        # Trigger cookie extraction
        ydl.cookiejar
        print("Successfully initialized YouTube downloader with cookies")
        return ydl
    except Exception as e:
        print(f"Error initializing YouTube downloader: {e}")
        return None

def clean_caption_text(text):
    # Remove timestamps and numbering
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\n', '', text)
    text = re.sub(r'^\d+\n', '', text, flags=re.MULTILINE)
    # Remove empty lines and extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def fetch_video_list(channel_url, ydl):
    try:
        print("Fetching video list... This may take a while for large channels.")
        print("If this takes too long, try using a more specific URL (e.g., with /videos or /streams)")
        
        # Update options for playlist fetching
        ydl.params.update({
            "extract_flat": True,
            "quiet": False,
            "no_warnings": False,
        })
        
        print("Connecting to YouTube...")
        start_time = time.time()
        info = ydl.extract_info(channel_url, download=False)
        
        if not info:
            print("No information could be extracted from the URL")
            sys.exit(1)
            
        if "entries" in info:
            videos = [entry["id"] for entry in info["entries"] if entry]
            print(f"\nFound {len(videos)} videos")
            return videos
        else:
            print("No videos found in channel.")
            print("Try using a more specific URL (e.g., with /videos or /streams)")
            sys.exit(1)
    except DownloadError as e:
        print(f"Error fetching video list: {e}")
        print("Try using a more specific URL (e.g., with /videos or /streams)")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Try using a more specific URL (e.g., with /videos or /streams)")
        sys.exit(1)

def is_valid_caption_file(file_path):
    """
    Check if a file is a valid caption file by verifying:
    1. The file exists and is not empty
    2. The file contains proper caption content
    3. The file has the correct format (title, date, timestamps, and text)
    """
    try:
        if not os.path.exists(file_path):
            logging.error(f"File does not exist: {file_path}")
            return False

        if os.path.getsize(file_path) == 0:
            logging.error(f"File is empty: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into lines and check format
        lines = content.split('\n')
        if len(lines) < 4:  # Need at least title, date, blank line, and one caption
            logging.error(f"File too short: {file_path}")
            return False

        # Check for title and date format
        if not lines[0].strip() or not lines[1].strip():
            logging.error(f"Missing title or date: {file_path}")
            return False

        # Check for at least one timestamp and caption text
        has_timestamp = False
        has_caption_text = False
        for line in lines[3:]:  # Skip title, date, and blank line
            # Check for timestamp format [HH:MM:SS] followed by text
            if re.match(r'\[\d{2}:\d{2}:\d{2}\].*', line):
                has_timestamp = True
                # If there's text after the timestamp, it's caption text
                if len(line.split(']', 1)) > 1 and line.split(']', 1)[1].strip():
                    has_caption_text = True
            # Also check for any non-empty line that's not just a timestamp
            elif line.strip() and not line.strip().startswith('['):
                has_caption_text = True

        if not has_timestamp:
            logging.error(f"File does not contain any timestamps: {file_path}")
            return False

        if not has_caption_text:
            logging.error(f"File does not contain any caption text: {file_path}")
            return False

        return True

    except Exception as e:
        logging.error(f"Error validating file {file_path}: {str(e)}")
        return False

def download_caption(video_id, ydl, retry_count=3, force_redo=False):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    last_error = None
    
    # First check if we already have a valid file for this video
    for filename in os.listdir(CAPTIONS_FOLDER):
        if filename.endswith('.txt') and filename not in [MERGED_CAPTIONS_FILE, FAILURES_FILE]:
            file_path = os.path.join(CAPTIONS_FOLDER, filename)
            if is_valid_caption_file(file_path):
                if not force_redo:
                    print(f"Using existing file for {video_id}")
                    return True, None
                else:
                    print(f"Force re-downloading {video_id} despite existing file")
                    break
    
    for attempt in range(retry_count):
        try:
            # First get video info without downloading
            print(f"Getting info for {video_id}...")
            info = ydl.extract_info(video_url, download=False)
            title = info.get("title", "Unknown Title")
            upload_date = info.get("upload_date", "Unknown Date")
            filename = f"{upload_date} - {title}.txt"
            txt_path = os.path.join(CAPTIONS_FOLDER, sanitize_filename(filename))
            
            # Get subtitles info
            print(f"Checking captions for {video_id}...")
            subtitles = info.get('subtitles', {})
            auto_subs = info.get('automatic_captions', {})
            
            # Debug information about available captions
            if not subtitles and not auto_subs:
                error_msg = f"No captions available for {video_id} ({title}) - No subtitles or auto-captions found"
                print(error_msg)
                return False, error_msg
                
            # Try to get English subtitles first
            caption_data = None
            if 'en' in subtitles:
                caption_data = subtitles['en'][0]
                print(f"Found English subtitles for {video_id}")
            elif 'en' in auto_subs:
                caption_data = auto_subs['en'][0]
                print(f"Found English auto-captions for {video_id}")
            else:
                # Try any available language
                available_langs = list(subtitles.keys()) + list(auto_subs.keys())
                if available_langs:
                    print(f"Found captions in languages: {', '.join(available_langs)} for {video_id}")
                    # Try first available language
                    for lang in available_langs:
                        if lang in subtitles and subtitles[lang]:
                            caption_data = subtitles[lang][0]
                            break
                        elif lang in auto_subs and auto_subs[lang]:
                            caption_data = auto_subs[lang][0]
                            break
                else:
                    error_msg = f"No captions available for {video_id} ({title}) - No languages found"
                    print(error_msg)
                    return False, error_msg
            
            if not caption_data or 'url' not in caption_data:
                error_msg = f"No caption URL available for {video_id} ({title})"
                print(error_msg)
                return False, error_msg
                
            # Download the caption file
            try:
                print(f"Downloading captions for {video_id}...")
                caption_url = caption_data['url']
                caption_response = ydl.urlopen(caption_url).read().decode('utf-8')
            except Exception as e:
                error_msg = f"Failed to download caption file for {video_id} ({title}): {str(e)}"
                print(error_msg)
                return False, error_msg
            
            # Parse the JSON response
            try:
                print(f"Processing captions for {video_id}...")
                caption_json = json.loads(caption_response)
                # Extract the caption text with timestamps
                caption_text = ""
                for event in caption_json.get('events', []):
                    if 'tStartMs' in event and 'segs' in event:
                        # Convert milliseconds to HH:MM:SS format
                        total_seconds = event['tStartMs'] / 1000
                        hours = int(total_seconds // 3600)
                        minutes = int((total_seconds % 3600) // 60)
                        seconds = int(total_seconds % 60)
                        timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                        
                        # Combine all segments for this event
                        event_text = ""
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                event_text += seg['utf8']
                        
                        if event_text.strip():
                            caption_text += f"{timestamp} {event_text.strip()}\n"
            except json.JSONDecodeError:
                # If it's not JSON, assume it's already text
                caption_text = caption_response
                
            if not caption_text:
                error_msg = f"Failed to extract captions for {video_id} ({title}) - Empty caption text"
                print(error_msg)
                return False, error_msg
                
            # Save the captions with timestamps
            print(f"Saving captions for {video_id}...")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"{title}\n{upload_date}\n\n")
                f.write(caption_text)
                
            print(f"Successfully saved captions for {video_id} ({title})")
            return True, None
            
        except Exception as e:
            last_error = str(e)
            if attempt < retry_count - 1:
                print(f"Attempt {attempt + 1} failed for {video_id}, retrying...")
                time.sleep(2)  # Wait before retrying
            else:
                error_msg = f"Error downloading captions for {video_id}: {last_error}"
                print(error_msg)
                return False, error_msg

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in " ._-").rstrip()

def merge_captions():
    print("\nMerging all caption files...")
    merged_path = os.path.join(CAPTIONS_FOLDER, MERGED_CAPTIONS_FILE)
    total_files = 0
    
    with open(merged_path, "w", encoding="utf-8") as merged:
        for filename in sorted(os.listdir(CAPTIONS_FOLDER)):
            if filename.endswith(".txt") and filename != MERGED_CAPTIONS_FILE and filename != FAILURES_FILE:
                file_path = os.path.join(CAPTIONS_FOLDER, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:  # Only include non-empty files
                            merged.write("\n\n=== " + filename.replace(".txt", "") + " ===\n\n")
                            merged.write(content)
                            total_files += 1
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
    
    print(f"\nSuccessfully merged {total_files} caption files into {MERGED_CAPTIONS_FILE}")

def save_failures(failures):
    if failures:
        with open(os.path.join(CAPTIONS_FOLDER, FAILURES_FILE), "w", encoding="utf-8") as f:
            for video_id in failures:
                f.write(video_id + "\n")
        print(f"Failures saved to {FAILURES_FILE}")

def find_broken_captions():
    """Find all broken or missing caption files"""
    broken_files = []
    missing_videos = []
    existing_videos = set()
    good_files = []
    processed_videos = set()  # Track processed videos to prevent duplicates
    
    # First check all existing files
    print("\nChecking existing caption files...")
    for filename in os.listdir(CAPTIONS_FOLDER):
        if filename.endswith('.txt') and filename not in [MERGED_CAPTIONS_FILE, FAILURES_FILE]:
            file_path = os.path.join(CAPTIONS_FOLDER, filename)
            if is_valid_caption_file(file_path):
                try:
                    # Extract date from filename (format: YYYYMMDD)
                    date_str = filename.split(' - ')[0]
                    if len(date_str) == 8 and date_str.isdigit():
                        good_files.append((filename, date_str))
                        print(f"Found valid file: {filename}")
                except:
                    pass
            else:
                broken_files.append((filename, None))
                print(f"Found broken file: {filename}")
    
    # Now check for missing videos from the channel
    print("\nChecking for missing videos...")
    channel_url = input("Enter your YouTube Channel URL to check for missing videos: ").strip()
    if not any(x in channel_url for x in ['/videos', '/streams', '/playlists']):
        channel_url = channel_url.rstrip('/') + '/videos'
    
    ydl = create_ydl_instance()
    if ydl:
        # Update ydl options
        ydl.params.update({
            'socket_timeout': 10,
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'retries': 3,
            'fragment_retries': 3,
        })
        
        videos = fetch_video_list(channel_url, ydl)
        print(f"\nFound {len(videos)} videos in channel")
        print(f"Found {len(good_files)} valid caption files")
        print(f"Found {len(broken_files)} broken files")
        
        # Process videos with retry logic
        print("\nVerifying missing videos...")
        for video_id in videos:
            if video_id in processed_videos:
                continue
                
            found = False
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    info = ydl.extract_info(video_url, download=False)
                    if not info:
                        print(f"Failed to get info for {video_id} (attempt {attempt + 1})")
                        time.sleep(retry_delay)
                        continue
                        
                    upload_date = info.get("upload_date", "")
                    if not upload_date:
                        print(f"No upload date found for {video_id}")
                        break
                        
                    # Check for matching file
                    for filename, file_date in good_files:
                        if upload_date == file_date:
                            found = True
                            processed_videos.add(video_id)
                            break
                            
                    if found:
                        break
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} failed for {video_id}, retrying...")
                        time.sleep(retry_delay)
                    else:
                        print(f"Failed to process video {video_id} after {max_retries} attempts: {str(e)}")
                        break
                    
            if not found and video_id not in processed_videos:
                missing_videos.append(video_id)
                processed_videos.add(video_id)
                print(f"Confirmed missing video: {video_id}")
                
            time.sleep(0.5)  # Rate limiting delay
    
    # Print summary
    print("\nFile Status Summary:")
    print(f"Good files: {len(good_files)}")
    print(f"Broken files: {len(broken_files)}")
    print(f"Missing videos: {len(missing_videos)}")
    
    if good_files:
        print("\nGood files:")
        for filename, _ in good_files:
            print(f"- {filename}")
    
    if broken_files:
        print("\nBroken files:")
        for filename, _ in broken_files:
            print(f"- {filename}")
    
    if missing_videos:
        print("\nMissing videos:")
        for video_id in missing_videos:
            print(f"- {video_id}")
    
    return broken_files, missing_videos, good_files

def main():
    clear_terminal()
    print("\nFoSGamers Caption Downloader - Final Mac Version\n" + "-"*66)
    print("This script will download, clean, and merge auto-generated captions from your YouTube channel.")
    print("It uses your Chrome cookies for authentication and processes videos in batches.\n")

    ensure_directories()

    print("\nChoose mode:")
    print("[1] Find and Fix - Check all files and fix broken ones")
    print("[2] New Only - Only download new captions")
    print("[3] Force Redo - Redownload all captions")
    mode = input("Enter 1, 2, or 3: ").strip()

    # Initialize YouTube downloader once at the start
    ydl = create_ydl_instance()
    if not ydl:
        print("Failed to initialize YouTube downloader. Please try again.")
        sys.exit(1)

    if mode == "1":
        # Find and Fix mode
        print("\nFinding broken and missing captions...")
        broken_files, missing_videos, good_files = find_broken_captions()
        
        if not broken_files and not missing_videos:
            print("\nNo broken or missing captions found!")
            return
            
        proceed = input("\nDo you want to fix these issues? (y/n): ").strip().lower()
        if proceed != 'y':
            return
            
        # Fix broken files
        for filename, video_id in broken_files:
            if video_id:
                print(f"\nFixing {filename}...")
                success, error_msg = download_caption(video_id, ydl, force_redo=True)
                if not success:
                    print(f"Failed to fix {filename}: {error_msg}")
        
        # Download missing videos
        for video_id in missing_videos:
            print(f"\nDownloading missing video {video_id}...")
            success, error_msg = download_caption(video_id, ydl)
            if not success:
                print(f"Failed to download {video_id}: {error_msg}")
                
    else:
        # New Only or Force Redo mode
        channel_url = input("\nEnter your YouTube Channel URL (example: https://www.youtube.com/@FoSGamers/streams): ").strip()
        
        # Add /videos to URL if not present
        if not any(x in channel_url for x in ['/videos', '/streams', '/playlists']):
            channel_url = channel_url.rstrip('/') + '/videos'
            print(f"\nUsing URL: {channel_url}")

        print("\nFetching video list from YouTube...")
        videos = fetch_video_list(channel_url, ydl)
        print(f"\nTotal videos found: {len(videos)}\n")

        # Build list of videos we already have
        existing_videos = set()
        print("Checking existing caption files...")
        for filename in os.listdir(CAPTIONS_FOLDER):
            if filename.endswith('.txt') and filename not in [MERGED_CAPTIONS_FILE, FAILURES_FILE]:
                file_path = os.path.join(CAPTIONS_FOLDER, filename)
                if is_valid_caption_file(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Look for video ID in the content
                            if 'youtube.com/watch?v=' in content:
                                video_id = content.split('v=')[1].split('&')[0].split()[0]
                                if video_id:
                                    existing_videos.add(video_id)
                                    print(f"Found valid file for video {video_id}")
                    except:
                        pass

        # Filter out videos we already have
        if mode == "2":  # New Only mode
            videos_to_download = [v for v in videos if v not in existing_videos]
            print(f"\nFound {len(existing_videos)} existing valid files")
            print(f"Need to download {len(videos_to_download)} new videos")
        else:  # Force Redo mode
            videos_to_download = videos
            print(f"\nForce redoing all {len(videos)} videos")

        if not videos_to_download:
            print("\nNo new videos to download!")
            return

        proceed = input("\nDo you want to proceed? (y/n): ").strip().lower()
        if proceed != 'y':
            return

        failures = []
        total_processed = 0
        total_success = 0

        # Update options for video downloading
        ydl.params.update({
            "quiet": True,
            "no_warnings": True,
        })

        print("\nStarting caption processing...")
        for i in range(0, len(videos_to_download), BATCH_SIZE):
            batch = videos_to_download[i:i+BATCH_SIZE]
            print(f"\nProcessing batch {i//BATCH_SIZE + 1}/{(len(videos_to_download) + BATCH_SIZE - 1)//BATCH_SIZE}")
            for count, video_id in enumerate(batch, 1):
                print(f"[{i+count}/{len(videos_to_download)}] Processing {video_id}...")
                success, error_msg = download_caption(video_id, ydl, force_redo=(mode == "3"))
                total_processed += 1
                if not success:
                    print(f"Failed: {video_id}")
                    failures.append((video_id, error_msg))
                else:
                    total_success += 1
            print(f"\nProgress: {total_processed}/{len(videos_to_download)} videos processed")
            print(f"Success: {total_success}, Failed: {len(failures)}")
            time.sleep(BATCH_DELAY)

        merge_captions()
        
        # Save detailed failure information
        if failures:
            with open(os.path.join(CAPTIONS_FOLDER, FAILURES_FILE), "w", encoding="utf-8") as f:
                for video_id, error_msg in failures:
                    f.write(f"{video_id} - {error_msg}\n")
            print(f"\nFailures saved to {FAILURES_FILE}")
            print("\nFailed videos:")
            for video_id, error_msg in failures:
                print(f"- {video_id}: {error_msg}")

        print(f"\nAll Done!\nTotal processed: {len(videos_to_download)}\nSuccess: {total_success}\nFailed: {len(failures)}\nCaptions saved in {CAPTIONS_FOLDER}")

if __name__ == "__main__":
    main()
