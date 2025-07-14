# streamlit_llamaindex_app.py
"""
Analyse d'Appels d'Offres - Architecture Multi-Agents
-----------------------------------------------------
▶️  Ce script fournit :
   • Upload multi-fichiers (PDF, DOCX, TXT, XLSX…)
   • Classification automatique des documents
   • Analyse spécialisée par type de document
   • Agents spécialisés (Règlement, CCTP, CCAP, DPGF)
   • Chat contextuel avec mémoire technique

⚙️  Dépendances :
   pip install -r requirements.txt

Lancez :
   streamlit run streamlit_llamaindex_app.py
"""

from __future__ import annotations
import os, uuid, tempfile, shutil, time, json, traceback, re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import streamlit as st
from dotenv import load_dotenv
import pandas as pd
try:
    import pdfplumber
except ImportError:
    pdfplumber = None
    st.warning("⚠️  pdfplumber non installé. L'extraction PDF sera limitée.")

# ╭─ LlamaIndex – Core + Agents ───────────────────────────────╮
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    ServiceContext,
    Settings,
    Document,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore  
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
# from llama_index.agent import ReActAgent  # Commenté pour l'instant
# from llama_index.tools import QueryEngineTool  # Commenté pour l'instant
# from llama_index.core.query_engine import SubQuestionQueryEngine  # Commenté pour l'instant
# from llama_index.core.retrievers import VectorIndexRetriever  # Commenté pour l'instant

# ╰─────────────────────────────────────────────────────────────╯

# --------------------------- Configuration Environnement ---------------------------

# Chargement des variables d'environnement
load_dotenv()

# Configuration OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    st.warning("⚠️  OPENAI_API_KEY manquant dans l'env (dotenv ou shell)")
    st.info("💡 Créez un fichier .env avec : OPENAI_API_KEY=your_key_here")

# Configuration des modèles
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

# Configuration de l'application
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configuration des limites
MAX_TOKENS_PER_REQUEST = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4000"))
AUTO_PURGE_DAYS = int(os.getenv("AUTO_PURGE_DAYS", "3"))

# --------------------------- Types et Enums ---------------------------

class DocumentType(Enum):
    REGLEMENT = "Règlement de consultation"
    CCTP = "Cahier des Clauses Techniques Particulières"
    CCAP = "Cahier des Clauses Administratives Particulières"
    DPGF = "Détail Quantitatif et Estimatif"
    PLANS = "Plans et notes historiques"
    AUTRE = "Autre document"

@dataclass
class DocumentInfo:
    name: str
    type: DocumentType
    content: str
    metadata: Dict[str, Any]
    analysis: Dict[str, Any] = None  # type: ignore

# --------------------------- Config ---------------------------
DATA_DIR = Path("./uploads")
VECTOR_DIR = Path("./storage")
DATA_DIR.mkdir(exist_ok=True)
VECTOR_DIR.mkdir(exist_ok=True)

# Limite mémoire : auto-purge indices anciens
purge_seconds = AUTO_PURGE_DAYS * 24 * 3600
for d in VECTOR_DIR.iterdir():
    if d.is_dir() and (time.time() - d.stat().st_mtime) > purge_seconds:
        shutil.rmtree(d, ignore_errors=True)

# ---------------------- Classification des Documents --------------------

def classify_document(filename: str, content: str = "") -> DocumentType:
    """Classe automatiquement un document selon son nom et contenu."""
    
    # Classification par nom de fichier
    filename_lower = filename.lower()
    
    # Règles de classification
    if any(keyword in filename_lower for keyword in ["reglement", "consultation", "rc"]):
        return DocumentType.REGLEMENT
    elif any(keyword in filename_lower for keyword in ["cctp", "technique", "techniques"]):
        return DocumentType.CCTP
    elif any(keyword in filename_lower for keyword in ["ccap", "administratif", "administratives"]):
        return DocumentType.CCAP
    elif any(keyword in filename_lower for keyword in ["dpgf", "quantitatif", "estimatif", "quantite"]):
        return DocumentType.DPGF
    elif any(keyword in filename_lower for keyword in ["plan", "plans", "historique", "note"]):
        return DocumentType.PLANS
    
    # Si pas de classification par nom, analyser le contenu
    if content:
        content_lower = content.lower()
        
        # Analyse sémantique basique
        if any(term in content_lower for term in ["critères de sélection", "modalités", "attribution"]):
            return DocumentType.REGLEMENT
        elif any(term in content_lower for term in ["exigences techniques", "matériaux", "méthodes"]):
            return DocumentType.CCTP
        elif any(term in content_lower for term in ["pénalités", "délais", "obligations administratives"]):
            return DocumentType.CCAP
        elif any(term in content_lower for term in ["quantités", "estimations", "coûts unitaires"]):
            return DocumentType.DPGF
    
    return DocumentType.AUTRE

# ---------------------- Extraction de Contenu --------------------

def extract_pdf_content(file_path: Path) -> str:
    """Extrait le contenu texte d'un PDF avec pdfplumber."""
    if pdfplumber is None:
        st.error("pdfplumber non installé. Impossible d'extraire le contenu PDF.")
        return ""
    
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Erreur extraction PDF {file_path.name}: {e}")
        return ""

def extract_excel_content(file_path: Path) -> str:
    """Extrait le contenu d'un fichier Excel."""
    try:
        df = pd.read_excel(file_path)
        return df.to_string()
    except Exception as e:
        st.error(f"Erreur extraction Excel {file_path.name}: {e}")
        return ""

def extract_document_content(file_path: Path) -> str:
    """Extrait le contenu selon le type de fichier."""
    if file_path.suffix.lower() == '.pdf':
        return extract_pdf_content(file_path)
    elif file_path.suffix.lower() in ['.xlsx', '.xls']:
        return extract_excel_content(file_path)
    else:
        # Pour les autres types, lecture simple
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""

# ---------------------- Agents Spécialisés --------------------

