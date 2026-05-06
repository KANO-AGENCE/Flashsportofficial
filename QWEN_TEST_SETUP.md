# Test Qwen2.5-VL local pour OCR dossards

## 1. Installation Ollama (Mac)

```bash
# Installer Ollama
brew install ollama

# OU telecharger depuis https://ollama.com/download
```

## 2. Lancer Ollama

```bash
ollama serve
```

Ollama tourne sur `http://localhost:11434` par defaut.

## 3. Telecharger le modele

Le modele se telecharge automatiquement au premier appel du pipeline.
Pour le pre-telecharger manuellement :

```bash
ollama pull qwen2.5vl:7b
```

Taille : ~5 Go. Apple Silicon recommande (M1/M2/M3/M4).

## 4. Verifier que tout marche

```bash
# Verifier qu'Ollama tourne
curl http://localhost:11434/api/tags

# Tester le modele
ollama run qwen2.5vl:7b "Dis bonjour"
```

## 5. Lancer le pipeline

```bash
# Backend (dans le venv)
cd "/Users/arthurdamas/Documents/Sites web /Flashsport tri "
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (autre terminal)
cd frontend
npm run dev
```

Le pipeline utilise maintenant Qwen local au lieu de GPT-4o-mini pour lire les dossards.
La rotation reste geree par GPT-4o (si la cle OpenAI est configuree).

## 6. Ce qui a change

- `app/services/ocr_qwen.py` : nouveau fichier, appel Ollama local
- `app/services/pipeline.py` : `read_bib_qwen` remplace `read_bib_gpt` comme OCR primaire
- Fallback PaddleOCR toujours actif si Qwen echoue

## 7. Retour a GPT (rollback)

```bash
# Option 1 : revenir sur la branche main
git checkout main

# Option 2 : revert le changement dans pipeline.py
# Remplacer dans app/services/pipeline.py :
#   from app.services.ocr_qwen import read_bib_qwen
# Par :
#   from app.services.ocr_gpt import read_bib_gpt
#
# Et remplacer :
#   bib_number, confidence = read_bib_qwen(...)
# Par :
#   bib_number, confidence = read_bib_gpt(...)
```

## 8. Logs

Les logs Qwen incluent :
- Reponse brute du modele
- Temps d'execution par appel
- Erreurs detaillees (Ollama down, timeout, modele absent)

Exemple de log :
```
INFO - Qwen OCR raw response: '243' (1.34s)
INFO - Qwen OCR: bib=243 (1.34s)
ERROR - Qwen OCR: Ollama not reachable (0.01s). Is 'ollama serve' running?
```
