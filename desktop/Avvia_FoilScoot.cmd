@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 client.py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
      "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" client.py
    ) else (
      echo Python 3.10 o successivo non trovato. Installare Python e riaprire questo file.
    )
  ) else (
    python client.py
  )
)
if errorlevel 1 pause
