@echo off
setlocal
cd /d "%~dp0"
if "%PYTHON%"=="" set PYTHON=python
set ACTION=%1
if "%ACTION%"=="" set ACTION=test
if /i "%ACTION%"=="test" (
    %PYTHON% -m unittest
    exit /b %ERRORLEVEL%
)
if /i not "%ACTION%"=="demo" (
    echo Usage: run.bat [test^|demo] 1>&2
    exit /b 2
)
if not exist out mkdir out
call :run_program copy_array 400-404 || exit /b 1
call :run_program sqrt_demo 300-300 || exit /b 1
call :run_program sqrt_vector 300-304 || exit /b 1
call :run_program example_squares 300-304 || exit /b 1
call :run_program example_rounding 300-304 || exit /b 1
call :run_program example_chain 200-204 || exit /b 1
exit /b 0

:run_program
%PYTHON% src\assembler.py programs\%1.csv out\%1.bin || exit /b 1
%PYTHON% src\interpreter.py out\%1.bin out\%1.csv %2 || exit /b 1
type out\%1.csv
exit /b 0
