; LEX VIRIDIS - Inno Setup Script
; Buscador Jurídico Ambiental de Honduras v1.1.0
; Generado el 7 de agosto de 2025

[Setup]
; Información básica de la aplicación
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=LEX VIRIDIS
AppVersion=1.1.0
AppVerName=LEX VIRIDIS v1.1.0
AppPublisher=LEX VIRIDIS Development Team
AppPublisherURL=https://lexviridis.hn
AppSupportURL=https://lexviridis.hn/soporte
AppUpdatesURL=https://lexviridis.hn/actualizaciones
AppCopyright=Copyright (C) 2025 LEX VIRIDIS Team

; Configuración del instalador
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

; Configuración de Windows
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
DisableProgramGroupPage=yes
DisableWelcomePage=no

; Configuración visual
; WizardImageFile=assets\wizard_image.bmp
; WizardSmallImageFile=assets\wizard_small.bmp
UninstallDisplayIcon={app}\LEX_VIRIDIS.exe
UninstallDisplayName=LEX VIRIDIS - Buscador Jurídico Ambiental

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startmenu"; Description: "Crear acceso directo en el menú Inicio"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked
Name: "associate"; Description: "Asociar archivos .pdf con LEX VIRIDIS (opcional)"; GroupDescription: "Asociaciones de archivos"

[Files]
; Ejecutable principal
Source: "dist\LEX_VIRIDIS.exe"; DestDir: "{app}"; Flags: ignoreversion

; Archivos de documentación
Source: "LEX_VIRIDIS_EJECUTABLE_INFO.txt"; DestDir: "{app}"; DestName: "Información.txt"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; DestName: "Léeme.txt"; Flags: ignoreversion isreadme

; Recursos gráficos
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Base de datos legal (incluir todos los archivos)
Source: "COMPENDIO LEYES FEMA\*.pdf"; DestDir: "{app}\COMPENDIO LEYES FEMA"; Flags: ignoreversion

; Archivos de configuración y caché
Source: "cache\*"; DestDir: "{app}\cache"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist

[Icons]
; Icono en el menú Inicio
Name: "{group}\LEX VIRIDIS"; Filename: "{app}\LEX_VIRIDIS.exe"; IconFilename: "{app}\assets\lux_viridis_2.ico.ico"; Comment: "Buscador Jurídico Ambiental de Honduras"

; Icono en el escritorio
Name: "{autodesktop}\LEX VIRIDIS"; Filename: "{app}\LEX_VIRIDIS.exe"; IconFilename: "{app}\assets\lux_viridis_2.ico.ico"; Comment: "Buscador Jurídico Ambiental de Honduras"; Tasks: desktopicon

; Icono en la barra de tareas (Quick Launch)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\LEX VIRIDIS"; Filename: "{app}\LEX_VIRIDIS.exe"; IconFilename: "{app}\assets\lux_viridis_2.ico.ico"; Comment: "Buscador Jurídico Ambiental de Honduras"; Tasks: quicklaunchicon

; Desinstalador
Name: "{group}\Desinstalar LEX VIRIDIS"; Filename: "{uninstallexe}"; IconFilename: "{app}\assets\lux_viridis_2.ico.ico"

; Información y ayuda
Name: "{group}\Información de LEX VIRIDIS"; Filename: "{app}\Información.txt"; IconFilename: "{app}\assets\lux_viridis_2.ico.ico"

[Run]
; Ejecutar la aplicación después de la instalación
Filename: "{app}\LEX_VIRIDIS.exe"; Description: "{cm:LaunchProgram,LEX VIRIDIS}"; Flags: nowait postinstall skipifsilent

; Abrir archivo de información
Filename: "{app}\Información.txt"; Description: "Ver información de la aplicación"; Flags: postinstall skipifsilent shellexec unchecked

[UninstallDelete]
; Limpiar archivos temporales y logs al desinstalar
Type: filesandordirs; Name: "{app}\temp_pdfs"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.tmp"

