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
   [DEBUG] Forbidden pattern found in filename: private_file.py
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
3. **pre-commit-personal-dev**: Custom hook for personal development

### Common Issues and Debugging

#### 1. "Forbidden private content" or "Reference to private directory found" Errors
- **Error Message:**
  ```
  [ERROR] Reference to private directory found in public file: <file>
  ```
- **Cause:**
  - The file contains a reference to a private directory
  - The file is not in an exempt location
- **Solution:**
  - Move the reference to a private directory
  - Add the file to the exemption list if it needs to reference private content

#### 2. "Forbidden private file pattern" Errors
- **Error Message:**
  ```
  [ERROR] Forbidden private file pattern detected in: <file>
  ```
- **Cause:**
  - The filename contains a forbidden pattern (PRIVATE, PERSONAL, SECRET)
  - The file is not in a private directory
- **Solution:**
  - Rename the file to remove the forbidden pattern
  - Move the file to a private directory if it contains private content

#### 3. "Attempt to commit file(s) in private directory" Errors
- **Error Message:**
  ```
  [ERROR] Attempt to commit file(s) in private directory (should be in .gitignore)
  ```
- **Cause:**
  - Trying to commit files from a private directory
  - The private directory is not properly ignored
- **Solution:**
  - Ensure the private directory is in `.gitignore`
  - Move the files to a public location if they should be committed

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
   # Look for private directory references
   grep -E 'private_directory' "$file"
   
   # Look for forbidden patterns
   grep -E 'PRIVATE|PERSONAL|SECRET' "$file"
   ```

3. **Check Git Status**
   ```bash
   # Check if private directory is being tracked
   git ls-files | grep 'private_directory'
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
   - Keep all private files in a private directory
   - Use clear, descriptive names for public files
   - Avoid forbidden patterns in filenames

2. **Documentation:**
   - Document any exemptions in `Standards/DEBUGGING.md`
   - Keep the changelog updated with hook changes
   - Use debug logs to diagnose issues

3. **Testing:**
   - Test hooks with debug logs enabled
   - Verify exemptions work as expected
   - Check that private content is properly protected

### Troubleshooting Checklist

1. **For "Reference to private directory" Errors:**
   - [ ] Is the file in an exempt location?
   - [ ] Does the file need to reference private content?
   - [ ] Should the file be moved to a private directory?

2. **For "Forbidden pattern" Errors:**
   - [ ] Does the filename contain a forbidden pattern?
   - [ ] Should the file be renamed?
   - [ ] Should the file be moved to a private directory?

3. **For "Attempt to commit private files" Errors:**
   - [ ] Is the private directory in `.gitignore`?
   - [ ] Are you trying to commit from the wrong branch?
   - [ ] Should the files be moved to a public location?

4. **For General Issues:**
   - [ ] Are the hooks executable?
   - [ ] Are the debug logs showing the expected output?
   - [ ] Have all exemptions been properly added?
   - [ ] Is the changelog updated with recent changes?

Remember: The hooks are there for security. Always consider the security implications before bypassing or modifying them. 