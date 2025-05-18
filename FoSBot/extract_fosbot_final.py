import os
import re
import json
import yaml
import ast
import html.parser
import logging
import shutil
import difflib
import argparse
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from io import StringIO
import jsbeautifier
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # Fallback for progress bar

# Set up logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('extraction_issues.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HTMLValidator(html.parser.HTMLParser):
    """Simple HTML parser to detect basic syntax errors."""
    def __init__(self):
        super().__init__()
        self.errors = []

    def error(self, message):
        self.errors.append(f"HTML error: {message}")

def validate_python(content: str, file_path: str) -> List[str]:
    """Validate Python syntax using ast.parse."""
    errors = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Python syntax error in {file_path}: {e}")
    return errors

def validate_json(content: str, file_path: str) -> List[str]:
    """Validate JSON syntax."""
    errors = []
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON syntax error in {file_path}: {e}")
    return errors

def validate_yaml(content: str, file_path: str) -> List[str]:
    """Validate YAML syntax."""
    errors = []
    try:
        yaml.safe_load(StringIO(content))
    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error in {file_path}: {e}")
    return errors

def validate_html(content: str, file_path: str) -> List[str]:
    """Validate HTML syntax using HTMLParser."""
    parser = HTMLValidator()
    try:
        parser.feed(content)
        parser.close()
    except Exception as e:
        parser.errors.append(f"HTML parsing error in {file_path}: {e}")
    return parser.errors

def validate_javascript(content: str, file_path: str) -> List[str]:
    """Validate JavaScript syntax using jsbeautifier."""
    errors = []
    try:
        opts = jsbeautifier.default_options()
        jsbeautifier.beautify(content, opts)
    except Exception as e:
        errors.append(f"JavaScript syntax error in {file_path}: {e}")
    return errors

def auto_fix_content(content: str, file_path: str, issues: List[str]) -> Tuple[str, List[str]]:
    """Attempt to automatically fix common issues with user confirmation."""
    fixed_content = content
    fix_issues = []

    # Fix missing logger import in Python files
    if file_path.endswith('.py') and 'logger' in content and 'from app.core.config import logger' not in content:
        if input(f"Add missing logger import to {file_path}? (y/n): ").lower() == 'y':
            fixed_content = 'from app.core.config import logger\n' + content
            fix_issues.append(f"Added missing logger import to {file_path}")

    # Fix smart quotes
    if '’' in content or '“' in content or '”' in content:
        if input(f"Replace smart quotes in {file_path}? (y/n): ").lower() == 'y':
            fixed_content = fixed_content.replace('’', "'").replace('“', '"').replace('”', '"')
            fix_issues.append(f"Replaced smart quotes in {file_path}")

    return fixed_content, fix_issues

def generate_diff(original: str, modified: str, file_path: str) -> str:
    """Generate a diff between original and modified content."""
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"original/{file_path}",
        tofile=f"modified/{file_path}"
    )
    return ''.join(diff)

def clean_content(content: str, file_path: str) -> Tuple[str, List[str]]:
    """Clean content by removing common copy-paste artifacts and report issues."""
    issues = []
    original_content = content

    # Remove trailing whitespace and extra newlines
    content = content.rstrip()
    lines = content.splitlines()
    cleaned_lines = [line.rstrip() for line in lines if line.strip() or not line]
    content = '\n'.join(cleaned_lines)

    if len(lines) != len(cleaned_lines):
        issues.append(f"Removed extra newlines/whitespace in {file_path}")

    # Check for non-ASCII characters
    non_ascii = [c for c in content if ord(c) > 127]
    if non_ascii:
        issues.append(f"Non-ASCII characters found in {file_path}: {non_ascii[:10]}")

    # Fix indentation for Python files
    if file_path.endswith('.py'):
        try:
            indent_level = 0
            fixed_lines = []
            for line in cleaned_lines:
                stripped = line.lstrip()
                if stripped:
                    current_indent = len(line) - len(stripped)
                    expected_indent = indent_level * 4
                    if current_indent != expected_indent:
                        issues.append(f"Fixed indentation in {file_path} at line: {line}")
                        line = ' ' * expected_indent + stripped
                    if stripped.endswith(':'):
                        indent_level += 1
                    elif not stripped.startswith('#') and indent_level > 0:
                        indent_level = max(0, indent_level - 1)
                fixed_lines.append(line)
            content = '\n'.join(fixed_lines)
        except Exception as e:
            issues.append(f"Indentation fix failed in {file_path}: {e}")

    # FoSBot-specific checks
    if file_path.endswith('.py') and 'import' in content:
        if 'from app.core.config import logger' not in content and 'logger' in content:
            issues.append(f"Missing logger import in {file_path}")
        if 'FastAPI' in content and 'from fastapi import FastAPI' not in content:
            issues.append(f"Missing FastAPI import in {file_path}")

    if content != original_content:
        issues.append(f"Content modified during cleaning in {file_path}")

    return content, issues

