# 📝 Changelog

## [1.3.0] - 2025-07-15

### ✅ Ajouté
- **Génération automatique de mémoires techniques** complètes
- **Templates spécialisés** par type de chantier (façade, intérieur, structure)
- **Sections structurées** : présentation entreprise, méthodologie, planning, garanties
- **Export Markdown** pour intégration dans les réponses d'appels d'offres
- **Configuration personnalisable** des informations d'entreprise
- **Résumé exécutif** automatique de la mémoire technique
- **Interface de génération** avec validation utilisateur
- **Sauvegarde automatique** des mémoires techniques par session
- **Script de test Phase 3** (`test_phase3.py`) pour validation

### 🔧 Amélioré
- **Intégration complète** de la génération de mémoires dans l'interface Streamlit
- **Persistance des mémoires** techniques avec les sessions d'analyse
- **Chargement automatique** des mémoires lors de la reprise de session
- **Interface utilisateur** pour la configuration des informations d'entreprise

### 📋 Nouvelles fonctionnalités
- **TechnicalMemoryGenerator** : Classe principale pour la génération de mémoires
- **Templates par type** : restauration_facade, renovation_interieur, consolidation_structure
- **Sections automatiques** : 9 sections structurées par mémoire technique
- **Export formaté** : Markdown prêt pour intégration dans les réponses
- **Configuration entreprise** : Interface pour personnaliser les informations

## [1.2.0] - 2025-07-15

### ✅ Ajouté
- **Prompts spécialisés détaillés** pour chaque type de document
- **Détection de similitudes** avec chantiers précédents
- **Analyse environnementale spécialisée** (nuisances, biodiversité, déchets)
- **Analyse logistique spécialisée** (accès, livraisons, horaires)
- **Analyse croisée** et recommandations stratégiques
- **Base de connaissances** des chantiers précédents
- **Interface enrichie** avec synthèses par contraintes

### 🔧 Amélioré
- **Prompts plus détaillés** avec sous-sections structurées
- **Analyse multi-dimensionnelle** (technique, environnemental, logistique)
- **Recommandations stratégiques** basées sur l'analyse croisée
- **Affichage organisé** des résultats par catégories

### 📋 Nouvelles fonctionnalités
- **Analyse environnementale** : Gestion des nuisances, protection biodiversité, économie circulaire
- **Analyse logistique** : Accès chantier, stationnement, horaires, gestion des flux
- **Détection similitudes** : Comparaison avec chantiers précédents
- **Recommandations** : Stratégie de réponse, planning, gestion des risques, optimisations

## [1.1.0] - 2025-07-15

### ✅ Ajouté
- **Configuration d'environnement avancée** avec fichier `.env`
- **Variables configurables** pour tous les paramètres (modèles, limites, etc.)
- **Script de configuration** (`setup_env.py`) pour faciliter la mise en place
- **Documentation complète** (`CONFIGURATION.md`) pour la configuration
- **Script de test rapide** (`test_demo.py`) pour valider l'application
- **Fichiers de démonstration** pour tester l'application

### 🔧 Corrigé
- **Erreur ChromaDB** : Sérialisation JSON des métadonnées complexes
- **Gestion des métadonnées** : Support des types simples uniquement (str, int, float, None)
- **Chargement des analyses** : Désérialisation automatique du JSON
- **Affichage des résultats** : Gestion correcte des analyses structurées

### 🚀 Amélioré
- **Gestion des erreurs** : Messages d'erreur plus clairs
- **Configuration centralisée** : Tous les paramètres dans le fichier `.env`
- **Tests automatisés** : Scripts de validation complets
- **Documentation** : Guides d'installation et de configuration

### 📋 Variables d'environnement ajoutées
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

## [1.0.0] - 2025-07-15

### ✅ Ajouté
- **Architecture Multi-Agents** pour l'analyse d'appels d'offres
- **Classification automatique** des documents par type
- **Agents spécialisés** (Règlement, CCTP, CCAP, DPGF)
- **Extraction avancée** de contenu (PDF, Excel)
- **Analyse structurée** avec métadonnées JSON
- **Chat intelligent** avec contexte spécialisé
- **Interface Streamlit** complète
- **Persistance des sessions** avec ChromaDB

### 🏗️ Architecture
- **DocumentAnalyzer** : Classe principale pour l'analyse
- **Classification** : Règles automatiques par nom/contenu
- **Extraction** : PDF (pdfplumber) + Excel (pandas)
- **Analyse** : Prompts spécialisés par type de document
- **Stockage** : ChromaDB avec métadonnées structurées

### 📄 Types de documents supportés
- **Règlement** : Critères, délais, modalités
- **CCTP** : Exigences techniques, matériaux
- **CCAP** : Risques, pénalités, obligations
- **DPGF** : Quantités, coûts, planning
- **Plans** : Contexte architectural

---

## 🎯 Prochaines versions

### [1.2.0] - Phase 2 : Extraction Avancée (✅ Terminée)
- [x] Prompts spécialisés plus détaillés
- [x] Détection de similitudes avec chantiers précédents
- [x] Extraction de contraintes environnementales
- [x] Analyse logistique (accès, livraisons)
- [x] Analyse croisée et recommandations stratégiques

### [1.3.0] - Phase 3 : Mémoire Technique (✅ Terminée)
- [x] Génération assistée de mémoires
- [x] Spécificité par chantier
- [x] Interface de validation utilisateur
- [x] Templates spécialisés par type de projet
- [x] Export Markdown pour intégration
- [x] Configuration personnalisable entreprise

### [1.4.0] - Phase 4 : N8N (Optionnel)
- [ ] Workflows automatisés
- [ ] Intégration webhook
- [ ] Monitoring avancé 