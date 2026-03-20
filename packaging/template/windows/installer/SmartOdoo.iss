; SmartOdoo Windows installer (Inno Setup)
; Build with ISCC.exe SmartOdoo.iss

#define MyAppName "SmartOdoo"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#ifndef MySourceRoot
  #define MySourceRoot "..\..\..\.."
#endif
#ifndef MyOutputDir
  #define MyOutputDir "..\..\..\build"
#endif
#ifndef MyConfigJsonPath
  #define MyConfigJsonPath "..\..\..\build\config.windows.json"
#endif
#define MyAppPublisher "SmartOdoo"
#define PythonVersion "3.14.0"
#define PythonInstallerName "python-3.14.0-amd64.exe"
#define PythonInstallerUrl "https://www.python.org/ftp/python/3.14.0/python-3.14.0-amd64.exe"
#define DockerInstallerName "Docker Desktop Installer.exe"
#define DockerInstallerUrl "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

[Setup]
AppId={{9E8A4B2A-9C6E-4678-8A8D-BE04A61DAA22}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\SmartOdoo
DefaultGroupName=SmartOdoo
DisableProgramGroupPage=yes
OutputDir={#MyOutputDir}
OutputBaseFilename=SmartOdoo-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={localappdata}\SmartOdoo\venv\Scripts\python.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "installpython"; Description: "Install Python 3.14 (recommended)"; GroupDescription: "Runtime components:"; Flags: checkedonce
Name: "installdocker"; Description: "Install Docker Desktop (recommended)"; GroupDescription: "Runtime components:"; Flags: checkedonce
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Root files
Source: "{#MySourceRoot}\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceRoot}\.env"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceRoot}\launch.json"; DestDir: "{app}\.vscode"; DestName: "launch.json"; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#MySourceRoot}\.vscode\launch.json"; DestDir: "{app}\.vscode"; DestName: "launch.json"; Flags: ignoreversion skipifsourcedoesntexist

; App packages
Source: "{#MySourceRoot}\app\__init__.py"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "{#MySourceRoot}\app\setup.py"; DestDir: "{app}\app"; Flags: ignoreversion
Source: "{#MySourceRoot}\app\core\*"; DestDir: "{app}\app\core"; Excludes: "__pycache__\*;*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceRoot}\app\platform\__init__.py"; DestDir: "{app}\app\platform"; Flags: ignoreversion
Source: "{#MySourceRoot}\app\platform\windows\*"; DestDir: "{app}\app\platform\windows"; Excludes: "__pycache__\*;*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs

; Runtime support files
Source: "{#MySourceRoot}\docker\*"; DestDir: "{app}\docker"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceRoot}\scripts\encpass.sh"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Config folder used by the tool
Source: "{#MySourceRoot}\config\*"; DestDir: "{app}\config"; Excludes: "config.json"; Flags: ignoreversion onlyifdoesntexist recursesubdirs createallsubdirs
Source: "{#MyConfigJsonPath}"; DestDir: "{app}\config"; DestName: "config.json"; Flags: ignoreversion onlyifdoesntexist

[Run]
; Step 1: ensure Python 3.14 is installed for this user.
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$ErrorActionPreference='Stop'; $url='{#PythonInstallerUrl}'; $out=Join-Path $env:TEMP '{#PythonInstallerName}'; $target=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314'; Invoke-WebRequest -Uri $url -OutFile $out; & $out /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_venv=1 Include_tcltk=1 Include_test=0 TargetDir=$target; exit $LASTEXITCODE"""; \
  StatusMsg: "Installing Python {#PythonVersion}..."; \
  Flags: runhidden waituntilterminated; \
  Tasks: installpython; \
  Check: not HasPython314
; Optional Docker Desktop installation (can prompt for elevation).
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$ErrorActionPreference='Stop'; $url='{#DockerInstallerUrl}'; $out=Join-Path $env:TEMP '{#DockerInstallerName}'; Invoke-WebRequest -Uri $url -OutFile $out; & $out install --quiet --accept-license; exit $LASTEXITCODE"""; \
  StatusMsg: "Installing Docker Desktop..."; \
  Flags: runhidden waituntilterminated; \
  Tasks: installdocker; \
  Check: not HasDockerDesktop
; Step 2: create/recreate venv from Python 3.14.
Filename: "cmd.exe"; \
  Parameters: "/C set ""VENV=%LOCALAPPDATA%\SmartOdoo\venv"" && set ""PY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"" && if not exist ""%PY%"" set ""PY=%LOCALAPPDATA%\Programs\Python\Python314t\python.exe"" && if not exist ""%PY%"" set ""PY=%ProgramFiles%\Python314\python.exe"" && if exist ""%VENV%"" rmdir /S /Q ""%VENV%"" && if exist ""%PY%"" ""%PY%"" -m venv ""%VENV%"""; \
  StatusMsg: "Creating Python virtual environment..."; \
  Flags: runhidden waituntilterminated
; Step 3: fallback via bundled Python launcher path if the first venv attempt failed.
Filename: "cmd.exe"; \
  Parameters: "/C if not exist ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\python.exe"" if exist ""%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"" ""%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"" -3.14 -m venv ""%LOCALAPPDATA%\SmartOdoo\venv"""; \
  StatusMsg: "Retrying virtual environment bootstrap with Python launcher..."; \
  Flags: runhidden waituntilterminated
