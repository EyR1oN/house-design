@echo off
setlocal
set "HOUSE_BLENDER=%~dp0Tools\blender-4.5.3-windows-x64\blender.exe"
if exist "%HOUSE_BLENDER%" goto launch
if defined BLENDER_EXE set "HOUSE_BLENDER=%BLENDER_EXE%"
if exist "%HOUSE_BLENDER%" goto launch
where blender.exe >nul 2>nul
if not errorlevel 1 (
set "HOUSE_BLENDER=blender.exe"
goto launch
)
echo Blender not found. See START_HERE_UK.md.
pause
exit /b 1
:launch
pushd "%~dp0"
start "" "%HOUSE_BLENDER%" --disable-autoexec "%~dp0House_Library_Design\House_Library_Design.blend"
popd
endlocal
