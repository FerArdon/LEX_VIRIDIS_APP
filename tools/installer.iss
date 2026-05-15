; LEX VIRIDIS - Inno Setup Installer Script Professional Edition
; Generador de instalador robusto para Windows

#define MyAppName "LEX VIRIDIS 2"
#define MyAppVersion "3.2.0.2026"
#define MyAppPublisher "Fer Ardón"
#define MyAppURL "https://lexviridis.hn"
#define MyAppExeName "LEX_VIRIDIS_2.exe"
#define MyAppAssocName "LEX VIRIDIS Database"
#define MyAppAssocExt ".lvdb"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Información básica
AppId=LEX-VIRIDIS-PRO-2026-V3
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Requisitos y Arquitectura
MinVersion=10.0.10240
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Prevención de conflictos
AppMutex=LEXVIRIDIS_MUTEX_GLOBAL
CloseApplications=yes
RestartApplications=yes

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

; Salida
OutputDir=installer
OutputBaseFilename=LexViridis_2026
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}

; Privilegios
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile=LICENSE.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Despliegue completo de PyInstaller (Binarios, DLLs, Assets empaquetados)
Source: "dist\LEX_VIRIDIS_2\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; Base de Datos y entorno (Externo al build de PyInstaller)
Source: "lexviridis.db"; DestDir: "{app}"; Flags: ignoreversion
Source: "LEX_VIRIDIS_DB\*"; DestDir: "{app}\LEX_VIRIDIS_DB"; Flags: ignoreversion recursesubdirs createallsubdirs

; PDFs - Compendio de Leyes FEMA (Externo al build de PyInstaller por tamaño)
Source: "COMPENDIO LEYES FEMA\*"; \
    DestDir: "{app}\COMPENDIO LEYES FEMA"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; Documentación adicional
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Estructura de persistencia en AppData (Fix Disk I/O)
Name: "{userappdata}\{#MyAppName}"
Name: "{userappdata}\{#MyAppName}\data"
Name: "{userappdata}\{#MyAppName}\data\index"
Name: "{userappdata}\{#MyAppName}\data\cache"
Name: "{userappdata}\{#MyAppName}\data\backups"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\LEXVIRIDIS_WHITE_BG.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\LEXVIRIDIS_WHITE_BG.ico"; Tasks: desktopicon

[Registry]
; Datos de Instalación para trazabilidad
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

; Asociación de archivos .lvdb
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpieza de temporales pero preservando AppData (opcional según Code)
Type: filesandordirs; Name: "{app}\__pycache__"

[Messages]
spanish.BeveledLabel=LEX VIRIDIS - Compendio Legal Ambiental de Honduras

[CustomMessages]
spanish.LaunchProgram=Ejecutar LEX VIRIDIS
spanish.CreateDesktopIcon=Crear icono en el escritorio
spanish.AdditionalIcons=Iconos adicionales
spanish.UninstallProgram=Desinstalar %1

[Code]
// Función para confirmar desinstalación y advertir sobre datos de usuario
function InitializeUninstall(): Boolean;
begin
  Result := MsgBox('¿Está seguro de que desea desinstalar LEX VIRIDIS?' + #13#10#13#10 +
                   'Se eliminarán los archivos del programa, pero sus favoritos y búsquedas guardadas podrían conservarse en AppData.', 
                   mbConfirmation, MB_YESNO) = IDYES;
end;

procedure CurUninstallStepChanged(UninstallStep: TUninstallStep);
begin
  if UninstallStep = usPostUninstall then
  begin
    // Aquí se podría preguntar si desea borrar también la carpeta de AppData
  end;
end;
