#!/usr/bin/env python3

import os
import subprocess
import sys
import shutil
import zipfile
import stat # To make scripts executable
from pathlib import Path
from datetime import datetime
import time
import platform
import secrets # For suggesting APP_SECRET_KEY

# --- Configuration ---
PROJECT_DIR_NAME = "FoSBot"
PYTHON_VERSION_TARGET = "3.13"
PYTHON_VERSION_PACKAGE = f"python@{PYTHON_VERSION_TARGET}"
DATA_DIR_NAME = "data"
VENV_DIR_NAME = "venv"
# Install into a subdirectory of the current working directory
INSTALL_LOCATION = Path.cwd()
ROOT_DIR = INSTALL_LOCATION / PROJECT_DIR_NAME
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
BACKUP_DIR = INSTALL_LOCATION / f"fosbot_backup_{TIMESTAMP}"
MIN_PYTHON_MAJOR, MIN_PYTHON_MINOR = 3, 13 # Minimum required version to run *this* script

# File content dictionary (populated below with ALL reconciled file contents)
FILE_CONTENTS = {}

# --- Helper Functions ---

def print_header(title):
    """Prints a formatted header."""
    print("\n" + "=" * 70)
    print(f"=== {title.upper():^62} ===")
    print("=" * 70)

def print_step(step, total_steps, message):
    """Prints a step indicator."""
    print(f"\n--- Step {step}/{total_steps}: {message} ---")
    time.sleep(0.5) # Small delay for readability

def print_info(message):
    print(f"    [INFO] {message}")

def print_warning(message):
    print(f"    [WARN] {message}")

def print_success(message):
    print(f"    [ OK ] {message}")

def print_error(message, exit_code=1):
    """Prints an error message and optionally exits."""
    print(f"    [FAIL] {message}", file=sys.stderr)
    if exit_code is not None:
        print("\n" + "!" * 70)
        print(f"!!! SETUP FAILED !!!")
        print("!" * 70)
        sys.exit(exit_code)

def run_command(command, check=True, capture_output=False, text=True, shell=False, cwd=None, env=None, print_cmd=True):
    """Runs a shell command, handling errors and output."""
    if print_cmd:
        cmd_str = ' '.join(command) if isinstance(command, list) else command
        print(f"    Running: {cmd_str}")
    try:
        # Always capture stderr
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=text,
            shell=shell,
            cwd=cwd,
            env=env
        )
        stdout, stderr = process.communicate()
        returncode = process.returncode

        if check and returncode != 0:
            raise subprocess.CalledProcessError(returncode, command, output=stdout, stderr=stderr)

        if capture_output:
            return stdout.strip() if stdout else ""
        return True # Indicate success if check=False or returncode is 0

    except FileNotFoundError:
        print_error(f"Command not found: {command[0]}", exit_code=None) # Don't exit immediately
        return False # Indicate failure
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed (Exit Code {e.returncode})", exit_code=None)
        # Always print stderr if available
        if e.stderr: print(f"      STDERR:\n{e.stderr.strip()}", file=sys.stderr)
        if e.stdout and capture_output: print(f"      STDOUT:\n{e.stdout.strip()}", file=sys.stderr) # Print stdout only if captured
        if check: # Exit only if check=True
             sys.exit(1)
        return False # Indicate failure
    except Exception as e:
        print_error(f"An unexpected error occurred running command: {e}", exit_code=1)
        return False # Indicate failure (although will likely exit)

def command_exists(command):
    """Checks if a command exists using shutil.which."""
    return shutil.which(command) is not None

def check_environment():
    """Verify running on macOS and correct Python version."""
    print_header("Checking Environment")
    # Check OS
    if platform.system() != "Darwin":
        print_error("This setup script is designed for macOS and uses Homebrew.", exit_code=1)
    print_success("macOS detected.")

    # Check Python version for this script
    major, minor = sys.version_info[:2]
    if (major, minor) < (MIN_PYTHON_MAJOR, MIN_PYTHON_MINOR):
         print_error(f"This script requires Python {MIN_PYTHON_MAJOR}.{MIN_PYTHON_MINOR} or later to run.")
         print_error(f"You are using {major}.{minor}. Please run with a newer Python version.", exit_code=1)
    print_success(f"Script running with compatible Python {major}.{minor}.")

def backup_existing():
    """Backs up existing project directory if it exists."""
    print_header("Backing Up Existing Directory (if any)")
    if ROOT_DIR.exists():
        print_warning(f"Existing directory found at {ROOT_DIR}")
        print_info(f"Backing up to {BACKUP_DIR}...")
        try:
            shutil.move(str(ROOT_DIR), str(BACKUP_DIR))
            print_success(f"Backup complete: {BACKUP_DIR}")
        except Exception as e:
            print_error(f"Failed to backup existing directory: {e}", exit_code=1)
    else:
        print_info(f"No existing directory found at {ROOT_DIR}. No backup needed.")

def create_project_structure():
    """Creates the necessary directories."""
    print_header("Creating Project Structure")
    print_info(f"Creating project root: {ROOT_DIR}")
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    # Use reconciled structure
    dirs_to_create = [
        "app/core", "app/apis", "app/services",
        "static", "whatnot_extension/icons", DATA_DIR_NAME
    ]
    print_info("Creating subdirectories...")
    for d in dirs_to_create:
        (ROOT_DIR / d).mkdir(parents=True, exist_ok=True)
    print_success("Project directory structure created.")

def create_project_files():
    """Writes all project files from the FILE_CONTENTS dictionary."""
    print_header("Writing Project Files")
    total_files = len(FILE_CONTENTS)
    print_info(f"Writing {total_files} files...")
    for i, (rel_path_str, content) in enumerate(FILE_CONTENTS.items()):
        file_path = ROOT_DIR / rel_path_str
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Remove version history comments before writing
            lines = content.splitlines()
            clean_content = "\n".join(line for line in lines if not line.strip().startswith("# Version History:"))
            # Add a header indicating the file was generated by the script
            generated_header = f"# Generated by install_fosbot.py on {datetime.now().isoformat()}\n"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(generated_header)
                f.write(clean_content.strip() + "\n") # Write content, ensure trailing newline

            # Make shell scripts executable
            if rel_path_str.endswith(".sh"):
                 current_permissions = file_path.stat().st_mode
                 file_path.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        except Exception as e:
            print_error(f"Failed to write file {file_path}: {e}", exit_code=None) # Don't exit immediately
            # Decide whether to continue or exit
            # sys.exit(1)
    print_success(f"All {total_files} project files written.")
    # Create empty JSON data files explicitly
    print_info("Creating empty data files...")
    for data_file in ["settings.json", "checkins.json", "counters.json", "commands.json"]:
        (ROOT_DIR / DATA_DIR_NAME / data_file).touch(exist_ok=True)
        # Optionally write empty JSON object {}
        try:
            with open(ROOT_DIR / DATA_DIR_NAME / data_file, "w") as f:
                 f.write("{}")
        except Exception as e:
             print_warning(f"Could not write empty JSON to {data_file}: {e}")

