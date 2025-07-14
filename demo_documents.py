#!/usr/bin/env python3
"""
Générateur de Documents de Démonstration
----------------------------------------
Crée des fichiers d'exemple pour tester l'application d'analyse d'appels d'offres.
"""

import json
from pathlib import Path

def create_demo_reglement():
    """Crée un règlement de consultation de démonstration."""
    content = """
RÈGLEMENT DE CONSULTATION
Appel d'offres pour la restauration de la façade de l'église Saint-Pierre

Article 1 - Objet de la consultation
La présente consultation a pour objet la restauration complète de la façade 
principale de l'église Saint-Pierre, classée Monument Historique.

Article 2 - Critères de sélection
Les critères de sélection sont les suivants :
- Expérience dans la restauration de monuments historiques (40%)
- Capacité technique et références (30%)
- Prix de l'offre (30%)

Article 3 - Délais
- Date limite de dépôt des offres : 15 mars 2024 à 12h00
- Durée du chantier : 6 mois maximum
- Réception provisoire : 30 septembre 2024

Article 4 - Modalités administratives
- Garantie : 5% du montant HT
- Assurance décennale obligatoire
- Cautionnement : 3% du montant HT

Article 5 - Documents requis
- Attestation d'assurance décennale
- Justificatifs d'expérience
- Plan de charge détaillé
- Mémoire technique
"""
    return content

def create_demo_cctp():
    """Crée un CCTP de démonstration."""
    content = """
CAHIER DES CLAUSES TECHNIQUES PARTICULIÈRES
Restauration façade église Saint-Pierre

1. EXIGENCES TECHNIQUES

1.1 Matériaux
- Pierre de taille : Pierre de Bourgogne ou équivalent
- Mortier : Chaux hydraulique NHL 3.5
- Joints : 15 mm maximum
- Ancrages : Acier inoxydable A4

1.2 Méthodes de travail
- Démontage pierre par pierre avec numérotation
- Nettoyage par micro-gommage
- Remplacement des pierres dégradées
- Reprise des joints à la chaux
- Protection hydrofuge compatible

1.3 Contraintes spécifiques
- Respect des techniques traditionnelles
- Pas d'utilisation de ciment
- Protection des vitraux existants
- Accès limité par échafaudage

2. NORMES ET RÉFÉRENCES
- DTU 20.1 - Maçonnerie de pierre
- Norme NF EN 998-2 - Mortiers de maçonnerie
- Guide de bonnes pratiques - Restauration MH

3. CONTRAINTES ENVIRONNEMENTALES
- Gestion des poussières
- Protection de la biodiversité (nichoirs)
- Tri et recyclage des déchets
- Limitation des nuisances sonores
"""
    return content

def create_demo_ccap():
    """Crée un CCAP de démonstration."""
    content = """
CAHIER DES CLAUSES ADMINISTRATIVES PARTICULIÈRES

1. RISQUES ET PÉNALITÉS

1.1 Retards
- Pénalité de retard : 1/1000 du montant HT par jour
- Résiliation automatique après 30 jours de retard
- Indemnité forfaitaire : 10% du montant HT

1.2 Non-conformités
- Refus de réception en cas de non-respect des normes
- Mise en demeure avec délai de 8 jours
- Résiliation pour faute après 2 mises en demeure

2. DÉLAIS CRITIQUES
- Début des travaux : 1er avril 2024
- Achèvement : 30 septembre 2024
- Réception provisoire : 15 octobre 2024
- Réception définitive : 15 avril 2025

3. OBLIGATIONS ADMINISTRATIVES
- Plan de prévention obligatoire
- Registre de sécurité
- Déclaration d'accident dans les 24h
- Visites de chantier hebdomadaires

4. CONDITIONS DE PAIEMENT
- Acompte à la commande : 20%
- Acomptes mensuels : 70%
- Retenue de garantie : 10%
- Paiement sous 30 jours

5. GARANTIES ET ASSURANCES
- Garantie de parfait achèvement : 1 an
- Garantie biennale : 2 ans
- Assurance décennale : 10 ans
- Responsabilité civile : 2M€ minimum
"""
    return content

def create_demo_dpgf():
    """Crée un DPGF de démonstration."""
    content = """
DÉTAIL QUANTITATIF ET ESTIMATIF

LOT 1 - MAÇONNERIE DE PIERRE

| N° | Désignation | Unité | Qté | PU HT | Montant HT |
|----|-------------|-------|-----|-------|------------|
| 1.1 | Démontage pierres existantes | m² | 150 | 45,00 € | 6 750,00 € |
| 1.2 | Nettoyage par micro-gommage | m² | 150 | 25,00 € | 3 750,00 € |
| 1.3 | Remplacement pierres dégradées | m² | 25 | 180,00 € | 4 500,00 € |
| 1.4 | Reprise joints à la chaux | m² | 150 | 35,00 € | 5 250,00 € |
| 1.5 | Protection hydrofuge | m² | 150 | 15,00 € | 2 250,00 € |

LOT 2 - ÉCHAFAUDAGE ET PROTECTION

| N° | Désignation | Unité | Qté | PU HT | Montant HT |
|----|-------------|-------|-----|-------|------------|
| 2.1 | Échafaudage façade | m² | 200 | 12,00 € | 2 400,00 € |
| 2.2 | Protection vitraux | m² | 50 | 8,00 € | 400,00 € |
| 2.3 | Bâches de protection | m² | 200 | 5,00 € | 1 000,00 € |

TOTAL HT : 26 300,00 €
TVA 20% : 5 260,00 €
TOTAL TTC : 31 560,00 €

PLANNING PRÉVISIONNEL
- Semaine 1-2 : Installation échafaudage
- Semaine 3-8 : Démontage et nettoyage
- Semaine 9-16 : Remplacement pierres
- Semaine 17-20 : Reprise joints
- Semaine 21-22 : Protection hydrofuge
- Semaine 23-24 : Démontage échafaudage
"""
    return content

def create_demo_files():
    """Crée tous les fichiers de démonstration."""
    demo_dir = Path("demo_documents")
    demo_dir.mkdir(exist_ok=True)
    
    # Créer les fichiers
    files = {
        "01_reglement_consultation.txt": create_demo_reglement(),
        "02_CCTP_techniques.txt": create_demo_cctp(),
        "03_CCAP_administratif.txt": create_demo_ccap(),
        "04_DPGF_quantitatif.txt": create_demo_dpgf(),
    }
    
    for filename, content in files.items():
        file_path = demo_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Créé : {file_path}")
    
    # Créer un fichier de métadonnées
    metadata = {
        "projet": "Restauration façade église Saint-Pierre",
        "maitre_ouvrage": "Commune de Saint-Pierre",
        "montant_estime": "31 560 € TTC",
        "duree_chantier": "6 mois",
        "documents": list(files.keys())
    }
    
    metadata_path = demo_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Créé : {metadata_path}")
    print(f"\n📁 Dossier de démonstration créé : {demo_dir}")
    print("Vous pouvez maintenant tester l'application avec ces fichiers !")

if __name__ == "__main__":
    create_demo_files() 