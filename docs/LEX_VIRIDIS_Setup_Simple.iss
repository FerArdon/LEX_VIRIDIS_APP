; LEX VIRIDIS - Inno Setup Script (Versión Simplificada)
; Buscador Jurídico Ambiental de Honduras v1.1.0

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=LEX VIRIDIS
AppVersion=1.1.0
AppVerName=LEX VIRIDIS v1.1.0
AppPublisher=LEX VIRIDIS Development Team
AppCopyright=Copyright (C) 2025 LEX VIRIDIS Team
DefaultDirName={autopf}\LEX VIRIDIS
DefaultGroupName=LEX VIRIDIS
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=README_INSTALACION.txt
InfoAfterFile=INSTRUCCIONES_USO.txt
OutputDir=installer
OutputBaseFilename=LEX_VIRIDIS_v1.1.0_Setup
SetupIconFile=assets\lux_viridis_2.ico.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\LEX_VIRIDIS.exe
UninstallDisplayName=LEX VIRIDIS - Buscador Jurídico Ambiental

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Iconos adicionales:"
Name: "startmenu"; Description: "Crear acceso directo en el menú Inicio"; GroupDescription: "Iconos adicionales:"

[Files]
Source: "dist\LEX_VIRIDIS.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LEX_VIRIDIS_EJECUTABLE_INFO.txt"; DestDir: "{app}"; DestName: "Información.txt"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; DestName: "Léeme.txt"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "COMPENDIO LEYES FEMA\*.pdf"; DestDir: "{app}\COMPENDIO LEYES FEMA"; Flags: ignoreversion
Source: "cache\*"; DestDir: "{app}\cache"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist skipifsourcedoesntexist
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist skipifsourcedoesntexist

[Icons]
Name: "{group}\LEX VIRIDIS"; Filename: "{app}\LEX_VIRIDIS.exe"; Comment: "Buscador Jurídico Ambiental de Honduras"
Name: "{autodesktop}\LEX VIRIDIS"; Filename: "{app}\LEX_VIRIDIS.exe"; Comment: "Buscador Jurídico Ambiental de Honduras"; Tasks: desktopicon
Name: "{group}\Desinstalar LEX VIRIDIS"; Filename: "{uninstallexe}"
Name: "{group}\Información de LEX VIRIDIS"; Filename: "{app}\Información.txt"

[Run]
Filename: "{app}\LEX_VIRIDIS.exe"; Description: "Ejecutar LEX VIRIDIS"; Flags: nowait postinstall skipifsilent
Filename: "{app}\Información.txt"; Description: "Ver información de la aplicación"; Flags: postinstall skipifsilent shellexec unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}\temp_pdfs"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.tmp"

[Registry]
Root: HKLM; Subkey: "Software\LEX VIRIDIS"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\LEX VIRIDIS"; ValueType: string; ValueName: "Version"; ValueData: "1.1.0"; Flags: uninsdeletekey

[Code]
function InitializeSetup(): Boolean;
begin
  if not IsWin64 then
  begin
    MsgBox('LEX VIRIDIS requiere Windows de 64 bits. Su sistema no es compatible.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not DirExists(ExpandConstant('{app}\logs')) then
      CreateDir(ExpandConstant('{app}\logs'));
    if not DirExists(ExpandConstant('{app}\temp_pdfs')) then
      CreateDir(ExpandConstant('{app}\temp_pdfs'));
  end;
end;
