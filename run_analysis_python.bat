@echo off
rem Runs the full Python analysis. Output goes to output_python\ and output_python\run_log_python.txt
cd /d "%~dp0"
if not exist output_python mkdir output_python
set "PY="
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%d\python.exe" set "PY=%%d\python.exe"
if not defined PY for /d %%d in ("%ProgramFiles%\Python3*") do if exist "%%d\python.exe" set "PY=%%d\python.exe"
if not defined PY ( where py 1>NUL 2>&1 && set "PY=py" )
if not defined PY ( echo Python was not found. Install it first, ticking "Add python.exe to PATH". > output_python\run_log_python.txt & type output_python\run_log_python.txt & pause & exit /b 1 )
echo Using %PY%
echo Installing or checking packages (pandas, numpy, matplotlib)...
"%PY%" -m pip install --user --disable-pip-version-check pandas numpy matplotlib > output_python\pip_log.txt 2>&1
"%PY%" Regulation_Demand_Shocks_Renter_Burdens.py > output_python\run_log_python.txt 2>&1
echo Finished. See output_python\run_log_python.txt
type output_python\run_log_python.txt
pause
