; LumaRef Inno Setup installer script
; Produces a single LumaRef-Setup.exe that installs the PyInstaller-built exe,
; registers .lref file association, and creates Start Menu shortcuts.
;
; Usage:
;   1. Build the exe:  pyinstaller ZeeRef.spec
;   2. Build installer: iscc installer.iss
;
; The installer exe lands in dist/LumaRef-Setup.exe

#define AppName "LumaRef"
; AppVersion is passed in by CI via `iscc /DAppVersion=...`.
#ifndef AppVersion
  #define AppVersion "dev"
#endif
#define AppPublisher "Zack Gomez"
#define AppURL "https://github.com/safalevent/lumaref"

[Setup]
AppId={{E8A3F2B1-7C45-4D89-9B6E-2F1A3C5D7E90}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=LumaRef-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Per-user install by default (no admin required)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=zeeref\assets\logo.ico
UninstallDisplayIcon={app}\LumaRef.exe
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The PyInstaller single-file exe. Wildcard handles the version in the filename.
; Rename to ZeeRef.exe on install for a clean path.
Source: "dist\LumaRef-{#AppVersion}.exe"; DestDir: "{app}"; DestName: "LumaRef.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\LumaRef.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\LumaRef.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "fileassoc"; Description: "Associate .lref files with {#AppName}"; GroupDescription: "File associations:"; Flags: checkedonce

[Registry]
; File association: .lref → LumaRef.Document
Root: HKA; Subkey: "Software\Classes\.lref"; ValueType: string; ValueName: ""; ValueData: "LumaRef.Document"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\LumaRef.Document"; ValueType: string; ValueName: ""; ValueData: "LumaRef Scene"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\LumaRef.Document\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\LumaRef.exe,0"; Tasks: fileassoc
Root: HKA; Subkey: "Software\Classes\LumaRef.Document\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\LumaRef.exe"" ""%1"""; Tasks: fileassoc
