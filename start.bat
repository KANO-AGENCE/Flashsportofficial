@echo off
chcp 65001 >nul 2>&1
title FlashSport - Launcher
color 0A

echo ============================================
echo        FLASHSPORT - LANCEMENT AUTO
echo ============================================
echo.

:: ---- Vérification des logiciels ----
echo [1/7] Verification des logiciels...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo   ERREUR : Python n'est pas installe !
    echo   Lance install.bat d'abord.
    pause
    exit /b 1
)
echo   Python ............. OK

node --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo   ERREUR : Node.js n'est pas installe !
    echo   Lance install.bat d'abord.
    pause
    exit /b 1
)
echo   Node.js ............ OK

:: Ajouter PostgreSQL au PATH temporairement
set "PGPATH=C:\Program Files\PostgreSQL\16\bin"
if exist "%PGPATH%\psql.exe" set "PATH=%PGPATH%;%PATH%"

pg_isready >nul 2>&1
if %errorlevel% neq 0 (
    echo   PostgreSQL ne tourne pas, tentative de demarrage...
    net start postgresql-x64-16 >nul 2>&1
    timeout /t 3 /nobreak >nul
    pg_isready >nul 2>&1
    if %errorlevel% neq 0 (
        color 0C
        echo   ERREUR : PostgreSQL ne demarre pas !
        echo   Lance install.bat d'abord.
        pause
        exit /b 1
    )
)
echo   PostgreSQL ......... OK
echo.

:: ---- Se placer dans le bon dossier ----
cd /d "%~dp0"

:: ---- Environnement virtuel Python ----
echo [2/7] Preparation de l'environnement Python...
if not exist "venv\Scripts\activate.bat" (
    echo   Creation du venv...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo   Venv ............... OK
echo.

:: ---- Installation des dependances Python ----
echo [3/7] Installation des dependances Python...
echo.
echo   Premiere fois = 5-10 min, les fois suivantes = quelques secondes.
echo   Les paquets deja installes seront ignores.
echo.
pip install -r requirements.txt 2>&1
echo.
echo   Dependances Python . OK
echo.

:: ---- Installation des dependances Frontend ----
echo [4/7] Installation des dependances Frontend...
if not exist "frontend\node_modules" (
    echo   Premiere installation des modules frontend...
    cd frontend
    call npm install
    cd ..
)
echo   Dependances Front .. OK
echo.

:: ---- Init DB + Admin ----
echo [5/7] Initialisation de la base de donnees...
python scripts/init_db.py 2>nul
python scripts/seed_admin.py 2>nul
echo   Base de donnees .... OK
echo.

:: ---- Lancement du Backend ----
echo [6/7] Lancement du Backend (port 8000)...
start "FlashSport-Backend" cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && python main.py"
timeout /t 5 /nobreak >nul
echo   Backend ............ OK
echo.

:: ---- Lancement du Frontend ----
echo [7/7] Lancement du Frontend (port 5173)...
start "FlashSport-Frontend" cmd /c "cd /d "%~dp0\frontend" && npm run dev"
timeout /t 5 /nobreak >nul
echo   Frontend ........... OK
echo.

:: ---- Ouverture du navigateur ----
echo ============================================
echo   FLASHSPORT EST PRET !
echo.
echo   App    : http://localhost:5173
echo   Login  : admin@flashsport.fr
echo   Pass   : admin
echo   API    : http://localhost:8000/docs
echo ============================================
echo.
echo Ouverture du navigateur...
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo (Cette fenetre peut etre fermee, les serveurs
echo  tournent dans leurs propres fenetres)
echo.
pause
