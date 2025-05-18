#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sys
import time # Used for timestamp in output file header

# --- Configuration ---

# Files/extensions to definitely include. Case-insensitive matching for extensions.
# Add or remove as needed.
INCLUDED_EXTENSIONS = {
    # Code
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.kt', '.swift', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.pl', '.sh', '.bat', '.ps1', '.sql',
    # Markup/Config/Web
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.json', '.yaml', '.yml',
    '.xml', '.ini', '.cfg', '.conf', '.toml', '.md', '.txt', '.rst', '.tex',
    # Build/Dependencies/Env
    '.dockerfile', 'dockerfile', '.gitignore', '.gitattributes', '.env', '.env.example',
    'makefile', 'requirements.txt', 'package.json', 'pom.xml', 'build.gradle',
    # Logs (as requested)
    '.log',
    # Add any other specific file names or extensions
}

# Directory names to *always* exclude. Case-sensitive matching.
# Keep this list tight to avoid excluding potentially relevant logs/configs.
# Virtual environments and VCS metadata are usually safe bets to exclude.
EXCLUDED_DIRECTORIES = {
    '.git', '.hg', '.svn',            # Version control metadata
    '__pycache__',                    # Python cache
    '.pytest_cache', '.mypy_cache',   # Testing/typing cache
    'node_modules',                   # Node.js dependencies (can be huge)
    # 'vendor',                       # PHP/Ruby dependencies (uncomment if needed)
    # 'target', 'build', 'dist', 'out',# Common build output directories (uncomment if needed)
    '.venv', 'venv', 'env',           # Virtual environments
    '.idea', '.vscode', '.settings',  # IDE configuration
    # 'logs', # Intentionally NOT excluded per user request
    # 'tmp',  # Consider excluding if it contains irrelevant temporary files
}

# Skip hidden files/directories (those starting with '.')?
# Set to False if you need files like .bashrc, .profile, .env, etc.
SKIP_HIDDEN = True

# Default logging level if not running interactively
DEFAULT_LOG_LEVEL = "INFO"

# --- Global variable for script's own log file path (not used without args, but keep structure) ---
# We won't be using a separate log file in this version, logs go to console.
script_log_file_path_abs = None

# --- Core Functions ---

def setup_logging(log_level_str=DEFAULT_LOG_LEVEL):
    """Configures basic logging for the script's execution to stderr."""
    numeric_level = getattr(logging, log_level_str.upper(), logging.INFO)

    log_format = '%(asctime)s - %(levelname)-8s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Get root logger
    logger = logging.getLogger()
    # Set lowest level to capture everything intended by handlers
    # If you need DEBUG level by default, change DEFAULT_LOG_LEVEL above
    logger.setLevel(logging.DEBUG if numeric_level == logging.DEBUG else logging.INFO)

    # Remove existing handlers to avoid duplication if run multiple times
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console Handler (outputs to stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level) # Filter based on default or desired level
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logging.debug("Logging setup complete.")


def get_file_content(filepath):
    """
    Tries to read a file's content using common text encodings.
    Returns file content as a string, or None if reading fails or file is likely binary.
    """
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252'] # Common text encodings
    max_file_size = 50 * 1024 * 1024 # 50 MB limit to avoid memory issues

    try:
        # Basic check for very large files
        file_size = os.path.getsize(filepath)
        if file_size > max_file_size:
            logging.warning(f"Skipping file (>{max_file_size // 1024 // 1024}MB): {filepath}")
            return None
        if file_size == 0:
             logging.debug(f"Skipping empty file: {filepath}")
             return "" # Return empty string for empty files, don't skip entirely

        # Try reading with different encodings
        for enc in encodings_to_try:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                logging.debug(f"Decoding failed with {enc} for: {filepath}")
                continue # Try next encoding
            except Exception as e:
                logging.error(f"Error reading file {filepath} (encoding {enc}): {e}")
                return None # Unrecoverable read error

        # If all encodings failed, log a warning
        logging.warning(f"Could not decode {filepath} with {encodings_to_try}. Skipping content (may be binary or use unknown encoding).")
        return None

    except OSError as e:
         logging.error(f"OS error accessing file {filepath}: {e}")
         return None
    except Exception as e:
        logging.error(f"Unexpected error getting content for {filepath}: {e}")
        return None