class DocumentAnalyzer:
    """Classe pour analyser les documents avec des agents spécialisés avancés."""
    
    def __init__(self):
        self.llm = OpenAI(model=LLM_MODEL, temperature=TEMPERATURE)
        self.embed_model = OpenAIEmbedding(model=EMBEDDING_MODEL)
        
        # Base de connaissances des chantiers précédents (simulée)
        self.previous_projects = {
            "restauration_facade": {
                "type": "Restauration façade monument historique",
                "contraintes": ["échafaudage", "protection vitraux", "pierre de taille"],
                "duree": "6 mois",
                "montant": "30000-50000€"
            },
            "renovation_interieur": {
                "type": "Rénovation intérieur église",
                "contraintes": ["conservation peintures", "accès limité", "éclairage"],
                "duree": "4 mois",
                "montant": "20000-35000€"
            },
            "consolidation_structure": {
                "type": "Consolidation structure",
                "contraintes": ["renforcement", "étaiement", "sécurité"],
                "duree": "8 mois",
                "montant": "50000-80000€"
            }
        }
        
    def analyze_reglement(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du règlement de consultation."""
        prompt = f"""
        Analyse ce règlement de consultation et extrait les informations clés de manière détaillée :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière exhaustive :
        
        1. CRITÈRES DE SÉLECTION ET D'ATTRIBUTION
           - Critères techniques (pourcentage, poids)
           - Critères financiers (pourcentage, poids)
           - Critères d'expérience (pourcentage, poids)
           - Critères de capacité (pourcentage, poids)
           - Méthode de notation et de classement
        
        2. DÉLAIS IMPORTANTS
           - Date limite de dépôt des offres
           - Date d'ouverture des plis
           - Durée du chantier (début/fin)
           - Délais de réception provisoire/définitive
           - Périodes critiques à identifier
        
        3. MODALITÉS ADMINISTRATIVES
           - Garanties requises (pourcentage, montant)
           - Assurances obligatoires (types, montants)
           - Cautionnement (pourcentage, montant)
           - Conditions de paiement
           - Modalités de réception
        
        4. CONDITIONS PARTICULIÈRES
           - Contraintes spécifiques au site
           - Conditions d'accès au chantier
           - Contraintes environnementales
           - Contraintes de voisinage
           - Conditions météorologiques
        
        5. DOCUMENTS REQUIS
           - Attestations obligatoires
           - Justificatifs d'expérience
           - Plans et documents techniques
           - Mémoire technique (contenu requis)
           - Planning détaillé
        
        6. RISQUES IDENTIFIÉS
           - Risques techniques majeurs
           - Risques administratifs
           - Risques financiers
           - Risques de délais
           - Pénalités applicables
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"analyse": response.text}
    
    def analyze_cctp(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du CCTP (Cahier des Clauses Techniques Particulières)."""
        prompt = f"""
        Analyse ce CCTP et extrait les exigences techniques de manière exhaustive :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière détaillée :
        
        1. EXIGENCES TECHNIQUES PRÉCISES
           - Spécifications techniques détaillées
           - Normes et références applicables
           - Classes de résistance et caractéristiques
           - Contrôles et essais requis
           - Tolérances et marges acceptables
        
        2. MATÉRIAUX ET MÉTHODES REQUIS
           - Types de matériaux spécifiés
           - Origines et qualités requises
           - Méthodes de mise en œuvre
           - Équipements et outils nécessaires
           - Conditions de stockage et transport
        
        3. CONTRAINTES SPÉCIFIQUES
           - Contraintes de mise en œuvre
           - Contraintes de sécurité
           - Contraintes de qualité
           - Contraintes de délais
           - Contraintes d'environnement
        
        4. NORMES ET RÉFÉRENCES TECHNIQUES
           - Normes françaises (NF)
           - Normes européennes (EN)
           - DTU et guides techniques
           - Cahiers des charges types
           - Référentiels spécifiques
        
        5. CONTRAINTES ENVIRONNEMENTALES
           - Gestion des déchets
           - Protection de la biodiversité
           - Limitation des nuisances
           - Économie circulaire
           - Développement durable
        
        6. SIMILITUDES AVEC CHANTIERS PRÉCÉDENTS
           - Types d'ouvrages similaires
           - Techniques communes
           - Matériaux identiques
           - Contraintes comparables
           - Expériences réutilisables
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            result = json.loads(response.text)
            # Ajouter la détection de similitudes
            result["similitudes_chantiers"] = self._detect_similar_projects(content)
            return result
        except:
            return {"analyse": response.text}
    
    def analyze_ccap(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du CCAP (Cahier des Clauses Administratives Particulières)."""
        prompt = f"""
        Analyse ce CCAP et extrait les contraintes administratives de manière exhaustive :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière détaillée :
        
        1. RISQUES ET PÉNALITÉS
           - Pénalités de retard (montant, calcul)
           - Pénalités de non-conformité
           - Résiliation pour faute
           - Indemnités forfaitaires
           - Garanties de bonne fin
        
        2. DÉLAIS CRITIQUES
           - Dates de début et fin
           - Jalons intermédiaires
           - Réceptions provisoire/définitive
           - Délais de paiement
           - Délais de garantie
        
        3. OBLIGATIONS ADMINISTRATIVES
           - Plan de prévention
           - Registre de sécurité
           - Déclarations d'accident
           - Visites de chantier
           - Réunions de coordination
        
        4. CONDITIONS DE PAIEMENT
           - Acomptes et modalités
           - Retenues de garantie
           - Délais de paiement
           - Justificatifs requis
           - Conditions de déblocage
        
        5. GARANTIES ET ASSURANCES
           - Garantie de parfait achèvement
           - Garantie biennale
           - Assurance décennale
           - Responsabilité civile
           - Montants et durées
        
        6. CONTRAINTES LOGISTIQUES
           - Accès au chantier
           - Stationnement et livraisons
           - Horaires de travail
           - Nuisances sonores
           - Gestion des flux
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"analyse": response.text}
    
    def analyze_dpgf(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du DPGF (Détail Quantitatif et Estimatif)."""
        prompt = f"""
        Analyse ce DPGF et extrait les informations quantitatives de manière exhaustive :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière détaillée :
        
        1. QUANTITÉS ET ESTIMATIONS
           - Détail quantitatif par lot
           - Unités de mesure
           - Quantités estimées
           - Marges d'incertitude
           - Répartition géographique
        
        2. DÉTAIL DES PRESTATIONS
           - Description technique détaillée
           - Méthodes de réalisation
           - Matériaux et équipements
           - Main d'œuvre requise
           - Contrôles et essais
        
        3. COÛTS UNITAIRES
           - Prix unitaires HT
           - Coûts de main d'œuvre
           - Coûts de matériaux
           - Coûts d'équipements
           - Frais généraux
        
        4. RÉPARTITION DES LOTS
           - Découpage en lots
           - Montants par lot
           - Interdépendances
           - Planning par lot
           - Risques par lot
        
        5. PLANNING PRÉVISIONNEL
           - Phases de réalisation
           - Durées par phase
           - Enchaînement des tâches
           - Ressources nécessaires
           - Points critiques
        
        6. ANALYSE ÉCONOMIQUE
           - Répartition des coûts
           - Postes les plus coûteux
           - Optimisations possibles
           - Risques financiers
           - Marges bénéficiaires
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"analyse": response.text}
    
    def _detect_similar_projects(self, content: str) -> Dict[str, Any]:
        """Détecte les similitudes avec des chantiers précédents."""
        prompt = f"""
        Analyse ce contenu et identifie les similitudes avec des types de chantiers connus :
        
        CONTENU :
        {content[:2000]}
        
        Types de chantiers de référence :
        - restauration_facade : Restauration façade monument historique
        - renovation_interieur : Rénovation intérieur église  
        - consolidation_structure : Consolidation structure
        
        Identifie :
        1. Type de chantier le plus similaire
        2. Contraintes communes
        3. Techniques similaires
        4. Matériaux identiques
        5. Risques comparables
        
        Réponds au format JSON.
        """
        
        try:
            response = self.llm.complete(prompt)
            return json.loads(response.text)
        except:
            return {"similitudes": "Analyse non disponible"}
    
    def analyze_environmental_constraints(self, content: str) -> Dict[str, Any]:
        """Analyse spécialisée des contraintes environnementales."""
        prompt = f"""
        Analyse ce document et extrait toutes les contraintes environnementales :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Identifie et structure :
        
        1. GESTION DES NUISANCES
           - Nuisances sonores (horaires, niveaux)
           - Nuisances visuelles (échafaudages, bâches)
           - Nuisances olfactives (produits, déchets)
           - Vibrations (équipements, méthodes)
        
        2. PROTECTION DE LA BIODIVERSITÉ
           - Espèces protégées présentes
           - Périodes de reproduction
           - Nichoirs et habitats
           - Mesures de protection
           - Suivi écologique
        
        3. GESTION DES DÉCHETS
           - Types de déchets générés
           - Quantités estimées
           - Tri et recyclage
           - Évacuation et traitement
           - Traçabilité
        
        4. ÉCONOMIE CIRCULAIRE
           - Réutilisation de matériaux
           - Recyclage sur site
           - Approvisionnement local
           - Réduction des déchets
           - Optimisation des ressources
        
        5. DÉVELOPPEMENT DURABLE
           - Énergies renouvelables
           - Matériaux écologiques
           - Transport propre
           - Bilan carbone
           - Certifications
        
        Réponds au format JSON structuré.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"contraintes_environnementales": response.text}
    
    def analyze_logistical_constraints(self, content: str) -> Dict[str, Any]:
        """Analyse spécialisée des contraintes logistiques."""
        prompt = f"""
        Analyse ce document et extrait toutes les contraintes logistiques :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Identifie et structure :
        
        1. ACCÈS AU CHANTIER
           - Voies d'accès disponibles
           - Restrictions de circulation
           - Largeurs et hauteurs
           - Capacités de charge
           - Permis de circulation
        
        2. STATIONNEMENT ET LIVRAISONS
           - Zones de stationnement
           - Horaires de livraison
           - Espaces de manœuvre
           - Gestion des flux
           - Coordination logistique
        
        3. HORAIRES DE TRAVAIL
           - Plages horaires autorisées
           - Jours de travail
           - Pauses obligatoires
           - Travail de nuit
           - Dimanches et fêtes
        
        4. GESTION DES FLUX
           - Circulation des engins
           - Flux de matériaux
           - Évacuation des déchets
           - Accès des intervenants
           - Sécurisation des zones
        
        5. CONTRAINTES DE VOISINAGE
           - Proximité d'habitations
           - Établissements sensibles
           - Commerces et activités
           - Mesures d'apaisement
           - Communication
        
        Réponds au format JSON structuré.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"contraintes_logistiques": response.text}

