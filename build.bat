@echo off
echo ========================================
echo    XillenDoS C++ Engine Builder
echo ========================================
echo.

echo Configuring CMake...
if not exist build mkdir build
cd build
cmake .. -G "Visual Studio 16 2019" -A x64
if %errorlevel% neq 0 goto :error

echo.
echo Building C++ Engine...
cmake --build . --config Release
if %errorlevel% neq 0 goto :error

echo.
echo Copying engine to project directory...
copy Release\dos_engine.dll ..\engine\
if %errorlevel% neq 0 goto :error

cd ..
echo.
echo ✅ Build successful!
echo C++ engine ready: engine\dos_engine.dll
goto :end

:error
echo.
echo ❌ Build failed!
cd ..
pause
exit /b 1

:end
pause