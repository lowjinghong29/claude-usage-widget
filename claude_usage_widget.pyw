"""Small floating Claude button that opens a compact panel with plan usage.

Reads the Claude Code OAuth token from ~/.claude/.credentials.json (never stored or
printed) and asks Anthropic's own usage endpoint every 5 minutes.
Button: click = show/hide panel, drag = move, right-click = quit.
         Ring and number on the button = Weekly (all models) usage % (green < 70%, amber < 90%, red).
Panel: "–" = minimize to the button, double-click = refresh now.
Self-check: python claude_usage_widget.pyw --test
"""
import json, shutil, subprocess, sys, threading, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.1"
CREDS = Path.home() / ".claude" / ".credentials.json"
CLAUDE_JSON = Path.home() / ".claude.json"  # Claude Code's config; oauthAccount = who is logged in
CENTER_PNG = Path.home() / ".claude-usage-widget" / "center.png"  # optional: your own picture inside the ring
URL = "https://api.anthropic.com/api/oauth/usage"
REFRESH_MS = 5 * 60 * 1000
MIN_GAP = 30  # seconds between non-forced fetches; the usage endpoint rate-limits (HTTP 429)
NAMES = {"five_hour": "5-hour", "seven_day": "Weekly", "weekly": "Weekly", "session": "5-hour"}

BG, TEXT, MUTED, TRACK, CORAL = "#202020", "#f2f2f2", "#9a9a9a", "#3a3a3a", "#d97757"
KEY = "#010101"  # window color Windows treats as transparent
BAR_W, BTN = 190, 40


