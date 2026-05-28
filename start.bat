@echo off
chcp 65001 >nul 2>&1
title FlashSport
color 0A

echo.
echo    ╔══════════════════════════════════════╗
echo    ║                                      ║
echo    ║       ⚡  F L A S H S P O R T  ⚡    ║
echo    ║                                      ║
echo    ╚══════════════════════════════════════╝
echo.
echo.

:: ---- Se placer dans le bon dossier ----
cd /d "%~dp0"

:: ---- Vérification des logiciels ----
echo    Verification des logiciels...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo    ✘ Python n'est pas installe !
    echo      Lance install.bat d'abord.
    pause
    exit /b 1
)
echo    ✔ Python

node --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo    ✘ Node.js n'est pas installe !
    echo      Lance install.bat d'abord.
    pause
    exit /b 1
)
echo    ✔ Node.js

:: Ajouter PostgreSQL au PATH temporairement
set "PGPATH=C:\Program Files\PostgreSQL\16\bin"
if exist "%PGPATH%\psql.exe" set "PATH=%PGPATH%;%PATH%"

pg_isready >nul 2>&1
if %errorlevel% neq 0 (
    echo    ⏳ Demarrage de PostgreSQL...
    net start postgresql-x64-16 >nul 2>&1
    timeout /t 3 /nobreak >nul
    pg_isready >nul 2>&1
    if %errorlevel% neq 0 (
        color 0C
        echo    ✘ PostgreSQL ne demarre pas !
        echo      Lance install.bat d'abord.
        pause
        exit /b 1
    )
)
echo    ✔ PostgreSQL
echo.

:: ---- Environnement virtuel Python ----
echo    ⏳ Preparation de l'environnement...
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo    ✔ Environnement Python
echo.

:: ---- Installation des dependances Python ----
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo    ⏳ Installation des dependances Python...
    echo      Premiere fois = 5-10 min, patience...
    echo.
    pip install -r requirements.txt 2>&1
    echo.
)
echo    ✔ Dependances Python
echo.

:: ---- Installation des dependances Frontend ----
if not exist "frontend\node_modules" (
    echo    ⏳ Installation des dependances Frontend...
    cd frontend
    call npm install
    cd ..
    echo.
)
echo    ✔ Dependances Frontend
echo.

:: ---- Init DB + Admin ----
echo    ⏳ Verification de la base de donnees...
python scripts/init_db.py >nul 2>&1
python scripts/seed_admin.py >nul 2>&1
echo    ✔ Base de donnees prete
echo.

:: ---- Lancement du Backend (caché) ----
echo    ⏳ Demarrage du serveur...

:: Créer un script VBS pour lancer le backend sans fenêtre visible
echo Set ws = CreateObject("WScript.Shell") > "%~dp0_launch_backend.vbs"
echo ws.Run "cmd /c cd /d ""%~dp0"" && call venv\Scripts\activate.bat && python main.py", 0, False >> "%~dp0_launch_backend.vbs"
wscript "%~dp0_launch_backend.vbs"

:: Créer un script VBS pour lancer le frontend sans fenêtre visible
echo Set ws = CreateObject("WScript.Shell") > "%~dp0_launch_frontend.vbs"
echo ws.Run "cmd /c cd /d ""%~dp0frontend"" && npm run dev", 0, False >> "%~dp0_launch_frontend.vbs"
wscript "%~dp0_launch_frontend.vbs"

:: Attendre que le backend soit prêt
echo.
echo    Demarrage en cours
set /a count=0
:wait_backend
set /a count+=1
if %count% gtr 30 (
    echo.
    echo    ✘ Le backend ne repond pas.
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/docs -o nul -w "%%{http_code}" 2>nul | findstr "200" >nul
if %errorlevel% neq 0 (
    <nul set /p "=."
    goto wait_backend
)
echo.
echo    ✔ Backend demarre
echo.

:: Attendre que le frontend soit prêt
set /a count=0
:wait_frontend
set /a count+=1
if %count% gtr 20 (
    echo.
    echo    ✘ Le frontend ne repond pas.
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
curl -s http://localhost:5173 -o nul -w "%%{http_code}" 2>nul | findstr "200" >nul
if %errorlevel% neq 0 (
    <nul set /p "=."
    goto wait_frontend
)
echo    ✔ Frontend demarre
echo.

:: ---- Nettoyage des fichiers temporaires ----
del "%~dp0_launch_backend.vbs" >nul 2>&1
del "%~dp0_launch_frontend.vbs" >nul 2>&1

:: ---- Ouverture du navigateur ----
echo.
echo    ╔══════════════════════════════════════╗
echo    ║                                      ║
echo    ║     ✔  FLASHSPORT EST PRET !         ║
echo    ║                                      ║
echo    ║     Login : admin@flashsport.fr      ║
echo    ║     Pass  : admin                    ║
echo    ║                                      ║
echo    ╚══════════════════════════════════════╝
echo.

timeout /t 2 /nobreak >nul
start http://localhost:5173

timeout /t 5 /nobreak >nul
exit