def consolidate_files(start_dir, output_filepath):
    """
    Walks through start_dir, reads specified files, and writes content to output_filepath.
    Returns True on success, False on failure.
    """
    processed_file_count = 0
    total_bytes_processed = 0
    start_dir_abs = os.path.abspath(start_dir)
    output_filepath_abs = os.path.abspath(output_filepath)

    # --- Pre-checks ---
    if not os.path.isdir(start_dir_abs):
        logging.error(f"Scan directory not found or is not a directory: '{start_dir_abs}'")
        return False
    # Check if we can write to the output directory
    output_dir = os.path.dirname(output_filepath_abs)
    if not os.path.isdir(output_dir):
        try:
            # Attempt to create the output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True) # exist_ok=True prevents error if it already exists
            logging.info(f"Ensured output directory exists: {output_dir}")
        except OSError as e:
             logging.error(f"Output directory does not exist and cannot be created: {output_dir} - Error: {e}")
             return False
    if not os.access(output_dir, os.W_OK):
        logging.error(f"Cannot write to output directory: {output_dir}")
        return False

    logging.info(f"Starting scan in: {start_dir_abs}")
    logging.info(f"Output file will be: {output_filepath_abs}")
    logging.info(f"Included extensions/filenames (case-insensitive for ext): {INCLUDED_EXTENSIONS}")
    logging.info(f"Excluded directories (case-sensitive): {EXCLUDED_DIRECTORIES or 'None'}")
    logging.info(f"Skip hidden files/dirs: {SKIP_HIDDEN}")

    try:
        with open(output_filepath_abs, 'w', encoding='utf-8') as outfile:
            # Write a header to the consolidated file
            outfile.write(f"# Consolidated Files from: {start_dir_abs}\n")
            outfile.write(f"# Generated by script: {os.path.basename(__file__)}\n")
            outfile.write(f"# Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n") # Use time module

            # Walk the directory tree (THIS HANDLES SUBDIRECTORIES)
            for root, dirs, files in os.walk(start_dir_abs, topdown=True):
                rel_root = os.path.relpath(root, start_dir_abs)
                logging.debug(f"Scanning directory: '{rel_root if rel_root != '.' else '<root>'}'")

                # --- Directory Filtering (modify dirs in-place) ---
                dirs_to_skip = set()
                for d in list(dirs): # Iterate over a copy
                    is_hidden = d.startswith('.')
                    is_excluded = d in EXCLUDED_DIRECTORIES

                    # Prevent descending into an output dir if it happens to be inside the scan dir
                    current_dir_abs = os.path.abspath(os.path.join(root, d))
                    if os.path.dirname(output_filepath_abs) == current_dir_abs:
                         logging.debug(f"  Skipping directory (looks like output dir): {d}")
                         dirs_to_skip.add(d)
                         if d in dirs: dirs.remove(d)
                         continue

                    if is_excluded or (SKIP_HIDDEN and is_hidden):
                        dirs_to_skip.add(d)
                        if d in dirs: dirs.remove(d)

                if dirs_to_skip:
                    logging.debug(f"  Skipping subdirectories: {', '.join(sorted(list(dirs_to_skip)))}")

                # --- File Processing ---
                for filename in files:
                    filepath = os.path.join(root, filename)
                    script_abspath = os.path.abspath(__file__)

                    # Skip the script file itself, comparing absolute paths
                    if os.path.abspath(filepath) == script_abspath:
                        logging.debug(f"  Skipping the script file itself: {os.path.relpath(filepath, start_dir_abs)}")
                        continue

                    filepath_abs = os.path.abspath(filepath) # Use absolute path for comparisons
                    # THIS CALCULATES THE PATH TO SHOW IN THE OUTPUT
                    relative_filepath = os.path.relpath(filepath_abs, start_dir_abs)

                    # Basic file checks
                    is_hidden = filename.startswith('.')
                    if SKIP_HIDDEN and is_hidden:
                        logging.debug(f"  Skipping hidden file: {relative_filepath}")
                        continue

                    # Skip the output file itself (double check using absolute path)
                    if filepath_abs == output_filepath_abs:
                        logging.info(f"  Skipping output file itself: {relative_filepath}")
                        continue

                    # Check if file type should be included
                    _, ext = os.path.splitext(filename)
                    # Use lower() for case-insensitive check of extensions and specific filenames
                    is_included = (filename.lower() in INCLUDED_EXTENSIONS or
                                   ext.lower() in INCLUDED_EXTENSIONS)

                    if not is_included:
                        logging.debug(f"  Skipping file (type not included): {relative_filepath}")
                        continue

                    # --- Read and Write File Content ---
                    logging.info(f"  Adding file: {relative_filepath}")
                    content = get_file_content(filepath_abs)

                    if content is not None: # content can be "" for empty files
                        try:
                            # THIS WRITES THE HEADER WITH THE FILE PATH
                            outfile.write(f"{'=' * 25} File: {relative_filepath} {'=' * 25}\n\n")
                            outfile.write(content)
                            # Ensure a newline separates files clearly
                            if content and not content.endswith('\n'):
                                outfile.write('\n')
                            outfile.write("\n\n") # Extra blank lines for separation

                            processed_file_count += 1
                            try:
                                total_bytes_processed += os.path.getsize(filepath_abs)
                            except OSError:
                                pass
                        except Exception as write_err:
                            logging.error(f"Error writing content for {relative_filepath} to output: {write_err}")
                            continue

        # --- Post-processing ---
        logging.info("-" * 60)
        logging.info("Scan complete.")
        logging.info(f"Processed {processed_file_count} files.")
        logging.info(f"Total size included: {total_bytes_processed / 1024:.2f} KB")
        logging.info(f"Consolidated content written to: {output_filepath_abs}")
        return True

    except IOError as e:
        logging.error(f"Fatal I/O error writing to output file '{output_filepath_abs}': {e}")
        return False
    except Exception as e:
        logging.exception(f"An unexpected fatal error occurred: {e}")
        return False