def install_macos_dependencies():
    """Installs Xcode Tools, Homebrew, Python 3.13, Git, ImageMagick."""
    print_header("Installing macOS Dependencies")
    steps_total = 5

    # 1. Xcode Command Line Tools
    print_step(1, steps_total, "Checking/Installing Xcode Command Line Tools")
    try:
        # Check if tools are installed by running pkgutil (more reliable than xcode-select -p sometimes)
        cmd = ['pkgutil', '--pkg-info=com.apple.pkg.CLTools_Executables']
        run_command(cmd, check=True, capture_output=True, print_cmd=False) # Don't print this check command
        print_success("Xcode Tools already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("Xcode Tools not found or not configured.")
        print_info("Attempting to initiate installation...")
        print_info(">>> Please click 'Install' in the macOS dialog if prompted. <<<")
        print_info("    (This might take several minutes, requires internet)")
        # Trigger install - this command might return before install finishes
        run_command(['xcode-select', '--install'], check=False)

        # Loop to wait for installation completion
        print_info("Waiting for Xcode Tools installation (up to 15 minutes)...")
        timeout = time.time() + 60 * 15 # 15 minute timeout
        installed = False
        while time.time() < timeout:
            try:
                run_command(['pkgutil', '--pkg-info=com.apple.pkg.CLTools_Executables'], check=True, capture_output=True, print_cmd=False)
                print_success("Xcode Tools installation detected.")
                installed = True
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("    Waiting...")
                time.sleep(20) # Wait longer between checks
        if not installed:
            print_error("Xcode Tools installation timed out or failed.", exit_code=None)
            print_error("Please install them manually ('xcode-select --install') and restart this script.", exit_code=1)

    # 2. Homebrew
    print_step(2, steps_total, "Checking/Installing Homebrew")
    brew_executable = shutil.which("brew")
    if not brew_executable:
        print_warning("Homebrew not found.")
        print_info("Installing Homebrew...")
        print_warning(">>> The Homebrew installer might ask for your macOS password. <<<")
        print_info("    (Script will continue, please enter password in terminal if prompted)")
        # Use non-interactive mode if possible, but may still need password
        homebrew_install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        env = os.environ.copy()
        env['NONINTERACTIVE'] = '1' # Attempt non-interactive install
        # Run with shell=True is necessary here
        run_command(homebrew_install_cmd, check=True, shell=True, env=env)
        print_success("Homebrew installation script finished.")

        # Add brew to PATH for *this script execution*
        print_info("Attempting to configure Homebrew PATH for this session...")
        if Path("/opt/homebrew/bin/brew").is_file():
            print_info("Detected Apple Silicon Homebrew path.")
            brew_path_prefix = "/opt/homebrew/bin"
        elif Path("/usr/local/bin/brew").is_file():
            print_info("Detected Intel Homebrew path.")
            brew_path_prefix = "/usr/local/bin"
        else:
             brew_path_prefix = None
             print_error("Could not determine Homebrew installation path after install.", exit_code=1)

        if brew_path_prefix:
             os.environ['PATH'] = brew_path_prefix + os.pathsep + os.environ['PATH']
             print_info(f"Temporarily added {brew_path_prefix} to PATH for script.")
             brew_executable = shutil.which("brew") # Find it again with updated PATH
             if not brew_executable:
                  print_error("Failed to find brew command even after updating PATH.", exit_code=1)
             else:
                  print_success("Brew command found after PATH update.")
                  print_warning(f"IMPORTANT: You may need to add Homebrew to your shell's permanent PATH.")
                  print_warning(f"Run: 'echo 'eval \"\$({brew_executable} shellenv)\"' >> ~/.zprofile' (or your shell's equivalent)")
                  print_warning(f"And then run: 'source ~/.zprofile' or open a new terminal window.")
    else:
        print_success(f"Homebrew already installed at {brew_executable}.")

    print_info("Updating Homebrew (this may take a moment)...")
    run_command([brew_executable, 'update'], check=False) # Don't exit if update fails
    print_info("Running Homebrew doctor...")
    run_command([brew_executable, 'doctor'], check=False) # Run doctor for diagnostics

    # 3. Python 3.13
    print_step(3, steps_total, f"Checking/Installing {PYTHON_VERSION_PACKAGE} via Homebrew")
    run_command([brew_executable, 'install', PYTHON_VERSION_PACKAGE])
    print_success(f"{PYTHON_VERSION_PACKAGE} installed/updated.")

    # 4. Git
    print_step(4, steps_total, "Checking/Installing Git via Homebrew")
    run_command([brew_executable, 'install', 'git'])
    print_success("Git installed/updated.")

    # 5. ImageMagick (Optional)
    print_step(5, steps_total, "Checking/Installing ImageMagick (for icons, optional)")
    if not command_exists("convert"):
        print_warning("ImageMagick ('convert' command) not found.")
        if run_command([brew_executable, 'install', 'imagemagick'], check=False): # Don't fail script if this fails
            if command_exists("convert"): # Check again after install
                 print_success("ImageMagick installed.")
            else:
                print_warning("ImageMagick installed, but 'convert' command still not found in PATH.")
        else:
            print_warning("Failed to install ImageMagick. Icon generation will be skipped.")
    else:
        print_success("ImageMagick already installed.")

def find_python_executable() -> str:
    """Finds the installed Python 3.13 executable, preferring Homebrew."""
    print_info(f"Searching for Python {PYTHON_VERSION_TARGET} executable...")
    brew_executable = shutil.which("brew")
    if brew_executable:
        try:
            prefix_path_str = run_command([brew_executable, '--prefix', PYTHON_VERSION_PACKAGE], capture_output=True, print_cmd=False)
            if prefix_path_str:
                prefix_path = Path(prefix_path_str)
                potential_exec = prefix_path / "bin" / f"python{PYTHON_VERSION_TARGET}"
                if potential_exec.is_file() and os.access(potential_exec, os.X_OK):
                    print_success(f"Found executable via brew prefix: {potential_exec}")
                    return str(potential_exec)
        except Exception as e:
            print_warning(f"Could not get brew prefix for {PYTHON_VERSION_PACKAGE}: {e}")

    # Fallback checks
    common_paths = [
         f"/opt/homebrew/opt/{PYTHON_VERSION_PACKAGE}/bin/python{PYTHON_VERSION_TARGET}",
         f"/usr/local/opt/{PYTHON_VERSION_PACKAGE}/bin/python{PYTHON_VERSION_TARGET}",
         f"/opt/homebrew/bin/python{PYTHON_VERSION_TARGET}", # Linked path
         f"/usr/local/bin/python{PYTHON_VERSION_TARGET}" # Linked path
    ]
    for path_str in common_paths:
        path_obj = Path(path_str)
        if path_obj.is_file() and os.access(path_obj, os.X_OK):
            print_success(f"Found executable at common path: {path_obj}")
            return str(path_obj)

    # Last resort: check PATH directly
    path_in_command = shutil.which(f"python{PYTHON_VERSION_TARGET}")
    if path_in_command:
        print_warning(f"Using system PATH '{path_in_command}'. Ensure this is the Homebrew {PYTHON_VERSION_TARGET} version.")
        return path_in_command

    print_error(f"Could not find Python {PYTHON_VERSION_TARGET} executable.", exit_code=1)
    return "" # Should not be reached due to exit

def setup_python_venv():
    """Creates venv and installs dependencies."""
    print_header("Setting up Python Virtual Environment")
    steps_total = 3

    venv_path = ROOT_DIR / VENV_DIR_NAME

    # 1. Find Python Executable
    print_step(1, steps_total, f"Finding Python {PYTHON_VERSION_TARGET}")
    python_executable = find_python_executable()

    # 2. Create Virtual Environment
    print_step(2, steps_total, f"Creating virtual environment ('{VENV_DIR_NAME}')")
    if venv_path.exists():
        print_warning(f"Removing existing venv at: {venv_path}")
        shutil.rmtree(venv_path)
    run_command([python_executable, "-m", "venv", str(venv_path.name)], cwd=ROOT_DIR) # Use relative path name for venv command

    pip_path = venv_path / "bin" / "pip"
    python_in_venv = venv_path / "bin" / "python"
    if not pip_path.is_file() or not python_in_venv.is_file():
        print_error(f"Venv creation failed: Core executables missing in {venv_path / 'bin'}.", exit_code=1)
    print_success(f"Virtual environment created at {venv_path}")

    # 3. Install Dependencies
    print_step(3, steps_total, "Installing Python dependencies")
    requirements_file = ROOT_DIR / "requirements.txt"
    pip_executable = str(pip_path)
    print_info("Upgrading pip...")
    run_command([pip_executable, "install", "--upgrade", "pip", "--quiet"], cwd=ROOT_DIR)
    print_info("Installing packages from requirements.txt...")
    run_command([pip_executable, "install", "-r", str(requirements_file)], cwd=ROOT_DIR)
    print_success("Python dependencies installed.")

def generate_icons():
    """Generates placeholder icons using ImageMagick if available."""
    print_header("Generating Placeholder Icons")
    icon_dir = ROOT_DIR / "whatnot_extension" / "icons"
    # icon_dir is created during create_project_structure

    convert_executable = shutil.which("convert")
    if convert_executable:
        print_info("ImageMagick 'convert' found. Generating icons...")
        icon_color = "rgba(44,62,80,0.9)" # Dark blue-gray
        sizes = {"icon16.png": "16x16", "icon48.png": "48x48", "icon128.png": "128x128"}
        all_success = True
        for filename, size in sizes.items():
            output_path = icon_dir / filename
            if not run_command([convert_executable, '-size', size, f'xc:{icon_color}', str(output_path)], check=False):
                 print_warning(f"Failed to generate {filename}.")
                 all_success = False
        if all_success:
             print_success("Placeholder icons generated.")
        else:
             print_warning("Some icons failed to generate. Manual creation might be needed.")

    else:
        print_warning("ImageMagick 'convert' not found. Skipping icon generation.")
        print_info(f"Please create placeholder PNG icons manually in: {icon_dir}")

def create_extension_zip():
    """Creates the whatnot_extension.zip file in the static directory."""
    print_header("Creating Whatnot Extension ZIP")
    source_dir = ROOT_DIR / "whatnot_extension"
    target_zip = ROOT_DIR / "static" / "whatnot_extension.zip"
    target_zip.parent.mkdir(parents=True, exist_ok=True) # Ensure static dir exists

    if not source_dir.is_dir():
        print_error(f"Source directory not found: {source_dir}. Cannot create ZIP.", exit_code=None) # Don't exit script
        return

    try:
        print_info(f"Zipping contents of {source_dir} into {target_zip}...")
        with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file == '.DS_Store': continue # Skip macOS metadata
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
        print_success(f"Extension ZIP created: {target_zip}")
    except Exception as e:
        print_error(f"Failed to create extension ZIP: {e}", exit_code=None) # Don't exit script

def print_final_instructions():
    """Prints the necessary steps for the user after the script finishes."""
    print_header("Setup Complete! Next Steps:")
    print("1.  **Configure Secrets:**")
    print(f"    - Navigate to the project directory: cd {PROJECT_DIR_NAME}")
    print(f"    - Copy the example environment file: cp .env.example .env")
    print(f"    - **Edit the `.env` file:** Open it in a text editor.")
    print(f"    - Fill in YOUR **Application** credentials (`TWITCH_APP_CLIENT_ID`, etc.) from the developer portals.")
    print(f"    - Generate a unique `APP_SECRET_KEY` by running this in your terminal:")
    print(f"      `python -c \"import secrets; print(secrets.token_hex(32))\"`")
    print(f"    - Paste the generated key into the `APP_SECRET_KEY` field in `.env`.")
    print("\n2.  **Activate Environment & Run:**")
    print(f"    - Activate the virtual environment: `source venv/bin/activate`")
    print(f"    - Start the FoSBot application: `uvicorn app.main:app --reload`")
    print("\n3.  **Open Dashboard & Authenticate:**")
    print(f"    - Open your browser to: http://localhost:{settings.get('WS_PORT', 8000)}")
    print(f"    - Go to the 'Settings' tab.")
    print(f"    - Click 'Login' for Twitch, YouTube, and X. Follow the prompts to authorize **the account you want the bot to use**.")
    print("\n4.  **Set Up Whatnot Extension:**")
    print(f"    - On the Settings tab, click 'Download Whatnot Extension'.")
    print(f"    - Unzip the downloaded file.")
    print(f"    - In Chrome, go to `chrome://extensions/`, enable 'Developer mode', click 'Load unpacked', and select the unzipped folder.")
    print(f"    - Go to a Whatnot stream, click the extension icon, check 'Turn On Setup Mode', and follow the on-page instructions to click chat elements.")
    print(f"    - Click 'Done' in the setup panel, then 'Test Setup' in the popup. Uncheck 'Turn On Setup Mode'.")
    print("\n5.  **Start Services:**")
    print(f"    - On the Settings tab -> Service Control, click 'Start' for the platforms you want to use.")
    print("\n--- FoSBot is ready to go! ---")


# --- Main Execution ---
if __name__ == "__main__":

    # --- Populate FILE_CONTENTS Dictionary ---
    # Use raw strings (r"""...""") and ensure correct indentation inside the strings.
    # <<< PASTE THE HUGE RECONCILED FILE_CONTENTS DICTIONARY HERE >>>
    # (From the previous detailed response where we reconciled the files)
    # Example structure:
    FILE_CONTENTS = {
        # === Root Files ===
        ".env.example": r"""# --- File: .env.example --- START ---
# Copy this file to .env and fill in your values.
# DO NOT COMMIT .env TO GIT!

# --- Application Settings ---
COMMAND_PREFIX=!
WS_HOST=localhost
WS_PORT=8000
LOG_LEVEL=DEBUG # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
DATA_DIR=data

# --- OAuth Application Credentials (FOR APP OWNER ONLY) ---
# Obtain these by registering FoSBot as an application on each platform's developer portal.
# These are NOT the user's login credentials.
# Twitch: https://dev.twitch.tv/console/apps
TWITCH_APP_CLIENT_ID=YOUR_TWITCH_CLIENT_ID_HERE
TWITCH_APP_CLIENT_SECRET=YOUR_TWITCH_CLIENT_SECRET_HERE

# YouTube (Google Cloud Console): https://console.cloud.google.com/apis/credentials
# Ensure you enable the YouTube Data API v3. Create OAuth 2.0 Client ID (Web application).
# Add http://localhost:8000 and http://localhost:8000/auth/youtube/callback to Authorized JavaScript origins and Authorized redirect URIs.
YOUTUBE_APP_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com
YOUTUBE_APP_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET_HERE

# X (Twitter Developer Portal): https://developer.twitter.com/en/portal/projects-and-apps
# Create an app with OAuth 1.0a enabled. Set permissions (Read/Write needed for bot).
# Add http://localhost:8000/auth/x/callback as the Callback URI.
X_APP_CLIENT_ID=YOUR_X_API_KEY_HERE
X_APP_CLIENT_SECRET=YOUR_X_API_SECRET_HERE

# --- Security (FOR APP OWNER ONLY) ---
# Generate a strong, unique secret key for securing OAuth states.
# Use: python -c "import secrets; print(secrets.token_hex(32))"
APP_SECRET_KEY=YOUR_GENERATED_32_BYTE_HEX_SECRET_KEY_HERE
# --- File: .env.example --- END ---
""",
        ".gitignore": r"""# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.so
build/
dist/
*.egg-info/
wheels/
pip-wheel-metadata/
share/jupyter/
profile_default/
ipython_config.py

# Environments
.env
.venv
venv/
env/
ENV/
# Note: exclude .env only, NOT .env.example

# Data Files (Sensitive!)
data/*.json
# Keep empty placeholder files if needed for git tracking, but ignore content changes
# !data/.gitkeep

# Logs
*.log
*.log.*
logs/

# Runtime data
*.sqlite
*.sqlite3
*.db
*.db-journal
*.db-shm
*.db-wal
celerybeat-schedule.*
*.pid
*.pid.lock

# IDEs & Editors
.vscode/
.idea/
*.sublime-*
nbproject/
*.swp
*.swo
*~

# OS Generated files
.DS_Store
Thumbs.db

# Coverage reports
.coverage
.coverage.*
htmlcov/
.pytest_cache/

# Extension Build Artifacts
*.zip

# Backup Directories (Matches pattern in setup script)
fosbot_backup_*/
""",
        "requirements.txt": r"""fastapi>=0.110.0
uvicorn[standard]>=0.29.0
python-dotenv>=1.0.0
twitchio>=2.10.0
google-api-python-client>=2.80.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
tweepy>=4.13.0 # Ensure this version supports needed X API v2 endpoints
websockets>=11.0.0 # For FastAPI WebSockets and Whatnot Bridge server
httpx>=0.27.0 # For async HTTP requests (OAuth, API calls)
# aiohttp>=3.8.0 # Can often be replaced by httpx, keep if specifically needed by a library
nest-asyncio>=1.5.0 # Helpful for running async tasks within sync contexts if needed (e.g., some library callbacks)
aiofiles>=23.1.0 # For async file I/O
pydantic>=2.0.0
typing-extensions>=4.8.0
# Base uvicorn[standard] deps & others
click>=7.0
h11>=0.8
httptools>=0.5.0
pyyaml>=5.1
uvloop>=0.17.0 # Performance improvement for asyncio loop
watchfiles>=0.13 # For uvicorn --reload
certifi # SSL certificates
googleapis-common-protos>=1.56.2,<2.0.0 # Google API dependency
protobuf>=3.19.5,<7.0.0 # Google API dependency (adjust upper bound if needed)
proto-plus>=1.22.3,<2.0.0 # Google API dependency
cachetools>=2.0.0,<6.0 # Google API dependency
pyasn1-modules>=0.2.1 # Google API dependency
rsa>=3.1.4,<5 # Google API dependency
pyparsing!=3.0.0,!=3.0.1,!=3.0.2,!=3.0.3,<4,>=2.4.2 # Dependency
charset-normalizer<4,>=2 # Dependency (often via httpx/requests)
urllib3<3,>=1.21.1 # Dependency (often via httpx/requests)
sniffio>=1.1 # Async library dependency
pyasn1>=0.6.1,<0.8.0 # Google API dependency (adjusted upper bound)
attrs>=17.3.0 # Dependency
frozenlist>=1.1.1 # aiohttp dependency
multidict<7.0,>=4.5 # aiohttp dependency
yarl<2.0,>=1.0 # aiohttp dependency
annotated-types>=0.4.0 # Pydantic dependency
# typing-inspection>=0.4.0 # Optional Pydantic dependency
idna # Dependency
aiosignal>=1.1.2 # aiohttp dependency
oauthlib<4,>=3.2.0 # OAuth handling library (used by tweepy, google-auth)
# requests<3,>=2.27.0 # Replaced by httpx generally
httpcore>=1.0.0,<2.0.0 # httpx dependency
aiohappyeyeballs>=2.3.0 # aiohttp dependency
""",
        "README.md": r"""# FoSBot: Your Epic Stream Chat Adventure

Welcome, brave streamer, to **FoSBot**--the ultimate companion for your Magic: The Gathering and Dungeons & Dragons live streams! This bot unites Whatnot, YouTube, Twitch, and X chats into one magical dashboard, letting you engage your party with commands like `!checkin`, `!ping`, and `!roll`. Roll for initiative and let's get started!

## Your Quest: Setup (Level 1 - Easy)

### Prerequisites
-   **Python 3.13**: Your trusty spellbook. Install it from [python.org](https://www.python.org/downloads/) or via Homebrew (`brew install python@3.13`).
-   **Chrome Browser**: Your enchanted portal to the dashboard.
-   **Git**: For version control (optional but recommended). `brew install git`.
-   **(Optional) ImageMagick**: For icon generation during setup. `brew install imagemagick`.

### Step 1: Get the Code
1.  **Clone or Download**:
    *   **Git:** `git clone <your-repo-url> FoSBot`
    *   **Manual:** Download the source code (e.g., `fosbot.zip`) and unzip it into a `FoSBot` folder.
2.  **Navigate**:
    *   Open Terminal (Mac: Spotlight > "Terminal").
    *   Change to the project directory: `cd path/to/FoSBot`

### Step 2: Configure Your Arcane Secrets (.env)
1.  **Create `.env`**: Copy the example file: `cp .env.example .env`
2.  **Edit `.env`**: Open the new `.env` file in a text editor.
3.  **Fill in App Credentials**:
    *   Go to the developer portals for Twitch, Google Cloud (for YouTube), and X (Twitter). Register "FoSBot" as an application.
    *   **Crucially**: Paste your application's `CLIENT_ID` and `CLIENT_SECRET` (or API Key/Secret for X) into the corresponding `TWITCH_APP_*`, `YOUTUBE_APP_*`, `X_APP_*` variables in `.env`.
    *   **Callback URLs**: Ensure you register the correct callback URLs in each developer portal:
        *   Twitch: `http://localhost:8000/auth/twitch/callback`
        *   YouTube: `http://localhost:8000/auth/youtube/callback` (Also add `http://localhost:8000` as an authorized JavaScript origin).
        *   X/Twitter: `http://localhost:8000/auth/x/callback`
4.  **Generate Security Key**:
    *   Run this command in your terminal: `python -c "import secrets; print(secrets.token_hex(32))"`
    *   Paste the generated key as the value for `APP_SECRET_KEY` in `.env`.
5.  **Review Other Settings**: Adjust `COMMAND_PREFIX`, `LOG_LEVEL`, `WS_HOST`, `WS_PORT` if needed.

### Step 3: Prepare Your Magic Circle (venv & Dependencies)
1.  **Create Virtual Environment**:
    *   `python3.13 -m venv venv` (Use the specific Python 3.13 command).
2.  **Activate Environment**:
    *   `source venv/bin/activate` (You should see `(venv)` at the start of your prompt).
3.  **Install Dependencies**:
    *   `pip install -r requirements.txt`

### Step 4: Launch the Portal (Run the App)
1.  **Run Uvicorn**:
    *   `uvicorn app.main:app --host localhost --port 8000 --reload`
    *   `--reload` automatically restarts the server when code changes (good for development). Remove it for "production" use.
    *   Look for the "Application startup complete" log message.

### Step 5: Enter the Dashboard & Authenticate
1.  **Open Dashboard**: In Chrome, go to `http://localhost:8000`.
2.  **Authenticate Platforms**:
    *   Navigate to the **Settings** tab.
    *   Click "Login with Twitch", "Login with YouTube", "Login with X".
    *   Follow the prompts on each platform's website, authorizing FoSBot to access the necessary permissions **for the account you want the bot to use**.
    *   You'll be redirected back to the dashboard. A success message should appear briefly, and the status should update to "Logged in as [YourUsername]".
3.  **Configure Twitch Channels (If Bot != Streamer)**:
    *   If your bot account is different from your streaming channel, enter the channel name(s) you want the bot to join in the "Extra Twitch Channels" field on the Settings tab and click Save. If left blank, it defaults to the bot's own channel name.
4.  **Whatnot Extension Setup**:
    *   Go to the **Settings** tab -> **Whatnot Integration**.
    *   Click the "Download Whatnot Extension" link (`/whatnot_extension.zip`).
    *   Unzip the downloaded file into a dedicated folder (e.g., `~/FoSBot_Whatnot_Extension`).
    *   Open Chrome, go to `chrome://extensions/`.
    *   Enable "Developer mode" (usually a toggle in the top-right).
    *   Click "Load unpacked".
    *   Select the `FoSBot_Whatnot_Extension` folder you unzipped.
    *   Navigate to an active Whatnot stream page.
    *   Click the FoSBot puzzle piece icon in your Chrome toolbar.
    *   Check the "Turn On Setup Mode" box in the popup.
    *   A setup panel will appear overlaid on the Whatnot page. Carefully follow its prompts:
        *   Click the main area where chat messages appear.
        *   Click *any single* chat message container/row.
        *   Click the *username* within that message row.
        *   Click the *message text* within that same row.
    *   Click "Next" in the setup panel after *each* selection.
    *   When all steps are done, click "Done" in the setup panel. The panel will disappear.
    *   Go back to the extension popup (click the icon again) and click "Test Setup". You should see a success message if the selectors are working.
    *   **Important**: Uncheck "Turn On Setup Mode" in the popup when finished.
    *   *(Optional)* Watch the setup video: [Link to your video if available]

### Step 6: Start Services
-   Go to the **Settings** tab -> **Service Control**.
-   Click "Start" for each service (Twitch, YouTube, X, Whatnot) you want the bot to actively monitor and participate in.
-   Monitor the status indicators in the header and the logs in the sidebar/terminal for confirmation or errors.

## Using FoSBot
-   **Chat Tab**: View aggregated chat from all *started* and *connected* services. Type messages or commands (e.g., `!ping`) in the input box and click "Send" to broadcast or execute commands.
-   **Commands Tab**:
    *   View existing custom commands.
    *   Add new commands using the form (don't include the `!` prefix). Use `{user}` to mention the user who triggered the command.
    *   Delete commands using the "Delete" link.
    *   Upload commands in bulk using a CSV file (format: first column `command_name`, second column `response_text`, optional header row).
-   **Settings Tab**:
    *   Manage platform logins/logouts.
    *   Adjust `COMMAND_PREFIX`, `LOG_LEVEL`, `TWITCH_CHANNELS`.
    *   Start/Stop/Restart individual platform services.

## Troubleshooting
-   **Login Issues?**
    *   Verify `APP_SECRET_KEY` and `*_APP_CLIENT_ID`/`*_APP_CLIENT_SECRET` in your `.env` are correct and match your developer portal configurations.
    *   Ensure Callback/Redirect URIs (`http://localhost:8000/...`) are correctly registered in the developer portals.
    *   Check the terminal logs (`uvicorn` output) for specific error messages during the OAuth callback.
    *   Ensure you are granting the necessary permissions during the platform's authorization step.
-   **Whatnot Not Working?**
    *   This is the most fragile part due to website changes.
    *   Redo the extension setup process *carefully* on an active stream.
    *   Click "Test Setup" in the extension popup. If it fails, the selectors are likely wrong or the Whatnot page structure changed.
    *   Check the browser's DevTools Console (on the Whatnot page) and the FoSBot terminal logs for errors related to the extension or WebSocket connection.
    *   Ensure the "Whatnot" service is "Started" in the FoSBot Settings tab.
-   **App Won't Run?**
    *   Confirm Python 3.13: `python3.13 --version`.
    *   Confirm venv is active: `which python` should point inside your `venv` directory.
    *   Reinstall dependencies: `pip install -r requirements.txt`.
    *   Check terminal for Uvicorn/FastAPI startup errors.
-   **Services Won't Start/Connect?**
    *   Verify authentication status on the Settings tab. Re-login if necessary.
    *   Check API keys/tokens are valid (platforms sometimes expire them). Check terminal logs for connection errors from `twitchio`, `googleapiclient`, `tweepy`, or `websockets`.
    *   Ensure the relevant API is enabled in the developer portal (e.g., YouTube Data API v3).
    *   Check network connectivity and firewalls.

*Good luck with your stream!*
""",

        # === app/ Files ===
        "app/__init__.py": r"""# Generated by install_fosbot.py
# Empty file to make app a package
""",
        "app/main.py": r"""# Generated by install_fosbot.py
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
import zipfile # For creating zip file
import os # For walking directory

# Core Imports
# Use settings object directly now
from app.core.config import logger, settings, DATA_DIR
from app.core.event_bus import event_bus

# API Routers
from app.apis import ws_endpoints, settings_api, auth_api, commands_api

# Service Control & Setup
from app.services.twitch_service import start_twitch_service_task, stop_twitch_service
from app.services.youtube_service import start_youtube_service_task, stop_youtube_service
from app.services.x_service import start_x_service_task, stop_x_service
from app.services.whatnot_bridge import start_whatnot_bridge_task, stop_whatnot_bridge
from app.services.chat_processor import setup_chat_processor
from app.services.dashboard_service import setup_dashboard_service_listeners
# Corrected import name based on file presence
from app.services.streamer_command_handler import setup_streamer_command_handler

# Events
from app.events import ServiceControl

# Global State
background_tasks: set[asyncio.Task] = set()
_service_tasks_map: dict[str, asyncio.Task | None] = {}

# Service Control Mapping
service_control_map = {
    "twitch": {"start": start_twitch_service_task, "stop": stop_twitch_service},
    "youtube": {"start": start_youtube_service_task, "stop": stop_youtube_service},
    "x": {"start": start_x_service_task, "stop": stop_x_service},
    "whatnot": {"start": start_whatnot_bridge_task, "stop": stop_whatnot_bridge},
}

async def handle_service_control(event: ServiceControl):
    """Handles start/stop/restart commands for services via the event bus."""
    service_name = event.service_name.lower()
    command = event.command.lower()
    logger.info(f"Handling control: '{command}' for '{service_name}'...")
    logger.debug(f"Service control event details: {event}")
    control_funcs = service_control_map.get(service_name)
    current_task = _service_tasks_map.get(service_name)

    if not control_funcs:
        logger.error(f"No control functions found for service '{service_name}'.")
        return

    start_func = control_funcs.get("start")
    stop_func = control_funcs.get("stop")

    async def safe_stop():
        """Wrapper to safely call stop function and handle cancellation."""
        task_was_running = False
        if current_task and not current_task.done():
            task_was_running = True
            logger.info(f"Attempting to stop service '{service_name}'...")
            if stop_func:
                try:
                    # Check if stop_func is a coroutine function
                    if asyncio.iscoroutinefunction(stop_func):
                        await stop_func()
                    else:
                        # If it's a regular function, run it in an executor
                        # This prevents blocking the main event loop if stop_func is synchronous
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, stop_func)

                    logger.info(f"Service '{service_name}' stop function called successfully.")
                    # Give a brief moment for async cleanup within the service
                    await asyncio.sleep(0.5)
                    return True # Indicate stop function was called
                except Exception as e:
                    logger.error(f"Error calling stop function for service '{service_name}': {e}", exc_info=True)
                    # Fall through to cancellation if stop fails
            else:
                logger.warning(f"No stop function defined for '{service_name}'.")

            # If no stop function or stop failed, try direct cancellation
            logger.warning(f"Attempting direct cancellation for '{service_name}' task.")
            if not current_task.cancelling():
                current_task.cancel()
                try:
                    # Give cancellation a moment, don't wait indefinitely
                    await asyncio.wait_for(current_task, timeout=2.0)
                except asyncio.CancelledError:
                    logger.info(f"Task for '{service_name}' cancelled successfully.")
                    return True # Cancellation succeeded
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for '{service_name}' task cancellation.")
                except Exception as e:
                     logger.error(f"Error awaiting cancelled task '{service_name}': {e}", exc_info=True)
            return False # Indicate stop might not have been fully graceful
        else:
            logger.info(f"Service '{service_name}' not running or already stopped/done.")
            return True # No stop action needed

    if command == "stop":
        await safe_stop()
        _service_tasks_map[service_name] = None # Clear task ref after stop attempt

    elif command == "start":
        if current_task and not current_task.done():
            logger.warning(f"Service '{service_name}' already running or starting.")
            return

        if start_func:
            logger.info(f"Executing start for '{service_name}'...")
            try:
                # Start func should return the task
                new_task = start_func()
                if new_task and isinstance(new_task, asyncio.Task):
                    _service_tasks_map[service_name] = new_task
                    background_tasks.add(new_task)
                    # Remove from set upon completion (or error/cancellation)
                    new_task.add_done_callback(background_tasks.discard)
                    logger.info(f"Task for '{service_name}' started and added to background tasks.")
                elif new_task is None:
                    logger.warning(f"Start function for '{service_name}' returned None (maybe disabled/failed pre-check?).")
                else:
                    logger.error(f"Start function for '{service_name}' returned invalid object type: {type(new_task)}")
            except Exception as e:
                logger.error(f"Error calling start function for '{service_name}': {e}", exc_info=True)
        else:
            logger.warning(f"No start function defined for '{service_name}'.")

    elif command == "restart":
        logger.info(f"Executing restart for '{service_name}'...")
        await safe_stop() # Attempt graceful stop first
        await asyncio.sleep(1) # Brief pause to allow resources release
        _service_tasks_map[service_name] = None # Ensure old task ref is cleared

        # Now attempt start (same logic as 'start' command)
        if start_func:
            logger.info("...restarting service instance.")
            try:
                new_task = start_func()
                if new_task and isinstance(new_task, asyncio.Task):
                    _service_tasks_map[service_name] = new_task
                    background_tasks.add(new_task)
                    new_task.add_done_callback(background_tasks.discard)
                    logger.info(f"Task for '{service_name}' created after restart.")
                elif new_task is None:
                    logger.warning(f"Start function for '{service_name}' did not return task on restart.")
                else:
                     logger.error(f"Start function '{service_name}' returned invalid object on restart: {type(new_task)}")
            except Exception as e:
                logger.error(f"Error calling start function for '{service_name}' during restart: {e}", exc_info=True)
        else:
            logger.warning(f"No start function available for restart of '{service_name}'.")

# Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("--- FoSBot Application Startup Sequence ---")
    logger.info("Starting event bus worker...")
    await event_bus.start()
    logger.info("Setting up event listeners...")
    # Setup core components first
    try: await setup_chat_processor(); logger.debug("Chat processor setup.")
    except Exception as e: logger.error(f"Error setting up chat processor: {e}", exc_info=True)
    try: setup_dashboard_service_listeners(); logger.debug("Dashboard listeners setup.")
    except Exception as e: logger.error(f"Error setting up dashboard listeners: {e}", exc_info=True)
    try: setup_streamer_command_handler(); logger.debug("Streamer command handler setup.")
    except Exception as e: logger.error(f"Error setting up streamer command handler: {e}", exc_info=True)

    # Subscribe the main service controller
    event_bus.subscribe(ServiceControl, handle_service_control)
    logger.info("Service control handler subscribed.")
    logger.info("Attempting initial start of services (if configured with valid tokens)...")

    # Attempt to start services that might have existing valid tokens
    initial_start_tasks = [
        handle_service_control(ServiceControl(service_name="twitch", command="start")),
        handle_service_control(ServiceControl(service_name="youtube", command="start")),
        handle_service_control(ServiceControl(service_name="x", command="start")),
        handle_service_control(ServiceControl(service_name="whatnot", command="start")) # Whatnot bridge connects to extension
    ]
    # Run starts concurrently, ignoring errors (individual services log issues)
    await asyncio.gather(*initial_start_tasks, return_exceptions=True)
    logger.info("--- Application startup complete. FoSBot is Running! ---")

    yield # App runs here

    logger.info("--- FoSBot Application Shutdown Sequence ---")
    logger.info("Stopping platform services...")
    stop_tasks = [
        # Use handle_service_control for graceful shutdown/cancellation
        handle_service_control(ServiceControl(service_name=name, command="stop"))
        for name in service_control_map.keys()
    ]
    try:
        await asyncio.gather(*stop_tasks, return_exceptions=True)
        logger.info("Service stop commands processed.")
    except Exception as e:
        logger.error(f"Error during service stop gathering: {e}", exc_info=True)

    logger.info("Waiting briefly for service task cleanup...")
    await asyncio.sleep(2)

    logger.info("Stopping event bus worker...")
    await event_bus.stop()

    # Final check for any remaining background tasks
    # Copy the set as it might be modified during iteration by callbacks
    remaining_tasks = list(background_tasks)
    if remaining_tasks:
        logger.warning(f"Attempting final cancellation for {len(remaining_tasks)} lingering tasks...")
        for task in remaining_tasks:
            if task and not task.done():
                task.cancel()
        try:
            await asyncio.wait_for(asyncio.gather(*remaining_tasks, return_exceptions=True), timeout=5.0)
            logger.debug("Gathered lingering background tasks after cancellation attempt.")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for lingering background tasks to cancel.")
        except Exception as e:
            logger.exception(f"Error during final gathering of cancelled tasks: {e}")
    else:
        logger.info("No lingering background tasks found during shutdown.")
    logger.info("--- Application shutdown complete. ---")


# FastAPI App Creation
app = FastAPI(
    title="FoSBot (Multi-Platform Streaming Assistant)",
    version="0.7.3", # Reflecting integrated state
    lifespan=lifespan
)

# --- API Routers ---
app.include_router(auth_api.router) # Handles /auth/... routes
app.include_router(ws_endpoints.router, prefix="/ws") # Handles /ws/... routes
app.include_router(settings_api.router, prefix="/api") # Handles /api/settings, /api/control
app.include_router(commands_api.router, prefix="/api") # Handles /api/commands

# --- Serve Whatnot Extension ZIP ---
EXTENSION_ZIP_NAME = "whatnot_extension.zip"
static_extension_zip_path = Path("static") / EXTENSION_ZIP_NAME
source_extension_dir = Path("whatnot_extension")

async def ensure_extension_zip():
    """Creates or updates the extension zip file in static dir if source is newer."""
    if not source_extension_dir.is_dir():
        logger.error(f"Source extension directory not found: {source_extension_dir}")
        return None

    # Check modification times to avoid unnecessary zipping
    try:
        source_files = list(source_extension_dir.rglob('*'))
        if not source_files: # Handle empty source dir case
             logger.warning(f"Source extension directory {source_extension_dir} is empty.")
             return None
        source_mtime = max(f.stat().st_mtime for f in source_files if f.is_file())
        target_exists = static_extension_zip_path.exists()
        target_mtime = static_extension_zip_path.stat().st_mtime if target_exists else 0

        if not target_exists or source_mtime > target_mtime:
            logger.info(f"Creating/updating {static_extension_zip_path} from {source_extension_dir}...")
            static_extension_zip_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(static_extension_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in source_files:
                     if file_path.is_file() and file_path.name != '.DS_Store':
                          arcname = file_path.relative_to(source_extension_dir)
                          zipf.write(file_path, arcname)
            logger.info(f"Successfully created/updated {static_extension_zip_path}")
        # else: logger.debug("Extension zip is up-to-date.") # Optional: log if up-to-date
    except Exception as e:
        logger.error(f"Failed to check/create extension zip: {e}", exc_info=True)
        return None # Return None if creation failed

    return static_extension_zip_path # Return path


@app.get(f"/{EXTENSION_ZIP_NAME}")
async def serve_whatnot_extension():
    """Serves the Whatnot extension ZIP file, creating/updating it if necessary."""
    target_zip = await ensure_extension_zip()
    if target_zip and target_zip.is_file():
        return FileResponse(target_zip, media_type="application/zip", filename=EXTENSION_ZIP_NAME)
    else:
        # Fallback check at root (less preferred)
        root_zip_path = Path(EXTENSION_ZIP_NAME)
        if root_zip_path.is_file():
             logger.warning(f"Serving extension zip from root directory: {root_zip_path}")
             return FileResponse(root_zip_path, media_type="application/zip", filename=EXTENSION_ZIP_NAME)

        logger.error(f"Whatnot extension ZIP file could not be created or found at {static_extension_zip_path} or root.")
        raise HTTPException(status_code=404, detail=f"{EXTENSION_ZIP_NAME} not found or could not be created.")


# --- Mount Static Files for Dashboard UI ---
STATIC_DIR = "static"
static_path = Path(STATIC_DIR)
if not static_path.is_dir():
    logger.error(f"Static files directory '{STATIC_DIR}' not found at {static_path.resolve()}. Dashboard UI unavailable.")
else:
    try:
        # Ensure index.html exists
        if not (static_path / "index.html").is_file():
             logger.error(f"index.html not found in static directory '{STATIC_DIR}'. Dashboard UI will not load correctly.")
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
        ws_port = settings.get('WS_PORT', 8000)
        # Determine accessible host address
        ws_host = settings.get('WS_HOST', 'localhost')
        display_host = '127.0.0.1' if ws_host == '0.0.0.0' else ws_host # Use 127.0.0.1 for browser access if listening on all interfaces
        logger.info(f"Mounted static files. Access Dashboard at: http://{display_host}:{ws_port}")
    except Exception as e:
        logger.exception(f"Failed to mount static files directory './{STATIC_DIR}': {e}")

# --- Direct Run (for Debugging) ---
if __name__ == "__main__":
    import uvicorn
    logger.warning("Running via main.py is intended for debugging ONLY.")
    logger.warning("Use 'uvicorn app.main:app --reload --host 0.0.0.0' for development access from other devices on network.")
    # Use settings from config object
    uvicorn.run("app.main:app",
                host=settings.get('WS_HOST', 'localhost'), # Host for the server to bind to
                port=settings.get('WS_PORT', 8000),
                log_level=settings.get('LOG_LEVEL', 'info').lower(),
                reload=True) # Reload is useful for development
""",
        "app/events.py": r"""# Generated by install_fosbot.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import datetime

# Base Event Class (Optional but good practice)
class Event:
    """Base class for all events."""
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

# --- Chat & Bot Events ---
@dataclass
class InternalChatMessage(Event):
    """Standardized internal representation of a chat message."""
    platform: str
    user: str
    text: str
    channel: Optional[str] = None # Channel/Stream ID where msg occurred
    user_id: Optional[str] = None # Platform-specific user ID
    display_name: Optional[str] = None # User's display name (if different)
    message_id: Optional[str] = None # Platform-specific message ID
    is_command: bool = False # Flag set by chat_processor if it's a command
    raw_data: Dict[str, Any] = field(default_factory=dict) # Original platform data

@dataclass
class ChatMessageReceived(Event):
    """Published when any platform service receives a chat message."""
    message: InternalChatMessage

@dataclass
class CommandDetected(Event):
    """Published by chat_processor when a valid command prefix is found."""
    command: str             # The command name (e.g., "ping")
    args: List[str]          # List of arguments after the command
    source_message: InternalChatMessage # The original message that triggered command

@dataclass
class BotResponse(Event): # Renamed for clarity, represents the *data* for a response
    """Represents the data needed to send a bot message."""
    target_platform: str        # Platform to send to (e.g., "twitch")
    text: str                   # Message content
    target_channel: Optional[str] = None # Specific channel/chat ID to send to
    # Optional fields for context/replying
    reply_to_user: Optional[str] = None     # Username to mention/reply to
    reply_to_message_id: Optional[str] = None # Platform message ID to reply to

@dataclass
class BotResponseToSend(Event): # This is the event that triggers sending
    """Published when a service wants to send a response."""
    response: BotResponse

# --- Streamer Dashboard / Input Events ---
@dataclass
class StreamerInputReceived(Event):
    """Published when text is submitted via the dashboard input."""
    text: str

@dataclass
class BroadcastStreamerMessage(Event):
    """Published when streamer input is determined to be a broadcast message."""
    text: str

# --- System & Service Status Events ---
@dataclass
class PlatformStatusUpdate(Event):
    """Published by platform services to report their connection status."""
    platform: str        # e.g., "twitch", "youtube", "x", "whatnot", "websocket"
    status: str          # e.g., "connecting", "connected", "disconnected", "error", "auth_error", "disabled", "stopped", "waiting"
    message: Optional[str] = None # Optional context message

@dataclass
class ServiceControl(Event):
    """Published by the API (or potentially other services) to control platform services."""
    service_name: str # e.g., "twitch", "youtube"
    command: str      # e.g., "start", "stop", "restart"

@dataclass
class SettingsUpdated(Event):
    """Published when settings are successfully saved via the API."""
    keys_updated: List[str] # List of setting keys that were changed

@dataclass
class LogMessage(Event):
    """Published internally to allow centralized logging or dashboard display."""
    level: str # e.g., "INFO", "WARNING", "ERROR", "CRITICAL"
    message: str
    module: Optional[str] = None # Name of the module originating the log

# --- Game-Related Events (Placeholders for Future Phases) ---
@dataclass
class GameEvent(Event):
    """Base class for game-specific events."""
    pass

# Example specific game event
# @dataclass
# class PlayerJoinedGame(GameEvent):
#     player_id: str
#     player_name: str
""",

        # === app/core/ Files ===
        "app/core/__init__.py": r"""# Generated by install_fosbot.py
# Empty file to make core a package
""",
        "app/core/config.py": r"""# Generated by install_fosbot.py
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import warnings

# --- Determine Project Root ---
# Assumes config.py is in app/core/
project_root = Path(__file__).parent.parent.parent

# --- Load .env File ---
env_path = project_root / '.env'
loaded_env = load_dotenv(dotenv_path=env_path, verbose=True)

# --- Setup Logging ---
# Determine log level from environment or default BEFORE basicConfig
raw_log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level_int = getattr(logging, raw_log_level, logging.INFO)

logging.basicConfig(
    level=log_level_int,
    format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__) # Logger for this module
logger.setLevel(log_level_int)

if loaded_env:
    logger.info(f"Loaded .env config from: {env_path.resolve()}")
else:
    logger.info(f"INFO: .env file not found at {env_path.resolve()}. Using defaults and environment variables.")

# --- Initialize Settings Dictionary with Defaults/Env Vars ---
# Non-secrets first
settings = {
    'COMMAND_PREFIX': os.getenv('COMMAND_PREFIX', '!'),
    'WS_HOST': os.getenv('WS_HOST', 'localhost'),
    'WS_PORT': int(os.getenv('WS_PORT', 8000)),
    'LOG_LEVEL': raw_log_level, # Store the string representation
    'DATA_DIR': Path(os.getenv('DATA_DIR', project_root / "data")), # Ensure it's a Path object
}

# Application OAuth Credentials (Loaded from .env ONLY)
TWITCH_APP_CLIENT_ID = os.getenv("TWITCH_APP_CLIENT_ID")
TWITCH_APP_CLIENT_SECRET = os.getenv("TWITCH_APP_CLIENT_SECRET")
YOUTUBE_APP_CLIENT_ID = os.getenv("YOUTUBE_APP_CLIENT_ID")
YOUTUBE_APP_CLIENT_SECRET = os.getenv("YOUTUBE_APP_CLIENT_SECRET")
X_APP_CLIENT_ID = os.getenv("X_APP_CLIENT_ID")
X_APP_CLIENT_SECRET = os.getenv("X_APP_CLIENT_SECRET")

# Security Key (Loaded from .env ONLY)
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

# --- Load Overrides from settings.json ---
# This loads user-specific tokens AND non-secret overrides
settings_file_path = settings['DATA_DIR'] / 'settings.json'
# Create data directory if it doesn't exist *before* trying to read file
DATA_DIR_PATH = settings['DATA_DIR']
try:
    DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
except OSError as e:
     logger.critical(f"CRITICAL ERROR: Could not create data directory '{DATA_DIR_PATH.resolve()}': {e}. Cannot load/save settings.")
     # Exit or raise if data dir is critical
     # raise SystemExit(f"Failed to access data directory: {DATA_DIR_PATH.resolve()}")
     file_settings = {} # Use empty if dir creation failed
else:
    if settings_file_path.is_file():
        try:
            with settings_file_path.open('r', encoding='utf-8') as f:
                file_settings = json.load(f)
            # Update the main settings dict, potentially overriding .env values for non-secrets
            # This allows UI changes to persist over .env defaults
            settings.update(file_settings)
            logger.info(f"Loaded and merged settings from {settings_file_path.resolve()}")
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {settings_file_path.resolve()}. File might be corrupt. Using defaults/env.")
            file_settings = {}
        except Exception as e:
            logger.error(f"Error loading settings from {settings_file_path.resolve()}: {e}", exc_info=True)
            file_settings = {}
    else:
        logger.info(f"Settings file not found at {settings_file_path.resolve()}. Using .env/defaults. Will be created on first save.")
        file_settings = {} # Ensure it's a dict

# --- Post-Load Processing and Validation ---
# Ensure DATA_DIR is a Path object (important!)
if not isinstance(settings['DATA_DIR'], Path):
     settings['DATA_DIR'] = Path(settings['DATA_DIR'])
DATA_DIR = settings['DATA_DIR'] # Make it easily accessible globally if needed

# Update logger level if overridden by settings.json
log_level_str = settings.get('LOG_LEVEL', 'INFO').upper()
log_level_int_final = getattr(logging, log_level_str, logging.INFO)
if logging.getLogger().getEffectiveLevel() != log_level_int_final:
    logger.info(f"Updating root logger level to {log_level_str} based on settings.")
    logging.getLogger().setLevel(log_level_int_final)
    # Also update this module's logger
    logger.setLevel(log_level_int_final)

# Quiet down noisy libraries unless log level is DEBUG
if log_level_int_final > logging.DEBUG:
    noisy_loggers = ["twitchio", "websockets", "googleapiclient", "google.auth", "httpx", "watchfiles", "tweepy"]
    for log_name in noisy_loggers:
        logging.getLogger(log_name).setLevel(logging.WARNING)

# Validate essential App Owner secrets (from .env)
missing_secrets = []
if not TWITCH_APP_CLIENT_ID: missing_secrets.append("TWITCH_APP_CLIENT_ID")
if not TWITCH_APP_CLIENT_SECRET: missing_secrets.append("TWITCH_APP_CLIENT_SECRET")
if not YOUTUBE_APP_CLIENT_ID: missing_secrets.append("YOUTUBE_APP_CLIENT_ID")
if not YOUTUBE_APP_CLIENT_SECRET: missing_secrets.append("YOUTUBE_APP_CLIENT_SECRET")
if not X_APP_CLIENT_ID: missing_secrets.append("X_APP_CLIENT_ID")
if not X_APP_CLIENT_SECRET: missing_secrets.append("X_APP_CLIENT_SECRET")
if not APP_SECRET_KEY: missing_secrets.append("APP_SECRET_KEY")

if missing_secrets:
     logger.critical(f"CRITICAL CONFIGURATION ERRORS: The following required settings are missing from your .env file: {', '.join(missing_secrets)}")
     logger.critical("OAuth flows and potentially other features will fail. Please create/update your .env file.")
     # You might want to exit here in a production scenario
     # sys.exit(1)
     if "APP_SECRET_KEY" in missing_secrets:
          warnings.warn(
               "CRITICAL SECURITY WARNING: APP_SECRET_KEY is missing. OAuth state validation is insecure. Generate a key and add it to .env.",
               RuntimeWarning, stacklevel=2
          )
          APP_SECRET_KEY = "fallback_insecure_secret_key_32_bytes_long" # Insecure fallback

logger.info(f"Final Config Loaded: Prefix='{settings['COMMAND_PREFIX']}', WS={settings['WS_HOST']}:{settings['WS_PORT']}, LogLevel={settings['LOG_LEVEL']}, DataDir='{DATA_DIR.resolve()}'")
# Avoid logging the full settings dict at INFO level as it contains tokens
# logger.debug(f"Full settings dict (Includes sensitive tokens if loaded): {settings}")
""",
        "app/core/event_bus.py": r"""# Generated by install_fosbot.py
import asyncio
import logging
from collections import defaultdict
from typing import Type, Callable, Dict, List, TypeVar, Coroutine, Any
try:
    # Attempt to import the actual Event base class
    from app.events import Event
except ImportError:
    # Fallback placeholder if events.py isn't found during standalone testing/linting
    class Event: pass
    print("WARNING: Could not import app.events. Using placeholder Event for type hints.")

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=Event) # Generic type for event instances

class AsyncEventBus:
    """A simple asynchronous publish/subscribe event bus."""
    def __init__(self):
        self._listeners: Dict[Type[Event], List[Callable[[T], Coroutine[Any, Any, None]]]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=1000) # Increased queue size
        self._worker_task: asyncio.Task | None = None
        self._running = False

    def subscribe(self, event_type: Type[T], handler: Callable[[T], Coroutine[Any, Any, None]]):
        """Subscribe an async handler to an event type. Idempotent."""
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError(f"Handler {getattr(handler,'__name__', repr(handler))} must be an async function (coroutine)")

        # Ensure handler is not already subscribed to avoid duplicate calls
        if handler not in self._listeners[event_type]:
            self._listeners[event_type].append(handler)
            logger.debug(f"Handler '{getattr(handler, '__name__', repr(handler))}' subscribed to {event_type.__name__}")
        else:
             logger.warning(f"Handler '{getattr(handler, '__name__', repr(handler))}' already subscribed to {event_type.__name__}. Ignoring duplicate subscription.")

    def unsubscribe(self, event_type: Type[T], handler: Callable[[T], Coroutine[Any, Any, None]]):
        """Unsubscribe a specific handler from an event type."""
        try:
            # Ensure the list exists before trying to remove
            if event_type in self._listeners:
                self._listeners[event_type].remove(handler)
                logger.debug(f"Handler '{getattr(handler, '__name__', repr(handler))}' unsubscribed from {event_type.__name__}")
                # Clean up empty listener lists (optional, for memory)
                if not self._listeners[event_type]:
                     del self._listeners[event_type]
            else:
                logger.warning(f"Attempted to unsubscribe handler '{getattr(handler, '__name__', repr(handler))}' from {event_type.__name__}, but event type has no listeners.")
        except ValueError:
            logger.warning(f"Attempted to unsubscribe handler '{getattr(handler, '__name__', repr(handler))}' from {event_type.__name__}, but it was not found in the list.")


    def publish(self, event: Event):
        """Publish an event to the queue for async processing."""
        if not isinstance(event, Event):
             logger.error(f"Attempted to publish non-Event object: {type(event)}. Discarding.")
             return

        if not self._running:
            logger.warning(f"Event bus not running, discarding event: {type(event).__name__}")
            return
        try:
            self._queue.put_nowait(event)
            # Reduce log noise: Log publication only at INFO or higher if queue is getting full
            qsize = self._queue.qsize()
            if qsize > self._queue.maxsize * 0.8:
                 logger.info(f"Event {type(event).__name__} published (Queue approaching full: {qsize}/{self._queue.maxsize}).")
            else:
                 logger.debug(f"Event {type(event).__name__} published (qsize: {qsize}).")
        except asyncio.QueueFull:
            logger.error(f"Event bus queue FULL! (maxsize={self._queue.maxsize}). Discarding event: {type(event).__name__}. Check handler performance or increase queue size.")

    async def _process_events(self):
        """Worker coroutine that processes events from the queue."""
        logger.info("Event bus processor task started.")
        while self._running:
            try:
                # Wait indefinitely for an event, relies on sentinel for shutdown
                event = await self._queue.get()

                # Handle sentinel value for clean shutdown
                if event is None:
                    logger.debug("Received None sentinel, checking running state for shutdown.")
                    if not self._running: # If stop() was called, exit loop
                         break
                    else: # If None somehow got in queue otherwise, ignore it
                         logger.warning("Received None in event queue unexpectedly, ignoring.")
                         self._queue.task_done()
                         continue

                if not isinstance(event, Event):
                    logger.error(f"Dequeued non-Event object: {type(event)}. Skipping.")
                    self._queue.task_done()
                    continue

                event_type = type(event)
                logger.debug(f"Processing event {event_type.__name__} from queue (qsize: {self._queue.qsize()}).")

                handlers_to_call = []
                # Check for handlers registered for this specific type or any parent type
                # Iterate over a copy of keys in case listeners change during processing
                for registered_type in list(self._listeners.keys()):
                    # Check instance relationship carefully
                    if isinstance(event, registered_type):
                         # Get potentially updated list of handlers for this type
                         current_handlers = self._listeners.get(registered_type, [])
                         handlers_to_call.extend(current_handlers)

                if not handlers_to_call:
                    logger.debug(f"No listeners found for event type {event_type.__name__}")
                    self._queue.task_done()
                    continue

                # Execute handlers concurrently
                tasks = [
                    asyncio.create_task(
                        handler(event),
                        name=f"event_handler_{getattr(handler, '__name__', f'unknown_{id(handler)}')}_{event_type.__name__}"
                    )
                    for handler in handlers_to_call
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log exceptions from handlers
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        # Ensure handler still exists in case of dynamic unsubscription
                        if i < len(handlers_to_call):
                            handler_name = getattr(handlers_to_call[i], '__name__', repr(handlers_to_call[i]))
                            # Log full traceback only if log level is DEBUG
                            log_traceback = logger.isEnabledFor(logging.DEBUG)
                            logger.error(
                                f"Exception in handler '{handler_name}' for event {event_type.__name__}: {result}",
                                exc_info=result if log_traceback else False # Pass exception instance directly if DEBUG
                            )
                        else:
                             logger.error(f"Exception occurred in a handler that might have been removed during execution for {event_type.__name__}: {result}")


                self._queue.task_done() # Mark event as processed

            except asyncio.CancelledError:
                logger.info("Event bus processing task cancelled.")
                break # Exit the loop cleanly on cancellation
            except Exception as e:
                # Catch unexpected errors in the loop itself
                logger.exception(f"Critical error in event processing loop: {e}")
                # Avoid busy-waiting if the error persists
                await asyncio.sleep(1)

        logger.info("Event bus processor task finished.")

    async def start(self):
        """Start the background event processing worker."""
        if self._running:
            logger.warning("Event bus already running.")
            return
        logger.info("Starting event bus...")
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events(), name="EventBusProcessor")
        logger.info("Event bus started successfully.")

    async def stop(self):
        """Stop the background event processing worker gracefully."""
        if not self._running or not self._worker_task or self._worker_task.done():
            logger.info("Event bus already stopped or not started.")
            return

        logger.info("Stopping event bus worker...")
        self._running = False # Signal the processing loop to stop

        # Put sentinel value to unblock the queue.get() if it's waiting
        try:
            # Use timeout to avoid blocking indefinitely if queue is full
            await asyncio.wait_for(self._queue.put(None), timeout=1.0)
        except asyncio.QueueFull:
            logger.warning("Event queue full during shutdown initiation, worker might need cancellation.")
            # Cancellation below will handle this
        except asyncio.TimeoutError:
            logger.warning("Timeout putting sentinel value in event queue during shutdown.")
        except Exception as e:
             logger.error(f"Error putting sentinel value in event queue: {e}")

        # Cancel the task if it hasn't finished processing the sentinel
        if self._worker_task and not self._worker_task.done():
             if not self._worker_task.cancelling():
                  logger.debug("Cancelling event bus processor task...")
                  self._worker_task.cancel()
             else:
                  logger.debug("Event bus processor task already cancelling.")

        # Wait for the task to complete
        if self._worker_task:
            try:
                # Wait with a timeout for the task to finish cancellation/processing
                await asyncio.wait_for(self._worker_task, timeout=5.0)
                logger.info("Event bus worker stopped gracefully.")
            except asyncio.CancelledError:
                # This is expected if we cancelled it and it acknowledged
                logger.info("Event bus worker stop confirmed (task was cancelled).")
            except asyncio.TimeoutError:
                 logger.warning("Timeout waiting for event bus worker task to stop.")
            except Exception as e:
                 logger.exception(f"Error encountered while waiting for event bus worker task to stop: {e}")

        self._worker_task = None
        logger.info("Event bus stopped.")

# Global instance (Singleton pattern)
event_bus = AsyncEventBus()
""",
        "app/core/json_store.py": r"""# Generated by install_fosbot.py
import json
import logging
import aiofiles
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List # Added List
from collections import defaultdict
import time

# Use settings object which includes DATA_DIR Path object
from app.core.config import logger, settings, DATA_DIR

_file_locks: Dict[Path, asyncio.Lock] = defaultdict(asyncio.Lock)

async def _ensure_data_dir():
    """Ensures the data directory exists."""
    try:
        # Use the DATA_DIR Path object directly
        if not DATA_DIR.exists():
             logger.warning(f"Data directory '{DATA_DIR.resolve()}' not found. Attempting to create.")
             DATA_DIR.mkdir(parents=True, exist_ok=True)
             logger.info(f"Data directory created: {DATA_DIR.resolve()}")
        elif not DATA_DIR.is_dir():
             logger.critical(f"CRITICAL: Path '{DATA_DIR.resolve()}' exists but is not a directory!")
             raise OSError(f"'{DATA_DIR.resolve()}' is not a directory.")
    except OSError as e:
        logger.critical(f"CRITICAL ERROR: Could not create/access data directory '{DATA_DIR.resolve()}': {e}", exc_info=True)
        raise # Re-raise after logging

# --- Specific Data File Names ---
# Defined here for clarity and use within this module
SETTINGS_FILE = "settings"
CHECKINS_FILE = "checkins"
COUNTERS_FILE = "counters"
COMMANDS_FILE = "commands"

async def load_json_data(filename: str, default: Any = None) -> Optional[Any]:
    """Loads data asynchronously from a JSON file in the data directory."""
    await _ensure_data_dir() # Ensure directory exists before proceeding
    filepath = DATA_DIR / f"{filename}.json"
    lock = _file_locks[filepath]
    try:
        async with lock:
            logger.debug(f"Acquired lock for READ: {filepath}")
            try:
                if not filepath.is_file():
                    # For critical files, create them if they don't exist
                    if filename in [SETTINGS_FILE, COMMANDS_FILE, CHECKINS_FILE, COUNTERS_FILE]:
                        logger.warning(f"Essential file not found: {filepath}. Creating empty file.")
                        # Initialize with empty dict for structure
                        await save_json_data(filename, {}) # Use the save function
                        return {} # Return the empty structure immediately
                    else:
                         logger.warning(f"JSON file not found: {filepath}. Returning default.")
                         return default

                # Read file content
                async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
                    content = await f.read()

                # Handle empty file case
                if not content:
                    logger.warning(f"JSON file is empty: {filepath}. Returning default structure for core files, else provided default.")
                    # Return empty dict for core files to prevent type errors later
                    return {} if filename in [SETTINGS_FILE, COMMANDS_FILE, CHECKINS_FILE, COUNTERS_FILE] else default

                # Decode JSON
                data = json.loads(content)
                logger.debug(f"Successfully loaded data from {filepath}")
                return data

            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from file: {filepath}. File might be corrupted. Returning default.", exc_info=True)
                return {} if filename in [SETTINGS_FILE, COMMANDS_FILE, CHECKINS_FILE, COUNTERS_FILE] else default
            except Exception as e:
                logger.error(f"Unexpected error loading JSON file {filepath}: {e}", exc_info=True)
                return {} if filename in [SETTINGS_FILE, COMMANDS_FILE, CHECKINS_FILE, COUNTERS_FILE] else default
            finally:
                 logger.debug(f"Released lock for READ: {filepath}")

    except asyncio.CancelledError:
        logger.warning(f"Operation cancelled while loading {filename}")
        # Return default, but consider if returning {} is safer for core files
        return {} if filename in [SETTINGS_FILE, COMMANDS_FILE, CHECKINS_FILE, COUNTERS_FILE] else default
    except Exception as e:
        # This catches errors acquiring the lock or during ensure_data_dir
        logger.error(f"Unexpected error related to file access for {filename}: {e}", exc_info=True)
        return {} if filename in [SETTINGS_FILE, COMMANDS_FILE, CHECKINS_FILE, COUNTERS_FILE] else default


async def save_json_data(filename: str, data: Any) -> bool:
    """Saves data asynchronously to a JSON file in the data directory."""
    await _ensure_data_dir()
    filepath = DATA_DIR / f"{filename}.json"
    lock = _file_locks[filepath]
    # Generate a more unique temp filename
    task_name = asyncio.current_task().get_name() if asyncio.current_task() else 'notask'
    temp_filepath = filepath.with_suffix(f'.{task_name}_{time.monotonic_ns()}.tmp')

    try:
        async with lock:
            logger.debug(f"Acquired lock for WRITE: {filepath} (Temp: {temp_filepath})")
            try:
                # Write to temporary file first
                async with aiofiles.open(temp_filepath, mode='w', encoding='utf-8') as f:
                    # Use wait_for to prevent indefinite blocking on write
                    await asyncio.wait_for(
                        f.write(json.dumps(data, indent=4, ensure_ascii=False)),
                        timeout=10.0 # Generous timeout for writing
                    )
                    await f.flush() # Ensure data is written to OS buffer

                # Atomic rename (on POSIX systems)
                temp_filepath.rename(filepath)
                logger.info(f"Successfully saved data to {filepath}")
                return True
            except (asyncio.TimeoutError, Exception) as e:
                logger.error(f"Error saving JSON file {filepath} (during write/rename): {e}", exc_info=True)
                # Cleanup temp file if rename failed or write errored
                if temp_filepath.exists():
                    try:
                        temp_filepath.unlink(missing_ok=True) # Python 3.8+
                        logger.debug(f"Removed temporary file {temp_filepath} after error.")
                    except OSError as unlink_e:
                        logger.error(f"Error removing temporary file {temp_filepath}: {unlink_e}")
                return False
            finally:
                logger.debug(f"Released lock for WRITE: {filepath}")
    except asyncio.CancelledError:
        logger.warning(f"Operation cancelled while saving {filename}")
        if temp_filepath.exists():
             try: temp_filepath.unlink(missing_ok=True); logger.debug(f"Removed temp file {temp_filepath} after cancellation.")
             except OSError as e: logger.error(f"Error removing temp file {temp_filepath} on cancellation: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error acquiring lock for saving {filename}: {e}", exc_info=True)
        return False


# --- Token Management (Essential for OAuth) ---
async def save_tokens(platform: str, token_data: Dict[str, Any]) -> bool:
    """
    Saves OAuth token data for a specific platform into settings.json.
    Merges with existing settings. Publishes SettingsUpdated event.
    """
    if not isinstance(token_data, dict):
         logger.error(f"Invalid token_data type for {platform}: {type(token_data)}. Expected dict.")
         return False
    logger.info(f"Attempting to save tokens for platform: {platform}")
    current_settings = await load_settings() # Load everything currently in settings.json
    if current_settings is None:
        current_settings = {} # Start fresh if load failed

    updated_keys = []
    keys_to_process = ['access_token', 'refresh_token', 'expires_in', 'scope', 'user_id', 'user_login', 'access_token_secret'] # Include X's secret

    for key in keys_to_process:
        new_value = token_data.get(key)
        storage_key = f"{platform}_{key}"

        # Special handling for expires_in -> expires_at
        if key == 'expires_in' and new_value is not None:
             try:
                  # Calculate expiry timestamp with buffer
                  expires_at = time.time() + int(new_value) - 300 # 5 min buffer
                  storage_key = f"{platform}_expires_at"
                  new_value = expires_at
             except (ValueError, TypeError):
                  logger.error(f"Invalid 'expires_in' value for {platform}: {new_value}. Skipping expiry calculation.")
                  continue # Skip this key if invalid

        # Special handling for scope (ensure list)
        elif key == 'scope' and new_value is not None:
             if isinstance(new_value, str):
                  new_value = new_value.split()
             elif not isinstance(new_value, list):
                  logger.warning(f"Unexpected type for 'scope' for {platform}: {type(new_value)}. Storing as is.")
             # Ensure it's always a list, even if empty
             new_value = list(new_value) if new_value else []

        # Store user_id as string
        elif key == 'user_id' and new_value is not None:
             new_value = str(new_value)

        # Only update if the value is actually provided in token_data
        if new_value is not None:
             # Check if value changed before updating
             if current_settings.get(storage_key) != new_value:
                  current_settings[storage_key] = new_value
                  updated_keys.append(storage_key)
                  logger.debug(f"Updated setting '{storage_key}' for {platform}")
             else:
                  logger.debug(f"Setting '{storage_key}' for {platform} unchanged, skipping save.")

    if not updated_keys:
        logger.info(f"No token changes to save for {platform}.")
        return True # Indicate success as no save was needed

    logger.warning(f"Saving potentially sensitive OAuth tokens ({', '.join(updated_keys)}) for {platform} to plain JSON file.")
    saved = await save_settings(current_settings) # Save the entire updated settings dict

    if saved:
        # Publish event only after successful save
        from app.events import SettingsUpdated
        from app.core.event_bus import event_bus # Import locally to avoid circular dependency at module level
        event_bus.publish(SettingsUpdated(keys_updated=updated_keys))
        logger.info(f"Successfully saved tokens for {platform} and published SettingsUpdated.")
    else:
         logger.error(f"Failed to save settings file after updating tokens for {platform}.")

    return saved

async def load_tokens(platform: str) -> Optional[Dict[str, Any]]:
    """Loads OAuth token data for a specific platform from settings.json."""
    settings_data = await load_settings()
    if not isinstance(settings_data, dict):
         logger.error(f"Failed to load settings or got invalid type ({type(settings_data)}) when loading tokens for {platform}.")
         return None

    token_info = {
        "access_token": settings_data.get(f"{platform}_access_token"),
        "refresh_token": settings_data.get(f"{platform}_refresh_token"),
        "expires_at": settings_data.get(f"{platform}_expires_at"), # Timestamp
        "scopes": settings_data.get(f"{platform}_scopes", []),
        "user_id": settings_data.get(f"{platform}_user_id"),
        "user_login": settings_data.get(f"{platform}_user_login"),
        "access_token_secret": settings_data.get(f"{platform}_access_token_secret"), # For X OAuth1a
    }

    # Basic check: If no access token, assume not authenticated
    if not token_info["access_token"]:
        logger.debug(f"No stored access token found for platform: {platform}")
        return None

    # Convert expires_at to float if it exists and is valid
    if token_info["expires_at"] is not None:
        try:
            token_info["expires_at"] = float(token_info["expires_at"])
        except (ValueError, TypeError):
            logger.warning(f"Invalid expires_at value stored for {platform}: {token_info['expires_at']}. Treating as None.")
            token_info["expires_at"] = None

    # Remove keys with None values for cleaner return, except essential access_token
    return {k: v for k, v in token_info.items() if v is not None or k == "access_token"}


async def clear_tokens(platform: str) -> bool:
    """Removes OAuth token data for a specific platform from settings.json."""
    logger.info(f"Clearing tokens for platform: {platform}")
    current_settings = await load_settings()
    if not isinstance(current_settings, dict):
         logger.error(f"Cannot clear tokens for {platform}: Failed to load settings or got invalid type.")
         return False # Failed to load/modify

    keys_to_remove = [
        f"{platform}_access_token", f"{platform}_refresh_token",
        f"{platform}_expires_at", f"{platform}_scopes",
        f"{platform}_user_id", f"{platform}_user_login",
        f"{platform}_access_token_secret" # Include X secret
    ]
    updated_keys = []
    changed = False
    for key in keys_to_remove:
        if key in current_settings:
            del current_settings[key]
            updated_keys.append(key)
            changed = True
            logger.debug(f"Removed setting '{key}' for {platform}")

    if changed:
        logger.info(f"Saving settings after clearing tokens for {platform}.")
        saved = await save_settings(current_settings)
        if saved:
            from app.events import SettingsUpdated
            from app.core.event_bus import event_bus # Import locally
            event_bus.publish(SettingsUpdated(keys_updated=updated_keys))
            logger.info(f"Successfully cleared tokens for {platform} and published SettingsUpdated.")
            return True
        else:
            logger.error(f"Failed to save settings after clearing tokens for {platform}.")
            return False
    else:
        logger.info(f"No tokens found to clear for {platform}.")
        return True # No changes needed, considered successful

# --- Generic Settings Management ---
async def load_settings() -> Dict[str, Any]:
    """Loads the main application settings file (settings.json). Returns empty dict on failure."""
    settings_data = await load_json_data(SETTINGS_FILE, default={})
    # Ensure it's always a dictionary
    return settings_data if isinstance(settings_data, dict) else {}

async def save_settings(settings_data: Dict[str, Any]) -> bool:
    """Saves the main application settings (settings.json)."""
    if not isinstance(settings_data, dict):
         logger.error(f"Attempted to save non-dict type ({type(settings_data)}) as settings. Aborting.")
         return False
    # Also update the in-memory settings dict used by config.py
    global settings
    settings.update(settings_data) # Ensure in-memory reflects saved state
    return await save_json_data(SETTINGS_FILE, settings_data)

async def get_setting(key: str, default: Any = None) -> Any:
    """Convenience function to get a single non-token setting from settings.json."""
    # Use this primarily for settings managed by the UI that aren't tokens
    settings_data = await load_settings()
    return settings_data.get(key, default)

async def update_setting(key: str, value: Any) -> bool:
    """Updates a single non-token setting in settings.json. Publishes SettingsUpdated."""
    current_settings = await load_settings()
    if not isinstance(current_settings, dict):
        logger.error(f"Cannot update setting '{key}': Failed to load settings or invalid format.")
        return False

    # Prevent accidentally overwriting token keys via this generic function
    # Check against a broader set of patterns
    sensitive_patterns = ['_token', '_secret', '_key', '_id', '_password', '_scopes', '_expires']
    known_non_secrets = ["COMMAND_PREFIX", "LOG_LEVEL", "TWITCH_CHANNELS", "DATA_DIR", "WS_HOST", "WS_PORT"]
    if any(pattern in key.lower() for pattern in sensitive_patterns) and key not in known_non_secrets:
        logger.error(f"Attempted to update potentially sensitive key '{key}' using generic update_setting. Use specific token functions or review key naming.")
        return False

    if current_settings.get(key) != value:
        logger.info(f"Updating setting '{key}' to '{value}'")
        current_settings[key] = value
        saved = await save_settings(current_settings) # save_settings now updates in-memory 'settings' too
        if saved:
            # Event publication handled by save_tokens or explicit publish after successful save_settings
            from app.events import SettingsUpdated
            from app.core.event_bus import event_bus # Import locally
            event_bus.publish(SettingsUpdated(keys_updated=[key]))
            logger.info(f"Successfully updated setting '{key}' and published SettingsUpdated.")
            return True
        else:
            logger.error(f"Failed to save settings after updating key '{key}'.")
            return False
    else:
        logger.debug(f"Setting '{key}' already has value '{value}'. No update needed.")
        return True # No change needed, considered successful

# --- Other Data Files ---
async def load_checkins() -> Dict[str, Any]:
    """Loads check-in data (checkins.json). Returns empty dict on failure."""
    checkins_data = await load_json_data(CHECKINS_FILE, default={})
    return checkins_data if isinstance(checkins_data, dict) else {}

async def save_checkins(data: Dict[str, Any]) -> bool:
    """Saves check-in data (checkins.json)."""
    if not isinstance(data, dict): return False
    return await save_json_data(CHECKINS_FILE, data)

async def load_counters() -> Dict[str, int]:
    """Loads counter data (counters.json), ensuring values are integers. Returns empty dict on failure."""
    counters_data = await load_json_data(COUNTERS_FILE, default={})
    valid_counters = {}
    if isinstance(counters_data, dict):
        for k, v in counters_data.items():
            try:
                valid_counters[k] = int(v)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value '{v}' for counter '{k}' in {COUNTERS_FILE}.json. Ignoring.")
    else:
        logger.warning(f"Loaded counters data is not a dict ({type(counters_data)}). Returning empty.")
    return valid_counters


async def save_counters(data: Dict[str, int]) -> bool:
    """Saves counter data (counters.json)."""
    if not isinstance(data, dict): return False
    # Ensure all values are integers before saving
    sanitized_data = {k: int(v) for k, v in data.items() if isinstance(v, (int, float)) or str(v).isdigit()}
    return await save_json_data(COUNTERS_FILE, sanitized_data)

async def load_commands() -> Dict[str, str]:
    """Loads custom commands (commands.json). Returns empty dict on failure."""
    commands_data = await load_json_data(COMMANDS_FILE, default={})
    # Ensure keys are lowercase and stripped for consistent lookup
    return {k.lower().strip(): str(v) for k, v in commands_data.items() if k and str(v).strip()} if isinstance(commands_data, dict) else {}

async def save_commands(data: Dict[str, str]) -> bool:
    """Saves custom commands (commands.json)."""
    if not isinstance(data, dict): return False
    # Ensure keys (command names) are lowercase and stripped before saving
    sanitized_data = {k.strip().lower(): str(v).strip() for k, v in data.items() if k.strip() and str(v).strip()}
    # Publish event after successful save
    saved = await save_json_data(COMMANDS_FILE, sanitized_data)
    if saved:
        # Reload commands in chat processor or notify it
        # For simplicity, chat_processor reloads on command add/delete/upload via API
        # Or could publish a specific event
        # from app.events import CustomCommandsUpdated; event_bus.publish(CustomCommandsUpdated())
        pass
    return saved

# --- File: app/core/json_store.py --- END ---
""",

        # === app/apis/ Files ===
        "app/apis/__init__.py": r"""# Generated by install_fosbot.py
from .settings_api import router as settings_router
from .auth_api import router as auth_router
from .commands_api import router as commands_router
from .ws_endpoints import router as ws_endpoints_router

# Export routers to be included in main.py
__all__ = [
    "settings_router",
    "auth_router",
    "commands_router",
    "ws_endpoints_router",
]
""",
        "app/apis/auth_api.py": r"""# Generated by install_fosbot.py
# --- File: app/apis/auth_api.py --- START ---
import logging
import secrets
from urllib.parse import urlencode, quote # Import quote for message encoding
from typing import Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Request # Added Request
from fastapi.responses import RedirectResponse
import httpx
import tweepy
import asyncio

# Configuration (Import App Owner Credentials)
from app.core.config import (
    logger, # Use configured logger
    settings, # Access in-memory settings if needed (like WS_HOST/PORT for redirect base?)
    TWITCH_APP_CLIENT_ID, TWITCH_APP_CLIENT_SECRET,
    YOUTUBE_APP_CLIENT_ID, YOUTUBE_APP_CLIENT_SECRET,
    X_APP_CLIENT_ID, X_APP_CLIENT_SECRET,
    APP_SECRET_KEY # Crucial for state validation
)

# Token Storage (User Tokens)
from app.core.json_store import save_tokens, clear_tokens, load_tokens

# Event Bus
from app.core.event_bus import event_bus
from app.events import PlatformStatusUpdate, ServiceControl

# --- Router Setup ---
router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Constants ---
# Determine base URL dynamically? For now, assume localhost based on common setup.
# This might need adjustment if deployed elsewhere or behind a proxy.
BASE_URL = f"http://{settings.get('WS_HOST', 'localhost')}:{settings.get('WS_PORT', 8000)}"
TWITCH_REDIRECT_URI = f"{BASE_URL}/auth/twitch/callback"
YOUTUBE_REDIRECT_URI = f"{BASE_URL}/auth/youtube/callback"
X_REDIRECT_URI = f"{BASE_URL}/auth/x/callback"

TWITCH_AUTHORIZATION_BASE_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate" # Use validate for user info + client_id check
TWITCH_REVOKE_URL = "https://id.twitch.tv/oauth2/revoke"
TWITCH_SCOPES = ["chat:read", "chat:edit"] # Minimal required scopes

YOUTUBE_AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
YOUTUBE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo" # Standard OIDC endpoint
# Scopes for live chat reading/posting + user info
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "openid", "email", "profile"
]

X_AUTHORIZATION_BASE_URL = "https://api.twitter.com/oauth/authorize" # OAuth 1.0a
X_REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
X_ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
# Note: X OAuth 1.0a scopes are set at the app level on developer.twitter.com

# --- State Management ---
# Simple in-memory store. For multi-instance, use Redis or DB.
# Key: state_token, Value: platform (e.g., 'twitch')
_oauth_state_store: Dict[str, str] = {}
# Store for OAuth 1.0a request tokens (X/Twitter)
# Key: oauth_token (returned by X), Value: {'oauth_token': ..., 'oauth_token_secret': ...}
_x_request_tokens: Dict[str, Dict[str, str]] = {}

# --- Helper Functions ---
def generate_state(platform: str) -> str:
    """Generates a secure random state token and stores it."""
    if not APP_SECRET_KEY or APP_SECRET_KEY == "fallback_insecure_secret_key_32_bytes_long":
        logger.critical("Cannot generate secure state: APP_SECRET_KEY is missing or insecure!")
        # Fallback FOR DEV ONLY
        state = secrets.token_urlsafe(16) # Shorter fallback for readability if insecure
    else:
        state = secrets.token_urlsafe(32)
    _oauth_state_store[state] = platform # Store mapping: state -> platform
    logger.debug(f"Generated state for {platform}: {state}")
    return state

def verify_state(received_state: str, expected_platform: str) -> bool:
    """Verifies the received state token against the store and clears it."""
    if not APP_SECRET_KEY or APP_SECRET_KEY == "fallback_insecure_secret_key_32_bytes_long":
         logger.warning("State verification is insecure: APP_SECRET_KEY is missing or default.")
         # Basic check for DEV ONLY - This is NOT secure against CSRF
         stored_platform = _oauth_state_store.pop(received_state, None)
         return stored_platform == expected_platform

    # Proper verification
    stored_platform = _oauth_state_store.pop(received_state, None)
    if stored_platform == expected_platform:
        logger.debug(f"State verified successfully for {expected_platform}.")
        return True
    else:
        logger.error(f"OAuth state mismatch for {expected_platform}! Received: '{received_state}', Expected platform for this state: '{stored_platform}'. Possible CSRF attack.")
        return False

async def get_twitch_user_info_from_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Gets user ID and login using the /validate endpoint."""
    if not TWITCH_APP_CLIENT_ID:
        logger.error("Cannot validate Twitch token: TWITCH_APP_CLIENT_ID is not configured.")
        return None
    headers = {"Authorization": f"OAuth {access_token}"}
    # Use a timeout for external requests
    async with httpx.AsyncClient(timeout=10.0) as client: # Add timeout
        try:
            response = await client.get(TWITCH_VALIDATE_URL, headers=headers)
            response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx
            data = response.json()
            # Validate response includes necessary fields and matches our client_id
            if (data.get("user_id") and data.get("login") and
                data.get("client_id") == TWITCH_APP_CLIENT_ID):
                logger.info(f"Twitch token validated successfully for user {data['login']} ({data['user_id']})")
                return {
                    "user_id": data["user_id"],
                    "user_login": data["login"],
                    "scopes": data.get("scopes", []) # Use validated scopes
                }
            else:
                logger.error(f"Twitch validation response invalid or client_id mismatch. Data: {data}")
                return None
        except httpx.TimeoutException:
             logger.error("Timeout validating Twitch token.")
             return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error validating Twitch token: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error validating Twitch token: {e}")
            return None

async def get_youtube_user_info_from_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Gets user info using Google's userinfo endpoint."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(YOUTUBE_USERINFO_URL, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Google OIDC standard fields: sub (user_id), name, email (if scoped)
            if data.get("sub"):
                logger.info(f"YouTube token validated successfully for user {data.get('name', 'Unknown')} ({data['sub']})")
                return {
                    "user_id": data["sub"],
                    "user_login": data.get("name", f"User_{data['sub'][-6:]}"), # Use name, fallback to partial ID
                    "email": data.get("email") # Store email if available
                }
            else:
                logger.error(f"YouTube userinfo response missing 'sub' field. Data: {data}")
                return None
        except httpx.TimeoutException:
            logger.error("Timeout getting YouTube userinfo.")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting YouTube userinfo: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error getting YouTube userinfo: {e}")
            return None

async def get_x_user_info_from_tokens(access_token: str, access_token_secret: str) -> Optional[Dict[str, Any]]:
    """Gets X/Twitter user info using acquired OAuth 1.0a tokens."""
    if not X_APP_CLIENT_ID or not X_APP_CLIENT_SECRET:
         logger.error("Cannot fetch X user info: X App credentials missing.")
         return None
    try:
        # Authenticate using the user's obtained tokens
        client = tweepy.Client(
            consumer_key=X_APP_CLIENT_ID,
            consumer_secret=X_APP_CLIENT_SECRET,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True # Let tweepy handle basic rate limits
        )
        # Use asyncio.to_thread for the synchronous tweepy call
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
             None, # Use default executor
             lambda: client.get_me(user_fields=["id", "username", "name"]) # Request specific fields
        )

        if response.data:
            user_data = response.data
            logger.info(f"X user info obtained successfully for @{user_data.username} ({user_data.id})")
            return {
                "user_id": str(user_data.id),
                "user_login": user_data.username, # The @handle
                "display_name": user_data.name    # The display name
            }
        else:
             # Log error details if available
             error_detail = f"Errors: {response.errors}" if hasattr(response, 'errors') and response.errors else "No data returned."
             logger.error(f"Failed to get X user info. {error_detail}")
             return None
    except tweepy.errors.TweepyException as e:
        logger.error(f"Tweepy error getting X user info: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error getting X user info: {e}")
        return None

def create_error_redirect(platform: str, message: str, status_code=303) -> RedirectResponse:
    """Creates a redirect response back to the UI with an error message."""
    logger.error(f"OAuth Error ({platform}): {message}")
    # URL encode the message for safety
    encoded_message = quote(message)
    # Redirect to root ('/') where the frontend handles query params
    return RedirectResponse(f"/?auth_error={platform}&message={encoded_message}", status_code=status_code) # Use 303 for POST-Redirect-GET pattern

def create_success_redirect(platform: str, status_code=303) -> RedirectResponse:
     """Creates a redirect response back to the UI indicating success."""
     logger.info(f"OAuth successful for {platform}.")
     return RedirectResponse(f"/?auth_success={platform}", status_code=status_code)


# --- Twitch Auth Endpoints ---
@router.get("/twitch/login")
async def twitch_login():
    """Initiates Twitch OAuth flow."""
    if not TWITCH_APP_CLIENT_ID or not TWITCH_APP_CLIENT_SECRET:
        logger.critical("Twitch App credentials not configured on server.")
        # Don't expose internal details to user
        raise HTTPException(status_code=503, detail="Twitch Integration Not Configured by Admin")
    state = generate_state("twitch")
    params = {
        "client_id": TWITCH_APP_CLIENT_ID,
        "redirect_uri": TWITCH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(TWITCH_SCOPES),
        "state": state,
        # "force_verify": "true", # Optional: forces login prompt every time
    }
    auth_url = f"{TWITCH_AUTHORIZATION_BASE_URL}?{urlencode(params)}"
    logger.info("Redirecting user to Twitch for authorization...")
    return RedirectResponse(auth_url)

@router.get("/twitch/callback")
async def twitch_callback(code: Optional[str] = Query(None), state: Optional[str] = Query(None), error: Optional[str] = Query(None), error_description: Optional[str] = Query(None)):
    """Handles Twitch OAuth callback."""
    if error:
        return create_error_redirect("twitch", f"{error}: {error_description or 'Unknown Twitch error'}")
    if not code or not state:
        return create_error_redirect("twitch", "Missing code or state parameter from Twitch.")
    if not verify_state(state, "twitch"):
        return create_error_redirect("twitch", "Invalid OAuth state. Potential CSRF attempt.")

    token_params = {
        "client_id": TWITCH_APP_CLIENT_ID,
        "client_secret": TWITCH_APP_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": TWITCH_REDIRECT_URI,
    }
    async with httpx.AsyncClient(timeout=15.0) as client: # Increased timeout
        try:
            logger.debug("Requesting Twitch access token...")
            response = await client.post(TWITCH_TOKEN_URL, data=token_params)
            response.raise_for_status()
            token_data = response.json()
            logger.info("Received tokens from Twitch.")

            user_info = await get_twitch_user_info_from_token(token_data['access_token'])
            if not user_info:
                 return create_error_redirect("twitch", "Failed to validate token and get user info.")

            # Prepare token data for saving (add user info)
            save_data = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
                "scope": user_info.get("scopes", []), # Use validated scopes
                "user_id": user_info["user_id"],
                "user_login": user_info["user_login"]
            }

            # Save tokens asynchronously, don't block the redirect
            async def save_and_restart():
                 if await save_tokens("twitch", save_data):
                      logger.info(f"Twitch tokens saved successfully for {user_info['user_login']}.")
                      event_bus.publish(ServiceControl(service_name="twitch", command="restart"))
                 else:
                      logger.error("Failed to save Twitch tokens to storage after successful OAuth.")
                      # Consider publishing an error status?
                      event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message='Failed to save token'))

            asyncio.create_task(save_and_restart())

            # Redirect immediately upon successful token exchange & user info retrieval
            return create_success_redirect("twitch")

        except httpx.TimeoutException:
            return create_error_redirect("twitch", "Timeout contacting Twitch token endpoint.")
        except httpx.RequestError as e:
            return create_error_redirect("twitch", f"Network error contacting Twitch: {e}")
        except httpx.HTTPStatusError as e:
            return create_error_redirect("twitch", f"Error from Twitch ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            logger.exception("Unexpected error during Twitch callback.")
            return create_error_redirect("twitch", f"Internal server error: {type(e).__name__}")

@router.post("/twitch/logout", status_code=200)
async def twitch_logout():
    """Logs out from Twitch, revoking token and clearing local storage."""
    logger.info("Processing Twitch logout request.")
    tokens = await load_tokens("twitch")
    token_to_revoke = tokens.get("access_token") if tokens else None

    # Always attempt to clear local tokens first
    cleared_local = await clear_tokens("twitch")

    # Attempt revocation if possible
    if token_to_revoke and TWITCH_APP_CLIENT_ID:
        revoke_params = {"client_id": TWITCH_APP_CLIENT_ID, "token": token_to_revoke}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                revoke_response = await client.post(TWITCH_REVOKE_URL, data=revoke_params)
                if 200 <= revoke_response.status_code < 300:
                    logger.info("Successfully revoked Twitch token.")
                else:
                     logger.warning(f"Failed to revoke Twitch token (Status: {revoke_response.status_code}): {revoke_response.text}")
            except httpx.TimeoutException:
                logger.error("Timeout revoking Twitch token.")
            except Exception as e:
                 logger.error(f"Error during Twitch token revocation request: {e}", exc_info=True)
    else:
        logger.info("Skipping Twitch token revocation (no token/client_id found).")

    # Trigger service stop/restart regardless of revocation status
    asyncio.create_task(event_bus.publish(ServiceControl(service_name="twitch", command="restart"))) # Restart often better than just stop

    if cleared_local:
         return {"message": "Twitch logout processed. Local tokens cleared."}
    else:
         # This indicates a potential issue with json_store saving after clearing
         raise HTTPException(status_code=500, detail="Logout processed, but failed to save cleared token state.")


# --- YouTube Auth Endpoints ---
@router.get("/youtube/login")
async def youtube_login():
    """Initiates YouTube OAuth flow."""
    if not YOUTUBE_APP_CLIENT_ID or not YOUTUBE_APP_CLIENT_SECRET:
        logger.critical("YouTube App credentials not configured on server.")
        raise HTTPException(status_code=503, detail="YouTube Integration Not Configured by Admin")
    state = generate_state("youtube")
    params = {
        "client_id": YOUTUBE_APP_CLIENT_ID,
        "redirect_uri": YOUTUBE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(YOUTUBE_SCOPES),
        "state": state,
        "access_type": "offline", # Request refresh token
        "prompt": "consent" # Force consent screen to ensure refresh token is granted
    }
    auth_url = f"{YOUTUBE_AUTHORIZATION_BASE_URL}?{urlencode(params)}"
    logger.info("Redirecting user to YouTube for authorization...")
    return RedirectResponse(auth_url)

@router.get("/youtube/callback")
async def youtube_callback(code: Optional[str] = Query(None), state: Optional[str] = Query(None), error: Optional[str] = Query(None)):
    """Handles YouTube OAuth callback."""
    if error:
        return create_error_redirect("youtube", f"{error}: User likely denied access.")
    if not code or not state:
        return create_error_redirect("youtube", "Missing code or state parameter from YouTube.")
    if not verify_state(state, "youtube"):
        return create_error_redirect("youtube", "Invalid OAuth state. Potential CSRF attempt.")

    token_params = {
        "client_id": YOUTUBE_APP_CLIENT_ID,
        "client_secret": YOUTUBE_APP_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": YOUTUBE_REDIRECT_URI,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            logger.debug("Requesting YouTube access token...")
            response = await client.post(YOUTUBE_TOKEN_URL, data=token_params)
            response.raise_for_status()
            token_data = response.json()
            logger.info("Received tokens from YouTube.")

            # Verify token and get user info
            user_info = await get_youtube_user_info_from_token(token_data['access_token'])
            if not user_info:
                 return create_error_redirect("youtube", "Failed to validate token and get user info.")

            save_data = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"), # Crucial for offline access
                "expires_in": token_data.get("expires_in"),
                "scope": token_data.get("scope", "").split(), # Use scopes from token response
                "user_id": user_info["user_id"],
                "user_login": user_info["user_login"]
            }

            async def save_and_restart_yt():
                 if await save_tokens("youtube", save_data):
                      logger.info(f"YouTube tokens saved successfully for {user_info['user_login']}.")
                      event_bus.publish(ServiceControl(service_name="youtube", command="restart"))
                 else:
                      logger.error("Failed to save YouTube tokens to storage after successful OAuth.")
                      event_bus.publish(PlatformStatusUpdate(platform='youtube', status='error', message='Failed to save token'))

            asyncio.create_task(save_and_restart_yt())

            return create_success_redirect("youtube")

        except httpx.TimeoutException:
            return create_error_redirect("youtube", "Timeout contacting YouTube token endpoint.")
        except httpx.RequestError as e:
            return create_error_redirect("youtube", f"Network error contacting YouTube: {e}")
        except httpx.HTTPStatusError as e:
             return create_error_redirect("youtube", f"Error from YouTube ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            logger.exception("Unexpected error during YouTube callback.")
            return create_error_redirect("youtube", f"Internal server error: {type(e).__name__}")

@router.post("/youtube/logout", status_code=200)
async def youtube_logout():
    """Logs out from YouTube, revoking token and clearing local storage."""
    logger.info("Processing YouTube logout request.")
    tokens = await load_tokens("youtube")
    cleared_local = await clear_tokens("youtube")

    # Google recommends revoking the access token *or* the refresh token
    token_to_revoke = None
    if tokens:
        token_to_revoke = tokens.get("refresh_token") or tokens.get("access_token")

    if token_to_revoke:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                revoke_response = await client.post(
                    YOUTUBE_REVOKE_URL,
                    params={'token': token_to_revoke},
                    headers={'Content-Type': 'application/x-www-form-urlencoded'} # Google expects this header
                )
                if 200 <= revoke_response.status_code < 300:
                     logger.info(f"Attempted revocation for YouTube token ({'refresh' if tokens.get('refresh_token') else 'access'}). Status: {revoke_response.status_code}")
                else:
                    # Log warning, but don't fail logout if revoke fails (token might already be invalid)
                    logger.warning(f"Failed to revoke YouTube token (Status: {revoke_response.status_code}): {revoke_response.text}")
            except httpx.TimeoutException:
                 logger.error("Timeout revoking YouTube token.")
            except Exception as e:
                 logger.error(f"Error during YouTube token revocation request: {e}", exc_info=True)
    else:
        logger.info("Skipping YouTube token revocation (no token found).")

    asyncio.create_task(event_bus.publish(ServiceControl(service_name="youtube", command="restart")))

    if cleared_local:
         return {"message": "YouTube logout processed. Local tokens cleared."}
    else:
        raise HTTPException(status_code=500, detail="Logout processed, but failed to save cleared token state.")


# --- X (Twitter) Auth Endpoints (OAuth 1.0a) ---
@router.get("/x/login")
async def x_login():
    """Initiates X/Twitter OAuth 1.0a flow."""
    if not X_APP_CLIENT_ID or not X_APP_CLIENT_SECRET:
         logger.critical("X App credentials not configured on server.")
         return create_error_redirect("x", "X/Twitter Integration Not Configured by Admin. Check .env file.")

    # Use tweepy's OAuth1UserHandler for the 3-legged flow
    try:
        auth = tweepy.OAuth1UserHandler(
            X_APP_CLIENT_ID, X_APP_CLIENT_SECRET,
            callback=X_REDIRECT_URI # Must match callback URL in Twitter App settings
        )
        # Step 1: Get request token
        # Run synchronous tweepy call in executor
        loop = asyncio.get_running_loop()
        redirect_url = await loop.run_in_executor(None, auth.get_authorization_url, True) # signin_with_twitter=True

        # Store the request token secret temporarily, linking it via the oauth_token
        request_token_key = auth.request_token['oauth_token']
        _x_request_tokens[request_token_key] = auth.request_token # Store the whole dict

        logger.debug(f"Stored X request token secret for token: {request_token_key}")
        logger.info("Redirecting user to X for authorization...")
        return RedirectResponse(redirect_url)

    except tweepy.errors.TweepyException as e:
        logger.error(f"Error initiating X OAuth 1.0a flow: {e}")
        # Check for common callback URL error
        if "Callback URL not approved" in str(e):
             return create_error_redirect("x", "Callback URL not approved. Ensure 'http://localhost:8000/auth/x/callback' is in your X App settings.")
        else:
             return create_error_redirect("x", f"Tweepy error during login: {e}")
    except Exception as e:
        logger.exception("Unexpected error during X login initiation.")
        return create_error_redirect("x", f"Internal server error: {type(e).__name__}")

@router.get("/x/callback")
async def x_callback(oauth_token: Optional[str] = Query(None), oauth_verifier: Optional[str] = Query(None), denied: Optional[str] = Query(None)):
    """Handles X/Twitter OAuth 1.0a callback."""
    if denied:
        # User denied access on Twitter's side
        request_token_secret = _x_request_tokens.pop(denied, None) # 'denied' query param contains the request token
        logger.warning(f"X OAuth flow denied by user for request token: {denied}")
        return create_error_redirect("x", "Authorization denied by user.")

    if not oauth_token or not oauth_verifier:
        return create_error_redirect("x", "Missing oauth_token or oauth_verifier from X callback.")

    # Retrieve the stored request token secret using the returned oauth_token
    stored_token_info = _x_request_tokens.pop(oauth_token, None)
    if not stored_token_info or 'oauth_token_secret' not in stored_token_info:
        logger.error(f"Could not find stored request token secret for oauth_token: {oauth_token}")
        return create_error_redirect("x", "Invalid or expired OAuth session (request token mismatch).")

    # Step 3: Exchange request token for access token
    try:
        auth = tweepy.OAuth1UserHandler(
            X_APP_CLIENT_ID, X_APP_CLIENT_SECRET,
            callback=X_REDIRECT_URI
        )
        # Set the retrieved request token before getting the access token
        auth.request_token = stored_token_info
        # Run synchronous tweepy call in executor
        loop = asyncio.get_running_loop()
        access_token, access_token_secret = await loop.run_in_executor(
             None, auth.get_access_token, oauth_verifier
        )

        # Get user info using the new access tokens
        user_info = await get_x_user_info_from_tokens(access_token, access_token_secret)
        if not user_info:
             return create_error_redirect("x", "Successfully obtained tokens, but failed to verify user info.")

        # Prepare data for saving
        save_data = {
            "access_token": access_token,
            "access_token_secret": access_token_secret,
            "user_id": user_info["user_id"],
            "user_login": user_info["user_login"]
            # X OAuth 1.0a tokens don't expire in the same way, omit expires_in/refresh
            # Scopes are managed at the app level, not per-token
        }

        async def save_and_restart_x():
             if await save_tokens("x", save_data):
                  logger.info(f"X tokens saved successfully for @{user_info['user_login']}.")
                  event_bus.publish(ServiceControl(service_name="x", command="restart"))
             else:
                  logger.error("Failed to save X tokens to storage after successful OAuth.")
                  event_bus.publish(PlatformStatusUpdate(platform='x', status='error', message='Failed to save token'))

        asyncio.create_task(save_and_restart_x())

        return create_success_redirect("x")

    except tweepy.errors.TweepyException as e:
         logger.error(f"Error exchanging X request token for access token: {e}")
         return create_error_redirect("x", f"Tweepy error during callback: {e}")
    except Exception as e:
        logger.exception("Unexpected error during X callback.")
        return create_error_redirect("x", f"Internal server error: {type(e).__name__}")


@router.post("/x/logout", status_code=200)
async def x_logout():
    """Logs out from X by clearing local tokens (no standard revoke)."""
    logger.info("Processing X logout request.")
    # X OAuth 1.0a doesn't have a standard token revocation endpoint.
    # We just clear the stored tokens locally.
    cleared_local = await clear_tokens("x")
    asyncio.create_task(event_bus.publish(ServiceControl(service_name="x", command="restart")))

    if cleared_local:
        return {"message": "X logout processed. Local tokens cleared."}
    else:
        raise HTTPException(status_code=500, detail="Logout processed, but failed to save cleared token state.")

# --- File: app/apis/auth_api.py --- END ---
""",
        "app/apis/settings_api.py": r"""# Generated by install_fosbot.py
# --- File: app/apis/settings_api.py --- START ---
import logging
from fastapi import APIRouter, HTTPException, Body, status
from pydantic import BaseModel, Field, field_validator # Use field_validator
from typing import Dict, Any, List, Optional

# Use specific helpers from json_store
from app.core.json_store import load_settings, update_setting, load_tokens
from app.core.event_bus import event_bus
from app.events import SettingsUpdated, ServiceControl # PlatformStatusUpdate is handled by services

logger = logging.getLogger(__name__)
router = APIRouter() # Mounted under /api in main.py

# --- Pydantic Models for Settings ---
# Define allowed log levels
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class AppSettingsUpdateModel(BaseModel):
    """Model for updating non-sensitive, non-token application settings via the API."""
    COMMAND_PREFIX: Optional[str] = Field(None, min_length=1, max_length=5)
    LOG_LEVEL: Optional[str] = Field(None)
    TWITCH_CHANNELS: Optional[str] = None # Comma-separated string

    # Use Pydantic v2 validator
    @field_validator('LOG_LEVEL')
    @classmethod
    def check_log_level(cls, v: Optional[str]):
        if v is not None and v.upper() not in VALID_LOG_LEVELS:
            raise ValueError(f'LOG_LEVEL must be one of: {", ".join(VALID_LOG_LEVELS)}')
        return v.upper() if v is not None else None

    class Config:
        extra = 'forbid' # Prevent unexpected fields

# --- API Endpoints ---

@router.get("/settings", response_model=Dict[str, Any], summary="Get Current Non-Token Settings & Auth Status")
async def get_current_settings():
    """
    Retrieves non-sensitive settings (like prefix, log level, channels)
    and the login status for OAuth platforms. Secrets/tokens are NOT returned.
    """
    logger.debug("GET /api/settings request received")
    all_settings = await load_settings() # Loads the entire settings.json
    if not isinstance(all_settings, dict):
         logger.error("Failed to load settings or invalid format encountered.")
         all_settings = {} # Return empty if load failed

    # Filter out sensitive keys explicitly
    non_sensitive_keys = ["COMMAND_PREFIX", "LOG_LEVEL", "TWITCH_CHANNELS"] # Add other non-secrets here
    display_settings = {k: all_settings.get(k) for k in non_sensitive_keys if k in all_settings}

    # Add default values if missing from file
    display_settings.setdefault('COMMAND_PREFIX', '!')
    display_settings.setdefault('LOG_LEVEL', 'INFO')
    display_settings.setdefault('TWITCH_CHANNELS', '')

    # Add authentication status for each platform
    platforms = ["twitch", "youtube", "x"]
    for p in platforms:
        tokens = await load_tokens(p) # Checks for stored access token
        display_settings[f"{p}_auth_status"] = {
            "logged_in": bool(tokens), # True if tokens were loaded (i.e., access_token exists)
            "user_login": tokens.get("user_login") if tokens else None # Display username if available
        }

    # Add Whatnot status (placeholder, maybe bridge reports this?)
    # For now, assume if bridge service is running (task exists?), it's 'connected'
    # This isn't perfect as it doesn't guarantee the *extension* is connected
    from app.main import _service_tasks_map #   
    whatnot_task = _service_tasks_map.get("whatnot")
    whatnot_running = bool(whatnot_task and not whatnot_task.done())
    display_settings["whatnot_auth_status"] = {
        "logged_in": whatnot_running, # Use task status as proxy
         "user_login": "Extension Connected" if whatnot_running else "Extension Disconnected/Off"
    }


    logger.debug(f"Returning non-token settings & auth status: {display_settings}")
    return display_settings

@router.post("/settings", status_code=status.HTTP_200_OK, summary="Update Non-Token Application Settings")
async def update_settings_endpoint(new_settings: AppSettingsUpdateModel = Body(...)):
    """
    Updates non-sensitive application settings like command prefix, log level,
    and Twitch channels. Does NOT handle API keys or tokens (use OAuth flow).
    """
    logger.info("POST /api/settings request received for non-auth settings.")
    # Get only the fields explicitly set in the request body
    update_data = new_settings.dict(exclude_unset=True)

    if not update_data:
        logger.info("Update settings request received with no data.")
        # Return 200 OK but indicate no changes were made
        return {"message": "No settings provided for update."}

    logger.info(f"Attempting to update non-auth keys: {list(update_data.keys())}")
    updated_keys: List[str] = []
    failed_keys: List[str] = []
    actually_changed_keys: List[str] = [] # Track keys whose values genuinely changed

    initial_settings = await load_settings() # Load current state before update

    # Iterate through provided fields and update using the json_store helper
    for key, value in update_data.items():
        initial_value = initial_settings.get(key)
        try:
            # update_setting handles loading current, checking diff, saving, and publishing event
            # It returns True if save was successful OR if value was unchanged
            # It returns False if save failed
            success = await update_setting(key, value) # update_setting now updates global `settings` too
            if success:
                 # Check if the value actually changed compared to initial state
                 if initial_value != value:
                      actually_changed_keys.append(key)
                 # Add to potential success list (even if unchanged)
                 if key not in failed_keys:
                     updated_keys.append(key)
            else:
                # update_setting returned False, meaning save failed
                failed_keys.append(key)
        except Exception as e:
            # Catch unexpected errors during the update process for a specific key
            logger.exception(f"Unexpected error updating setting '{key}': {e}")
            failed_keys.append(key)

    # Consolidate unique keys
    final_updated_keys = list(set(actually_changed_keys) - set(failed_keys)) # Only report genuinely changed & saved keys
    failed_keys = list(set(failed_keys))

    if failed_keys:
        # If any key failed, report a 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings for keys: {', '.join(failed_keys)}."
        )

    if not final_updated_keys:
        # If no keys failed and no keys were actually updated
        return {"message": "No setting values were changed."}

    # If successful and changes were made
    # SettingsUpdated event is published by update_setting now
    return {"message": f"Settings updated successfully: {', '.join(final_updated_keys)}."}


@router.post("/control/{service_name}/{command}", status_code=status.HTTP_202_ACCEPTED, summary="Control Platform Services")
async def control_service(service_name: str, command: str):
    """Sends a command (start, stop, restart) to a specified platform service via the event bus."""
    allowed_services = ["twitch", "youtube", "x", "whatnot"]
    allowed_commands = ["start", "stop", "restart"]
    service_name_lower = service_name.lower()
    command_lower = command.lower()

    if service_name_lower not in allowed_services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not recognized. Allowed: {', '.join(allowed_services)}"
        )
    if command_lower not in allowed_commands:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid command '{command}'. Allowed: {', '.join(allowed_commands)}"
        )

    logger.info(f"Control command '{command_lower}' for service '{service_name_lower}' received via API.")
    # Publish the event for main.py's handler
    event_bus.publish(ServiceControl(service_name=service_name_lower, command=command_lower))

    # Return 202 Accepted: The request is accepted, but processing happens asynchronously.
    return {"message": f"'{command_lower}' command queued for '{service_name_lower}' service."}

