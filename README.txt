Claude Usage Widget (unofficial)
================================

A small floating button that shows how much of your Claude plan you have used.
Unofficial tool. Not made or endorsed by Anthropic.

Before you install
------------------
- Windows 10 or 11.
- Claude Code signed in: either the `claude` command line, or the Code tab of
  the Claude desktop app (same sign-in). If you are not signed in, open the
  panel and click "Sign in to Claude Code": your browser opens, approve it, and
  the widget updates by itself. An API key login has no plan limits to show.
- Windows may warn that this installer is unrecognised, because it is not
  code-signed. To continue: More info > Run anyway.

How to use
----------
- The ring around the button shows your Weekly usage:
  green below 70%, amber below 90%, red from 90%.
- Click the button to open or close the panel with every limit and its reset time.
- "-" in the panel minimizes it back to the button.
- Drag the button to move it. Right-click the button to quit.
- Double-click the panel to refresh now. It refreshes by itself every 5 minutes
  and right away when you switch Claude Code accounts.

Privacy
-------
The widget reads your Claude Code sign-in from your own computer
(%USERPROFILE%\.claude\.credentials.json) and sends it only to Anthropic
(api.anthropic.com) to ask for your usage. It does not save or send it anywhere else.

The usage address it calls is not a documented Anthropic API, so it may stop
working if Anthropic changes it.

Uninstall
---------
Windows Settings > Apps > Installed apps > Claude Usage Widget (unofficial) > Uninstall.
