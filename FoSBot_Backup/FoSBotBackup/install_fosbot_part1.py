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

Welcome, brave streamer, to **FoSBot**—the ultimate companion for your Magic: The Gathering and Dungeons & Dragons live streams! This bot unites Whatnot, YouTube, Twitch, and X chats into one magical dashboard, letting you engage your party with commands like `!checkin`, `!ping`, and `!roll`. Roll for initiative and let's get started!

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