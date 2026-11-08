; Bộ cài đặt Windows cho phần mềm rà soát vị trí việc làm - Thư viện thành phố Cần Thơ
; Biên dịch: ISCC.exe installer\qlvtvl.iss  (sau khi đã chạy PyInstaller)

#define AppName "QL-VTVL - Rà soát vị trí việc làm"
#define AppShort "QL-VTVL"
#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif
#define AppPublisher "Thư viện thành phố Cần Thơ"
#define AppExe "QL-VTVL.exe"

[Setup]
AppId={{6E4C1B7A-2D3F-4C59-9B1E-7A0C3F2D8E41}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppShort}
DefaultGroupName={#AppShort}
DisableProgramGroupPage=yes
; Cho phép cài cho riêng người dùng hiện tại nếu không có quyền quản trị
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\installer
OutputBaseFilename=CaiDat_QL-VTVL_{#AppVersion}
SetupIconFile=..\qlvtvl\assets\app.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=yes

[Languages]
#ifexist "Vietnamese.isl"
Name: "vi"; MessagesFile: "Vietnamese.isl"
#endif
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "assoc"; Description: "Mở tệp hồ sơ .vtvl bằng {#AppShort}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\QL-VTVL\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\docs\HuongDanSuDung.pdf"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#AppShort}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppShort}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\.vtvl"; ValueType: string; ValueName: ""; ValueData: "QLVTVL.HoSo"; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\QLVTVL.HoSo"; ValueType: string; ValueName: ""; ValueData: "Hồ sơ vị trí việc làm"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\QLVTVL.HoSo\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe},0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\QLVTVL.HoSo\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: assoc

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppShort}}"; Flags: nowait postinstall skipifsilent
