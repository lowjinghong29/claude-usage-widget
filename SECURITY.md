# Security policy

## Reporting a problem

Please report security problems **privately**: on GitHub, open the **Security** tab of this repository
and click **Report a vulnerability**. Don't open a public issue for security problems.

**Never send anyone your `.credentials.json`, tokens or screenshots that show them**, including in a report.
Nobody working on this project will ever ask for them.

## Supported versions

Only the latest release gets fixes.

## What the widget can access

See "Security and privacy" in the [README](README.md): it reads your local Claude Code sign-in and sends it
only to `api.anthropic.com`, stores nothing, and runs only Claude Code's own `claude auth` commands.

## Checking a download

Every release lists the installer's SHA-256 hash in `SHA256SUMS.txt`. Compare it with:

```powershell
Get-FileHash .\ClaudeUsageWidget-Setup.exe -Algorithm SHA256
```

The installer is not code-signed. Only download it from this repository's Releases page.
