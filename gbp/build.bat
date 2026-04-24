@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Building C++ GBP Solver (MSVC version)
echo ==========================================
echo.

set SCIP_DIR=C:\Program Files\SCIPOptSuite 10.0.2
set SCIP_INC=%SCIP_DIR%\include
set SCIP_LIB=%SCIP_DIR%\lib
set SCIP_DLL=%SCIP_DIR%\bin\libscip.dll

set OUT=gbp\solver.dll
set SRC=gbp\solver.cpp

echo SCIP Include : %SCIP_INC%
echo SCIP Lib     : %SCIP_LIB%
echo Output       : %OUT%
echo.

REM ==============================
REM Check SCIP installation
REM ==============================
if not exist "%SCIP_INC%" (
    echo ERROR: SCIP include not found
    exit /b 1
)

if not exist "%SCIP_LIB%\libscip.lib" (
    echo ERROR: libscip.lib NOT found in %SCIP_LIB%
    echo You MUST install SCIP MSVC development package.
    exit /b 1
)

REM ==============================
REM Step 1: Compile with MSVC
REM ==============================
echo Step 1: Compiling solver.cpp with MSVC...

cl /O2 /LD %SRC% ^
 /I "%SCIP_INC%" ^
 /link ^
 /LIBPATH:"%SCIP_LIB%" libscip.lib ^
 /OUT:%OUT%

if %ERRORLEVEL% neq 0 (
    echo.
    echo FAILED: compilation error
    exit /b 1
)

echo.
echo ==========================================
echo SUCCESS: solver.dll built at %OUT%
echo ==========================================
echo.
echo IMPORTANT:
echo - Make sure libscip.dll is in PATH at runtime
echo - Or copy it next to your Python script
echo.

endlocal