import streamlit as st
import pandas as pd
import pymongo
import bcrypt
import os

# Configuration MongoDB
def get_mongodb_url():
    """Récupère l'URL MongoDB depuis différentes sources"""
    
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

# Utiliser toute la largeur de la fenêtre
st.set_page_config(layout="wide", page_icon="🍔", page_title="BURGER - Recherche Postes RTE")

# Configuration MongoDB
@st.cache_resource
def init_mongodb():
    """Initialise la connexion MongoDB"""
    try:
        # Utiliser notre fonction alternative
        mongodb_url = get_mongodb_url()
        
        # Vérifier si l'URL est valide
        if not mongodb_url or "username:password" in mongodb_url:
            return None
            
        client = pymongo.MongoClient(
            mongodb_url,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        
        # Tester la connexion
        client.admin.command('ping')
        
        db = client["burger_app"]
        users_collection = db["users"]
        
        return users_collection
        
    except pymongo.errors.ServerSelectionTimeoutError as e:
        st.error(f"❌ Timeout de connexion MongoDB : {e}")
        return None
    except pymongo.errors.ConfigurationError as e:
        st.error(f"❌ Erreur de configuration MongoDB : {e}")
        return None
    except pymongo.errors.OperationFailure as e:
        st.error(f"❌ Erreur d'authentification MongoDB : {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur MongoDB inattendue : {e}")
        return None

def hash_password(password):
    """Hashe un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Vérifie un mot de passe avec son hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def authenticate_user(username, password):
    """Authentifie un utilisateur depuis MongoDB uniquement"""
    users_collection = init_mongodb()
    
    # MongoDB obligatoire - pas de fallback pour la sécurité
    if users_collection is None:
        return False
    
    # Authentification MongoDB
    try:
        user = users_collection.find_one({"username": username})
        
        if user and verify_password(password, user["password_hash"]):
            return True
        else:
            return False
            
    except Exception as e:
        # En cas d'erreur, refuser la connexion (sécurité)
        return False

# Fonction d'authentification
def check_password():
    def password_entered():
        # Récupérer les valeurs des champs selon le contexte
        username = st.session_state.get("username") or st.session_state.get("username_retry", "")
        password = st.session_state.get("password") or st.session_state.get("password_retry", "")
        
        if username and password and authenticate_user(username, password):
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = username
            # Nettoyer les mots de passe de la session
            if "password" in st.session_state:
                del st.session_state["password"]
            if "password_retry" in st.session_state:
                del st.session_state["password_retry"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Première fois - afficher les champs de connexion
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1>🔐 BURGER - Authentification</h1>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("👤 Nom d'utilisateur", key="username")
            st.text_input("🔒 Mot de passe", type="password", key="password")
            st.button(" Se connecter", on_click=password_entered, use_container_width=True)
            
            # Vérifier si MongoDB est configuré
            if get_mongodb_url() is None:
                st.warning("⚠️ MongoDB non configuré. Veuillez configurer MONGODB_URL dans les secrets.")
        
        st.markdown("---")
        st.markdown("💡 **Aide :** Contactez GBO pour obtenir vos identifiants")
        return False
    elif not st.session_state["password_correct"]:
        # Mot de passe incorrect
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1>🔐 BURGER - Authentification</h1>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("👤 Nom d'utilisateur", key="username_retry")
            st.text_input("🔒 Mot de passe", type="password", key="password_retry")
            st.error("❌ Nom d'utilisateur ou mot de passe incorrect")
            st.button("🚀 Se connecter", on_click=password_entered, use_container_width=True)
            
            # Vérifier si MongoDB est configuré
            if get_mongodb_url() is None:
                st.warning("⚠️ MongoDB non configuré. Veuillez configurer MONGODB_URL dans les secrets.")
        
        st.markdown("---")
        st.markdown("💡 **Aide :** Contactez Guillaume B. pour obtenir vos identifiants")
        return False
    else:
        # Mot de passe correct
        return True

# Vérifier l'authentification
if check_password():
    # Header avec info utilisateur et déconnexion
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("BURGER 🍔 : Base Unifiée de Référencement des Grands Equipements RTE")
    with col3:
        st.markdown(f"👤 Connecté : **{st.session_state['current_user']}**")
        if st.button("🚪 Se déconnecter"):
            del st.session_state["password_correct"]
            del st.session_state["current_user"]
            st.rerun()

    # Charger le fichier Excel
    df = pd.read_excel("fusion_postes_resultat.xlsx")

    # Saisie du nom du poste
    col1, col2, col3, col4, col5 = st.columns([1,2,3,2,1])
    with col3:
        st.markdown(
            "<span style='color:gray;'><i>(À noter que tous les postes ne sont pas encore correctement répertoriés : environ 200 sur 2700 sont validés à 100 % - MAJ:29/07/2025)</i></span>",
            unsafe_allow_html=True
        )
        search_nom = st.text_input("🔎 Entrez le nom du poste:", key="search_input")

    if search_nom:
        # Filtrer les lignes où le nom du poste correspond (insensible à la casse)
        result = df[df['Nom poste'].str.lower().str.contains(search_nom.lower(), na=False)]
        if not result.empty:
            st.success(f"📍 {len(result)} résultat(s) trouvé(s)")
            st.dataframe(result, use_container_width=True)
            
            # Afficher les liens Google Maps pour chaque résultat
            for idx, row in result.iterrows():
                lat = row.get('Geo Point', None)
                if lat:
                    try:
                        lat_str, lon_str = str(lat).split(',')
                        lat_str = lat_str.strip()
                        lon_str = lon_str.strip()
                        url = f"https://www.google.com/maps/search/?api=1&query={lat_str},{lon_str}"
                        st.markdown(f"📍 **{row['Nom poste']}** : [🗺️ Voir sur Google Maps]({url})")
                    except Exception:
                        pass
        else:
            st.warning("❌ Aucun poste trouvé avec ce nom.")

    # Texte de fin et remerciements
    st.markdown("<hr style='margin-top:40px;margin-bottom:10px;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>v0.1.1 - DB and APP by Guillaume B. 🍔</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>Special thanks to Kévin G. and Hervé G.</div>", unsafe_allow_html=True)