def validate_file_content(file_path: str, content: str) -> List[str]:
    """Validate content based on file extension."""
    errors = []
    extension = os.path.splitext(file_path)[1].lower()

    if extension == '.py':
        errors.extend(validate_python(content, file_path))
    elif extension == '.json':
        errors.extend(validate_json(content, file_path))
    elif extension == '.yml' or extension == '.yaml':
        errors.extend(validate_yaml(content, file_path))
    elif extension == '.html':
        errors.extend(validate_html(content, file_path))
    elif extension == '.js':
        errors.extend(validate_javascript(content, file_path))

    # Check for placeholder content
    if 'Placeholder' in content and (file_path.endswith('.png') or file_path.endswith('.zip')):
        errors.append(f"Placeholder content detected in {file_path}. Replace with actual file.")

    return errors

def validate_fosbot_specific(file_path: str, content: str) -> List[str]:
    """Validate FoSBot-specific configurations."""
    errors = []
    if file_path == 'FoSBot/.env.example':
        required_keys = [
            'COMMAND_PREFIX', 'WS_HOST', 'WS_PORT', 'LOG_LEVEL', 'DATA_DIR',
            'TWITCH_APP_CLIENT_ID', 'TWITCH_APP_CLIENT_SECRET',
            'YOUTUBE_APP_CLIENT_ID', 'YOUTUBE_APP_CLIENT_SECRET',
            'X_APP_CLIENT_ID', 'X_APP_CLIENT_SECRET', 'APP_SECRET_KEY'
        ]
        for key in required_keys:
            if f"{key}=" not in content:
                errors.append(f"Missing required key '{key}' in {file_path}")

    if file_path == 'FoSBot/requirements.txt':
        required_deps = ['fastapi', 'uvicorn', 'twitchio', 'tweepy', 'google-api-python-client']
        for dep in required_deps:
            if dep not in content.lower():
                errors.append(f"Missing required dependency '{dep}' in {file_path}")

    return errors

def generate_env_file(output_base_path: Path):
    """Generate a minimal .env file from .env.example if missing."""
    env_example = output_base_path / '.env.example'
    env_file = output_base_path / '.env'
    if env_example.exists() and not env_file.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        # Replace sensitive values with prompts
        content = re.sub(r'(TWITCH_APP_CLIENT_ID)=.*', r'\1=ENTER_YOUR_TWITCH_CLIENT_ID', content)
        content = re.sub(r'(TWITCH_APP_CLIENT_SECRET)=.*', r'\1=ENTER_YOUR_TWITCH_SECRET', content)
        content = re.sub(r'(YOUTUBE_APP_CLIENT_ID)=.*', r'\1=ENTER_YOUR_YOUTUBE_CLIENT_ID', content)
        content = re.sub(r'(YOUTUBE_APP_CLIENT_SECRET)=.*', r'\1=ENTER_YOUR_YOUTUBE_SECRET', content)
        content = re.sub(r'(X_APP_CLIENT_ID)=.*', r'\1=ENTER_YOUR_X_CLIENT_ID', content)
        content = re.sub(r'(X_APP_CLIENT_SECRET)=.*', r'\1=ENTER_YOUR_X_SECRET', content)
        content = re.sub(r'(APP_SECRET_KEY)=.*', r'\1=GENERATE_WITH_PYTHON_SECRETS', content)
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Generated minimal {env_file}")

def interactive_issue_resolution(issues: List[Tuple[str, str]]):
    """Prompt user to resolve critical issues interactively."""
    critical_issues = [(file_path, issue) for file_path, issue in issues if 'syntax error' in issue.lower()]
    if not critical_issues:
        return
    logger.info(f"Found {len(critical_issues)} critical issues requiring attention.")
    for file_path, issue in critical_issues:
        response = input(f"Critical issue: {issue}\nOpen {file_path} to fix manually? (y/n/skip): ").lower()
        if response == 'y':
            logger.info(f"Please edit {file_path} to resolve: {issue}")
        elif response == 'skip':
            logger.info(f"Skipped issue in {file_path}")

