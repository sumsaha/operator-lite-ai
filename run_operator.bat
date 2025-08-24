@echo off
if "%~1"=="" (
  echo Usage: run_operator.bat "Your instruction here"
  exit /b 1
)

echo =======================================
echo  Running Operator with natural language
echo =======================================

python operator.py %1
pause
