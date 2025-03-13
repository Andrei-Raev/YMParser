@echo off
chcp 1251 >nul

REM ? 0. ���������� ����������� ���������
call ..\.venv\Scripts\activate.bat

REM ? 1. ��������� ���������� � .ui ������� � ��� ������ .py ������
SET "UI_DIR=interface"
SET "OUT_DIR=cache"

REM ? 2. ��������� � ���������� � .ui �������
cd /d "%UI_DIR%"

REM ? 3. ���������, ���������� �� ���������� ��� ������, ���� ��� � ������ �
if not exist "..\%OUT_DIR%" (
    mkdir "..\%OUT_DIR%"
)

REM ? 4. ������� ��� .ui ����� � ������������ �� � .py, �������� � OUT_DIR
for %%f in (*.ui) do (
    pyside6-uic "%%f" -o "..\%OUT_DIR%\%%~nf.py"
    echo ������������� ����: "%%f"
)

REM ?? ���������� �������� � ������ ����� nopause
if /i "%1"=="nopause" or /i "%2"=="nopause" (
    REM ? ���� ������ ���� nopause, ��������� ��� �����
    goto :EOF
) else (
    REM ? �����, ������� ��������� � ����� ������� �������
    echo ����������� ���������. ����� ��������� � ���������� "%OUT_DIR%".
    pause
)

exit