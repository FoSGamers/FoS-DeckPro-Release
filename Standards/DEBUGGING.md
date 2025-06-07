# Debugging Guide

## Git Hooks and Security Checks

### Overview
The repository uses git hooks to enforce security and hygiene rules. These hooks are located in `.git/hooks/` and run automatically during git operations.

### Key Hooks
1. **pre-commit**: Runs before each commit
2. **pre-push**: Runs before pushing to remote
3. **pre-commit-personal-dev**: Custom hook for personal development

### Common Issues and Debugging

#### 1. "Forbidden private content" or "Reference to user_private/ found" Errors

**Symptoms:**
- Error during commit or push: `[ERROR] Forbidden private content detected in: <file>`
- Error during commit or push: `[ERROR] Reference to user_private/ found in public file: <file>`

**Cause:**
- The pre-commit and pre-push hooks check for references to private content in public files
- These hooks scan all files (except those in `user_private/`) for:
  - References to `user_private/`
  - References to `PERSONAL_DEV_MASTER_ARCHIVE.md`
  - Forbidden patterns (`PRIVATE`, `PERSONAL`, `SECRET`)

**Exemptions:**
The following files are exempt from these checks:
- Files in `.github/workflows/`
- `Standards/CHANGELOG.md`

**Debugging Steps:**
1. Check if the file is in an exempt location:
   ```bash
   # Is it in .github/workflows/?
   [[ "$file" == .github/workflows/* ]]
   
   # Is it Standards/CHANGELOG.md?
   [[ "$file" == "Standards/CHANGELOG.md" ]]
   ```

2. If not exempt, check the file content:
   ```bash
   # Look for user_private/ references
   grep -E 'user_private/' "$file"
   
   # Look for other forbidden patterns
   grep -E 'PRIVATE|PERSONAL|SECRET' "$file"
   ```

3. If the file should be exempt, update the hooks:
   - Edit `.git/hooks/pre-commit` and `.git/hooks/pre-push`
   - Add the file to the exemption list:
     ```bash
     if [[ "$file" == .github/workflows/* ]] || [[ "$file" == "Standards/CHANGELOG.md" ]] || [[ "$file" == "your/file/path" ]]; then
       continue
     fi
     ```

#### 2. Temporary Bypass (if needed)
If you need to temporarily bypass the hooks for debugging:
```bash
# Disable hooks
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
mv .git/hooks/pre-push .git/hooks/pre-push.disabled

# Do your git operations
git add .
git commit -m "your message"
git push

# Re-enable hooks
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
mv .git/hooks/pre-push.disabled .git/hooks/pre-push
```

### Hook Configuration
The hooks are configured to:
1. Allow `user_private/` references in:
   - `.github/workflows/` files
   - `Standards/CHANGELOG.md`
2. Block `user_private/` references in all other files
3. Block any files in `user_private/` from being committed/pushed
4. Require `CHANGELOG.md` updates for code/config changes

### Best Practices
1. **Adding New Exemptions:**
   - Update both `pre-commit` and `pre-push` hooks
   - Document the exemption in this guide
   - Consider if the exemption is really needed

2. **Modifying Hook Behavior:**
   - Test changes in a separate branch
   - Update documentation
   - Consider impact on security

3. **Debugging Hook Issues:**
   - Use `git commit -v` to see detailed hook output
   - Check hook exit codes
   - Review hook logs in `.git/hooks/`

### Common Patterns
1. **Workflow Files:**
   - May need to reference `user_private/` for configuration
   - Should be exempt from checks

2. **Documentation:**
   - May need to reference private paths for examples
   - Should be carefully reviewed

3. **Configuration Files:**
   - Should not contain private references
   - May need special handling

### Troubleshooting Checklist
- [ ] Is the file in an exempt location?
- [ ] Does the file need to reference private content?
- [ ] Should the file be added to exemptions?
- [ ] Are both hooks updated?
- [ ] Is documentation updated?
- [ ] Have you tested the changes?

Remember: The hooks are there for security. Always consider the security implications before bypassing or modifying them. 