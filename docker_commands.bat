@echo off
REM Docker Management Commands for RAG Chat Application

echo Docker Management Commands
echo ============================

:menu
echo.
echo 1. Start application (build and run)
echo 2. Stop application
echo 3. View logs
echo 4. Check status
echo 5. Run tests
echo 6. Clean up (remove containers and volumes)
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto logs
if "%choice%"=="4" goto status
if "%choice%"=="5" goto test
if "%choice%"=="6" goto cleanup
if "%choice%"=="7" goto exit
goto menu

:start
echo Starting application...
wsl docker compose up --build -d
echo Application started! Access at: http://localhost:8000
goto menu

:stop
echo Stopping application...
wsl docker compose down
echo Application stopped.
goto menu

:logs
echo Showing logs...
wsl docker compose logs -f
goto menu

:status
echo Checking status...
wsl docker compose ps
goto menu

:test
echo Running tests...
python final_test.py
goto menu

:cleanup
echo WARNING: This will remove all containers and data!
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%"=="y" (
    wsl docker compose down -v
    wsl docker system prune -f
    echo Cleanup complete.
) else (
    echo Cleanup cancelled.
)
goto menu

:exit
echo Goodbye!
exit /b 0