class TechnicalMemoryGenerator:
    """Générateur de mémoires techniques basé sur les analyses de documents."""
    
    def __init__(self):
        self.llm = OpenAI(model=LLM_MODEL, temperature=0.4)  # Température légèrement plus élevée pour la créativité
        
        # Templates de mémoires techniques par type de chantier
        self.memory_templates = {
            "restauration_facade": {
                "sections": [
                    "Présentation de l'entreprise",
                    "Compréhension du projet",
                    "Méthodologie de travail",
                    "Organisation du chantier",
                    "Gestion des contraintes",
                    "Planning détaillé",
                    "Sécurité et environnement",
                    "Garanties et assurances"
                ]
            },
            "renovation_interieur": {
                "sections": [
                    "Présentation de l'entreprise",
                    "Analyse technique du projet",
                    "Méthodes de conservation",
                    "Organisation et planning",
                    "Gestion des contraintes d'accès",
                    "Protection des éléments existants",
                    "Contrôle qualité",
                    "Garanties"
                ]
            },
            "consolidation_structure": {
                "sections": [
                    "Présentation de l'entreprise",
                    "Diagnostic structurel",
                    "Solutions techniques proposées",
                    "Méthodes de renforcement",
                    "Organisation du chantier",
                    "Sécurité et étaiement",
                    "Contrôles et essais",
                    "Garanties décennales"
                ]
            }
        }
    
    def generate_technical_memory(self, project_analysis: Dict[str, Any], company_info: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Génère une mémoire technique complète basée sur l'analyse du projet."""
        
        # Déterminer le type de chantier
        project_type = self._identify_project_type(project_analysis)
        
        # Informations de l'entreprise par défaut
        if not company_info:
            company_info = {
                "nom": "Entreprise de Restauration du Patrimoine",
                "siret": "12345678901234",
                "adresse": "123 Rue du Patrimoine, 75001 Paris",
                "telephone": "01 23 45 67 89",
                "email": "contact@restauration-patrimoine.fr",
                "experience": "15 ans d'expérience en restauration de monuments historiques",
                "certifications": ["Qualibat 1511", "Monuments Historiques", "ISO 9001"]
            }
        
        # Générer chaque section de la mémoire
        memory_sections = {}
        
        # 1. Présentation de l'entreprise
        memory_sections["presentation_entreprise"] = self._generate_company_presentation(company_info)
        
        # 2. Compréhension du projet
        memory_sections["comprehension_projet"] = self._generate_project_understanding(project_analysis)
        
        # 3. Méthodologie de travail
        memory_sections["methodologie"] = self._generate_methodology(project_analysis, project_type)
        
        # 4. Organisation du chantier
        memory_sections["organisation_chantier"] = self._generate_site_organization(project_analysis)
        
        # 5. Gestion des contraintes
        memory_sections["gestion_contraintes"] = self._generate_constraints_management(project_analysis)
        
        # 6. Planning détaillé
        memory_sections["planning"] = self._generate_detailed_planning(project_analysis)
        
        # 7. Sécurité et environnement
        memory_sections["securite_environnement"] = self._generate_safety_environment(project_analysis)
        
        # 8. Garanties et assurances
        memory_sections["garanties"] = self._generate_guarantees(company_info)
        
        # 9. Annexes techniques
        memory_sections["annexes"] = self._generate_technical_annexes(project_analysis)
        
        return {
            "type_projet": project_type,
            "sections": memory_sections,
            "metadata": {
                "date_generation": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0",
                "nombre_sections": len(memory_sections)
            }
        }
    
    def _identify_project_type(self, project_analysis: Dict[str, Any]) -> str:
        """Identifie le type de projet basé sur l'analyse."""
        content = str(project_analysis).lower()
        
        if any(term in content for term in ["façade", "pierre", "échafaudage", "vitraux"]):
            return "restauration_facade"
        elif any(term in content for term in ["intérieur", "peinture", "conservation", "accès limité"]):
            return "renovation_interieur"
        elif any(term in content for term in ["structure", "consolidation", "renforcement", "étaiement"]):
            return "consolidation_structure"
        else:
            return "restauration_facade"  # Par défaut
    
    def _generate_company_presentation(self, company_info: Dict[str, Any]) -> str:
        """Génère la section présentation de l'entreprise."""
        prompt = f"""
        Génère une présentation professionnelle de l'entreprise pour une mémoire technique :
        
        INFORMATIONS ENTREPRISE :
        {json.dumps(company_info, indent=2, ensure_ascii=False)}
        
        Crée une présentation structurée incluant :
        - Présentation générale de l'entreprise
        - Expérience et références
        - Certifications et qualifications
        - Équipe et compétences
        - Valeurs et engagement qualité
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_project_understanding(self, project_analysis: Dict[str, Any]) -> str:
        """Génère la section compréhension du projet."""
        prompt = f"""
        Génère une section "Compréhension du projet" pour une mémoire technique :
        
        ANALYSE DU PROJET :
        {json.dumps(project_analysis, indent=2, ensure_ascii=False)}
        
        Crée une analyse structurée incluant :
        - Contexte et enjeux du projet
        - Contraintes identifiées
        - Objectifs techniques
        - Risques principaux
        - Opportunités d'optimisation
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_methodology(self, project_analysis: Dict[str, Any], project_type: str) -> str:
        """Génère la section méthodologie de travail."""
        prompt = f"""
        Génère une section "Méthodologie de travail" pour une mémoire technique :
        
        TYPE DE PROJET : {project_type}
        ANALYSE DU PROJET :
        {json.dumps(project_analysis, indent=2, ensure_ascii=False)}
        
        Crée une méthodologie structurée incluant :
        - Approche générale
        - Phases de travail détaillées
        - Techniques et matériaux
        - Contrôles qualité
        - Gestion des imprévus
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_site_organization(self, project_analysis: Dict[str, Any]) -> str:
        """Génère la section organisation du chantier."""
        prompt = f"""
        Génère une section "Organisation du chantier" pour une mémoire technique :
        
        ANALYSE DU PROJET :
        {json.dumps(project_analysis, indent=2, ensure_ascii=False)}
        
        Crée une organisation structurée incluant :
        - Équipe et responsabilités
        - Logistique et matériel
        - Coordination et communication
        - Gestion des flux
        - Sécurisation du site
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_constraints_management(self, project_analysis: Dict[str, Any]) -> str:
        """Génère la section gestion des contraintes."""
        prompt = f"""
        Génère une section "Gestion des contraintes" pour une mémoire technique :
        
        ANALYSE DU PROJET :
        {json.dumps(project_analysis, indent=2, ensure_ascii=False)}
        
        Crée une gestion des contraintes structurée incluant :
        - Contraintes techniques identifiées
        - Contraintes environnementales
        - Contraintes logistiques
        - Contraintes administratives
        - Solutions et mesures d'adaptation
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_detailed_planning(self, project_analysis: Dict[str, Any]) -> str:
        """Génère la section planning détaillé."""
        prompt = f"""
        Génère une section "Planning détaillé" pour une mémoire technique :
        
        ANALYSE DU PROJET :
        {json.dumps(project_analysis, indent=2, ensure_ascii=False)}
        
        Crée un planning structuré incluant :
        - Phases principales du chantier
        - Jalons et livrables
        - Ressources par phase
        - Délais critiques
        - Marges de sécurité
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_safety_environment(self, project_analysis: Dict[str, Any]) -> str:
        """Génère la section sécurité et environnement."""
        prompt = f"""
        Génère une section "Sécurité et environnement" pour une mémoire technique :
        
        ANALYSE DU PROJET :
        {json.dumps(project_analysis, indent=2, ensure_ascii=False)}
        
        Crée une section structurée incluant :
        - Mesures de sécurité
        - Protection de l'environnement
        - Gestion des déchets
        - Prévention des risques
        - Formation et sensibilisation
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_guarantees(self, company_info: Dict[str, Any]) -> str:
        """Génère la section garanties et assurances."""
        prompt = f"""
        Génère une section "Garanties et assurances" pour une mémoire technique :
        
        INFORMATIONS ENTREPRISE :
        {json.dumps(company_info, indent=2, ensure_ascii=False)}
        
        Crée une section structurée incluant :
        - Garanties contractuelles
        - Assurances obligatoires
        - Garantie de parfait achèvement
        - Garantie décennale
        - Engagements qualité
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def _generate_technical_annexes(self, project_analysis: Dict[str, Any]) -> str:
        """Génère les annexes techniques."""
        prompt = f"""
        Génère des "Annexes techniques" pour une mémoire technique :
        
        ANALYSE DU PROJET :
        {json.dumps(project_analysis, indent=2, ensure_ascii=False)}
        
        Crée des annexes structurées incluant :
        - Références techniques
        - Normes applicables
        - Schémas et plans
        - Fiches techniques
        - Certifications
        
        Format : Texte structuré avec paragraphes clairs.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def generate_memory_summary(self, technical_memory: Dict[str, Any]) -> str:
        """Génère un résumé exécutif de la mémoire technique."""
        prompt = f"""
        Génère un résumé exécutif de cette mémoire technique :
        
        MÉMOIRE TECHNIQUE :
        {json.dumps(technical_memory, indent=2, ensure_ascii=False)}
        
        Crée un résumé structuré incluant :
        - Points clés du projet
        - Approche proposée
        - Avantages concurrentiels
        - Engagements
        - Conclusion
        
        Format : Texte concis et professionnel.
        """
        
        response = self.llm.complete(prompt)
        return response.text
    
    def export_memory_to_markdown(self, technical_memory: Dict[str, Any]) -> str:
        """Exporte la mémoire technique au format Markdown."""
        markdown_content = f"""# Mémoire Technique - {technical_memory.get('type_projet', 'Projet de restauration').replace('_', ' ').title()}

*Générée le {technical_memory.get('metadata', {}).get('date_generation', 'Date inconnue')}*

---

## 1. Présentation de l'entreprise

{technical_memory.get('sections', {}).get('presentation_entreprise', 'Section non disponible')}

---

## 2. Compréhension du projet

{technical_memory.get('sections', {}).get('comprehension_projet', 'Section non disponible')}

---

## 3. Méthodologie de travail

{technical_memory.get('sections', {}).get('methodologie', 'Section non disponible')}

---

## 4. Organisation du chantier

{technical_memory.get('sections', {}).get('organisation_chantier', 'Section non disponible')}

---

## 5. Gestion des contraintes

{technical_memory.get('sections', {}).get('gestion_contraintes', 'Section non disponible')}

---

## 6. Planning détaillé

{technical_memory.get('sections', {}).get('planning', 'Section non disponible')}

---

## 7. Sécurité et environnement

{technical_memory.get('sections', {}).get('securite_environnement', 'Section non disponible')}

---

## 8. Garanties et assurances

{technical_memory.get('sections', {}).get('garanties', 'Section non disponible')}

---

## 9. Annexes techniques

{technical_memory.get('sections', {}).get('annexes', 'Section non disponible')}

---

*Mémoire technique générée automatiquement par l'IA Multi-Agents*
"""
        return markdown_content
    
    def analyze_reglement(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du règlement de consultation."""
        prompt = f"""
        Analyse ce règlement de consultation et extrait les informations clés de manière détaillée :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière exhaustive :
        
        1. CRITÈRES DE SÉLECTION ET D'ATTRIBUTION
           - Critères techniques (pourcentage, poids)
           - Critères financiers (pourcentage, poids)
           - Critères d'expérience (pourcentage, poids)
           - Critères de capacité (pourcentage, poids)
           - Méthode de notation et de classement
        
        2. DÉLAIS IMPORTANTS
           - Date limite de dépôt des offres
           - Date d'ouverture des plis
           - Durée du chantier (début/fin)
           - Délais de réception provisoire/définitive
           - Périodes critiques à identifier
        
        3. MODALITÉS ADMINISTRATIVES
           - Garanties requises (pourcentage, montant)
           - Assurances obligatoires (types, montants)
           - Cautionnement (pourcentage, montant)
           - Conditions de paiement
           - Modalités de réception
        
        4. CONDITIONS PARTICULIÈRES
           - Contraintes spécifiques au site
           - Conditions d'accès au chantier
           - Contraintes environnementales
           - Contraintes de voisinage
           - Conditions météorologiques
        
        5. DOCUMENTS REQUIS
           - Attestations obligatoires
           - Justificatifs d'expérience
           - Plans et documents techniques
           - Mémoire technique (contenu requis)
           - Planning détaillé
        
        6. RISQUES IDENTIFIÉS
           - Risques techniques majeurs
           - Risques administratifs
           - Risques financiers
           - Risques de délais
           - Pénalités applicables
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"analyse": response.text}
    
    def analyze_cctp(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du CCTP (Cahier des Clauses Techniques Particulières)."""
        prompt = f"""
        Analyse ce CCTP et extrait les exigences techniques de manière exhaustive :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière détaillée :
        
        1. EXIGENCES TECHNIQUES PRÉCISES
           - Spécifications techniques détaillées
           - Normes et références applicables
           - Classes de résistance et caractéristiques
           - Contrôles et essais requis
           - Tolérances et marges acceptables
        
        2. MATÉRIAUX ET MÉTHODES REQUIS
           - Types de matériaux spécifiés
           - Origines et qualités requises
           - Méthodes de mise en œuvre
           - Équipements et outils nécessaires
           - Conditions de stockage et transport
        
        3. CONTRAINTES SPÉCIFIQUES
           - Contraintes de mise en œuvre
           - Contraintes de sécurité
           - Contraintes de qualité
           - Contraintes de délais
           - Contraintes d'environnement
        
        4. NORMES ET RÉFÉRENCES TECHNIQUES
           - Normes françaises (NF)
           - Normes européennes (EN)
           - DTU et guides techniques
           - Cahiers des charges types
           - Référentiels spécifiques
        
        5. CONTRAINTES ENVIRONNEMENTALES
           - Gestion des déchets
           - Protection de la biodiversité
           - Limitation des nuisances
           - Économie circulaire
           - Développement durable
        
        6. SIMILITUDES AVEC CHANTIERS PRÉCÉDENTS
           - Types d'ouvrages similaires
           - Techniques communes
           - Matériaux identiques
           - Contraintes comparables
           - Expériences réutilisables
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            result = json.loads(response.text)
            # Ajouter la détection de similitudes
            result["similitudes_chantiers"] = self._detect_similar_projects(content)
            return result
        except:
            return {"analyse": response.text}
    
    def analyze_ccap(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du CCAP (Cahier des Clauses Administratives Particulières)."""
        prompt = f"""
        Analyse ce CCAP et extrait les contraintes administratives de manière exhaustive :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière détaillée :
        
        1. RISQUES ET PÉNALITÉS
           - Pénalités de retard (montant, calcul)
           - Pénalités de non-conformité
           - Résiliation pour faute
           - Indemnités forfaitaires
           - Garanties de bonne fin
        
        2. DÉLAIS CRITIQUES
           - Dates de début et fin
           - Jalons intermédiaires
           - Réceptions provisoire/définitive
           - Délais de paiement
           - Délais de garantie
        
        3. OBLIGATIONS ADMINISTRATIVES
           - Plan de prévention
           - Registre de sécurité
           - Déclarations d'accident
           - Visites de chantier
           - Réunions de coordination
        
        4. CONDITIONS DE PAIEMENT
           - Acomptes et modalités
           - Retenues de garantie
           - Délais de paiement
           - Justificatifs requis
           - Conditions de déblocage
        
        5. GARANTIES ET ASSURANCES
           - Garantie de parfait achèvement
           - Garantie biennale
           - Assurance décennale
           - Responsabilité civile
           - Montants et durées
        
        6. CONTRAINTES LOGISTIQUES
           - Accès au chantier
           - Stationnement et livraisons
           - Horaires de travail
           - Nuisances sonores
           - Gestion des flux
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"analyse": response.text}
    
    def analyze_dpgf(self, content: str) -> Dict[str, Any]:
        """Analyse avancée du DPGF (Détail Quantitatif et Estimatif)."""
        prompt = f"""
        Analyse ce DPGF et extrait les informations quantitatives de manière exhaustive :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Extrais et structure les informations suivantes de manière détaillée :
        
        1. QUANTITÉS ET ESTIMATIONS
           - Détail quantitatif par lot
           - Unités de mesure
           - Quantités estimées
           - Marges d'incertitude
           - Répartition géographique
        
        2. DÉTAIL DES PRESTATIONS
           - Description technique détaillée
           - Méthodes de réalisation
           - Matériaux et équipements
           - Main d'œuvre requise
           - Contrôles et essais
        
        3. COÛTS UNITAIRES
           - Prix unitaires HT
           - Coûts de main d'œuvre
           - Coûts de matériaux
           - Coûts d'équipements
           - Frais généraux
        
        4. RÉPARTITION DES LOTS
           - Découpage en lots
           - Montants par lot
           - Interdépendances
           - Planning par lot
           - Risques par lot
        
        5. PLANNING PRÉVISIONNEL
           - Phases de réalisation
           - Durées par phase
           - Enchaînement des tâches
           - Ressources nécessaires
           - Points critiques
        
        6. ANALYSE ÉCONOMIQUE
           - Répartition des coûts
           - Postes les plus coûteux
           - Optimisations possibles
           - Risques financiers
           - Marges bénéficiaires
        
        Réponds au format JSON structuré avec des sous-sections détaillées.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"analyse": response.text}
    
    def _detect_similar_projects(self, content: str) -> Dict[str, Any]:
        """Détecte les similitudes avec des chantiers précédents."""
        prompt = f"""
        Analyse ce contenu et identifie les similitudes avec des types de chantiers connus :
        
        CONTENU :
        {content[:2000]}
        
        Types de chantiers de référence :
        - restauration_facade : Restauration façade monument historique
        - renovation_interieur : Rénovation intérieur église  
        - consolidation_structure : Consolidation structure
        
        Identifie :
        1. Type de chantier le plus similaire
        2. Contraintes communes
        3. Techniques similaires
        4. Matériaux identiques
        5. Risques comparables
        
        Réponds au format JSON.
        """
        
        try:
            response = self.llm.complete(prompt)
            return json.loads(response.text)
        except:
            return {"similitudes": "Analyse non disponible"}
    
    def analyze_environmental_constraints(self, content: str) -> Dict[str, Any]:
        """Analyse spécialisée des contraintes environnementales."""
        prompt = f"""
        Analyse ce document et extrait toutes les contraintes environnementales :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Identifie et structure :
        
        1. GESTION DES NUISANCES
           - Nuisances sonores (horaires, niveaux)
           - Nuisances visuelles (échafaudages, bâches)
           - Nuisances olfactives (produits, déchets)
           - Vibrations (équipements, méthodes)
        
        2. PROTECTION DE LA BIODIVERSITÉ
           - Espèces protégées présentes
           - Périodes de reproduction
           - Nichoirs et habitats
           - Mesures de protection
           - Suivi écologique
        
        3. GESTION DES DÉCHETS
           - Types de déchets générés
           - Quantités estimées
           - Tri et recyclage
           - Évacuation et traitement
           - Traçabilité
        
        4. ÉCONOMIE CIRCULAIRE
           - Réutilisation de matériaux
           - Recyclage sur site
           - Approvisionnement local
           - Réduction des déchets
           - Optimisation des ressources
        
        5. DÉVELOPPEMENT DURABLE
           - Énergies renouvelables
           - Matériaux écologiques
           - Transport propre
           - Bilan carbone
           - Certifications
        
        Réponds au format JSON structuré.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"contraintes_environnementales": response.text}
    
    def analyze_logistical_constraints(self, content: str) -> Dict[str, Any]:
        """Analyse spécialisée des contraintes logistiques."""
        prompt = f"""
        Analyse ce document et extrait toutes les contraintes logistiques :
        
        CONTENU :
        {content[:MAX_TOKENS_PER_REQUEST]}
        
        Identifie et structure :
        
        1. ACCÈS AU CHANTIER
           - Voies d'accès disponibles
           - Restrictions de circulation
           - Largeurs et hauteurs
           - Capacités de charge
           - Permis de circulation
        
        2. STATIONNEMENT ET LIVRAISONS
           - Zones de stationnement
           - Horaires de livraison
           - Espaces de manœuvre
           - Gestion des flux
           - Coordination logistique
        
        3. HORAIRES DE TRAVAIL
           - Plages horaires autorisées
           - Jours de travail
           - Pauses obligatoires
           - Travail de nuit
           - Dimanches et fêtes
        
        4. GESTION DES FLUX
           - Circulation des engins
           - Flux de matériaux
           - Évacuation des déchets
           - Accès des intervenants
           - Sécurisation des zones
        
        5. CONTRAINTES DE VOISINAGE
           - Proximité d'habitations
           - Établissements sensibles
           - Commerces et activités
           - Mesures d'apaisement
           - Communication
        
        Réponds au format JSON structuré.
        """
        
        response = self.llm.complete(prompt)
        try:
            return json.loads(response.text)
        except:
            return {"contraintes_logistiques": response.text}

# ---------------------- LlamaIndex Helpers --------------------

def build_advanced_index(run_id: str, files) -> tuple:
    """Ingeste les fichiers, les classe, analyse et crée l'index multi-agents."""
    
    # 1. Sauvegarde des fichiers
    tmp_dir = DATA_DIR / run_id
    tmp_dir.mkdir(exist_ok=True)
    
    documents_info = []
    analyzer = DocumentAnalyzer()
    
    # 2. Traitement de chaque fichier
    for f in files:
        dest = tmp_dir / f.name
        with open(dest, "wb") as out:
            out.write(f.getvalue())
        
        # Extraction du contenu
        content = extract_document_content(dest)
        
        # Classification
        doc_type = classify_document(f.name, content)
        
        # Analyse spécialisée selon le type
        analysis = {}
        if doc_type == DocumentType.REGLEMENT:
            analysis = analyzer.analyze_reglement(content)
        elif doc_type == DocumentType.CCTP:
            analysis = analyzer.analyze_cctp(content)
            # Ajouter analyse environnementale pour les documents techniques
            env_analysis = analyzer.analyze_environmental_constraints(content)
            analysis["contraintes_environnementales"] = env_analysis
        elif doc_type == DocumentType.CCAP:
            analysis = analyzer.analyze_ccap(content)
            # Ajouter analyse logistique pour les documents administratifs
            log_analysis = analyzer.analyze_logistical_constraints(content)
            analysis["contraintes_logistiques"] = log_analysis
        elif doc_type == DocumentType.DPGF:
            analysis = analyzer.analyze_dpgf(content)
        
        # Analyse environnementale et logistique pour tous les documents
        if not analysis.get("contraintes_environnementales"):
            env_analysis = analyzer.analyze_environmental_constraints(content)
            analysis["contraintes_environnementales"] = env_analysis
        
        if not analysis.get("contraintes_logistiques"):
            log_analysis = analyzer.analyze_logistical_constraints(content)
            analysis["contraintes_logistiques"] = log_analysis
        
        # Création du document structuré
        doc_info = DocumentInfo(
            name=f.name,
            type=doc_type,
            content=content,
            metadata={
                "type": doc_type.value,
                "file_size": len(content)
            }
        )
        # Ajouter l'analyse comme attribut séparé
        doc_info.analysis = analysis
        documents_info.append(doc_info)
    
    # 3. Configuration LlamaIndex
    token_handler = TokenCountingHandler()
    cb_manager = CallbackManager([token_handler])
    
    Settings.llm = OpenAI(model=LLM_MODEL, temperature=TEMPERATURE)
    Settings.embed_model = OpenAIEmbedding(model=EMBEDDING_MODEL)
    Settings.node_parser = SentenceSplitter(chunk_size=2048, chunk_overlap=256)
    Settings.callback_manager = cb_manager
    
    # 4. Création des documents LlamaIndex
    llama_docs = []
    analyses_storage = {}  # Stockage séparé des analyses
    
    for doc_info in documents_info:
        # Créer le document LlamaIndex sans les analyses dans les métadonnées
        doc = Document(
            text=doc_info.content,
            metadata=doc_info.metadata
        )
        llama_docs.append(doc)
        
        # Stocker l'analyse séparément
        if hasattr(doc_info, 'analysis'):
            analyses_storage[doc_info.name] = doc_info.analysis
    
    # 5. Stockage Chroma persistant
    persist_dir = VECTOR_DIR / run_id
    import chromadb
    chroma_client = chromadb.PersistentClient(path=str(persist_dir))
    vector_store = ChromaVectorStore(chroma_collection=chroma_client.get_or_create_collection("documents"))
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    index = VectorStoreIndex.from_documents(
        llama_docs, storage_context=storage_context
    )
    
    index.storage_context.persist(persist_dir=str(persist_dir))
    
    # 6. Génération du résumé global
    synth = get_response_synthesizer()
    summary_parts = []
    for doc_info in documents_info:
        if doc_info.analysis:
            summary_parts.append(f"**{doc_info.type.value}** : {str(doc_info.analysis)}")
    
    global_summary = synth.get_response("", summary_parts) if summary_parts else "Aucune analyse disponible"
    
    # 7. Sauvegarde des analyses
    with open(persist_dir / "analyses.json", "w", encoding="utf-8") as f:
        json.dump([{
            "name": doc.name,
            "type": doc.type.value,
            "analysis": doc.analysis if doc.analysis else {}
        } for doc in documents_info], f, indent=2, ensure_ascii=False)
    
    with open(persist_dir / "global_summary.txt", "w", encoding="utf-8") as f:
        f.write(str(global_summary))
    
    # 8. Génération de synthèses croisées et recommandations
    cross_analysis = generate_cross_analysis(documents_info, analyzer)
    
    # 9. Sauvegarde de l'analyse croisée
    with open(persist_dir / "cross_analysis.json", "w", encoding="utf-8") as f:
        json.dump(cross_analysis, f, indent=2, ensure_ascii=False)
    
    # 10. Génération et sauvegarde de la mémoire technique
    memory_generator = TechnicalMemoryGenerator()
    technical_memory = memory_generator.generate_technical_memory(cross_analysis)
    
    with open(persist_dir / "technical_memory.json", "w", encoding="utf-8") as f:
        json.dump(technical_memory, f, indent=2, ensure_ascii=False)
    
    return index, str(global_summary), token_handler.total_llm_token_count, documents_info, cross_analysis, technical_memory