def ring_icon(n, pct, ring_color, label, transparent=False, center=None):
    """n x n usage ring with a label (or the `center` picture) in the middle. Ring drawn 4x, downsampled."""
    from PIL import Image, ImageDraw, ImageFont
    k = 4
    big = Image.new("RGBA" if transparent else "RGB", (n * k, n * k), (0, 0, 0, 0) if transparent else KEY)
    d = ImageDraw.Draw(big)
    inset, w = round(0.03 * n * k), round(0.08 * n * k)
    box = (inset, inset, n * k - inset, n * k - inset)
    d.ellipse(box, fill=BG, outline=TRACK, width=w)
    if pct >= 100:  # Pillow draws a 360° arc as nothing
        d.ellipse(box, outline=ring_color, width=w)
    elif pct > 0:
        d.arc(box, 270, 270 + 3.6 * pct, fill=ring_color, width=w)  # clockwise from 12 o'clock
    img = big.resize((n, n), Image.BOX)  # BOX keeps the see-through KEY area exact
    if center is not None:
        c = center.convert("RGBA")
        if c.width <= 64:  # pixel art: whole-pixel scaling keeps it sharp
            f = max(1, round(n * 0.65 / c.width))
            c = c.resize((c.width * f, c.height * f), Image.NEAREST)
        else:
            c.thumbnail((round(n * 0.6), round(n * 0.6)), Image.LANCZOS)
        img.paste(c, ((n - c.width) // 2, (n - c.height) // 2), c)
        return img
    size = round(n * (0.34 if len(label) <= 2 else 0.27))
    try:
        font = ImageFont.truetype("seguisb.ttf", size)  # Segoe UI Semibold, ships with Windows
    except OSError:
        font = ImageFont.load_default(size)
    ImageDraw.Draw(img).text((n / 2, n / 2), label, fill=TEXT, font=font, anchor="mm")
    return img


def rows(data):
    """[(label, percent, resets_in)] for every usage window in the response."""
    if data.get("limits"):  # same list the app's usage card shows, incl. per-model limits
        out = []
        for l in data["limits"]:
            model = ((l.get("scope") or {}).get("model") or {}).get("display_name")
            label = NAMES.get(l.get("group"), str(l.get("group", "")).replace("_", " ").title())
            out.append((f"{label} · {model}" if model else label, round(l["percent"]), resets_in(l.get("resets_at"))))
        return out
    out = []
    for key, v in data.items():
        if isinstance(v, dict) and isinstance(v.get("utilization"), (int, float)):
            label = NAMES.get(key) or key.replace("seven_day_", "Weekly ").replace("_", " ").title()
            out.append((label, round(v["utilization"]), resets_in(v.get("resets_at"))))
    return out


def resets_in(iso):
    if not iso:
        return ""
    secs = (datetime.fromisoformat(iso.replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds()
    if secs <= 0:
        return "now"
    d, h, m = int(secs // 86400), int(secs % 86400 // 3600), int(secs % 3600 // 60)
    return f"{d}d {h}h" if d else f"{h}h {m}m"


def fetch():
    token = json.loads(CREDS.read_text())["claudeAiOauth"]["accessToken"]
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "User-Agent": "claude-usage-widget",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return rows(json.load(r))


def account():
    """(account id, "name · plan") of the current Claude Code login."""
    try:
        a = json.loads(CLAUDE_JSON.read_text(encoding="utf-8")).get("oauthAccount") or {}
    except Exception:
        return None, ""
    name = a.get("displayName") or a.get("organizationName") or ""
    return a.get("accountUuid"), " · ".join(x for x in (name, a.get("planDisplayName")) if x)


def claude_exe():
    """Claude Code's command, from PATH or its usual install folders (npm, native installer)."""
    found = shutil.which("claude")
    for p in (Path.home() / ".local" / "bin" / "claude.exe", Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"):
        if not found and p.exists():
            found = str(p)
    return found


def renew_login():
    """Best effort: let Claude Code itself renew an expired sign-in, in a hidden window."""
    exe = claude_exe()
    if exe:
        try:
            subprocess.run([exe, "auth", "status"], capture_output=True, timeout=30,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass


def retry_after(e):
    """Seconds the server asked us to wait on a 429, or None."""
    try:
        return max(1, int(e.headers.get("Retry-After")))
    except (TypeError, ValueError):
        return None


def mtimes():
    return tuple(f.stat().st_mtime if f.exists() else 0 for f in (CREDS, CLAUDE_JSON))


def color(p):
    return "#5fb978" if p < 70 else "#e0a33a" if p < 90 else "#e5534b"


def round_corners(win, small=False):
    """Windows 11 native rounded corners + subtle border; older Windows keeps square corners."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        for attr, val in ((33, 3 if small else 2), (34, 0x003A3A3A)):  # DWMWA_WINDOW_CORNER_PREFERENCE, DWMWA_BORDER_COLOR (BGR)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(ctypes.c_int(val)), 4)
    except Exception:
        pass


def floating(win, bg):
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=bg)


def main():
    import tkinter as tk

    from PIL import ImageTk

    try:
        from PIL import Image
        center = Image.open(CENTER_PNG) if CENTER_PNG.exists() else None
    except Exception:  # unreadable picture: just show the number
        center = None

    def button_image(pct, ring_color, label):
        return ImageTk.PhotoImage(ring_icon(B, pct, ring_color, label, center=center))

    # --- the Claude button: round disc, rest of the window see-through ---
    try:
        import ctypes
        # one copy only (Startup and Start menu can both launch it)
        ctypes.windll.kernel32.CreateMutexW(None, False, "ClaudeUsageWidget")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            return
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # real screen resolution, not stretched/blurry
    except Exception:
        pass
    root = tk.Tk()
    scale = root.winfo_fpixels("1i") / 96
    px = lambda v: round(v * scale)
    B, W = px(BTN), px(BAR_W)
    floating(root, KEY)
    root.attributes("-transparentcolor", KEY)
    root.geometry(f"{B}x{B}+{root.winfo_screenwidth() - B - px(20)}+{px(140)}")
    btn = tk.Canvas(root, width=B, height=B, bg=KEY, highlightthickness=0, cursor="hand2")
    btn.pack()
    icon = {"img": button_image(0, MUTED, "–")}
    icon_item = btn.create_image(0, 0, image=icon["img"], anchor="nw")

    # --- the panel, hidden until the button is clicked ---
    panel = tk.Toplevel(root)
    floating(panel, BG)
    panel.attributes("-alpha", 0.88)  # slightly see-through; fully clear would make text unreadable
    panel.withdraw()
    box = tk.Frame(panel, bg=BG, padx=px(12), pady=px(10))
    box.pack()
    # result = last good rows for the account in "acct"
    state = {"result": None, "err": None, "open": False, "fetched": 0.0, "acct": account(), "mt": mtimes()}

    def text(parent, s, size=8, fg=TEXT, font="Segoe UI", **kw):
        return tk.Label(parent, text=s, fg=fg, bg=BG, font=(font, size), **kw)

    def render():
        result, err = state["result"], state["err"]
        for w in box.winfo_children():
            w.destroy()
        head = tk.Frame(box, bg=BG)
        head.pack(fill="x")
        text(head, "Claude usage", 10, TEXT, "Segoe UI Semibold").pack(side="left")
        mini = text(head, "–", 11, MUTED, cursor="hand2")  # minimize back to the button
        mini.pack(side="right")
        mini.bind("<Button-1>", lambda e: toggle())
        if state["acct"][1]:
            text(box, state["acct"][1], 8, MUTED).pack(anchor="w")
        if result is None:
            text(box, err or "Loading...", 9, "#e5534b" if err else MUTED, wraplength=W, justify="left").pack(anchor="w", pady=(px(4), 0))
            if state.get("login"):
                b = tk.Label(box, text="Sign in to Claude Code", bg=CORAL, fg="white", font=("Segoe UI Semibold", 9),
                             padx=px(10), pady=px(4), cursor="hand2")
                b.pack(anchor="w", pady=(px(8), 0))
                b.bind("<Button-1>", lambda e: sign_in())
        else:
            if err:  # keep showing the last good numbers
                text(box, f"Not updated: {err}", 8, "#e0a33a", wraplength=W, justify="left").pack(anchor="w", pady=(px(2), 0))
            h = px(6)
            for label, pct, reset in result:
                row = tk.Frame(box, bg=BG)
                row.pack(fill="x", pady=(px(8), 0))
                text(row, label, 9).pack(side="left")
                text(row, f"{pct}%", 11, color(pct), "Segoe UI Semibold").pack(side="right")
                bar = tk.Canvas(box, width=W, height=h, bg=BG, highlightthickness=0)
                bar.create_line(h / 2, h / 2, W - h / 2, h / 2, width=h, fill=TRACK, capstyle="round")
                if pct > 0:
                    bar.create_line(h / 2, h / 2, h / 2 + (W - h) * min(pct, 100) / 100, h / 2, width=h, fill=color(pct), capstyle="round")
                bar.pack(anchor="w", pady=(px(3), px(2)))
                if reset:
                    text(box, f"Resets in {reset}", 8, MUTED).pack(anchor="w")
        for w in [box, *box.winfo_children()]:
            w.bind("<Double-Button-1>", lambda e: refresh(force=True))
        # ring = the all-models "Weekly" limit; falls back to the highest one if absent
        top = next((p for l, p, _ in result if l == "Weekly"), max((p for _, p, _ in result), default=0)) if result else 0
        # keep a reference or Tk drops the image
        icon["img"] = button_image(top, color(top), str(top)) if result else button_image(0, MUTED, "–")
        btn.itemconfig(icon_item, image=icon["img"])
        if state["open"]:
            place_panel()

    def place_panel():
        panel.update_idletasks()
        w, h = panel.winfo_reqwidth(), panel.winfo_reqheight()
        gap = px(6)
        x = root.winfo_x() - w - gap if root.winfo_x() > w + gap else root.winfo_x() + B + gap
        y = min(root.winfo_y(), root.winfo_screenheight() - h - px(60))
        panel.geometry(f"+{x}+{y}")

    def toggle():
        state["open"] = not state["open"]
        if state["open"]:
            place_panel()
            panel.deiconify()
            panel.update_idletasks()
            round_corners(panel)
            refresh()
        else:
            panel.withdraw()

    def refresh(force=False):
        """Fetch usage. One call at a time, at most every MIN_GAP, and never during a 429 cool-down."""
        now = time.time()
        if state.get("fetching") or now < state.get("cooldown", 0):
            return
        if not force and now - state["fetched"] < MIN_GAP:  # dedupe bursts: loop + panel open + token rewrites
            return
        state["fetched"], state["fetching"] = now, True
        def work():
            try:
                who, login = state["acct"][0], False
                try:
                    try:
                        result = fetch()
                    except urllib.error.HTTPError as e:
                        if e.code != 401:
                            raise
                        renew_login()  # expired token: let Claude Code renew it, then try once more
                        result = fetch()
                    err = None
                    state["backoff"], state["cooldown"] = 0, 0
                except FileNotFoundError:
                    result, err, login = None, "Not signed in to Claude Code on this PC.", True
                except urllib.error.HTTPError as e:
                    login = e.code == 401
                    result = None
                    if e.code == 429:  # obey the server; else double the wait, 1 min to 30 min
                        wait = retry_after(e) or min(max(state.get("backoff", 0) * 2, 60), 1800)
                        state["backoff"], state["cooldown"] = wait, time.time() + wait
                        err = f"Rate limited by Anthropic, retrying in {max(1, round(wait / 60))} min"
                    else:
                        err = {401: "Claude Code sign-in has expired."}.get(e.code, f"HTTP {e.code}")
                except (ValueError, KeyError, TypeError):  # fixed messages only: nothing from the file reaches the screen
                    result, err = None, "Couldn't read the Claude Code sign-in file. Sign in again."
                except OSError:  # URLError, timeouts, no network
                    result, err = None, "Can't reach Anthropic. Check your connection."
                except Exception as e:
                    result, err = None, f"Unexpected error ({type(e).__name__})."
                if state["acct"][0] != who:  # login switched mid-fetch: drop this answer
                    return
                if result is not None:
                    state["result"] = result
                if login:  # signed out: don't keep showing the old numbers
                    state["result"] = None
                state["err"], state["login"] = err, login
                state["dirty"] = True  # never touch Tk from this thread; poll() redraws
            finally:
                state["fetching"] = False
        threading.Thread(target=work, daemon=True).start()

    def sign_in():
        """Open Claude Code's own sign-in (browser); watch() picks up the new login when it lands."""
        exe = claude_exe()
        if not exe:
            state["err"] = "Claude Code is not installed on this PC. Install it, then click Sign in again."
            render()
            return
        subprocess.Popen(f'cmd /c ""{exe}" auth login || pause"', creationflags=subprocess.CREATE_NEW_CONSOLE)

    def poll():
        if state.pop("dirty", False):
            render()
        root.after(300, poll)

    def watch():
        """Follow Claude login switches: local file check every 3s, network only on a change."""
        m = mtimes()
        if m != state["mt"]:
            creds_changed = m[0] != state["mt"][0]
            state["mt"] = m
            acct = account()
            if acct[0] != state["acct"][0]:  # another account: never show the old one's numbers
                state.update(acct=acct, result=None, err=None, backoff=0, cooldown=0)  # old cool-down was the old account's
                render()
                refresh(force=True)
            else:
                state["acct"] = acct
                if creds_changed:  # same account, new token (re-login)
                    refresh()
        root.after(3000, watch)

    def loop():
        refresh()
        root.after(REFRESH_MS, loop)

    # click vs drag on the button
    drag = {}
    def press(e):
        drag.update(x=e.x_root - root.winfo_x(), y=e.y_root - root.winfo_y(), sx=e.x_root, sy=e.y_root)
    def move(e):
        root.geometry(f"+{e.x_root - drag['x']}+{e.y_root - drag['y']}")
        if state["open"]:
            place_panel()
    def release(e):
        if abs(e.x_root - drag["sx"]) < 4 and abs(e.y_root - drag["sy"]) < 4:
            toggle()
    btn.bind("<ButtonPress-1>", press)
    btn.bind("<B1-Motion>", move)
    btn.bind("<ButtonRelease-1>", release)
    btn.bind("<Button-3>", lambda e: root.destroy())

    render()
    poll()
    watch()
    loop()
    root.mainloop()


if __name__ == "__main__":
    if "--test" in sys.argv:
        sample = {"five_hour": {"utilization": 12.4, "resets_at": "2099-01-01T00:00:00Z"},
                  "seven_day": {"utilization": 85, "resets_at": None},
                  "seven_day_opus": None, "extra_usage": {"is_enabled": False}}
        r = rows(sample)
        assert r[0][:2] == ("5-hour", 12) and r[1] == ("Weekly", 85, ""), r
        assert len(r) == 2 and color(50) != color(95)
        r = rows({"limits": [{"group": "weekly", "percent": 85, "scope": None},
                             {"group": "weekly", "percent": 100, "scope": {"model": {"display_name": "Fable"}}}]})
        assert r == [("Weekly", 85, ""), ("Weekly · Fable", 100, "")], r
        print("ok")
    else:
        main()
