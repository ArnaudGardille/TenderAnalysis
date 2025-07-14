#!/usr/bin/env python3
"""
Script de configuration de l'environnement
------------------------------------------
Aide à créer le fichier .env avec les bonnes variables d'environnement.
"""

import os
from pathlib import Path

def create_env_file():
    """Crée le fichier .env avec les variables par défaut."""
    
    env_content = """# Configuration OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Configuration de l'application
DEBUG=True
LOG_LEVEL=INFO

# Configuration des modèles
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
TEMPERATURE=0.3

# Configuration du stockage
STORAGE_DIR=./storage
UPLOADS_DIR=./uploads

# Configuration des limites
MAX_FILE_SIZE=50MB
MAX_TOKENS_PER_REQUEST=4000
AUTO_PURGE_DAYS=3
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  Le fichier .env existe déjà.")
        response = input("Voulez-vous le remplacer ? (y/N): ")
        if response.lower() != 'y':
            print("❌ Configuration annulée.")
            return
    
    try:
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ Fichier .env créé avec succès !")
        print("📝 N'oubliez pas de remplacer 'your_openai_api_key_here' par votre vraie clé API OpenAI.")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier .env : {e}")

def check_env_config():
    """Vérifie la configuration actuelle de l'environnement."""
    
    print("🔍 Vérification de la configuration...")
    
    # Vérifier si .env existe
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Fichier .env trouvé")
    else:
        print("❌ Fichier .env manquant")
        return False
    
    # Vérifier les variables importantes
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your_openai_api_key_here":
        print("✅ OPENAI_API_KEY configurée")
    else:
        print("⚠️  OPENAI_API_KEY non configurée ou valeur par défaut")
    
    # Afficher la configuration actuelle
    print("\n📋 Configuration actuelle :")
    print(f"   LLM_MODEL: {os.getenv('LLM_MODEL', 'gpt-4o')}")
    print(f"   EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')}")
    print(f"   TEMPERATURE: {os.getenv('TEMPERATURE', '0.3')}")
    print(f"   DEBUG: {os.getenv('DEBUG', 'True')}")
    print(f"   MAX_TOKENS_PER_REQUEST: {os.getenv('MAX_TOKENS_PER_REQUEST', '4000')}")
    
    return True

def main():
    """Fonction principale."""
    print("🚀 Configuration de l'environnement TenderAnalysis")
    print("=" * 50)
    
    while True:
        print("\nOptions disponibles :")
        print("1. Créer le fichier .env")
        print("2. Vérifier la configuration")
        print("3. Quitter")
        
        choice = input("\nVotre choix (1-3): ")
        
        if choice == "1":
            create_env_file()
        elif choice == "2":
            check_env_config()
        elif choice == "3":
            print("👋 Au revoir !")
            break
        else:
            print("❌ Choix invalide. Veuillez choisir 1, 2 ou 3.")

if __name__ == "__main__":
    main() 