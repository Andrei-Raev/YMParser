@echo off
chcp 1251 >nul

REM ? 0. Активируем виртуальное окружение
call ..\.venv\Scripts\activate.bat

REM ? 1. Указываем директории с .ui файлами и для вывода .py файлов
SET "UI_DIR=interface"
SET "OUT_DIR=cache"

REM ? 2. Переходим в директорию с .ui файлами
cd /d "%UI_DIR%"

REM ? 3. Проверяем, существует ли директория для вывода, если нет — создаём её
if not exist "..\%OUT_DIR%" (
    mkdir "..\%OUT_DIR%"
)

REM ? 4. Находим все .ui файлы и конвертируем их в .py, сохраняя в OUT_DIR
for %%f in (*.ui) do (
    pyside6-uic "%%f" -o "..\%OUT_DIR%\%%~nf.py"
    echo Конвертирован файл: "%%f"
)

REM ?? Завершение процесса с учётом флага nopause
if /i "%1"=="nopause" or /i "%2"=="nopause" (
    REM ? Если указан флаг nopause, завершить без паузы
    goto :EOF
) else (
    REM ? Иначе, вывести сообщение и ждать нажатия клавиши
    echo Конвертация завершена. Файлы сохранены в директории "%OUT_DIR%".
    pause
)

exit