# --- File: app/apis/settings_api.py --- END ---
""",
        "app/apis/ws_endpoints.py": r"""# Generated by install_fosbot.py
# --- File: app/apis/ws_endpoints.py --- START ---
import logging
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import datetime # For timestamping Whatnot messages if needed

# Service handlers for WebSocket logic
# dashboard_service handles the /dashboard endpoint
from app.services.dashboard_service import handle_dashboard_websocket
# whatnot_bridge now manages the connection state from this endpoint
from app.services.whatnot_bridge import set_whatnot_websocket, clear_whatnot_websocket

# Event Bus and Events for communication with backend
from app.core.event_bus import event_bus
from app.events import InternalChatMessage, ChatMessageReceived, LogMessage # Added LogMessage

# --- Setup ---
logger = logging.getLogger(__name__)
router = APIRouter()

# --- WebSocket Endpoints ---

@router.websocket("/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """Handles WebSocket connections from the Streamer Dashboard UI."""
    # Ensure dashboard_service exists and has this function
    try:
        await handle_dashboard_websocket(websocket) # Delegate to dashboard_service
    except NameError:
         logger.error("handle_dashboard_websocket function not found in dashboard_service.")
         await websocket.close(code=1011, reason="Dashboard service handler missing")
    except Exception as e:
        logger.exception(f"Error in dashboard websocket connection: {e}")
        # Attempt to close gracefully
        try: await websocket.close(code=1011)
        except: pass


@router.websocket("/whatnot")
async def websocket_whatnot_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections from the Whatnot Browser Extension.
    Accepts connection, registers it with whatnot_bridge, receives messages,
    parses them, and publishes ChatMessageReceived events.
    """
    client_host = websocket.client.host if websocket.client else "Unknown"
    client_port = websocket.client.port if websocket.client else "N/A"
    client_id = f"{client_host}:{client_port}"
    await websocket.accept()
    logger.info(f"Whatnot Extension client connected: {client_id}")
    # Register this active WebSocket with the bridge service
    try:
        set_whatnot_websocket(websocket)
    except NameError:
         logger.error("set_whatnot_websocket function not found in whatnot_bridge.")
         await websocket.close(code=1011, reason="Whatnot bridge handler missing")
         return
    except Exception as e:
        logger.exception(f"Error registering Whatnot websocket: {e}")
        await websocket.close(code=1011, reason="Backend registration error")
        return

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received raw data from Whatnot Ext {client_id}: {data}")

            try:
                message_data = json.loads(data)
                msg_type = message_data.get("type")

                if msg_type == "chat_message":
                    payload = message_data.get("payload", {})
                    user = payload.get("user")
                    text = payload.get("text")

                    if user and text: # Basic validation
                        # Create standardized internal message
                        msg = InternalChatMessage(
                            platform='whatnot',
                            user=user,
                            text=text,
                            channel=payload.get("channel", "whatnot_live"), # Add channel if available
                            user_id=payload.get("userId"), # Add user ID if available
                            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(), # Use current UTC time
                            raw_data=payload # Store original payload
                        )
                        # Publish event for dashboard and chat processor
                        event_bus.publish(ChatMessageReceived(message=msg))
                    else:
                         logger.warning(f"Invalid Whatnot chat_message payload from {client_id}: Missing user or text. Payload: {payload}")

                elif msg_type == "ping":
                    # Respond to keepalives from extension
                    await websocket.send_json({"type": "pong"})
                    logger.debug(f"Sent pong to Whatnot Ext {client_id}")
                elif msg_type == "debug":
                     # Forward debug messages from extension to backend logs/dashboard
                     log_payload = message_data.get("payload", {})
                     log_level = log_payload.get("level", "DEBUG").upper()
                     log_msg = log_payload.get("message", "No message content.")
                     # Use standard logging levels
                     numeric_level = getattr(logging, log_level, logging.DEBUG)
                     logger.log(numeric_level, f"[WhatnotExt Debug] {log_msg}")
                     # Optionally publish to event bus for dashboard display
                     event_bus.publish(LogMessage(level=log_level, message=log_msg, module="WhatnotExtension"))
                else:
                    logger.warning(f"Received unknown message type '{msg_type}' from Whatnot Ext {client_id}: {data}")

            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message from Whatnot Ext {client_id}: {data}")
            except Exception as e:
                # Catch errors during message processing within the loop
                logger.exception(f"Error processing message from Whatnot Ext {client_id}: {e}")

    except WebSocketDisconnect as e:
        logger.info(f"Whatnot Extension client {client_id} disconnected (Code: {e.code}, Reason: {e.reason or 'N/A'}).")
    except Exception as e:
        # Catch other errors like connection closed unexpectedly
        logger.error(f"Unexpected error in Whatnot Extension WebSocket handler for {client_id}: {e}", exc_info=True)
    finally:
         # Crucial: Clear the WebSocket reference in the bridge service on disconnect/error
         logger.info(f"Cleaning up Whatnot Extension connection handler for {client_id}")
         try:
             clear_whatnot_websocket()
         except NameError:
              logger.error("clear_whatnot_websocket function not found in whatnot_bridge.")
         except Exception as e:
              logger.exception(f"Error clearing Whatnot websocket: {e}")


@router.websocket("/debug")
async def websocket_debug_endpoint(websocket: WebSocket):
    """Optional endpoint for receiving debug logs from extensions or other clients."""
    await websocket.accept()
    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown Debug Client"
    logger.info(f"Debug client connected: {client_id}")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                debug_data = json.loads(data)
                if debug_data.get("type") == "debug":
                    message = debug_data.get("message", "No debug message content.")
                    source = debug_data.get("source", client_id) # Identify source if provided
                    level = debug_data.get("level", "DEBUG").upper()
                    log_level_int = getattr(logging, level, logging.DEBUG)
                    # Log clearly indicating the source
                    logger.log(log_level_int, f"[{source} DEBUG]: {message}")
                    # Optionally publish for dashboard display
                    # event_bus.publish(LogMessage(level=level, message=message, module=source)) # Maybe too noisy?
                else:
                    logger.warning(f"Received non-debug JSON via debug WS from {client_id}: {data}")
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON via debug WS from {client_id}: {data}")
            except Exception as e:
                logger.error(f"Error processing debug WS message from {client_id}: {e}")
    except WebSocketDisconnect:
        logger.info(f"Debug client {client_id} disconnected.")
    except Exception as e:
        logger.error(f"Unexpected error in debug WebSocket handler for {client_id}: {e}", exc_info=True)
    finally:
         logger.debug(f"Closing debug websocket connection for {client_id}")

# --- File: app/apis/ws_endpoints.py --- END ---
""",
        "app/apis/commands_api.py": r"""# Generated by install_fosbot.py
# --- File: app/apis/commands_api.py --- START ---
import logging
import csv
import io
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Body # Added Status, Body
from pydantic import BaseModel, field_validator
from typing import Dict, List, Optional

# Use the json_store functions
from app.core.json_store import load_commands, save_commands

logger = logging.getLogger(__name__)
router = APIRouter() # Mounted under /api in main.py

# --- Pydantic Models ---
class CommandModel(BaseModel):
    command: str # Command name (without prefix)
    response: str

    # Add validation if needed, e.g., prevent empty command/response
    @field_validator('command')
    @classmethod
    def command_must_not_be_empty(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError('Command name cannot be empty.')
        # Ensure command doesn't include the prefix
        # Assuming prefix might be passed accidentally
        from app.core.config import settings # Local import to avoid circular dependency at module level
        prefix = settings.get('COMMAND_PREFIX', '!')
        if v.startswith(prefix):
            logger.warning(f"Command '{v}' submitted with prefix. Stripping prefix.")
            v = v[len(prefix):]
        # Basic sanitization - ensure lowercase
        return v.strip().lower()

    @field_validator('response')
    @classmethod
    def response_must_not_be_empty(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError('Command response cannot be empty.')
        return v

# --- API Endpoints ---

@router.get("/commands", response_model=Dict[str, str], summary="Get All Custom Commands")
async def get_commands_endpoint():
    """Fetches all currently defined custom commands."""
    logger.debug("GET /api/commands request received")
    commands = await load_commands()
    if not isinstance(commands, dict):
        logger.error("Failed to load commands or invalid format.")
        # Return empty dict instead of raising 500, allows UI to function
        return {}
    logger.debug(f"Returning {len(commands)} commands.")
    return commands

@router.post("/commands", response_model=CommandModel, status_code=status.HTTP_201_CREATED, summary="Add or Update a Custom Command")
async def add_or_update_command_endpoint(command_data: CommandModel = Body(...)):
    """Adds a new custom command or updates an existing one."""
    command_name = command_data.command # Already validated and cleaned by Pydantic
    response_text = command_data.response

    logger.info(f"POST /api/commands: Attempting to add/update command '!{command_name}'")
    commands = await load_commands()
    if not isinstance(commands, dict):
        logger.error("Failed to load commands before add/update.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load existing commands.")

    is_update = command_name in commands
    action = "updated" if is_update else "added"

    commands[command_name] = response_text # Add or overwrite

    if await save_commands(commands):
        logger.info(f"Command '!{command_name}' successfully {action}.")
        # Reload commands in chat processor cache
        from app.services.chat_processor import load_and_cache_commands
        await load_and_cache_commands()
        # Return the saved command data
        return CommandModel(command=command_name, response=response_text)
    else:
        logger.error(f"Failed to save commands after attempting to {action} '!{command_name}'.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save command '!{command_name}'.")

@router.delete("/commands/{command_name}", status_code=status.HTTP_200_OK, summary="Delete a Custom Command")
async def delete_command_endpoint(command_name: str):
    """Deletes a specific custom command."""
    # Clean the input command name same way as Pydantic model does
    cleaned_command_name = command_name.strip().lower()
    if not cleaned_command_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Command name cannot be empty.")

    logger.info(f"DELETE /api/commands/{cleaned_command_name}: Attempting to delete command.")
    commands = await load_commands()
    if not isinstance(commands, dict):
         logger.error("Failed to load commands before delete.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load existing commands.")

    if cleaned_command_name in commands:
        del commands[cleaned_command_name]
        if await save_commands(commands):
            logger.info(f"Command '!{cleaned_command_name}' successfully deleted.")
            # Reload commands in chat processor cache
            from app.services.chat_processor import load_and_cache_commands
            await load_and_cache_commands()
            return {"message": f"Command '!{cleaned_command_name}' deleted successfully."}
        else:
            logger.error(f"Failed to save commands after deleting '!{cleaned_command_name}'.")
            # Add command back? Or just report error? Report error.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save changes after deleting command.")
    else:
        logger.warning(f"Attempted to delete non-existent command '!{cleaned_command_name}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Command '!{cleaned_command_name}' not found.")

@router.post("/commands/upload", status_code=status.HTTP_201_CREATED, summary="Upload Commands via CSV")
async def upload_commands_endpoint(file: UploadFile = File(...)):
    """
    Uploads multiple commands from a CSV file.
    Expects CSV format: 'command_name,response_text' (optional header row).
    Overwrites existing commands with the same name.
    """
    logger.info(f"POST /api/commands/upload: Received file '{file.filename}' ({file.content_type})")
    if file.content_type != 'text/csv' and not file.filename.lower().endswith('.csv'):
        logger.warning(f"Invalid file type uploaded: {file.content_type} / {file.filename}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload a CSV file.")

    commands = await load_commands()
    if not isinstance(commands, dict):
         logger.error("Failed to load commands before CSV upload.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load existing commands.")

    added_count = 0
    updated_count = 0
    skipped_count = 0
    rows_processed = 0

    try:
        content = await file.read()
        # Use universal newlines mode for StringIO
        csv_file = io.StringIO(content.decode('utf-8-sig'), newline=None) # Handle BOM, standard newlines
        # Sniff for header presence
        try:
            has_header = csv.Sniffer().has_header(csv_file.read(1024))
        except csv.Error:
             has_header = False # Assume no header if sniffing fails
        csv_file.seek(0) # Rewind after sniffing
        reader = csv.reader(csv_file)

        if has_header:
            try:
                header = next(reader) # Skip header row
                rows_processed += 1
                logger.debug(f"Skipped CSV header: {header}")
            except StopIteration:
                 logger.warning("CSV file seems to contain only a header row.")
                 return {"message": "CSV processed. No command rows found.", "added": 0, "updated": 0, "skipped": 0}


        for i, row in enumerate(reader, start=rows_processed + 1):
            if not row or len(row) < 2:
                logger.warning(f"Skipping malformed CSV row {i}: {row}")
                skipped_count += 1
                continue

            command_raw = row[0].strip()
            response_raw = row[1].strip()

            # Basic validation
            if not command_raw or not response_raw:
                 logger.warning(f"Skipping row {i} due to empty command or response: {row}")
                 skipped_count += 1
                 continue

            # Clean command name (lowercase, no prefix)
            from app.core.config import settings # Local import
            prefix = settings.get('COMMAND_PREFIX', '!')
            if command_raw.startswith(prefix):
                command_name = command_raw[len(prefix):].strip().lower()
            else:
                command_name = command_raw.lower()

            if not command_name: # Check again after stripping prefix
                 logger.warning(f"Skipping row {i} due to effectively empty command after prefix strip: {row}")
                 skipped_count += 1
                 continue

            # Add/Update command
            if command_name in commands:
                 updated_count += 1
            else:
                 added_count += 1
            commands[command_name] = response_raw
            logger.debug(f"Processed row {i}: Adding/Updating command '!{command_name}'")

    except UnicodeDecodeError:
         logger.error("Failed to decode CSV file. Ensure it is UTF-8 encoded.")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file encoding. Please use UTF-8.")
    except csv.Error as e:
        logger.error(f"Error parsing CSV file: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error parsing CSV: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error processing CSV upload: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during CSV processing.")
    finally:
        await file.close() # Ensure file handle is closed

    if added_count > 0 or updated_count > 0:
        if await save_commands(commands):
            logger.info(f"CSV upload successful: Added {added_count}, Updated {updated_count}, Skipped {skipped_count} commands.")
            # Reload commands in chat processor cache
            from app.services.chat_processor import load_and_cache_commands
            await load_and_cache_commands()
            return {
                "message": "Commands uploaded successfully.",
                "added": added_count,
                "updated": updated_count,
                "skipped": skipped_count
            }
        else:
            logger.error("Failed to save commands after CSV processing.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save commands after processing CSV.")
    else:
        logger.info(f"CSV processed. No new or updated commands found. Skipped {skipped_count} rows.")
        return {"message": "CSV processed. No new or updated commands found.", "added": 0, "updated": 0, "skipped": skipped_count}

# --- File: app/apis/commands_api.py --- END ---
""",

        # === app/services/ Files ===
        "app/services/__init__.py": r"""# Generated by install_fosbot.py
# Empty file to make services a package
""",
        "app/services/chat_processor.py": r"""# Generated by install_fosbot.py
# --- File: app/services/chat_processor.py (Derived from chat.py) --- START ---
import logging
import asyncio
import datetime
import random
import time # For cooldowns
from collections import defaultdict
from typing import Dict, List, Any, Optional, Awaitable, Callable # Added Callable, Awaitable

# Core imports
from app.core.event_bus import event_bus
from app.events import (
    ChatMessageReceived, CommandDetected, BotResponse, BotResponseToSend,
    StreamerInputReceived, BroadcastStreamerMessage, InternalChatMessage
)
from app.core.config import logger, settings # Use settings dict
# Use specific json_store functions
from app.core.json_store import load_checkins, save_checkins, load_commands, load_counters, save_counters, get_setting

# Command Handler Type Definition
CommandHandler = Callable[[CommandDetected], Awaitable[None]]
command_registry: Dict[str, CommandHandler] = {}
custom_commands: Dict[str, str] = {} # Cache for custom commands

# Cooldowns State
user_cooldowns: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float)) # {cmd: {user_key: timestamp}}
global_cooldowns: Dict[str, float] = defaultdict(float) # {cmd: timestamp}

# Cooldown Durations (Defaults, can be overridden per command)
# Using more descriptive keys
COOLDOWN_CONFIG = {
    "default_user_cooldown": 5.0,
    "default_global_cooldown": 1.5,
    "cmd_checkin_user": 300.0, # 5 minutes for !checkin per user
    "cmd_seen_user": 10.0,
    "cmd_socials_user": 30.0,
    "cmd_commands_user": 20.0,
    "cmd_uptime_global": 10.0,
    "cmd_roll_user": 3.0,
    "cmd_roll_global": 1.0,
    # Add specific overrides here as needed
}

# Bot start time
bot_start_time = datetime.datetime.now(datetime.timezone.utc)

# --- Helper Functions ---

def send_reply(event: CommandDetected, text: str):
    """Helper to create and publish a BotResponseToSend event."""
    source_msg = event.source_message
    if not source_msg or not source_msg.platform:
        logger.error(f"Cannot send reply for command '{event.command}': Missing source message or platform.")
        return

    response = BotResponse(
        target_platform=source_msg.platform,
        target_channel=source_msg.channel, # Use the channel from the source message
        text=text,
        reply_to_user=source_msg.user # Pass user for potential @mentioning by platform service
        # reply_to_message_id=source_msg.message_id # Optional: Pass message ID if platform supports direct replies
    )
    event_bus.publish(BotResponseToSend(response=response))
    logger.debug(f"Published BotResponseToSend to {source_msg.platform}:{source_msg.channel or 'DM'}")


def format_timedelta_human(delta: datetime.timedelta) -> str:
    """Formats a timedelta into a human-readable string like '3d 4h' or '5m 10s'."""
    total_seconds = int(delta.total_seconds())
    if total_seconds < 1: return "just now"

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0 and days == 0: parts.append(f"{minutes}m") # Only show mins if < 1 day
    if seconds > 0 and days == 0 and hours == 0: parts.append(f"{seconds}s") # Only show secs if < 1 hour

    return " ".join(parts[:2]) + " ago" if parts else "moments ago"

# --- Command Cooldown Check ---
def is_command_on_cooldown(command_name: str, user_platform: str, user_login: str) -> Optional[float]:
    """Checks user and global cooldowns. Returns remaining seconds if on cooldown, else None."""
    now = time.monotonic()
    is_admin = user_platform == 'dashboard' # Treat dashboard input as admin bypass
    if is_admin: return None

    user_key = f"{user_platform}:{user_login.lower()}" # Consistent key

    # Global Cooldown Check
    global_cd_key = f"cmd_{command_name}_global"
    global_duration = COOLDOWN_CONFIG.get(global_cd_key, COOLDOWN_CONFIG["default_global_cooldown"])
    last_global_use = global_cooldowns[command_name] # defaultdict defaults to 0.0
    if now < last_global_use + global_duration:
        remaining = (last_global_use + global_duration) - now
        logger.debug(f"Cmd '{command_name}' on global CD ({remaining:.1f}s left).")
        return remaining

    # User Cooldown Check
    user_cd_key = f"cmd_{command_name}_user"
    user_duration = COOLDOWN_CONFIG.get(user_cd_key, COOLDOWN_CONFIG["default_user_cooldown"])
    last_user_use = user_cooldowns[command_name][user_key] # defaultdict defaults to 0.0
    if now < last_user_use + user_duration:
        remaining = (last_user_use + user_duration) - now
        logger.debug(f"Cmd '{command_name}' on user CD for {user_key} ({remaining:.1f}s left).")
        return remaining

    return None # Not on cooldown

def update_cooldowns(command_name: str, user_platform: str, user_login: str):
    """Updates cooldown timestamps after successful execution."""
    now = time.monotonic()
    is_admin = user_platform == 'dashboard'
    if is_admin: return # Admins don't trigger cooldowns

    user_key = f"{user_platform}:{user_login.lower()}"
    global_cooldowns[command_name] = now
    user_cooldowns[command_name][user_key] = now
    logger.debug(f"Updated cooldowns for '{command_name}' (User: {user_key})")

# --- Built-in Command Handlers ---

async def handle_ping(event: CommandDetected):
    """Replies with Pong!"""
    send_reply(event, "Pong!")

async def handle_socials(event: CommandDetected):
    """Replies with social media links (loaded from config or hardcoded)."""
    # Example: Load from settings if available, otherwise use default
    social_text = await get_setting("SOCIALS_TEXT", "Follow me: twitch.tv/fos_gamers, youtube.com/@fos_gamers, x.com/fos_gamers")
    send_reply(event, social_text)

async def handle_lurk(event: CommandDetected):
    """Sends a thank you message for lurking."""
    send_reply(event, f"Thanks for the lurk, {event.source_message.user}! Enjoy the stream! o/")

async def handle_hype(event: CommandDetected):
    """Sends a hype message."""
    send_reply(event, "  _  HYPE! LET'S GOOOOO!   _ ")

async def handle_checkin(event: CommandDetected):
    """Records a user's check-in time."""
    user = event.source_message.user
    platform = event.source_message.platform
    user_id = str(event.source_message.user_id or user) # Prefer user_id if available
    checkin_key = f"{platform}:{user_id}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    checkins_data = await load_checkins() # Returns {} on failure/empty
    entry = checkins_data.get(checkin_key, {})

    entry['username'] = user # Always update username in case it changed
    entry['last_seen'] = now_iso
    entry['platform'] = platform # Store platform explicitly
    entry['channel'] = event.source_message.channel # Store channel

    checkin_count = entry.get('checkin_count', 0) + 1
    entry['checkin_count'] = checkin_count

    if 'first_seen' not in entry:
        entry['first_seen'] = now_iso
        reply_text = f"Welcome, {user}! You've checked in for the first time!"
        logger.info(f"First check-in for {user} ({checkin_key}).")
    else:
        reply_text = f"{user} checked in! (Total check-ins: {checkin_count})"
        logger.info(f"Check-in {checkin_count} for {user} ({checkin_key}).")

    checkins_data[checkin_key] = entry

    if await save_checkins(checkins_data):
        send_reply(event, reply_text)
    else:
        send_reply(event, "Sorry, there was an error saving your check-in.")
        logger.error(f"Failed to save checkin data for {checkin_key}")

async def handle_seen(event: CommandDetected):
    """Looks up when a user was last seen checked in."""
    if not event.args:
        send_reply(event, f"Usage: {settings.get('COMMAND_PREFIX', '!')}seen <username>")
        return

    target_user_lower = event.args[0].lstrip('@').lower()
    requesting_platform = event.source_message.platform
    found_record = None
    found_username = None

    checkins_data = await load_checkins()

    # Search for the user, prioritizing same platform, then others
    # Strategy: Find exact match on current platform first, then case-insensitive on current, then case-insensitive on others.
    search_order = [
        lambda k, r: r.get('platform') == requesting_platform and r.get('username', '').lower() == target_user_lower, # Exact platform, case-insensitive user
        lambda k, r: r.get('username', '').lower() == target_user_lower # Case-insensitive user on any platform
    ]

    for search_func in search_order:
        for key, record in checkins_data.items():
             if isinstance(record, dict) and search_func(key, record):
                  found_record = record
                  found_username = record.get('username', 'Unknown') # Use stored name
                  break # Found a match
        if found_record: break # Stop searching if found

    if found_record and found_username:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        try:
            last_seen_dt = datetime.datetime.fromisoformat(found_record['last_seen'])
            first_seen_dt = datetime.datetime.fromisoformat(found_record.get('first_seen', found_record['last_seen'])) # Fallback to last_seen if first_seen missing
            # Ensure they are timezone-aware (assume UTC if not specified by ISO string)
            if last_seen_dt.tzinfo is None: last_seen_dt = last_seen_dt.replace(tzinfo=datetime.timezone.utc)
            if first_seen_dt.tzinfo is None: first_seen_dt = first_seen_dt.replace(tzinfo=datetime.timezone.utc)

            last_seen_delta = now_utc - last_seen_dt
            first_seen_delta = now_utc - first_seen_dt
            last_seen_fmt = format_timedelta_human(last_seen_delta)
            first_seen_fmt = format_timedelta_human(first_seen_delta)
            platform_seen = found_record.get('platform', 'unknown platform')
            channel_seen = found_record.get('channel')
            location_str = f"on {platform_seen}" + (f" in #{channel_seen}" if channel_seen else "")

            send_reply(event, f"Found {found_username} {location_str}. First seen: {first_seen_fmt}. Last seen: {last_seen_fmt}.")
        except (ValueError, KeyError, TypeError) as e:
             logger.error(f"Error parsing stored timestamp for {found_username}: {e}", exc_info=True)
             send_reply(event, f"Sorry, couldn't read the stored time data for {event.args[0]}.")
    else:
        send_reply(event, f"Haven't seen a check-in from '{event.args[0]}' yet.")

async def handle_uptime(event: CommandDetected):
    """Reports how long the bot process has been running."""
    uptime_delta = datetime.datetime.now(datetime.timezone.utc) - bot_start_time
    uptime_str = format_timedelta_human(uptime_delta).replace(" ago", "")
    if uptime_str == "just now": uptime_str = "a few moments"
    elif not uptime_str or uptime_str == "moments": uptime_str = "just started"
    send_reply(event, f"Bot process uptime: {uptime_str}")

async def handle_commands(event: CommandDetected):
    """Lists available commands."""
    prefix = settings.get('COMMAND_PREFIX', '!')
    # Combine built-in and custom commands
    all_cmds = sorted(list(command_registry.keys()) + list(custom_commands.keys()))
    # TODO: Add permission filtering here later
    formatted_cmds = [f"{prefix}{cmd}" for cmd in all_cmds]

    reply_text = "Available commands: " + ", ".join(formatted_cmds)
    MAX_LEN = 480 # Max length for typical chat message after prefixes etc.
    if len(reply_text) > MAX_LEN:
         # Split into multiple messages if too long (basic split)
         parts = []
         current_part = "Available commands: "
         for cmd in formatted_cmds:
              if len(current_part) + len(cmd) + 2 < MAX_LEN:
                   current_part += f"{cmd}, "
              else:
                   parts.append(current_part.rstrip(', '))
                   current_part = f"... {cmd}, "
         parts.append(current_part.rstrip(', '))
         for part in parts:
              send_reply(event, part)
              await asyncio.sleep(0.5) # Small delay between parts
    else:
         send_reply(event, reply_text)

async def handle_inc_counter(event: CommandDetected):
    """Increments a counter (e.g., !death). Command name is the counter key."""
    counter_name = event.command # e.g., 'death'
    counters = await load_counters() # Returns {} on failure

    current_value = counters.get(counter_name, 0)
    new_value = current_value + 1
    counters[counter_name] = new_value

    if await save_counters(counters):
        send_reply(event, f"{counter_name.capitalize()} count increased to {new_value}!")
        logger.info(f"Counter '{counter_name}' incremented to {new_value}.")
    else:
        send_reply(event, f"Sorry, error saving '{counter_name}' counter.")
        logger.error(f"Failed to save counters data after incrementing {counter_name}")

async def handle_show_count(event: CommandDetected):
     """Shows the value of a specific counter or all counters."""
     counters = await load_counters()
     if not event.args:
          # Show all counters if no argument provided
          if not counters:
               send_reply(event, "No counters are currently being tracked.")
               return
          reply_parts = ["Current Counts:"]
          for name, value in counters.items():
               reply_parts.append(f"{name.capitalize()}: {value}")
          send_reply(event, " | ".join(reply_parts))
     else:
          counter_name = event.args[0].lower()
          value = counters.get(counter_name, 0)
          send_reply(event, f"The current count for '{counter_name}' is: {value}")

async def handle_roll(event: CommandDetected):
    """Rolls dice (e.g., !roll d20, !roll 2d6)."""
    args = event.args
    if not args:
        args = ["d20"] # Default to d20

    roll_input = args[0].lower()
    num_dice = 1
    num_sides = 0

    try:
        if 'd' in roll_input:
            parts = roll_input.split('d')
            # Allow empty string before 'd' (means 1 die)
            num_dice_str = parts[0]
            if num_dice_str and num_dice_str.isdigit():
                num_dice = int(num_dice_str)
            elif num_dice_str: # If something is before 'd' but not a number
                 raise ValueError("Invalid number of dice")

            if parts[1].isdigit():
                num_sides = int(parts[1])
            else:
                 raise ValueError("Invalid sides format")
        elif roll_input.isdigit():
            # Interpret as rolling a single die with that many sides (e.g., !roll 6 is like !roll d6)
            num_sides = int(roll_input)
            if num_sides <= 0: raise ValueError("Sides must be positive")
        else:
             raise ValueError("Invalid roll format")

        # Add reasonable limits
        if not 1 <= num_dice <= 100: raise ValueError("Number of dice must be between 1 and 100.")
        if not 2 <= num_sides <= 1000: raise ValueError("Number of sides must be between 2 and 1000.")

        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(rolls)
        # Only show individual rolls if few dice, otherwise just total
        if num_dice <= 10:
            rolls_str = ", ".join(map(str, rolls))
            if num_dice == 1:
                 response_text = f"@{event.source_message.user} rolled a d{num_sides}: {total}"
            else:
                 response_text = f"@{event.source_message.user} rolled {num_dice}d{num_sides}: [{rolls_str}] Total = {total}"
        else: # Too many dice to show individually
             response_text = f"@{event.source_message.user} rolled {num_dice}d{num_sides}: Total = {total}"

    except ValueError as e:
        response_text = f"Invalid roll! Usage: !roll [N]d[S] (e.g., !roll d20, !roll 3d6). Error: {e}"
    except Exception as e:
         logger.error(f"Error during roll command: {e}", exc_info=True)
         response_text = "Oops, something went wrong with the dice!"

    send_reply(event, response_text)


# --- Command Registration ---
def register_command(name: str, handler: CommandHandler):
    """Registers a built-in command handler."""
    command_registry[name.lower()] = handler
    logger.debug(f"Registered built-in command: {name}")

# --- Register Built-in Commands ---
register_command("ping", handle_ping)
register_command("socials", handle_socials)
register_command("lurk", handle_lurk)
register_command("hype", handle_hype)
register_command("checkin", handle_checkin)
register_command("seen", handle_seen)
register_command("uptime", handle_uptime)
register_command("commands", handle_commands)
register_command("roll", handle_roll)
# Register counter commands dynamically based on convention? Or explicitly? Explicit for now.
register_command("death", handle_inc_counter)
register_command("win", handle_inc_counter)
register_command("fail", handle_inc_counter)
register_command("drop", handle_inc_counter) # Example additional counter
register_command("showcount", handle_show_count)


# --- Main Processing Logic ---
async def load_and_cache_commands():
     """Loads custom commands from JSON store into memory."""
     global custom_commands
     loaded = await load_commands() # load_commands now ensures lowercase keys
     if isinstance(loaded, dict):
          custom_commands = loaded
          logger.info(f"Loaded/Refreshed {len(custom_commands)} custom commands.")
     else:
          logger.error("Failed to load custom commands or invalid format.")
          custom_commands = {} # Reset cache on failure


async def process_chat_message(event: ChatMessageReceived):
    """Central processor for incoming messages."""
    msg = event.message
    prefix = settings.get('COMMAND_PREFIX', '!') # Get prefix from settings

    # Basic validation
    if not msg or not msg.text or not msg.user or not prefix:
        return

    # Check for command prefix
    if msg.text.startswith(prefix):
        parts = msg.text[len(prefix):].strip().split()
        if not parts: return # Ignore if only prefix is sent

        command_name = parts[0].lower()
        args = parts[1:]
        # Avoid logging the command detection if it's from Whatnot (can be spammy)
        if msg.platform != 'whatnot':
            logger.info(f"Command detected: '!{command_name}' from {msg.platform}:{msg.user}")

        # Ignore commands from Whatnot platform for now (Phase 1 limitation)
        # Re-enable this check if Whatnot commands should be ignored globally
        if msg.platform == 'whatnot':
             logger.debug(f"Ignoring command '!{command_name}' from Whatnot user {msg.user} (Phase 1)")
             return

        # Check cooldowns
        cooldown_remaining = is_command_on_cooldown(command_name, msg.platform, msg.user)
        if cooldown_remaining is not None:
            # Optionally notify user they are on cooldown (can be spammy)
            # send_reply(CommandDetected(command_name, args, msg), f"Command !{command_name} is on cooldown ({cooldown_remaining:.1f}s left).")
            logger.info(f"Command '!{command_name}' by {msg.user} skipped due to cooldown ({cooldown_remaining:.1f}s).")
            return

        # Create CommandDetected event
        cmd_event = CommandDetected(command=command_name, args=args, source_message=msg)

        # Check built-in commands first
        handler = command_registry.get(command_name)
        if handler:
            try:
                await handler(cmd_event)
                update_cooldowns(command_name, msg.platform, msg.user) # Update cooldowns *after* successful execution
            except Exception as e:
                logger.exception(f"Error executing built-in command handler for '!{command_name}': {e}")
                try: send_reply(cmd_event, f"Oops! Error running command '!{command_name}'.")
                except: pass # Avoid error loops
            return # Command handled

        # Check custom commands (case-insensitive lookup)
        custom_response = custom_commands.get(command_name)
        if custom_response:
            try:
                # Replace placeholders like {user}
                # Use display_name if available, fallback to user
                user_mention = f"@{msg.display_name or msg.user}"
                final_response = custom_response.replace("{user}", user_mention)
                # Add more placeholders as needed: {channel}, {platform}, {args[0]} etc.
                final_response = final_response.replace("{channel}", msg.channel or "unknown")
                final_response = final_response.replace("{platform}", msg.platform)
                final_response = final_response.replace("{arg1}", args[0] if args else "")
                # Add more {argN} or {all_args} if useful
                final_response = final_response.replace("{all_args}", " ".join(args))


                send_reply(cmd_event, final_response)
                update_cooldowns(command_name, msg.platform, msg.user) # Apply cooldowns to custom commands too
            except Exception as e:
                 logger.exception(f"Error sending custom command response for '!{command_name}': {e}")
                 try: send_reply(cmd_event, f"Oops! Error running custom command '!{command_name}'.")
                 except: pass
            return # Command handled

        # Handle Unknown Command (only if not from admin)
        if msg.platform != 'dashboard':
             logger.info(f"Unknown command '!{command_name}' from {msg.user}")
             # Consider only replying if it looks like a plausible command attempt, not just random text starting with '!'
             # For now, reply to any unknown command starting with prefix
             send_reply(cmd_event, f"Unknown command: '!{command_name}'. Try {prefix}commands.")


# --- Streamer Input Handling ---
async def handle_streamer_input(event: StreamerInputReceived):
    """Handles input from the streamer via the dashboard."""
    text = event.text.strip()
    if not text: return
    prefix = settings.get('COMMAND_PREFIX', '!')

    logger.info(f"Processing streamer input: '{text[:100]}...'")

    if text.startswith(prefix):
        # Treat as an admin command to be processed like any other command
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


# --- Service Setup ---
async def setup_chat_processor():
    """Loads commands and subscribes message processors to the event bus."""
    logger.info("Setting up Chat Processor...")
    await load_and_cache_commands() # Load custom commands on startup
    event_bus.subscribe(ChatMessageReceived, process_chat_message)
    event_bus.subscribe(StreamerInputReceived, handle_streamer_input) # Handle direct streamer input
    # Subscribe to command API events to reload cache? Or rely on API handlers to call reload.
    # event_bus.subscribe(CustomCommandsUpdated, load_and_cache_commands) # If using an event
    logger.info("Chat Processor setup complete and subscribed to events.")

# --- File: app/services/chat_processor.py --- END ---
""",
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
from app.core.json_store import load_tokens, save_tokens, get_setting # Use get_setting for TWITCH_CHANNELS
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
             # This should ideally be caught before initialization, but handle defensively
             logger.error("CRITICAL: TwitchBot initialized without a valid token.")
             # Raise an error to prevent proceeding without auth
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
            # await clear_tokens("twitch")
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
                     # A simple way is to wait on the task itself, but that can lead to complex exception handling.
                     # A safer way is to check periodically or use a dedicated cancellation event if the bus supports it.
                     # For simplicity here, we'll rely on the main loop's cancellation check.
                     # We just wait on the update_future, potentially indefinitely if no update/cancellation occurs.
                     await update_future

                 except asyncio.CancelledError:
                     logger.info("Wait for settings update cancelled.")
                     raise # Re-raise to propagate cancellation
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
             from app.core.json_store import load_tokens, save_tokens, get_setting
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

             This script automates the entire setup based on our reconciled understanding, leaving only the essential manual configuration of secrets for the user."""
# AUTO-CLOSED UNTERMINATED DOCSTRING