# --- Main Execution Guard ---
if __name__ == "__main__":
    # --- Setup Logging ---
    setup_logging() # Use default log level

    # --- Determine Paths Automatically ---
    try:
        # Directory containing this script file
        script_abspath = os.path.abspath(__file__)
        scan_directory = os.path.dirname(script_abspath)

        # Directory containing the scan directory (one level up)
        parent_dir = os.path.dirname(scan_directory)
        if not parent_dir: # Handle case where script is in root directory '/'
            parent_dir = '.' # Output to current dir in that unlikely case
            logging.warning("Script appears to be in the root directory. Outputting to '.'")


        # Base name for the output file (e.g., "consolidated_FoSBot.txt")
        scan_dir_name = os.path.basename(scan_directory)
        if not scan_dir_name: # Handle case where script dir is root '/'
            scan_dir_name = "root"
        output_basename = f"consolidated_{scan_dir_name}.txt"

        # Full path for the output file
        output_filename = os.path.join(parent_dir, output_basename)

    except Exception as path_err:
        logging.error(f"Could not automatically determine scan/output paths: {path_err}")
        sys.exit(1)

    # --- Run Consolidation ---
    success = consolidate_files(scan_directory, output_filename)

    # --- Exit Status ---
    if success:
        logging.info("Script finished successfully.")
        sys.exit(0)
    else:
        logging.error("Script finished with errors.")
        sys.exit(1)