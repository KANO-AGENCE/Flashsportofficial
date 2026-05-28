@echo off
chcp 65001 >nul 2>&1
title FlashSport - Installation des logiciels
color 0E

echo ============================================
echo   FLASHSPORT - INSTALLATION AUTOMATIQUE
echo ============================================
echo.
echo   Ce script installe Python, Node.js et
echo   PostgreSQL automatiquement.
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
echo [1/3] Installation de Python 3.11...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   Python deja installe, on passe.
) else (
    winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements --silent
    echo   Python ............. INSTALLE
)
echo.

:: ---- Node.js ----
echo [2/3] Installation de Node.js LTS...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   Node.js deja installe, on passe.
) else (
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --silent
    echo   Node.js ............ INSTALLE
)
echo.

:: ---- PostgreSQL ----
echo [3/3] Installation de PostgreSQL 16...
pg_isready >nul 2>&1
if %errorlevel% equ 0 (
    echo   PostgreSQL deja installe, on passe.
) else (
    winget install PostgreSQL.PostgreSQL.16 --accept-package-agreements --accept-source-agreements --silent
    echo   PostgreSQL ......... INSTALLE
)
echo.

:: ---- Création de la base et de l'utilisateur ----
echo Configuration de la base de donnees...
echo   Attente du demarrage de PostgreSQL...
timeout /t 5 /nobreak >nul

:: Ajouter PostgreSQL au PATH temporairement
set "PGPATH=C:\Program Files\PostgreSQL\16\bin"
if exist "%PGPATH%\psql.exe" set "PATH=%PGPATH%;%PATH%"

:: Créer l'utilisateur et la base (ignore les erreurs si déjà existants)
psql -U postgres -c "CREATE USER flashsport WITH PASSWORD 'flashsport_pwd';" 2>nul
psql -U postgres -c "CREATE DATABASE flashsport_tri OWNER flashsport;" 2>nul
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE flashsport_tri TO flashsport;" 2>nul
echo   Base de donnees .... OK
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
