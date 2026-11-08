@echo off
chcp 65001 >nul
REM ================================================================
REM  Đóng gói phần mềm QL-VTVL thành bộ cài Windows
REM  Yêu cầu: Python 3.11+ (64-bit), Inno Setup 6 (tùy chọn, để tạo bộ cài)
REM ================================================================
cd /d "%~dp0"
echo [1/4] Tao moi truong ao...
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
echo [2/4] Cai thu vien...
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller pytest || goto :error
echo [3/4] Kiem thu va dong goi...
python -m pytest -q tests || goto :error
pyinstaller qlvtvl.spec --noconfirm --clean || goto :error
echo [4/4] Tao bo cai dat...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
  %ISCC% installer\qlvtvl.iss || goto :error
  echo.
  echo HOAN TAT: dist\installer\CaiDat_QL-VTVL_2.0.0.exe
) else (
  echo Khong tim thay Inno Setup 6 - chi tao ban chay truc tiep: dist\QL-VTVL\QL-VTVL.exe
)
pause
exit /b 0
:error
echo Co loi xay ra, vui long kiem tra thong bao phia tren.
pause
exit /b 1
