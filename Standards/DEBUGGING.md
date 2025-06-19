# Debugging Guide for Git Hooks and Security Checks

## Overview
This guide provides comprehensive information for debugging issues with git hooks and security checks in the ManaBox_Enhancer project.

## Git Hooks Debug Logging

### Enabling Debug Logs
The git hooks now include detailed debug logging that can help diagnose issues. Debug logs are written to stderr and will show:
- Which files are being checked
- What patterns are being searched for
- Which files are exempt from checks
- The results of each check
- Any errors that occur

To see the debug logs, you can run git commands with the `GIT_TRACE=1` environment variable:
```bash
GIT_TRACE=1 git commit -m "your message"
GIT_TRACE=1 git push
```

### Understanding Debug Output
The debug logs will show:
1. Hook initialization
2. Files being processed
3. Exemptions being applied
4. Pattern matching results
5. Content checking results
6. Final status

Example debug output:
```
[DEBUG] Starting pre-commit hook...
[DEBUG] Found staged files: file1.py file2.md
[DEBUG] Checking file: file1.py
[DEBUG] File is text, checking content: file1.py
[DEBUG] File passed all checks: file1.py
[DEBUG] Pre-commit hook completed successfully
```

### Common Debug Patterns
1. **Missing Exemptions**
   ```
   [DEBUG] File is exempt from checks: .github/workflows/example.yml
   ```
   If you see this for a file that should be exempt, check the exemption list in the hooks.

2. **Pattern Matches**
   ```
   [DEBUG] Forbidden pattern found in filename: [REDACTED]_file.py
   ```
   This indicates a file name contains a forbidden pattern.

3. **Content Checks**
   ```
   [DEBUG] File is text, checking content: documentation.md
   [DEBUG] Forbidden pattern found in content: documentation.md
   ```
   This shows when forbidden content is found in a file.

## Git Hooks and Security Checks

### Overview
The repository uses git hooks to enforce security and hygiene rules. These hooks are located in `.git/hooks/` and run automatically during git operations.

### Key Hooks
1. **pre-commit**: Runs before each commit
2. **pre-push**: Runs before pushing to remote
3. **pre-commit-[REDACTED]**: Custom hook for [REDACTED] development

### Common Issues and Debugging

#### 1. "Forbidden [REDACTED] content" or "Reference to [REDACTED] directory found" Errors
- **Error Message:**
  ```
  [ERROR] Reference to [REDACTED] directory found in public file: <file>
  ```
- **Cause:**
  - The file contains a reference to a [REDACTED] directory
  - The file is not in an exempt location
- **Solution:**
  - Move the reference to a [REDACTED] directory
  - Add the file to the exemption list if it needs to reference [REDACTED] content

#### 2. "Forbidden [REDACTED] file pattern" Errors
- **Error Message:**
  ```
  [ERROR] Forbidden [REDACTED] file pattern detected in: <file>
  ```
- **Cause:**
  - The filename contains a forbidden pattern ([REDACTED], [REDACTED], [REDACTED])
  - The file is not in a [REDACTED] directory
- **Solution:**
  - Move the file to a [REDACTED] directory if it contains [REDACTED] content

#### 3. "Attempt to commit file(s) in [REDACTED] directory" Errors
- **Error Message:**
  ```
  [ERROR] Attempt to commit file(s) in [REDACTED] directory (should be in .gitignore)
  ```
- **Cause:**
  - Trying to commit files from a [REDACTED] directory
  - The [REDACTED] directory is not properly ignored
- **Solution:**
  - Ensure the [REDACTED] directory is in `.gitignore`

### Debugging Process

1. **Check File Location**
   ```bash
   # Check if file is in an exempt location
   if [[ "$file" == .github/workflows/* ]] || [[ "$file" == "Standards/CHANGELOG.md" ]] || [[ "$file" == "Standards/DEBUGGING.md" ]]; then
       echo "File is exempt from checks"
   fi
   ```

2. **Check File Content**
   ```bash
   # Look for [REDACTED] directory references
   grep -E '[REDACTED]_directory' "$file"
   
   # Look for forbidden patterns
   grep -E '[REDACTED]|[REDACTED]|[REDACTED]' "$file"
   ```

3. **Check Git Status**
   ```bash
   # Check if [REDACTED] directory is being tracked
   git ls-files | grep '[REDACTED]_directory'
   ```

### Exemptions and Safelisting

1. **Current Exemptions:**
   - `.github/workflows/` files
   - `Standards/CHANGELOG.md`
   - `Standards/DEBUGGING.md`

2. **Adding New Exemptions:**
   - Update both pre-commit and pre-push hooks
   - Add the exemption to the debug documentation
   - Test the exemption with the debug logs enabled

### Best Practices

1. **File Organization:**
   - Keep all [REDACTED] files in a [REDACTED] directory
   - Use clear, descriptive names for public files
   - Avoid forbidden patterns in filenames

2. **Documentation:**
   - Document any exemptions in `Standards/DEBUGGING.md`
   - Keep the changelog updated with hook changes
   - Use debug logs to diagnose issues

3. **Testing:**
   - Test hooks with debug logs enabled
   - Verify exemptions work as expected
   - Check that [REDACTED] content is properly protected

### Troubleshooting Checklist

1. **For "Reference to [REDACTED] directory" Errors:**
   - [ ] Is the file in an exempt location?
   - [ ] Does the file need to reference [REDACTED] content?
   - [ ] Should the file be moved to a [REDACTED] directory?

2. **For "Forbidden pattern" Errors:**
   - [ ] Does the filename contain a forbidden pattern?
   - [ ] Should the file be renamed?
   - [ ] Should the file be moved to a [REDACTED] directory?

3. **For "Attempt to commit [REDACTED] files" Errors:**
   - [ ] Is the [REDACTED] directory in `.gitignore`?

Remember: The hooks are there for security. Always consider the security implications before bypassing or modifying them. 