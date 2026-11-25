"""Build dist/ClaudeUsageWidget-Setup.exe: icon -> PyInstaller app -> Inno Setup installer.

Needs: pip install --user pyinstaller pillow; Inno Setup 6 (winget install JRSoftware.InnoSetup).
Run: python build.py
"""
import os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
from importlib.machinery import SourceFileLoader
w = SourceFileLoader("w", str(HERE / "claude_usage_widget.pyw")).load_module()

# 1. app icon: the same ring as the button, with "%" in the middle
w.ring_icon(256, 70, w.color(70), "%", transparent=True).save(
    HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

# 2. standalone app (no Python needed on the other PC); onedir starts fast and trips antivirus less than onefile
v = tuple(int(x) for x in w.VERSION.split(".")) + (0,)
name = "Claude Usage Widget (unofficial)"
(HERE / "build").mkdir(exist_ok=True)
(HERE / "build" / "version.txt").write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={v}, prodvers={v}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'github.com/lowjinghong29/claude-usage-widget'),
    StringStruct('FileDescription', '{name}'),
    StringStruct('FileVersion', '{w.VERSION}'),
    StringStruct('InternalName', 'ClaudeUsageWidget'),
    StringStruct('LegalCopyright', 'MIT License. Not made or endorsed by Anthropic.'),
    StringStruct('OriginalFilename', 'ClaudeUsageWidget.exe'),
    StringStruct('ProductName', '{name}'),
    StringStruct('ProductVersion', '{w.VERSION}')])]),
  VarFileInfo([VarStruct('Translation', [1033, 1200])])])
""", encoding="utf-8")
shutil.copy(HERE / "claude_usage_widget.pyw", HERE / "ClaudeUsageWidget.py")
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
                "--name", "ClaudeUsageWidget", "--icon", str(HERE / "icon.ico"),
                "--version-file", str(HERE / "build" / "version.txt"),
                "--exclude-module", "numpy",  # Pillow imports it only if present; the widget never needs it
                "--distpath", str(HERE / "build" / "app"), "--workpath", str(HERE / "build" / "work"),
                "--specpath", str(HERE / "build"), str(HERE / "ClaudeUsageWidget.py")], check=True)
os.remove(HERE / "ClaudeUsageWidget.py")

# 3. installer
iscc = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Inno Setup 6" / "ISCC.exe"
if not iscc.exists():
    iscc = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
subprocess.run([str(iscc), f"/DAppVer={w.VERSION}", str(HERE / "setup.iss")], check=True)
print("Built", HERE / "dist" / "ClaudeUsageWidget-Setup.exe")
