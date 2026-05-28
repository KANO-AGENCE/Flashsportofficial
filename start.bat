@echo off
chcp 65001 >nul 2>&1
title FlashSport - Launcher
color 0A

echo ============================================
echo        FLASHSPORT - LANCEMENT AUTO
echo ============================================
echo.

:: ---- Vérification des logiciels ----
echo [1/9] Verification des logiciels...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo   ERREUR : Python n'est pas installe !
    echo   Telecharge-le sur python.org/downloads
    pause
    exit /b 1
)
echo   Python ............. OK

node --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo   ERREUR : Node.js n'est pas installe !
    echo   Telecharge-le sur nodejs.org
    pause
    exit /b 1
)
echo   Node.js ............ OK

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo   ERREUR : Docker Desktop n'est pas installe !
    echo   Telecharge-le sur docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo   Docker ............. OK
echo.

:: ---- Lancement de Docker Desktop si besoin ----
echo [2/9] Verification de Docker Engine...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo   Docker Engine ne tourne pas, lancement de Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo   Attente du demarrage de Docker Engine...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 goto wait_docker
)
echo   Docker Engine ...... OK
echo.

:: ---- Se placer dans le bon dossier ----
cd /d "%~dp0"

:: ---- Environnement virtuel Python ----
echo [3/9] Preparation de l'environnement Python...
if not exist "venv\Scripts\activate.bat" (
    echo   Creation du venv...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo   Venv ............... OK
echo.

:: ---- Installation des dependances Python ----
echo [4/9] Installation des dependances Python...
pip install -r requirements.txt --quiet 2>nul
echo   Dependances Python . OK
echo.

:: ---- Installation des dependances Frontend ----
echo [5/9] Installation des dependances Frontend...
if not exist "frontend\node_modules" (
    cd frontend
    call npm install --silent 2>nul
    cd ..
)
echo   Dependances Front .. OK
echo.

:: ---- PostgreSQL via Docker ----
echo [6/9] Lancement de PostgreSQL...
docker compose up db -d 2>nul
:: Attendre que PostgreSQL soit prêt
:wait_pg
timeout /t 2 /nobreak >nul
docker compose exec db pg_isready >nul 2>&1
if %errorlevel% neq 0 goto wait_pg
echo   PostgreSQL ......... OK
echo.

:: ---- Init DB + Admin ----
echo [7/9] Initialisation de la base de donnees...
python scripts/init_db.py 2>nul
python scripts/seed_admin.py 2>nul
echo   Base de donnees .... OK
echo.

:: ---- Lancement du Backend ----
echo [8/9] Lancement du Backend (port 8000)...
start "FlashSport-Backend" cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && python main.py"
timeout /t 5 /nobreak >nul
echo   Backend ............ OK
echo.

:: ---- Lancement du Frontend ----
echo [9/9] Lancement du Frontend (port 5173)...
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
