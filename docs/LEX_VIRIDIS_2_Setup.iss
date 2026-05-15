; ============================================================
; LEX VIRIDIS 2 - Inno Setup Script
; Plataforma de Gestion Legal Institucional v3.2.0.2026
; Actualizado: Mayo 2026
; ============================================================

[Setup]
AppId={{B2C3D4E5-F6A7-8901-BCDE-F12345678901}
AppName=LEX VIRIDIS 2
AppVersion=3.2.0.2026
AppVerName=LEX VIRIDIS 2 v3.2.0.2026
AppPublisher=Fer Ardon - Transformacion Digital
AppPublisherURL=https://lexviridis.hn
AppSupportURL=https://lexviridis.hn/soporte
AppUpdatesURL=https://lexviridis.hn/actualizaciones
AppCopyright=Copyright (C) 2026 LEX VIRIDIS - Transformacion Digital
DefaultDirName={autopf}\LEX VIRIDIS 2
DefaultGroupName=LEX VIRIDIS 2
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
InfoBeforeFile=..\docs\README_INSTALACION.txt
InfoAfterFile=..\docs\INSTRUCCIONES_USO.txt
OutputDir=..\installer
OutputBaseFilename=LEX_VIRIDIS_2_v3.2.0_Setup
SetupIconFile=..\assets\LEXVIRIDIS_WHITE_BG.ico
WizardImageFile=..\assets\LEXVIRIDIS_WHITE_BG.bmp
WizardSmallImageFile=..\assets\LEXVIRIDIS_WHITE_BG.bmp
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
LZMAUseSeparateProcess=yes
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UsedUserAreasWarning=no
DisableProgramGroupPage=yes
DisableWelcomePage=no
UninstallDisplayIcon={app}\LEX_VIRIDIS_2.exe
UninstallDisplayName=LEX VIRIDIS 2 - Plataforma de Gestion Legal Institucional
CreateUninstallRegKey=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startmenu"; Description: "Crear acceso directo en el menu Inicio"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; --- 1. Ejecutable principal ---
Source: "..\dist\LEX_VIRIDIS_2\LEX_VIRIDIS_2.exe"; DestDir: "{app}"; Flags: ignoreversion
; --- 2. Dependencias Python (_internal) ---
;     NOTA: _internal contiene el runtime completo generado por PyInstaller.
;     Se excluyen manualmente cache/ e index/ que PyInstaller pudo haber bundleado
;     con datos de desarrollo (62MB cache PDFs + 36MB indices .pkl).
Source: "..\dist\LEX_VIRIDIS_2\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; --- 3. Base de datos SQLite SEED (solo lectura — app la copia a %APPDATA% en primer arranque) ---
Source: "..\LEX_VIRIDIS_DB\legislacion_ambiental.db"; DestDir: "{app}\LEX_VIRIDIS_DB"; Flags: ignoreversion
; --- 4. Compendio legal FEMA (~185 PDFs) ---
Source: "..\COMPENDIO LEYES FEMA\*"; DestDir: "{app}\COMPENDIO LEYES FEMA"; Flags: ignoreversion recursesubdirs createallsubdirs
; --- 5. Sistema de licencias ---
Source: "..\LEX_VIRIDIS_LICENCIA\license_system.py"; DestDir: "{app}\LEX_VIRIDIS_LICENCIA"; Flags: ignoreversion
Source: "..\LEX_VIRIDIS_LICENCIA\GeneradorLicencias_LexViridis.exe"; DestDir: "{app}\LEX_VIRIDIS_LICENCIA"; Flags: ignoreversion
Source: "..\LEX_VIRIDIS_LICENCIA\INSTRUCCIONES_LICENCIAS.txt"; DestDir: "{app}\LEX_VIRIDIS_LICENCIA"; Flags: ignoreversion
; --- 6. Documentacion ---
Source: "..\docs\INSTRUCCIONES_USO.txt"; DestDir: "{app}"; DestName: "INSTRUCCIONES_USO.txt"; Flags: ignoreversion
; NOTA: Los directorios data\ (cache, index, backups, session) NO se instalan aqui.
;       En modo instalado el app usa %APPDATA%\LEX VIRIDIS\ (ver config.py DATA_DIR / DB_DIR).
;       La BD semilla se copia automaticamente al primer arranque desde {app}\LEX_VIRIDIS_DB.

[Icons]
Name: "{group}\LEX VIRIDIS 2"; Filename: "{app}\LEX_VIRIDIS_2.exe"; IconFilename: "{app}\_internal\assets\LEXVIRIDIS_WHITE_BG.ico"; Comment: "Plataforma de Gestion Legal Institucional"
Name: "{autodesktop}\LEX VIRIDIS 2"; Filename: "{app}\LEX_VIRIDIS_2.exe"; IconFilename: "{app}\_internal\assets\LEXVIRIDIS_WHITE_BG.ico"; Comment: "Plataforma de Gestion Legal Institucional"; Tasks: desktopicon
Name: "{group}\Desinstalar LEX VIRIDIS 2"; Filename: "{uninstallexe}"; IconFilename: "{app}\_internal\assets\LEXVIRIDIS_WHITE_BG.ico"

[Run]
Filename: "{app}\LEX_VIRIDIS_2.exe"; Description: "{cm:LaunchProgram,LEX VIRIDIS 2}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\temp_pdfs"
Type: filesandordirs; Name: "{app}\temp_pdfs_highlighted"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.tmp"

[Registry]
Root: HKLM; Subkey: "Software\LEX VIRIDIS 2"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\LEX VIRIDIS 2"; ValueType: string; ValueName: "Version"; ValueData: "3.2.0.2026"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\LEX VIRIDIS 2"; ValueType: string; ValueName: "InstallDate"; ValueData: "2026-05"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\LEX VIRIDIS 2"; ValueType: string; ValueName: "Publisher"; ValueData: "Fer Ardon - Transformacion Digital"; Flags: uninsdeletekey

[Messages]
spanish.WelcomeLabel1=Bienvenido al Asistente de Instalacion de LEX VIRIDIS 2
spanish.WelcomeLabel2=LEX VIRIDIS 2 es una plataforma de gestion legal institucional disenada para Honduras. Permite buscar y consultar la legislacion ambiental hondurena con soporte de Inteligencia Artificial.%n%nSe recomienda cerrar todas las demas aplicaciones antes de continuar.

[Code]

function InitializeSetup(): Boolean;
begin
  if not IsWin64 then
  begin
    MsgBox('LEX VIRIDIS 2 requiere Windows de 64 bits (Windows 10 o superior).' + #13#10 + 'Su sistema no es compatible.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'Software\LEX VIRIDIS 2') then
  begin
    if MsgBox('Se detecto una version anterior de LEX VIRIDIS 2 instalada.' + #13#10 + 'Desea actualizar a la version 3.2.0.2026?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  Result := True;
end;

procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel1.Font.Size := 12;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ForceDirectories(ExpandConstant('{app}\logs'));
    ForceDirectories(ExpandConstant('{app}\temp_pdfs'));
    ForceDirectories(ExpandConstant('{app}\temp_pdfs_highlighted'));
    ForceDirectories(ExpandConstant('{app}\exports'));
    ForceDirectories(ExpandConstant('{app}\backups'));
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('Desea eliminar tambien las configuraciones y datos de usuario de LEX VIRIDIS 2?' + #13#10 + '(Base de datos operativa, exportaciones, historial y sesion guardada)', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // %APPDATA%\LEX VIRIDIS — donde el app almacena la BD operativa y datos de usuario
      DelTree(ExpandConstant('{userappdata}\LEX VIRIDIS'), True, True, True);
    end;
  end;
end;

[CustomMessages]
spanish.InstallationComplete=LEX VIRIDIS 2 se ha instalado correctamente en su sistema.
spanish.LaunchNow=Ejecutar LEX VIRIDIS 2 ahora
english.InstallationComplete=LEX VIRIDIS 2 has been successfully installed on your system.
english.LaunchNow=Launch LEX VIRIDIS 2 now