def load_advanced_index(run_id: str):
    """Charge un index existant avec ses analyses."""
    persist_dir = VECTOR_DIR / run_id
    if not persist_dir.exists():
        return None, None
    
    # Chargement de l'index
    import chromadb
    chroma_client = chromadb.PersistentClient(path=str(persist_dir))
    vector_store = ChromaVectorStore(chroma_collection=chroma_client.get_or_create_collection("documents"))
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store, storage_context)
    
    # Chargement des analyses
    analyses_file = persist_dir / "analyses.json"
    analyses = []
    if analyses_file.exists():
        with open(analyses_file, "r", encoding="utf-8") as f:
            analyses = json.load(f)
    
    # Désérialiser les analyses JSON dans les métadonnées
    for analysis in analyses:
        if analysis.get('analysis') and isinstance(analysis['analysis'], str):
            try:
                analysis['analysis'] = json.loads(analysis['analysis'])
            except json.JSONDecodeError:
                analysis['analysis'] = {}
    
    return index, analyses

def display_analysis_section(section_name, section_content):
    """Affiche une section d'analyse de manière formatée."""
    st.markdown(f"### {section_name}")
    
    if isinstance(section_content, dict):
        # Afficher les sous-sections
        for subsection_name, subsection_content in section_content.items():
            if isinstance(subsection_content, dict):
                st.markdown(f"**{subsection_name}**")
                st.json(subsection_content)
            elif isinstance(subsection_content, list):
                st.markdown(f"**{subsection_name}**")
                for item in subsection_content:
                    st.markdown(f"- {item}")
            else:
                st.markdown(f"**{subsection_name}**: {subsection_content}")
    elif isinstance(section_content, list):
        for item in section_content:
            st.markdown(f"- {item}")
    else:
        st.markdown(f"{section_content}")
    
    st.markdown("---")

