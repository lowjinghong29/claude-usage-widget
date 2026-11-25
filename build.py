"""Build dist/ClaudeUsageWidget-Setup.exe: icon -> PyInstaller app -> Inno Setup installer.

Needs: pip install --user pyinstaller pillow; Inno Setup 6 (winget install JRSoftware.InnoSetup).
Run: python build.py
"""
import os, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from importlib.machinery import SourceFileLoader
w = SourceFileLoader("w", str(HERE / "claude_usage_widget.pyw")).load_module()

# 1. app icon: the button (Weekly ring + mascot) at 256px, saved with smaller sizes
n = 256
img = Image.new("RGBA", (n * 4, n * 4), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
inset, width = 40, 96
d.ellipse((inset, inset, n * 4 - inset, n * 4 - inset), fill=w.BG, outline="#e0a33a", width=width)
img = img.resize((n, n), Image.LANCZOS)
d = ImageDraw.Draw(img)
ps, py = 9, 18
ox, oy = (n - len(w.CLAWD[0]) * ps) // 2, (n - len(w.CLAWD) * py) // 2
for y, line in enumerate(w.CLAWD):
    for x, ch in enumerate(line):
        if ch == "#":
            d.rectangle((ox + x * ps, oy + y * py, ox + (x + 1) * ps - 1, oy + (y + 1) * py - 1), fill=w.CORAL)
img.save(HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

# 2. standalone app (no Python needed on the other PC); onedir starts fast and trips antivirus less than onefile
shutil.copy(HERE / "claude_usage_widget.pyw", HERE / "ClaudeUsageWidget.py")
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
                "--name", "ClaudeUsageWidget", "--icon", str(HERE / "icon.ico"),
                "--distpath", str(HERE / "build" / "app"), "--workpath", str(HERE / "build" / "work"),
                "--specpath", str(HERE / "build"), str(HERE / "ClaudeUsageWidget.py")], check=True)
os.remove(HERE / "ClaudeUsageWidget.py")

# 3. installer
iscc = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Inno Setup 6" / "ISCC.exe"
if not iscc.exists():
    iscc = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
subprocess.run([str(iscc), str(HERE / "setup.iss")], check=True)
print("Built", HERE / "dist" / "ClaudeUsageWidget-Setup.exe")
