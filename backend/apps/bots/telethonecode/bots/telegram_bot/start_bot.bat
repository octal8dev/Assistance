@echo off
echo Starting Telegram AI Assistant Bot...
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

REM Создание директории для логов если её нет
if not exist logs mkdir logs

echo Checking dependencies...
pip show python-telegram-bot >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo.
echo Starting bot...
echo Press Ctrl+C to stop the bot.
echo.

python main.py

echo.
echo Bot stopped.
pause
