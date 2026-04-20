@echo off
echo Starting SpaceIQ Lite...

echo ---------------------------
echo Ensuring dependencies and starting Backend...
echo ---------------------------
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
start cmd /k "venv\Scripts\activate && pip install -r requirements.txt && alembic upgrade head && python -m app.scripts.seed_demo_users && python -m app.scripts.seed_demo_inventory && echo Backend Started! && uvicorn app.main:app --reload"

echo ---------------------------
echo Ensuring dependencies and starting Frontend...
echo ---------------------------
cd ..\frontend
start cmd /k "npm install && echo Frontend Started! && npm run dev"

echo.
echo SpaceIQ Lite services are launching in separate windows!
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:3000
echo.
pause
