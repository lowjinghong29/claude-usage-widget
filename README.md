# Claude Usage Widget (unofficial)

A small floating button for Windows that shows how much of your Claude plan you have used.
The ring around the button is your weekly usage; click it to see every limit and when it resets.

**Unofficial. Not made or endorsed by Anthropic.**

## Install

1. Download `ClaudeUsageWidget-Setup.exe` from [Releases](../../releases).
2. Optional: check the file matches the published hash.
   ```powershell
   Get-FileHash .\ClaudeUsageWidget-Setup.exe -Algorithm SHA256
   ```
   Compare it with `SHA256SUMS.txt` in the same release.
3. Run it. The installer is not code-signed, so Windows may show "Windows protected your PC":
   click **More info → Run anyway**. It installs for your user only and needs no admin rights.

Uninstall: Settings → Apps → Installed apps → Claude Usage Widget (unofficial).

## Requirements

- Windows 10 or 11 (x64).
- Claude Code signed in with a Claude subscription, either the `claude` command line or the
  **Code** tab of the Claude desktop app. The widget uses that sign-in. If you are not signed in,
  the panel shows a **Sign in to Claude Code** button that starts Claude Code's own browser sign-in.

## Use

- Click the button: open or close the panel.
- Drag the button: move it. Right-click the button: quit.
- `–` in the panel: minimize back to the button. Double-click the panel: refresh now.
- Ring colour: green below 70%, amber below 90%, red from 90%.

## Security and privacy

- **What it reads:** your Claude Code sign-in (`%USERPROFILE%\.claude\.credentials.json`) and the
  account name and plan from `%USERPROFILE%\.claude.json`. Nothing else.
- **Where it sends it:** only to `https://api.anthropic.com/api/oauth/usage`, over HTTPS, to ask for
  your usage. No other server, no analytics, no telemetry.
- **What it stores:** nothing. The sign-in stays in memory and is never written, logged or shown.
  Error messages in the panel are fixed texts, never file contents.
- **What it runs:** only Claude Code's own `claude auth status` (to renew an expired sign-in) and
  `claude auth login` (when you click Sign in).
- It calls the server at most every 30 seconds, every 5 minutes on its own, and backs off when
  Anthropic asks it to (HTTP 429).
- The usage address is not a documented Anthropic API. It may change or stop working at any time.

## Build from source

Needs Python 3.14 and [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```powershell
python -m pip install --user -r requirements-build.txt
python build.py
```

Output: `dist\ClaudeUsageWidget-Setup.exe`. Self-check: `python claude_usage_widget.pyw --test`.

## License

MIT. See [LICENSE](LICENSE).
