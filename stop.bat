@echo off
REM =============================================================================
REM stop.bat — Stop the py_ts_scrapper stack (Windows CMD)
REM Usage: stop.bat          ^# stop containers (volumes preserved)
REM        stop.bat --clean  ^# stop + remove volumes (full reset)
REM =============================================================================
setlocal

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "CLEAN=0"

for %%A in (%*) do (
  if "%%A"=="--clean" set "CLEAN=1"
)

if "%CLEAN%"=="1" (
  echo [stop] Stopping containers and removing volumes (all data will be lost)...
  docker compose -f "%ROOT%\docker-compose.yml" down -v
  echo [stop] Stack stopped and volumes removed.
) else (
  echo [stop] Stopping containers (volumes preserved)...
  docker compose -f "%ROOT%\docker-compose.yml" down
  echo [stop] Stack stopped. Run start.bat to restart.
)

endlocal
