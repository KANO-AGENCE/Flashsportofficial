# FlashSport Tri

Plateforme de photographie evenementielle sportive. Tri automatique des photos par IA (detection de personnes + lecture de dossards), verification manuelle, boutique en ligne et mailing.

## Pipeline IA

```
Upload photos
  -> Detection personnes (YOLOv8)
  -> Lecture dossard (Qwen2.5-VL via Ollama)
  -> Analyse qualite (nettete + cadrage)
  -> Score global + classification
  -> Verification humaine
  -> Publication boutique
```

## Prerequis

- **Docker Desktop** — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Ollama** — [ollama.com](https://ollama.com) (pour l'OCR local Qwen)
- **Python 3.11+** (pour le developpement sans Docker)
- **Node.js 18+** (pour le developpement sans Docker)

## Installation rapide (Docker, recommande)

Fonctionne sur **Windows**, **macOS** et **Linux**.

```bash
# 1. Cloner le projet
git clone https://github.com/KANO-AGENCE/Flashsportofficial.git
cd Flashsportofficial

# 2. Copier la config
cp .env.example .env

# 3. Installer Ollama + modele Qwen
ollama pull qwen2.5vl:3b

# 4. Lancer tout
docker compose up --build -d

# 5. Creer le compte admin (premiere fois uniquement)
docker compose exec backend python scripts/seed_admin.py
```

L'application est accessible sur :
- **http://localhost** — Dashboard admin
- **http://localhost:8000/docs** — Documentation API (Swagger)

## Installation developpement (sans Docker)

### 1. Base de donnees

Lancer PostgreSQL seul via Docker :

```bash
docker compose up db -d
```

### 2. Backend

**macOS :**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_admin.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Windows :**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_admin.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Note Windows : si l'installation echoue a cause des chemins longs, activer le support dans PowerShell (admin) :
```powershell
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name 'LongPathsEnabled' -Value 1
```

### 3. Frontend admin

```bash
cd frontend
npm install
npm run dev
```

Accessible sur http://localhost:5173

### 4. Frontend boutique

```bash
cd frontend-web
npm install
npm run dev
```

Accessible sur http://localhost:5174

## URLs personnalisees (reseau local)

Pour acceder avec des noms propres au lieu d'IP, ajouter dans le fichier hosts de chaque poste :

**Windows :** `C:\Windows\System32\drivers\etc\hosts`
**macOS :** `/etc/hosts`

```
192.168.1.50    flashsport.app
192.168.1.50    boutique.flashsport.app
```

(Remplacer `192.168.1.50` par l'IP du serveur)

## Connexion

Compte par defaut :
- Email : `admin@flashsport.fr`
- Mot de passe : `admin`

**Changer le mot de passe en production.**

## Utilisation

1. **Creer un evenement** (nom, date, configuration course)
2. **Importer les participants** (fichier Excel)
3. **Importer les photos** (depuis carte SD ou dossier)
4. **Lancer le traitement IA** (detection + OCR + scoring)
5. **Verifier les resultats** (corriger les dossards incertains)
6. **Publier** vers la boutique en ligne
7. **Envoyer un mailing** aux participants (optionnel)

## Roles utilisateur

- **SUPERADMIN** — Acces total, gestion des utilisateurs
- **ADMIN** — Gestion des evenements et modules
- **POSTE_TRI** — Tri et verification des photos uniquement

## Modules

- **TRI** — Import, traitement IA, verification, exports
- **WEB** — Boutique en ligne, commandes, produits
- **MAILING** — Campagnes email aux participants

## Structure

```
main.py              # Point d'entree FastAPI
config.py            # Configuration (via .env)
docker-compose.yml   # Deploiement tout-en-un
Dockerfile           # Image Docker backend
nginx/               # Reverse proxy config
app/
  api/               # Routes FastAPI
  services/          # Detection, OCR, Qualite, Pipeline
  models/            # Modeles SQLAlchemy
  schemas/           # Schemas Pydantic
  db/                # Config base de donnees
frontend/            # Dashboard admin (Vue 3)
frontend-web/        # Boutique publique (Vue 3)
scripts/             # Init DB, seed admin
tests/               # Tests unitaires
```

## Tests

```bash
pytest tests/ -v
```

## Securite

- 100% local, aucune API externe
- OCR via Ollama (local)
- Stockage fichiers local
- JWT + roles + modules
- Pret pour deploiement sur serveur isole (LAN/VPN)
