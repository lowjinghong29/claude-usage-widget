; Inno Setup script for Claude Usage Widget. Built by build.py.
#define AppVer "1.0.0"

[Setup]
AppId={{6F3B2C1E-9A4D-4E7B-8C21-5D0A7B9E4F13}
AppName=Claude Usage Widget (unofficial)
AppVersion={#AppVer}
AppPublisher=Claude Usage Widget
AppComments=Unofficial tool. Not made or endorsed by Anthropic.
DefaultDirName={localappdata}\Programs\Claude Usage Widget
DefaultGroupName=Claude Usage Widget
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=ClaudeUsageWidget-Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\ClaudeUsageWidget.exe
InfoBeforeFile=README.txt
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "autostart"; Description: "Start automatically when I sign in to Windows"

[Files]
Source: "build\app\ClaudeUsageWidget\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\Claude Usage Widget"; Filename: "{app}\ClaudeUsageWidget.exe"
Name: "{userstartup}\Claude Usage Widget"; Filename: "{app}\ClaudeUsageWidget.exe"; Tasks: autostart

[Run]
Filename: "{app}\ClaudeUsageWidget.exe"; Description: "Start Claude Usage Widget now"; Flags: nowait postinstall skipifsilent

[Code]
// Stop a running widget first so its files can be replaced or removed.
procedure StopWidget();
var Code: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/im ClaudeUsageWidget.exe /f', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Sleep(500);
end;

function InitializeSetup(): Boolean;
begin
  StopWidget();
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  StopWidget();
  Result := True;
end;