def generate_cross_analysis(documents_info: List[DocumentInfo], analyzer: DocumentAnalyzer) -> Dict[str, Any]:
    """Génère une analyse croisée et des recommandations basées sur tous les documents."""
    
    # Collecter toutes les analyses
    all_analyses = {}
    for doc_info in documents_info:
        if doc_info.analysis:
            all_analyses[doc_info.type.value] = doc_info.analysis
    
    # Générer des recommandations croisées
    recommendations_prompt = f"""
    Basé sur les analyses suivantes de documents d'appel d'offres, génère des recommandations stratégiques :
    
    ANALYSES :
    {json.dumps(all_analyses, indent=2, ensure_ascii=False)}
    
    Génère des recommandations dans les domaines suivants :
    
    1. STRATÉGIE DE RÉPONSE
       - Points forts à mettre en avant
       - Risques à anticiper
       - Opportunités à saisir
       - Stratégie de prix
    
    2. PLANNING ET RESSOURCES
       - Délais critiques à respecter
       - Ressources humaines nécessaires
       - Matériaux et équipements
       - Sous-traitants potentiels
    
    3. GESTION DES RISQUES
       - Risques techniques identifiés
       - Risques administratifs
       - Risques financiers
       - Mesures de mitigation
    
    4. OPTIMISATIONS POSSIBLES
       - Réduction des coûts
       - Amélioration des délais
       - Optimisation des ressources
       - Innovations techniques
    
    5. SIMILITUDES AVEC EXPÉRIENCES PASSÉES
       - Chantiers similaires réalisés
       - Techniques éprouvées
       - Retours d'expérience
       - Améliorations possibles
    
    Réponds au format JSON structuré.
    """
    
    try:
        response = analyzer.llm.complete(recommendations_prompt)
        recommendations = json.loads(response.text)
    except:
        recommendations = {"recommandations": "Analyse non disponible"}
    
    # Générer une synthèse des contraintes
    constraints_summary = {
        "contraintes_environnementales": {},
        "contraintes_logistiques": {},
        "contraintes_techniques": {},
        "contraintes_administratives": {}
    }
    
    for doc_type, analysis in all_analyses.items():
        if isinstance(analysis, dict):
            # Contraintes environnementales
            if "contraintes_environnementales" in analysis:
                constraints_summary["contraintes_environnementales"][doc_type] = analysis["contraintes_environnementales"]
            
            # Contraintes logistiques
            if "contraintes_logistiques" in analysis:
                constraints_summary["contraintes_logistiques"][doc_type] = analysis["contraintes_logistiques"]
            
            # Contraintes techniques (CCTP)
            if doc_type == "Cahier des Clauses Techniques Particulières":
                constraints_summary["contraintes_techniques"] = analysis
            
            # Contraintes administratives (CCAP)
            if doc_type == "Cahier des Clauses Administratives Particulières":
                constraints_summary["contraintes_administratives"] = analysis
    
    return {
        "recommandations_strategiques": recommendations,
        "synthese_contraintes": constraints_summary,
        "documents_analyses": len(documents_info),
        "types_documents": [doc.type.value for doc in documents_info]
    }

