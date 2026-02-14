; LEX VIRIDIS - Inno Setup Installer Script
; Generador de instalador profesional para Windows

#define MyAppName "LEX VIRIDIS"
#define MyAppVersion "3.0"
#define MyAppPublisher "Fer Ardón"
#define MyAppURL "https://lexviridis.hn"
#define MyAppExeName "LEX_VIRIDIS.exe"
#define MyAppAssocName "LEX VIRIDIS Database"
#define MyAppAssocExt ".lvdb"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Información básica
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Directorios
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Compresión
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Iconos y gráficos
SetupIconFile=assets\LEXVIRIDIS_WHITE_BG.ico
WizardStyle=modern
WizardImageFile=assets\LEXVIRIDIS_WHITE_BG.bmp
WizardSmallImageFile=assets\LEXVIRIDIS_WHITE_BG.bmp


; Privilegios
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Salida
OutputDir=installer
OutputBaseFilename=LEX_VIRIDIS_Setup_v{#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}

; Licencia y términos
LicenseFile=LICENSE.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Ejecutable principal
Source: "dist\LEX_VIRIDIS.exe"; DestDir: "{app}"; Flags: ignoreversion

; Assets (iconos, imágenes)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Base de datos
Source: "LEX_VIRIDIS_DB\legislacion_ambiental.db"; DestDir: "{app}\LEX_VIRIDIS_DB"; Flags: ignoreversion

; Sistema de licencias (scripts de generación - opcional para admin)
Source: "LEX_VIRIDIS_LICENCIA\*"; DestDir: "{app}\LEX_VIRIDIS_LICENCIA"; Flags: ignoreversion

; Documentación
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Crear directorio para datos del usuario
Name: "{userappdata}\LEX VIRIDIS"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\LEXVIRIDIS_WHITE_BG.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\LEXVIRIDIS_WHITE_BG.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Asociación de archivos (opcional)
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".lvdb"; ValueData: ""

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\LEX VIRIDIS"

[Messages]
spanish.BeveledLabel=LEX VIRIDIS - Compendio Legal Ambiental de Honduras

[CustomMessages]
spanish.LaunchProgram=Ejecutar LEX VIRIDIS
spanish.CreateDesktopIcon=Crear icono en el escritorio
spanish.CreateQuickLaunchIcon=Crear icono en la barra de inicio rápido
spanish.AdditionalIcons=Iconos adicionales
spanish.UninstallProgram=Desinstalar %1
