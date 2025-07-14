# 🔧 Configuration de l'Environnement

Ce guide explique comment configurer l'environnement pour l'application d'analyse d'appels d'offres.

## 📋 Prérequis

- Python 3.8+
- Clé API OpenAI valide
- Compte OpenAI avec crédits

## 🚀 Installation Rapide

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Configuration de l'environnement
```bash
# Option 1 : Script automatique
python setup_env.py

# Option 2 : Création manuelle
cp .env.example .env
```

### 3. Configuration de l'API OpenAI
Éditez le fichier `.env` et remplacez :
```bash
OPENAI_API_KEY=your_openai_api_key_here
```
par votre vraie clé API :
```bash
OPENAI_API_KEY=sk-1234567890abcdef...
```

### 4. Lancement de l'application
```bash
streamlit run streamlit_llamaindex_app.py
```

## ⚙️ Variables d'Environnement

### Configuration OpenAI
| Variable | Description | Défaut |
|----------|-------------|--------|
| `OPENAI_API_KEY` | Clé API OpenAI | `your_openai_api_key_here` |

### Configuration des Modèles
| Variable | Description | Défaut |
|----------|-------------|--------|
| `LLM_MODEL` | Modèle LLM à utiliser | `gpt-4o` |
| `EMBEDDING_MODEL` | Modèle d'embeddings | `text-embedding-3-small` |
| `TEMPERATURE` | Température pour la génération | `0.3` |

### Configuration de l'Application
| Variable | Description | Défaut |
|----------|-------------|--------|
| `DEBUG` | Mode debug | `True` |
| `LOG_LEVEL` | Niveau de log | `INFO` |

### Configuration des Limites
| Variable | Description | Défaut |
|----------|-------------|--------|
| `MAX_TOKENS_PER_REQUEST` | Tokens max par requête | `4000` |
| `AUTO_PURGE_DAYS` | Jours avant purge auto | `3` |

## 🔍 Vérification de la Configuration

### Test de la configuration
```bash
python setup_env.py
# Choisir l'option 2 pour vérifier
```

### Test de l'API OpenAI
```bash
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('OPENAI_API_KEY')
print('✅ API Key configurée' if key and key != 'your_openai_api_key_here' else '❌ API Key manquante')
"
```

## 🛠️ Dépannage

### Erreur "API key not found"
1. Vérifiez que le fichier `.env` existe
2. Vérifiez que `OPENAI_API_KEY` est correctement définie
3. Redémarrez l'application

### Erreur "Invalid API key"
1. Vérifiez que votre clé API est valide
2. Vérifiez que vous avez des crédits sur votre compte OpenAI
3. Testez votre clé sur https://platform.openai.com/account/api-keys

### Erreur d'import de modules
```bash
pip install -r requirements.txt
```

## 📁 Structure des Fichiers

```
TenderAnalysis/
├── .env                    # Variables d'environnement (à créer)
├── .env.example           # Exemple de configuration
├── setup_env.py           # Script de configuration
├── requirements.txt       # Dépendances Python
├── streamlit_llamaindex_app.py  # Application principale
└── ...
```

## 🔐 Sécurité

- **Ne committez jamais** votre fichier `.env` dans Git
- Le fichier `.env` est déjà dans `.gitignore`
- Utilisez des clés API avec des permissions minimales
- Surveillez votre utilisation de l'API OpenAI

## 💡 Conseils

### Optimisation des coûts
- Utilisez `gpt-3.5-turbo` au lieu de `gpt-4o` pour les tests
- Réduisez `MAX_TOKENS_PER_REQUEST` si nécessaire
- Activez le mode debug pour voir les tokens utilisés

### Performance
- Augmentez `MAX_TOKENS_PER_REQUEST` pour de meilleures analyses
- Ajustez `TEMPERATURE` selon vos besoins (0.1-0.7)
- Utilisez `AUTO_PURGE_DAYS` pour gérer l'espace disque

## 🆘 Support

Si vous rencontrez des problèmes :
1. Vérifiez ce guide de configuration
2. Consultez les logs de l'application
3. Testez avec les fichiers de démonstration : `python demo_documents.py` 