; Step 4: fallback via py from PATH (for systems with existing Python install).
Filename: "cmd.exe"; \
  Parameters: "/C if not exist ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\python.exe"" where py >nul 2>nul && py -3 -m venv ""%LOCALAPPDATA%\SmartOdoo\venv"""; \
  StatusMsg: "Trying existing Python launcher from PATH..."; \
  Flags: runhidden waituntilterminated
; Step 5: fallback via python from PATH.
Filename: "cmd.exe"; \
  Parameters: "/C if not exist ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\python.exe"" where python >nul 2>nul && python -m venv ""%LOCALAPPDATA%\SmartOdoo\venv"""; \
  StatusMsg: "Trying existing Python interpreter from PATH..."; \
  Flags: runhidden waituntilterminated
; Step 6: fail fast if venv bootstrap did not produce python.exe.
Filename: "cmd.exe"; \
  Parameters: "/C if not exist ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\python.exe"" exit /b 1"; \
  StatusMsg: "Validating Python environment..."; \
  Flags: runhidden waituntilterminated
; Step 7: install runtime dependencies inside the prepared venv.
Filename: "{localappdata}\SmartOdoo\venv\Scripts\python.exe"; \
  Parameters: "-m pip install --upgrade pip setuptools wheel"; \
  StatusMsg: "Updating pip tooling..."; \
  Flags: runhidden waituntilterminated
Filename: "{localappdata}\SmartOdoo\venv\Scripts\python.exe"; \
  Parameters: "-m pip install -r ""{app}\requirements.txt"""; \
  StatusMsg: "Installing SmartOdoo dependencies..."; \
  Flags: runhidden waituntilterminated
; Step 8: validate required Python modules and show explicit message on failure.
Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$py=Join-Path $env:LOCALAPPDATA 'SmartOdoo\venv\Scripts\python.exe'; & $py -c 'import pygubu'; if ($LASTEXITCODE -ne 0) {{ Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Dependency installation failed (pygubu). Check internet access and Python package mirrors, then rerun setup.','SmartOdoo Setup',[System.Windows.Forms.MessageBoxButtons]::OK,[System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null; exit 1 }}"""; \
  StatusMsg: "Validating SmartOdoo dependencies..."; \
  Flags: runhidden waituntilterminated
; Step 9: provide pythonw.exe fallback for GUI startup if venv misses it.
Filename: "cmd.exe"; \
  Parameters: "/C if not exist ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\pythonw.exe"" if exist ""%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"" copy /Y ""%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"" ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\pythonw.exe"" >nul"; \
  StatusMsg: "Finalizing GUI runtime..."; \
  Flags: runhidden waituntilterminated

[Icons]
; Shortcuts use pythonw when available and fallback to python.
Name: "{group}\SmartOdoo"; Filename: "{cmd}"; Parameters: "/C if exist ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\pythonw.exe"" (start """" ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\pythonw.exe"" ""{app}\app\core\smartodoo_gui.py"") else (""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\python.exe"" ""{app}\app\core\smartodoo_gui.py"")"; WorkingDir: "{app}"
Name: "{autodesktop}\SmartOdoo"; Filename: "{cmd}"; Parameters: "/C if exist ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\pythonw.exe"" (start """" ""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\pythonw.exe"" ""{app}\app\core\smartodoo_gui.py"") else (""%LOCALAPPDATA%\SmartOdoo\venv\Scripts\python.exe"" ""{app}\app\core\smartodoo_gui.py"")"; WorkingDir: "{app}"; Tasks: desktopicon

[UninstallRun]
Filename: "cmd.exe"; \
  Parameters: "/C for /d /r ""{app}"" %d in (__pycache__) do @if exist ""%d"" rd /S /Q ""%d"" & del /S /Q ""{app}\*.pyc"" 2>nul"; \
  RunOnceId: "SmartOdooPyCacheCleanup"; \
  Flags: runhidden waituntilterminated
Filename: "cmd.exe"; \
  Parameters: "/C if exist ""%LOCALAPPDATA%\SmartOdoo"" rmdir /S /Q ""%LOCALAPPDATA%\SmartOdoo"""; \
  RunOnceId: "SmartOdooVenvCleanup"; \
  Flags: runhidden waituntilterminated

[UninstallDelete]
; Remove any runtime leftovers that were not part of the install log.
Type: filesandordirs; Name: "{app}\*"
Type: dirifempty; Name: "{app}"

[Code]
function HasPython314: Boolean;
begin
  Result :=
    FileExists(ExpandConstant('{localappdata}\Programs\Python\Python314\python.exe')) or
    FileExists(ExpandConstant('{localappdata}\Programs\Python\Python314t\python.exe')) or
    FileExists(ExpandConstant('{pf}\Python314\python.exe'));
end;

function HasDockerDesktop: Boolean;
begin
  Result :=
    FileExists(ExpandConstant('{pf}\Docker\Docker\Docker Desktop.exe')) or
    FileExists(ExpandConstant('{localappdata}\Programs\Docker Desktop\Docker Desktop.exe'));
end;
