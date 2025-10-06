
[Setup]
AppName=Video Downloader
AppVersion=1.0.0
AppPublisher=VTools
AppPublisherURL=https://github.com/abdula8/VideoDownloader
AppSupportURL=https://github.com/abdula8/VideoDownloader
AppUpdatesURL=https://github.com/abdula8/VideoDownloader
DefaultDirName={autopf}\Video Downloader
DefaultGroupName=Video Downloader
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=.
OutputBaseFilename=VideoDownloader_Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Start with Windows"; GroupDescription: "Startup Options:"; Flags: unchecked

[Files]
Source: "dist\VideoDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Video Downloader"; Filename: "{app}\VideoDownloader.exe"
Name: "{group}\{cm:UninstallProgram,Video Downloader}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Video Downloader"; Filename: "{app}\VideoDownloader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VideoDownloader.exe"; Description: "{cm:LaunchProgram,Video Downloader}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VideoDownloader"; ValueData: "{app}\VideoDownloader.exe"; Tasks: startup
