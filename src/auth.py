# 
# Authentification utilisateur (MongoDB, bcrypt)
# 
import bcrypt
import pymongo
import streamlit as st
from .config import get_mongodb_url

def hash_password(password):
    # Hashe un mot de passe avec bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    # Vérifie un mot de passe avec son hash
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def authenticate_user(username, password):
    # Authentifie un utilisateur depuis MongoDB uniquement
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
    def authenticate_with_form(username, password):
        # Afficher un indicateur de chargement
            if username and password and authenticate_user(username, password):
                st.session_state["password_correct"] = True
                st.session_state["current_user"] = username
                # Afficher un message de succès temporaire
                st.success("✅ Connexion réussie ! Redirection...")
                st.balloons()  # Animation de réussite
                # Petit délai pour laisser l'animation se jouer
                import time
                time.sleep(1.5)
                st.rerun()
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
            with st.form("login_form"):
                username = st.text_input("👤 Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
                password = st.text_input("🔒 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
                
                # Colonnes pour le bouton et l'indicateur
                btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
                with btn_col2:
                    submitted = st.form_submit_button("🚀 Se connecter", use_container_width=True, type="primary")
                with btn_col3:
                    if submitted and username and password:
                        st.markdown("""
                            <div style="display: flex; justify-content: center; align-items: center;">
                            <div style="border: 3px solid #f3f3f3; border-top: 3px solid #3498db; 
                                border-radius: 50%; width: 20px; height: 20px; 
                                animation: spin 1s linear infinite;"></div>
                            </div>
                            <style>
                                @keyframes spin {
                                0% { transform: rotate(0deg); }
                                100% { transform: rotate(360deg); }
                            }
                            </style>
                        """, unsafe_allow_html=True)
                
                if submitted:
                    if not username or not password:
                        st.error("⚠️ Veuillez remplir tous les champs")
                    else:
                        authenticate_with_form(username, password)
            
            if get_mongodb_url() is None:
                st.warning("⚠️ MongoDB non configuré. Veuillez configurer MONGODB_URL dans les secrets.")
        st.markdown("---")
        st.markdown("💡 **Aide :** Contactez GBO pour obtenir vos identifiants")
        st.markdown("⚡ **Astuce :** Le raccourci **Entrée** fonctionne désormais !")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1>🔐 BURGER - Authentification</h1>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_retry_form"):
                username_retry = st.text_input("👤 Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
                password_retry = st.text_input("🔒 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
                
                # Colonnes pour le bouton et l'indicateur
                btn_col1, btn_col2 = st.columns([3, 1])
                with btn_col1:
                    submitted_retry = st.form_submit_button("🚀 Se connecter", use_container_width=True, type="primary")
                with btn_col1:
                    if submitted_retry and username_retry and password_retry:
                        st.write("⏳")
                
                if submitted_retry:
                    if not username_retry or not password_retry:
                        st.error("⚠️ Veuillez remplir tous les champs")
                    else:
                        authenticate_with_form(username_retry, password_retry)
            
            st.error("❌ Nom d'utilisateur ou mot de passe incorrect")
            if get_mongodb_url() is None:
                st.warning("⚠️ MongoDB non configuré. Veuillez configurer MONGODB_URL dans les secrets.")
        st.markdown("---")
        st.markdown("💡 **Aide :** Contactez Guillaume B. pour obtenir vos identifiants")
        st.markdown("⚡ **Astuce :** Le raccourci **Entrée** fonctionne désormais !")
        return False
    else:
        return True

def init_mongodb():
    # Initialise la connexion MongoDB
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
