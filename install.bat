@echo off
chcp 65001 >nul 2>&1
title FlashSport - Installation des logiciels
color 0E

echo ============================================
echo   FLASHSPORT - INSTALLATION AUTOMATIQUE
echo ============================================
echo.
echo   Ce script installe Python, Node.js et
echo   Docker Desktop automatiquement.
echo.
echo   IMPORTANT : ce script doit etre lance
echo   en tant qu'ADMINISTRATEUR.
echo.
pause

:: ---- Vérifier droits admin ----
net session >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo   ERREUR : Ce script doit etre lance en
    echo   tant qu'administrateur !
    echo.
    echo   Clic droit sur install.bat ^>
    echo   "Executer en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

:: ---- Vérifier winget ----
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo   ERREUR : winget n'est pas disponible.
    echo   Mets a jour Windows via le Microsoft Store.
    pause
    exit /b 1
)
echo   winget ............. OK
echo.

:: ---- Python ----
echo [1/4] Installation de Python 3.11...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   Python deja installe, on passe.
) else (
    winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements --silent
    echo   Python ............. INSTALLE
)
echo.

:: ---- Node.js ----
echo [2/4] Installation de Node.js LTS...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   Node.js deja installe, on passe.
) else (
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --silent
    echo   Node.js ............ INSTALLE
)
echo.

:: ---- Docker Desktop ----
echo [3/4] Installation de Docker Desktop...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   Docker deja installe, on passe.
) else (
    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --silent
    echo   Docker Desktop ..... INSTALLE
)
echo.

:: ---- WSL ----
echo [4/4] Installation/mise a jour de WSL...
wsl --install --no-distribution >nul 2>&1
wsl --update >nul 2>&1
echo   WSL ................ OK
echo.

echo ============================================
echo   INSTALLATION TERMINEE !
echo.
echo   Tu dois REDEMARRER le PC maintenant.
echo   Apres le redemarrage, double-clique
echo   sur start.bat pour lancer FlashSport.
echo ============================================
echo.
set /p restart="Redemarrer maintenant ? (O/N) : "
if /i "%restart%"=="O" shutdown /r /t 10 /c "Redemarrage pour FlashSport"
pause
