# Access Control Restructuring Backup

## File Information
- Original Files:
  - `modules/access_control.py`
  - `modules/access.json`
  - `modules/gui/config.json` (access control section)
- Backup Date: 2025-04-26
- Reason: Centralizing access control management
- Action: Moving to new access control system

## Changes Made
- Creating centralized access control structure
- Standardizing permission checking
- Improving security features
- Consolidating access control logic

## Rollback Instructions
To restore these files:
1. Copy the files back to their original locations:
   ```bash
   cp access_control.py modules/
   cp access.json modules/
   cp config.json modules/gui/
   ```

## Notes
- This backup was created as part of access control standardization
- The new structure will be in the `modules/access/` directory
- All access control will be properly organized and validated
- No functional changes to the access control data itself 