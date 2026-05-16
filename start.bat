@echo off
REM =============================================================================
REM start.bat — Launch the full py_ts_scrapper stack (Windows CMD)
REM Usage: start.bat [--no-build]
REM =============================================================================
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "DASHBOARD_DIR=%ROOT%\services\dashboard"
set "NO_BUILD=0"

for %%A in (%*) do (
  if "%%A"=="--no-build" set "NO_BUILD=1"
)

echo [start] Checking Docker...

REM ---------------------------------------------------------------------------
REM 1. Ensure Docker daemon is running
REM ---------------------------------------------------------------------------
docker info >nul 2>&1
if errorlevel 1 (
  echo [start] Docker not running - launching Docker Desktop...
  start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

  set "READY=0"
  for /L %%i in (1,1,24) do (
    if "!READY!"=="0" (
      timeout /t 5 /nobreak >nul
      docker info >nul 2>&1
      if not errorlevel 1 (
        echo [start] Docker daemon ready.
        set "READY=1"
      ) else (
        echo [start] Waiting for Docker... %%i/24
      )
    )
  )
  if "!READY!"=="0" (
    echo [start] ERROR: Docker did not start within 2 minutes.
    exit /b 1
  )
) else (
  echo [start] Docker daemon is running.
)

REM ---------------------------------------------------------------------------
REM 2. Sync package-lock.json if needed
REM ---------------------------------------------------------------------------
findstr /c:"\"pino\"" "%DASHBOARD_DIR%\package-lock.json" >nul 2>&1
if errorlevel 1 (
  echo [start] Syncing dashboard package-lock.json...
  pushd "%DASHBOARD_DIR%"
  call npm install --silent
  popd
  echo [start] package-lock.json updated.
)

REM ---------------------------------------------------------------------------
REM 3. Start all services
REM ---------------------------------------------------------------------------
if "%NO_BUILD%"=="1" (
  echo [start] Starting services (no build)...
  docker compose -f "%ROOT%\docker-compose.yml" up -d
) else (
  echo [start] Building and starting services (first run may take several minutes)...
  docker compose -f "%ROOT%\docker-compose.yml" up --build -d
)

if errorlevel 1 (
  echo [start] ERROR: docker compose failed.
  exit /b 1
)

REM ---------------------------------------------------------------------------
REM 4. Wait for health endpoints
REM ---------------------------------------------------------------------------
echo [start] Waiting for Scraper API to become healthy...
for /L %%i in (1,1,20) do (
  curl -sf http://localhost:8000/health >nul 2>&1
  if not errorlevel 1 (
    echo [start] Scraper API is healthy.
    goto :api_ready
  )
  echo [start] Attempt %%i/20 - waiting 5s...
  timeout /t 5 /nobreak >nul
)
echo [start] WARNING: Scraper API did not respond in time.
:api_ready

echo [start] Waiting for Dashboard to become healthy...
for /L %%i in (1,1,24) do (
  curl -sf http://localhost:3000/api/health >nul 2>&1
  if not errorlevel 1 (
    echo [start] Dashboard is healthy.
    goto :dashboard_ready
  )
  echo [start] Attempt %%i/24 - waiting 5s...
  timeout /t 5 /nobreak >nul
)
echo [start] WARNING: Dashboard did not respond in time.
:dashboard_ready

REM ---------------------------------------------------------------------------
REM 5. Final status
REM ---------------------------------------------------------------------------
echo.
docker compose -f "%ROOT%\docker-compose.yml" ps
echo.
echo All services are up!
echo.
echo   Dashboard   ^-^> http://localhost:3000
echo   Scraper API ^-^> http://localhost:8000
echo   API Docs    ^-^> http://localhost:8000/docs
echo   n8n         ^-^> http://localhost:5679
echo   pgBouncer   ^-^> localhost:6432
echo   Postgres    ^-^> localhost:5432
echo.

endlocal
