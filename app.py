import streamlit as st
import pandas as pd

# Utiliser toute la largeur de la fenêtre
st.set_page_config(layout="wide", page_icon="🍔", page_title="BURGER - Recherche Postes RTE")

# Configuration des utilisateurs
USERS = {
    "admin": "burger202585",
}

# Fonction d'authentification
def check_password():
    def password_entered():
        if st.session_state["username"] in USERS and USERS[st.session_state["username"]] == st.session_state["password"]:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = st.session_state["username"]
            del st.session_state["password"]  # Supprimer le mot de passe de la session
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
            "<span style='color:gray;'><i>(À noter que tous les postes ne sont pas encore correctement répertoriés : environ 100 sur 2700 sont validés à 100 % - MAJ:28/07/2025)</i></span>",
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
    st.markdown("<div style='text-align:center; color:gray;'>PROOF OF CONCEPT - DB and APP by Guillaume B. 🍔</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>Special thanks to Kévin G. and Hervé G.</div>", unsafe_allow_html=True)
