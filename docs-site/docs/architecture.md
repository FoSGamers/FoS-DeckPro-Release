## Error Reporting (Privacy-Respecting, Opt-In)

ManaBox Enhancer / FoS-DeckPro includes an optional, anonymous error reporting system to help improve the app:

- **Disabled by default.** Users must explicitly enable it in the config.
- **No personal or sensitive data is ever collected or sent.**
- Reports include only error type, message, stack trace, and app version.
- The reporting endpoint is configurable and can be left blank to fully disable reporting.

### How to Enable

1. Open `FoS_DeckPro/utils/config.py`.
2. Set `ERROR_REPORTING_ENABLED = True`.
3. Set `ERROR_REPORTING_ENDPOINT` to your error collection endpoint (or leave blank to disable).

**Privacy Statement:**
> This system is strictly opt-in and never collects or transmits any personal, user, or machine-identifiable data. All reports are anonymous and used solely to improve software quality. 