@echo off
chcp 65001 >nul 2>&1
title FlashSport - Creation du raccourci

:: Crée un raccourci "FlashSport" sur le Bureau
powershell -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\FlashSport.lnk'); $sc.TargetPath = '%~dp0start.bat'; $sc.WorkingDirectory = '%~dp0'; $sc.Description = 'Lancer FlashSport'; $sc.IconLocation = 'shell32.dll,21'; $sc.Save()"

echo.
echo   Raccourci "FlashSport" cree sur le Bureau !
echo.
pause
