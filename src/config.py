# 
# Configuration MongoDB et gestion des secrets
# 
import os
import streamlit as st

KML_DIR = "kml"
CACHE_DIR = "data"

def get_mongodb_url():
    # Récupère l'URL MongoDB depuis différentes sources
    # 1. Essayer depuis les secrets Streamlit
    try:
        if hasattr(st, 'secrets') and "MONGODB_URL" in st.secrets:
            return st.secrets["MONGODB_URL"]
    except:
        pass
    # 2. Essayer depuis les variables d'environnement
    try:
        url = os.getenv("MONGODB_URL")
        if url:
            return url
    except:
        pass
    # 3. Pas d'URL par défaut pour la sécurité
    return None

def get_kml_path(filename):
    # Retourne le chemin complet d'un fichier KML dans le dossier kml
    return os.path.join(KML_DIR, filename)

def get_cache_path(filename):
    # Retourne le chemin complet d'un fichier de cache dans le dossier data
    return os.path.join(CACHE_DIR, filename)