def generate_technical_memory_from_analysis(cross_analysis: Dict[str, Any], company_info: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Génère une mémoire technique basée sur l'analyse croisée."""
    
    if not company_info:
        company_info = {
            "nom": "Entreprise de Restauration du Patrimoine",
            "siret": "12345678901234",
            "adresse": "123 Rue du Patrimoine, 75001 Paris",
            "telephone": "01 23 45 67 89",
            "email": "contact@restauration-patrimoine.fr",
            "experience": "15 ans d'expérience en restauration de monuments historiques",
            "certifications": ["Qualibat 1511", "Monuments Historiques", "ISO 9001"]
        }
    
    memory_generator = TechnicalMemoryGenerator()
    technical_memory = memory_generator.generate_technical_memory(cross_analysis, company_info)
    
    return technical_memory

# --------------------------- Streamlit UI ---------------------

st.set_page_config("Analyse AO – Multi-Agents", layout="wide")
st.title("📑 Analyse d'appels d'offres – IA Multi-Agents")

# Session state init
if "run_id" not in st.session_state:
    st.session_state.run_id = None
if "index" not in st.session_state:
    st.session_state.index = None
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "history" not in st.session_state:
    st.session_state.history = []
if "analyses" not in st.session_state:
    st.session_state.analyses = []
if "cross_analysis" not in st.session_state:
    st.session_state.cross_analysis = None
if "technical_memory" not in st.session_state:
    st.session_state.technical_memory = None

# 1️⃣ Upload + ingestion avancée
uploaded_files = st.file_uploader(
    "Dépose tes fichiers d'appel d'offres (PDF, DOCX, XLSX…) :", 
    accept_multiple_files=True
)

if uploaded_files and st.button("🚀 Lancer l'analyse multi-agents"):
    with st.spinner("Analyse en cours avec les agents spécialisés…"):
        run_id = uuid.uuid4().hex[:8]
        index, summary, tokens, documents_info, cross_analysis, technical_memory = build_advanced_index(run_id, uploaded_files)
        
        st.session_state.run_id = run_id
        st.session_state.index = index
        st.session_state.chat_engine = index.as_chat_engine()
        st.session_state.analyses = [{
            "name": doc.name,
            "type": doc.type.value,
            "analysis": doc.analysis if doc.analysis else {}
        } for doc in documents_info]
        st.session_state.cross_analysis = cross_analysis
        st.session_state.technical_memory = technical_memory
        
        st.success(f"✅ Analyse terminée ! Tokens LLM : {tokens}")
        
        # Affichage des résultats par type de document
        st.subheader("📊 Résultats de l'analyse par document")
        
        # Ordre logique des documents
        document_order = [
            DocumentType.REGLEMENT,
            DocumentType.CCTP,
            DocumentType.CCAP,
            DocumentType.DPGF
        ]
        
        # Trier les documents selon l'ordre logique
        sorted_documents = []
        for doc_type in document_order:
            for doc_info in documents_info:
                if doc_info.type == doc_type:
                    sorted_documents.append(doc_info)
        
        # Afficher les documents dans l'ordre
        for doc_info in sorted_documents:
            with st.expander(f"📄 {doc_info.name} ({doc_info.type.value})"):
                if doc_info.analysis:
                    # Formater proprement l'analyse
                    if isinstance(doc_info.analysis, dict):
                        # Afficher chaque section de l'analyse séparément
                        for section_name, section_content in doc_info.analysis.items():
                            display_analysis_section(section_name, section_content)
                    else:
                        st.json(doc_info.analysis)
                else:
                    st.info("Document traité mais pas d'analyse spécialisée disponible")
        
        st.session_state.history.append({"role": "assistant", "content": summary})
        
        # Affichage des analyses croisées
        if cross_analysis:
            st.subheader("🎯 Recommandations stratégiques")
            with st.expander("📊 Analyse croisée et recommandations"):
                recommendations = cross_analysis.get("recommandations_strategiques", {})
                if isinstance(recommendations, dict):
                    for section_name, section_content in recommendations.items():
                        display_analysis_section(section_name, section_content)
                else:
                    st.json(recommendations)
            
            st.subheader("🔍 Synthèse des contraintes")
            col1, col2 = st.columns(2)
            
            with col1:
                with st.expander("🌱 Contraintes environnementales"):
                    st.json(cross_analysis["synthese_contraintes"]["contraintes_environnementales"])
                
                with st.expander("🚚 Contraintes logistiques"):
                    st.json(cross_analysis["synthese_contraintes"]["contraintes_logistiques"])
            
            with col2:
                with st.expander("🔧 Contraintes techniques"):
                    st.json(cross_analysis["synthese_contraintes"]["contraintes_techniques"])
                
                with st.expander("📋 Contraintes administratives"):
                    st.json(cross_analysis["synthese_contraintes"]["contraintes_administratives"])
        
        st.write("**Résumé global :**")
        st.write(summary)
        
        # Phase 3 : Génération de mémoire technique
        st.subheader("📋 Phase 3 - Génération de Mémoire Technique")
        
        # Configuration de l'entreprise
        with st.expander("🏢 Configuration de l'entreprise"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Nom de l'entreprise", "Entreprise de Restauration du Patrimoine")
                company_siret = st.text_input("SIRET", "12345678901234")
                company_address = st.text_input("Adresse", "123 Rue du Patrimoine, 75001 Paris")
                company_phone = st.text_input("Téléphone", "01 23 45 67 89")
            
            with col2:
                company_email = st.text_input("Email", "contact@restauration-patrimoine.fr")
                company_experience = st.text_input("Expérience", "15 ans d'expérience en restauration de monuments historiques")
                company_certifications = st.text_area("Certifications", "Qualibat 1511\nMonuments Historiques\nISO 9001")
        
        # Bouton de génération de mémoire technique
        if st.button("📄 Générer la mémoire technique"):
            with st.spinner("Génération de la mémoire technique en cours..."):
                company_info = {
                    "nom": company_name,
                    "siret": company_siret,
                    "adresse": company_address,
                    "telephone": company_phone,
                    "email": company_email,
                    "experience": company_experience,
                    "certifications": company_certifications.split('\n') if company_certifications else []
                }
                
                technical_memory = generate_technical_memory_from_analysis(cross_analysis, company_info)
                st.session_state.technical_memory = technical_memory
                
                st.success("✅ Mémoire technique générée avec succès !")
                
                # Affichage de la mémoire technique
                st.subheader("📋 Mémoire Technique Générée")
                
                # Résumé exécutif
                memory_generator = TechnicalMemoryGenerator()
                summary = memory_generator.generate_memory_summary(technical_memory)
                
                with st.expander("📊 Résumé exécutif"):
                    st.markdown(summary)
                
                # Sections détaillées
                for section_name, section_content in technical_memory.get("sections", {}).items():
                    section_title = section_name.replace("_", " ").title()
                    with st.expander(f"📄 {section_title}"):
                        st.markdown(section_content)
                
                # Export Markdown
                markdown_content = memory_generator.export_memory_to_markdown(technical_memory)
                
                st.download_button(
                    label="📥 Télécharger la mémoire technique (Markdown)",
                    data=markdown_content,
                    file_name=f"memoire_technique_{st.session_state.run_id}.md",
                    mime="text/markdown"
                )

# 2️⃣ Chargement d'une session précédente
with st.sidebar:
    st.header("Sessions précédentes")
    runs = [p.name for p in VECTOR_DIR.iterdir() if p.is_dir()]
    sel = st.selectbox("Ré-ouvrir un run :", ["-"] + runs)
    if sel != "-" and sel != st.session_state.get("run_id"):
        index, analyses = load_advanced_index(sel)
        if index:
            st.session_state.index = index
            st.session_state.chat_engine = index.as_chat_engine()
            st.session_state.run_id = sel
            st.session_state.analyses = analyses
            st.session_state.history.append({
                "role": "assistant",
                "content": f"Session {sel} rechargée avec {len(analyses) if analyses else 0} documents analysés. Pose ta question !"
            })
            
            # Charger la mémoire technique si elle existe
            persist_dir = VECTOR_DIR / sel
            memory_file = persist_dir / "technical_memory.json"
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    st.session_state.technical_memory = json.load(f)

# 3️⃣ Affichage des analyses en cours
if st.session_state.analyses:
    st.subheader("📋 Documents analysés")
    for analysis in st.session_state.analyses:
        with st.expander(f"📄 {analysis['name']} ({analysis['type']})"):
            if analysis.get('analysis'):
                st.json(analysis['analysis'])
            else:
                st.info("Aucune analyse disponible")

# 4️⃣ Affichage de la mémoire technique existante
if st.session_state.technical_memory:
    st.subheader("📋 Mémoire Technique Générée")
    
    # Résumé exécutif
    memory_generator = TechnicalMemoryGenerator()
    summary = memory_generator.generate_memory_summary(st.session_state.technical_memory)
    
    with st.expander("📊 Résumé exécutif"):
        st.markdown(summary)
    
    # Sections détaillées
    for section_name, section_content in st.session_state.technical_memory.get("sections", {}).items():
        section_title = section_name.replace("_", " ").title()
        with st.expander(f"📄 {section_title}"):
            st.markdown(section_content)
    
    # Export Markdown
    markdown_content = memory_generator.export_memory_to_markdown(st.session_state.technical_memory)
    
    st.download_button(
        label="📥 Télécharger la mémoire technique (Markdown)",
        data=markdown_content,
        file_name=f"memoire_technique_{st.session_state.run_id}.md",
        mime="text/markdown"
    )

# 4️⃣ Zone de chat améliorée
if st.session_state.chat_engine:
    st.subheader("💬 Chat avec l'agent d'analyse")
    
    for h in st.session_state.history:
        avatar = "🧑‍💼" if h["role"] == "user" else "🤖"
        st.chat_message(avatar).markdown(h["content"])

    if q := st.chat_input("Pose ta question sur l'appel d'offres…"):
        st.session_state.history.append({"role": "user", "content": q})
        st.chat_message("🧑‍💼").markdown(q)
        with st.chat_message("🤖"):
            try:
                answer = st.session_state.chat_engine.chat(q)
                st.markdown(answer)
                st.session_state.history.append({"role": "assistant", "content": str(answer)})
            except Exception as e:
                error_msg = f"Erreur lors de la génération de la réponse : {str(e)}"
                st.error(error_msg)
                st.session_state.history.append({"role": "assistant", "content": error_msg})
else:
    st.info("➡️  Ajoute des fichiers puis lance l'analyse multi-agents pour activer le chat intelligent.")