[Registry]
; Registro de la aplicación en Windows
Root: HKLM; Subkey: "Software\LEX VIRIDIS"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\LEX VIRIDIS"; ValueType: string; ValueName: "Version"; ValueData: "1.1.0"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\LEX VIRIDIS"; ValueType: string; ValueName: "InstallDate"; ValueData: "{code:GetDateTimeString}"; Flags: uninsdeletekey

; Asociación de archivos PDF (opcional)
Root: HKCR; Subkey: ".pdf\OpenWithList\LEX_VIRIDIS.exe"; Flags: uninsdeletekey; Tasks: associate
Root: HKCR; Subkey: "Applications\LEX_VIRIDIS.exe"; ValueType: string; ValueName: ""; ValueData: "LEX VIRIDIS"; Flags: uninsdeletekey; Tasks: associate
Root: HKCR; Subkey: "Applications\LEX_VIRIDIS.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\LEX_VIRIDIS.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associate

[Messages]
; Mensajes personalizados en español
spanish.WelcomeLabel1=Bienvenido al Asistente de Instalación de LEX VIRIDIS
spanish.WelcomeLabel2=LEX VIRIDIS es un potente buscador jurídico ambiental diseñado específicamente para Honduras. Esta aplicación le permitirá buscar y consultar de manera eficiente la legislación ambiental hondureña.%n%nSe recomienda cerrar todas las demás aplicaciones antes de continuar.
spanish.ClickNext=Haga clic en Siguiente para continuar, o en Cancelar para salir de la instalación.
spanish.SelectDirLabel3=La instalación copiará los archivos de LEX VIRIDIS en la siguiente carpeta.
spanish.SelectDirBrowseLabel=Para continuar, haga clic en Siguiente. Si desea seleccionar una carpeta diferente, haga clic en Examinar.

[Code]
// Código Pascal para funciones personalizadas

function GetDateTimeString(Param: String): String;
begin
  Result := GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0);
end;

function InitializeSetup(): Boolean;
begin
  // Verificar si hay una versión anterior instalada
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'Software\LEX VIRIDIS') then
  begin
    if MsgBox('Se detectó una versión anterior de LEX VIRIDIS instalada. ¿Desea continuar con la instalación?', 
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  
  // Verificar requisitos del sistema
  if not IsWin64 then
  begin
    MsgBox('LEX VIRIDIS requiere Windows de 64 bits. Su sistema no es compatible.', 
           mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  Result := True;
end;

procedure InitializeWizard();
begin
  // Personalizar el asistente de instalación
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel1.Font.Size := 12;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  // Saltar páginas innecesarias en instalaciones silenciosas
  if WizardSilent then
  begin
    case PageID of
      wpWelcome, wpLicense, wpInfoBefore: Result := True;
    else
      Result := False;
    end;
  end else
    Result := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Crear directorio de logs si no existe
    if not DirExists(ExpandConstant('{app}\logs')) then
      CreateDir(ExpandConstant('{app}\logs'));
      
    // Crear directorio temporal si no existe
    if not DirExists(ExpandConstant('{app}\temp_pdfs')) then
      CreateDir(ExpandConstant('{app}\temp_pdfs'));
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Limpiar configuraciones de usuario
    if MsgBox('¿Desea eliminar también las configuraciones y datos de usuario de LEX VIRIDIS?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\LEX VIRIDIS'), True, True, True);
    end;
  end;
end;

[CustomMessages]
; Mensajes personalizados
spanish.FullInstallation=Instalación completa (incluye base de datos legal completa)
spanish.MinimalInstallation=Instalación mínima (solo ejecutable)
spanish.DatabaseSize=La base de datos legal completa ocupa aproximadamente 2 GB adicionales.
spanish.InstallationComplete=LEX VIRIDIS se ha instalado correctamente en su sistema.
spanish.LaunchNow=Ejecutar LEX VIRIDIS ahora
spanish.ViewInfo=Ver información de la aplicación

english.FullInstallation=Full installation (includes complete legal database)
english.MinimalInstallation=Minimal installation (executable only)
english.DatabaseSize=The complete legal database requires approximately 2 GB additional space.
english.InstallationComplete=LEX VIRIDIS has been successfully installed on your system.
english.LaunchNow=Launch LEX VIRIDIS now
english.ViewInfo=View application information
