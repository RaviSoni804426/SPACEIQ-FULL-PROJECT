@echo off
echo Merging folders and cleaning up unnecessary files!
echo Please wait...

REM Move essential folders to root
move spaceiq\backend .\backend > nul
move spaceiq\frontend .\frontend > nul

REM Move essential files to root
move spaceiq\.env .\.env > nul
move spaceiq\.env.example .\.env.example > nul
move spaceiq\INTERVIEW_GUIDE.md .\INTERVIEW_GUIDE.md > nul

REM Remove the now-empty wrapper folder
rd /s /q spaceiq

REM Clean up unwieldy cache folders so it's less space
if exist "frontend\node_modules" rd /s /q frontend\node_modules
if exist "frontend\.next" rd /s /q frontend\.next
if exist "venv" rd /s /q venv

REM Also remove pycache artifacts from backend
for /d /r backend %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Clean up any leftover IDE logs
del /f /q frontend\*.log > nul 2>&1
del /f /q backend\*.log > nul 2>&1

echo.
echo Everything is now cleaned up and merged into a standard structure!
echo Your project footprint is severely reduced. You can just run `run.bat` whenever you want to test it.
echo You can also safely delete this cleanup.bat file now.
echo.
pause
