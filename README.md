# Flashsport Tri

Tri automatique de photos sportives par detection de dossard et analyse qualite.

## Pipeline

```
Upload photos → Detection personnes (YOLOv8) → Extraction zone dossard → OCR (PaddleOCR)
→ Analyse qualite (nettete + cadrage) → Score global → Classification → Validation humaine
```

## Prerequis

- **Python 3.11+** (`brew install python@3.11` ou `pyenv install 3.11`)
- **Docker** (pour PostgreSQL)

## Installation

```bash
# 1. Cloner et entrer dans le dossier
cd "Flashsport tri"

# 2. Creer l'environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# 3. Installer les dependances
pip install -r requirements.txt

# 4. Lancer PostgreSQL
docker compose up -d

# 5. Lancer l'application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Ouvrir http://localhost:8000

## Utilisation

1. **Creer un evenement** (nom + date)
2. **Uploader les photos** (drag & drop ou selection de fichiers)
3. **Lancer le traitement** → detection + OCR + scoring automatique
4. **Consulter les resultats** par dossard ou par photo
5. **Valider** les photos "incertaines" (corriger numero, changer categorie)

## API Endpoints

| Methode | URL | Description |
|---------|-----|-------------|
| POST | `/api/events` | Creer un evenement |
| GET | `/api/events` | Lister les evenements |
| GET | `/api/events/{id}` | Detail d'un evenement |
| DELETE | `/api/events/{id}` | Supprimer un evenement |
| POST | `/api/events/{id}/photos` | Uploader des photos |
| GET | `/api/events/{id}/photos` | Lister les photos |
| GET | `/api/events/{id}/bibs` | Groupement par dossard |
| GET | `/api/photos/{id}` | Detail d'une photo |
| POST | `/api/events/{id}/process` | Lancer le traitement |
| GET | `/api/events/{id}/process/status` | Statut du traitement |
| PUT | `/api/detections/{id}/validate` | Valider une detection |

Documentation Swagger: http://localhost:8000/docs

## Classification

| Score | Categorie |
|-------|-----------|
| >= 70% | **Bon** - photo exploitable |
| 40-70% | **Incertain** - a verifier |
| < 40% | **Mauvais** - inexploitable |

## Score composite

| Critere | Poids |
|---------|-------|
| Confiance detection YOLO | 20% |
| Confiance OCR | 30% |
| Nettete (Laplacien) | 30% |
| Cadrage | 20% |

## Structure

```
├── main.py              # Point d'entree FastAPI
├── config.py            # Configuration
├── app/
│   ├── api/             # Routes FastAPI
│   ├── services/        # Detection, OCR, Qualite, Scoring, Pipeline
│   ├── models/          # Modeles SQLAlchemy
│   ├── schemas/         # Schemas Pydantic
│   └── db/              # Config base de donnees
├── frontend/            # Interface HTML/JS
├── tests/               # Tests unitaires
└── uploads/             # Photos (genere automatiquement)
```

## Tests

```bash
pytest tests/ -v
```

## Securite

- 100% local, aucune API externe
- Aucun appel reseau sortant
- Stockage fichiers local
- Pret pour deploiement sur serveur isole (LAN/VPN)

## Note sur la detection

Le MVP utilise YOLOv8n (modele general COCO) avec une heuristique pour localiser
la zone du dossard sur le torse des athletes detectes. Pour de meilleures performances,
entrainer un modele YOLOv8 custom sur des annotations de dossards.
