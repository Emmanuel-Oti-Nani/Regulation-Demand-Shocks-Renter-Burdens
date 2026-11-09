@echo off
rem Runs the full analysis with R. Output goes to output\ and output\run_log.txt
cd /d "%~dp0"
if not exist output mkdir output
set "RS="
for /f "delims=" %%i in ('where Rscript 2^>nul') do if not defined RS set "RS=%%i"
if not defined RS for /f "delims=" %%d in ('dir /b /ad /o-n "%ProgramFiles%\R\R-*" 2^>nul') do if not defined RS set "RS=%ProgramFiles%\R\%%d\bin\Rscript.exe"
if not defined RS ( echo Rscript was not found. > output\run_log.txt & echo Rscript was not found. & pause & exit /b 1 )
echo Using "%RS%"
"%RS%" Regulation_Demand_Shocks_Renter_Burdens.R > output\run_log.txt 2>&1
echo Finished. See output\run_log.txt
type output\run_log.txt
pause
