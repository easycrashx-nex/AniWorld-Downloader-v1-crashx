@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
if defined PYTHONPATH (
  set "PYTHONPATH=%SCRIPT_DIR%src;%PYTHONPATH%"
) else (
  set "PYTHONPATH=%SCRIPT_DIR%src"
)
py -m aniworld %*
endlocal
