# 📑 Analyse d'Appels d'Offres - IA Multi-Agents

Application Streamlit pour l'analyse intelligente d'appels d'offres avec architecture multi-agents spécialisés.

## 🎯 Fonctionnalités

### ✅ **Étape 1 - Multi-Agents (Implémentée)**
- **Classification automatique** des documents par type
- **Agents spécialisés** pour chaque type de document :
  - 🏛️ **Agent Règlement** : Critères de sélection, délais, modalités
  - 🔧 **Agent CCTP** : Exigences techniques, matériaux, contraintes
  - 📋 **Agent CCAP** : Risques, pénalités, obligations administratives
  - 📊 **Agent DPGF** : Quantités, estimations, coûts unitaires
- **Extraction avancée** de contenu (PDF, Excel)
- **Analyse structurée** avec métadonnées JSON
- **Chat intelligent** avec contexte spécialisé

### ✅ **Étape 2 - Extraction Avancée (Implémentée)**
- **Prompts spécialisés détaillés** par type de document
- **Détection de similitudes** avec chantiers précédents
- **Extraction de contraintes environnementales** (nuisances, biodiversité, déchets)
- **Analyse logistique** (accès, livraisons, horaires)
- **Analyse croisée** et recommandations stratégiques

### ✅ **Étape 3 - Mémoire Technique (Implémentée)**
- **Génération automatique** de mémoires techniques complètes
- **Templates spécialisés** par type de chantier (façade, intérieur, structure)
- **Sections structurées** : présentation entreprise, méthodologie, planning, garanties
- **Export Markdown** pour intégration dans les réponses d'appels d'offres
- **Configuration personnalisable** des informations d'entreprise
- **Résumé exécutif** automatique

### 🚧 **Étapes à venir**
- **Phase 4** : Intégration N8N (optionnel)

## 🚀 Installation

```bash
# Cloner le projet
git clone <repository>
cd TenderAnalysis

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
python setup_env.py
# Puis éditer le fichier .env pour ajouter votre clé OpenAI

# Lancer l'application
streamlit run streamlit_llamaindex_app.py

## 🧪 Tests

### Test rapide
```bash
python test_demo.py
```

### Test complet
```bash
python test_multi_agents.py
```

### Test Phase 2
```bash
python test_phase2.py
```

### Test Phase 3
```bash
python test_phase3.py
```

### Créer des fichiers de démonstration
```bash
python demo_documents.py
```
```

## 📋 Types de Documents Supportés

| Type | Description | Agent Spécialisé |
|------|-------------|------------------|
| **Règlement** | Règlement de consultation | Critères, délais, modalités |
| **CCTP** | Cahier des Clauses Techniques | Exigences techniques, matériaux |
| **CCAP** | Cahier des Clauses Administratives | Risques, pénalités, obligations |
| **DPGF** | Détail Quantitatif et Estimatif | Quantités, coûts, planning |
| **Plans** | Plans et notes historiques | Contexte architectural |

## 🏗️ Architecture

### **Workflow Multi-Agents**
```
Upload Fichiers
       ↓
Classification Automatique
       ↓
Extraction de Contenu (PDF/Excel)
       ↓
Agents Spécialisés par Type
       ↓
Analyse Structurée (JSON)
       ↓
Index Vectoriel + Chat Contextuel
```

### **Agents Implémentés**
- **DocumentAnalyzer** : Classe principale orchestrant les analyses
- **Classification** : Règles automatiques par nom/contenu
- **Extraction** : PDF (pdfplumber) + Excel (pandas)
- **Analyse** : Prompts spécialisés par type de document

## 💬 Utilisation

1. **Upload** : Déposez vos fichiers d'appel d'offres
2. **Analyse** : Lancez l'analyse multi-agents
3. **Consultation** : Consultez les résultats par document
4. **Chat** : Posez des questions contextuelles

## 📊 Exemple de Sortie

```json
{
  "critères_de_sélection": ["Expérience", "Capacité technique"],
  "délais_importants": {
    "dépôt": "2024-03-15",
    "durée_chantier": "6 mois"
  },
  "modalités_administratives": ["Garantie 5%", "Assurance décennale"]
}
```

## 🔧 Configuration

### **Variables d'environnement**
```bash
# Configuration OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Configuration des modèles
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
TEMPERATURE=0.3

# Configuration de l'application
DEBUG=True
LOG_LEVEL=INFO

# Configuration des limites
MAX_TOKENS_PER_REQUEST=4000
AUTO_PURGE_DAYS=3
```

**💡 Utilisez le script de configuration :**
```bash
python setup_env.py
```

### **Modèles utilisés**
- **LLM** : `gpt-4o` (température: 0.3-0.5)
- **Embeddings** : `text-embedding-3-small`
- **Vector Store** : ChromaDB (persistant)

## 📁 Structure des Données

```
TenderAnalysis/
├── uploads/           # Fichiers temporaires
├── storage/           # Index vectoriels + analyses
│   └── {run_id}/
│       ├── chroma.sqlite3
│       ├── analyses.json
│       └── global_summary.txt
└── streamlit_llamaindex_app.py
```

## 🎯 Prochaines Étapes

### **Phase 2 - Extraction Avancée (✅ Terminée)**
- [x] Prompts spécialisés plus détaillés
- [x] Détection de similitudes avec chantiers précédents
- [x] Extraction de contraintes environnementales
- [x] Analyse logistique (accès, livraisons)
- [x] Analyse croisée et recommandations stratégiques

### **Phase 3 - Mémoire Technique (✅ Terminée)**
- [x] Génération assistée de mémoires
- [x] Spécificité par chantier
- [x] Interface de validation utilisateur
- [x] Templates spécialisés par type de projet
- [x] Export Markdown pour intégration
- [x] Configuration personnalisable entreprise

### **Phase 4 - N8N (Optionnel)**
- [ ] Workflows automatisés
- [ ] Intégration webhook
- [ ] Monitoring avancé

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails.