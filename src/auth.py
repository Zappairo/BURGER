"""
Authentification utilisateur (MongoDB, bcrypt)
"""
import bcrypt
import pymongo
import streamlit as st
from .config import get_mongodb_url

def hash_password(password):
    """Hashe un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Vérifie un mot de passe avec son hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def authenticate_user(username, password):
    """Authentifie un utilisateur depuis MongoDB uniquement"""
    users_collection = init_mongodb()
    if users_collection is None:
        return False
    try:
        user = users_collection.find_one({"username": username})
        if user and verify_password(password, user["password_hash"]):
            return True
        else:
            return False
    except Exception:
        return False

def check_password():
    def password_entered():
        username = st.session_state.get("username") or st.session_state.get("username_retry", "")
        password = st.session_state.get("password") or st.session_state.get("password_retry", "")
        if username and password and authenticate_user(username, password):
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = username
            if "password" in st.session_state:
                del st.session_state["password"]
            if "password_retry" in st.session_state:
                del st.session_state["password_retry"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
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
            if get_mongodb_url() is None:
                st.warning("⚠️ MongoDB non configuré. Veuillez configurer MONGODB_URL dans les secrets.")
        st.markdown("---")
        st.markdown("💡 **Aide :** Contactez GBO pour obtenir vos identifiants")
        return False
    elif not st.session_state["password_correct"]:
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
            if get_mongodb_url() is None:
                st.warning("⚠️ MongoDB non configuré. Veuillez configurer MONGODB_URL dans les secrets.")
        st.markdown("---")
        st.markdown("💡 **Aide :** Contactez Guillaume B. pour obtenir vos identifiants")
        return False
    else:
        return True

def init_mongodb():
    """Initialise la connexion MongoDB"""
    try:
        mongodb_url = get_mongodb_url()
        if not mongodb_url or "username:password" in mongodb_url:
            return None
        client = pymongo.MongoClient(
            mongodb_url,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        client.admin.command('ping')
        db = client["burger_app"]
        users_collection = db["users"]
        return users_collection
    except Exception as e:
        st.error(f"❌ Erreur MongoDB : {e}")
        return None