def parse_and_extract_files(input_file_path: str, output_base_dir: str = "FoSBot", dry_run: bool = False, verbose: bool = False):
    """Extract files with validation, cleaning, and enhancements."""
    if not os.path.isfile(input_file_path):
        logger.error(f"Input file '{input_file_path}' not found.")
        return

    output_base_path = Path(output_base_dir)
    if not dry_run:
        output_base_path.mkdir(parents=True, exist_ok=True)

    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    file_pattern = re.compile(
        r'=== File: (FoSBot/.*?)(?:\s+===.*?)?\n([\s\S]*?)(?=(?:=== File:|$))',
        re.MULTILINE
    )
    matches = file_pattern.findall(content)

    if not matches:
        logger.error("No files found in the input document.")
        return

    total_issues = []
    # Use tqdm.tqdm if available, otherwise iterate normally
    iterable = tqdm(matches, desc="Extracting files", unit="file") if tqdm else matches
    for file_path, file_content in iterable:
        file_path = file_path.strip()
        full_file_path = output_base_path / file_path[len("FoSBot/"):]

        # Clean and validate content
        cleaned_content, cleaning_issues = clean_content(file_content, file_path)
        fixed_content, fix_issues = auto_fix_content(cleaned_content, file_path, cleaning_issues)
        validation_errors = validate_file_content(file_path, fixed_content)
        fosbot_errors = validate_fosbot_specific(file_path, fixed_content)

        # Log issues
        for issue in cleaning_issues + fix_issues:
            logger.warning(issue)
            total_issues.append((file_path, issue))
        for error in validation_errors + fosbot_errors:
            logger.error(error)
            total_issues.append((file_path, error))

        # Generate diff if content changed
        if fixed_content != file_content and verbose:
            diff = generate_diff(file_content, fixed_content, file_path)
            with open('extraction_diff.txt', 'a', encoding='utf-8') as f:
                f.write(f"\nDiff for {file_path}:\n{diff}\n")
            logger.info(f"Diff generated for {file_path} in extraction_diff.txt")

        if dry_run:
            logger.info(f"[Dry Run] Would create: {full_file_path}")
            continue

        # Create parent directory
        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        try:
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"Created file: {full_file_path}")
        except Exception as e:
            logger.error(f"Error writing file '{full_file_path}': {e}")
            total_issues.append((file_path, f"Write error: {e}"))

    # Verify file count against rebuild_genesis.json
    expected_files = 53  # From rebuild_genesis.json
    actual_files = len(matches)
    if actual_files != expected_files:
        logger.warning(f"File count mismatch: expected {expected_files}, extracted {actual_files}")
        total_issues.append(('', f"File count mismatch: expected {expected_files}, extracted {actual_files}"))

    # Generate .env file
    if not dry_run:
        generate_env_file(output_base_path)

    # Interactive issue resolution
    interactive_issue_resolution(total_issues)

    logger.info(f"Extraction complete. Total issues detected: {len(total_issues)}")
    if total_issues:
        logger.info("Review 'extraction_issues.log' and 'extraction_diff.txt' for details.")

def main():
    parser = argparse.ArgumentParser(description="Extract FoSBot files from a consolidated text file.")
    parser.add_argument('--input', default="GrokAIFoSBot.txt", help="Input text file path")
    parser.add_argument('--output', default="FoSBot", help="Output directory")
    parser.add_argument('--dry-run', action='store_true', help="Preview actions without writing files")
    parser.add_argument('--verbose', action='store_true', help="Log detailed debug information")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Backup input file and existing output directory
    if not args.dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.isfile(args.input):
            backup_input = f"{args.input}.{timestamp}.bak"
            shutil.copy(args.input, backup_input)
            logger.info(f"Backed up input file to {backup_input}")
        if os.path.exists(args.output):
            response = input(f"Directory '{args.output}' exists. Overwrite? (y/n): ").lower()
            if response != 'y':
                logger.info("Aborting extraction.")
                return
            backup_dir = f"{args.output}_{timestamp}"
            shutil.copytree(args.output, backup_dir)
            shutil.rmtree(args.output)
            logger.info(f"Backed up existing directory to {backup_dir}")

    logger.info(f"Extracting files from '{args.input}' to '{args.output}'...")
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed. YAML validation skipped. Install with: pip install pyyaml")
    try:
        import jsbeautifier
    except ImportError:
        logger.warning("jsbeautifier not installed. JavaScript validation skipped. Install with: pip install jsbeautifier")
    if not tqdm:
        logger.warning("tqdm not installed. Progress bar disabled. Install with: pip install tqdm")
    parse_and_extract_files(args.input, args.output, args.dry_run, args.verbose)

if __name__ == "__main__":
    main()