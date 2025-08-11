import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
# --- Modularized imports ---
from src.parsers import (
    parse_postes_kml_optimized,
    parse_gmr_kml_optimized,
    parse_gdp_kml_optimized,
    parse_postes_kml,
    parse_gmr_kml
)
from src.map_utils import (
    point_in_polygon,
    create_map_with_gmr_gdp,
    find_gmr_for_poste,
    find_gdp_for_poste
)
from src.auth import (
    hash_password,
    verify_password,
    authenticate_user,
    check_password,
    init_mongodb
)
from src.config import get_mongodb_url

# Cache pour les données KML
@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def load_and_cache_kml_data(high_precision=False):
    """Charge et met en cache les données KML optimisées"""
    postes_df = parse_postes_kml_optimized()
    gmr_df = parse_gmr_kml_optimized(high_precision)
    gdp_df = parse_gdp_kml_optimized(high_precision)
    return postes_df, gmr_df, gdp_df

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
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("BURGER 🍔 : Base Unifiée de Référencement des Grands Equipements RTE")
    with col3:
        st.markdown(f"👤 Connecté : **{st.session_state['current_user']}**")
        if st.button("🚪 Se déconnecter"):
            del st.session_state["password_correct"]
            del st.session_state["current_user"]
            st.rerun()

    # Options de performance (disponibles avant le chargement)
    with st.expander("⚙️ Options de performance", expanded=False):
        high_precision_gmr = st.checkbox("🔵 Précision maximale des polygones GMR (plus lent au chargement)", value=False)
        high_precision_gdp = st.checkbox("🟢 Précision maximale des polygones GDP (plus lent au chargement)", value=False)
        st.info("💡 La précision maximale améliore les contours des GMR et GDP mais augmente drastiquement le temps de chargement initial.")

    # Charger les données KML avec cache et indicateur de progression
    cache_key = f"data_loaded_{high_precision_gmr}_{high_precision_gdp}"
    if cache_key not in st.session_state:
        with st.spinner("🔄 Chargement initial des données (mis en cache pour les prochaines utilisations)..."):
            postes_df = parse_postes_kml_optimized()
            gmr_df = parse_gmr_kml_optimized(high_precision_gmr)
            gdp_df = parse_gdp_kml_optimized(high_precision_gdp)
            st.session_state[cache_key] = True
            st.session_state['current_precision_gmr'] = high_precision_gmr
            st.session_state['current_precision_gdp'] = high_precision_gdp
    else:
        # Vérifier si la précision a changé
        if (st.session_state.get('current_precision_gmr', False) != high_precision_gmr or
            st.session_state.get('current_precision_gdp', False) != high_precision_gdp):
            with st.spinner("🔄 Rechargement avec nouvelle précision..."):
                postes_df = parse_postes_kml_optimized()
                gmr_df = parse_gmr_kml_optimized(high_precision_gmr)
                gdp_df = parse_gdp_kml_optimized(high_precision_gdp)
                st.session_state['current_precision_gmr'] = high_precision_gmr
                st.session_state['current_precision_gdp'] = high_precision_gdp
        else:
            # Chargement rapide depuis le cache
            postes_df = parse_postes_kml_optimized()
            gmr_df = parse_gmr_kml_optimized(high_precision_gmr)
            gdp_df = parse_gdp_kml_optimized(high_precision_gdp)
    
    if postes_df.empty:
        st.error("❌ Impossible de charger les données des postes depuis le fichier KML")
    elif gmr_df.empty:
        st.error("❌ Impossible de charger les données des GMR depuis le fichier KML")
    elif gdp_df.empty:
        st.error("❌ Impossible de charger les données des GDP depuis le fichier KML")
    else:
        # Interface de recherche
        col1, col2, col3, col4, col5 = st.columns([1,2,3,2,1])
        with col3:
            search_nom = st.text_input("🔎 Entrez le nom du poste:", key="search_input")

            # Options pour afficher les GMR et GDP
            col_gmr, col_gdp = st.columns(2)
            with col_gmr:
                show_all_gmr = st.checkbox("🔵 Afficher tous les GMR", value=False)
            with col_gdp:
                show_all_gdp = st.checkbox("🟢 Afficher tous les GDP", value=False)

        if search_nom:
            # Filtrer les postes
            import re
            nom_col = 'Nom poste' if 'Nom poste' in postes_df.columns else 'Nom_du_pos'
            import unicodedata
            ARTICLES = {"le", "la", "les", "l"}
            def clean_and_split(s):
                if pd.isna(s):
                    return []
                import unicodedata
                s = str(s).lower()
                s = unicodedata.normalize('NFKD', s)
                s = ''.join([c for c in s if not unicodedata.combining(c)])
                s = re.sub(r"[-()]+", " ", s) # remplace tirets et parenthèses par espace
                words = [w for w in s.split() if w not in ARTICLES]
                return sorted(words)
            # Nettoyer les noms de poste
            postes_df["_nom_clean_list"] = postes_df[nom_col].apply(clean_and_split)
            search_nom_clean_list = clean_and_split(search_nom)
            # Recherche : tous les postes dont les mots (hors articles) correspondent peu importe l'ordre
            def match_words(row_words, search_words):
                return set(search_words) <= set(row_words)
            result = postes_df[postes_df["_nom_clean_list"].apply(lambda x: match_words(x, search_nom_clean_list))]
            
            if not result.empty:
                # Créer deux colonnes : tableau et carte
                col_table, col_map = st.columns([1, 1])
                
                with col_table:
                    st.subheader("📋 Résultats de la recherche")
                    # Afficher le tableau des résultats avec sélection de lignes
                    display_cols = [col for col in result.columns if col in ['Nom_du_pos', 'Identifian', 'Tension_d', 'latitude', 'longitude']]
                    result_for_editor = result[display_cols].copy()
                    result_for_editor["_selected"] = False
                    if len(result_for_editor) > 0:
                        result_for_editor.loc[result_for_editor.index[:2], "_selected"] = True
                    selected_result = st.data_editor(
                        result_for_editor,
                        use_container_width=True,
                        num_rows="dynamic",
                        column_config={"_selected": st.column_config.CheckboxColumn("Sélectionner")}
                    )
                    # Filtrer pour ne garder que les lignes sélectionnées
                    filtered_result = selected_result[selected_result["_selected"] == True].drop(columns=["_selected"])

                    # Afficher les liens Google Maps et Waze pour chaque résultat sélectionné
                    st.subheader("🗺️ Liens de navigation")
                    for idx, row in filtered_result.iterrows():
                        if 'latitude' in row and 'longitude' in row and pd.notna(row['latitude']) and pd.notna(row['longitude']):
                            lat_str = str(row['latitude'])
                            lon_str = str(row['longitude'])
                            # URL Google Maps
                            google_url = f"https://www.google.com/maps/search/?api=1&query={lat_str},{lon_str}"
                            # URL Waze
                            waze_url = f"https://waze.com/ul?ll={lat_str}%2C{lon_str}&navigate=yes"
                            poste_name = row.get('Nom poste', row.get('Nom_du_pos', 'Poste inconnu'))
                            st.markdown(f"📍 **{poste_name}** : [🗺️ Google Maps]({google_url}) | [🚗 Waze]({waze_url})")

                    # Afficher les informations GMR et GDP regroupées
                    st.subheader("🏢 Informations GMR et GDP :")
                    gmr_postes = {}
                    gdp_postes = {}
                    for idx, row in filtered_result.iterrows():
                        if 'latitude' in row and 'longitude' in row and pd.notna(row['latitude']) and pd.notna(row['longitude']):
                            # Informations GMR
                            gmr_info = find_gmr_for_poste(row['latitude'], row['longitude'], gmr_df)
                            if gmr_info is not None:
                                gmr_key = (gmr_info.get('GMR_alias', 'N/A'), gmr_info.get('GMR', 'N/A'), gmr_info.get('Siège_du_', 'N/A'))
                                poste_name = row.get('Nom poste', row.get('Nom_du_pos', 'Poste inconnu'))
                                if gmr_key not in gmr_postes:
                                    gmr_postes[gmr_key] = []
                                gmr_postes[gmr_key].append(poste_name)
                            # Informations GDP
                            gdp_info = find_gdp_for_poste(row['latitude'], row['longitude'], gdp_df)
                            if gdp_info is not None:
                                gdp_key = (gdp_info.get('Poste', 'N/A'), gdp_info.get('Code', 'N/A'), gdp_info.get('Nom_du_cen', 'N/A'), gdp_info.get('Siège_du_', 'N/A'))
                                poste_name = row.get('Nom poste', row.get('Nom_du_pos', 'Poste inconnu'))
                                if gdp_key not in gdp_postes:
                                    gdp_postes[gdp_key] = []
                                gdp_postes[gdp_key].append(poste_name)
                    # Afficher les GMR
                    if filtered_result.empty:
                        st.warning("Aucun poste sélectionné dans le tableau. Veuillez sélectionner au moins une ligne.")
                    else:
                        if not gmr_postes:
                            st.warning("Aucun GMR identifié pour les postes sélectionnés.")
                        else:
                            st.markdown("### 🔵 Groupements de Maintenance Régionale (GMR)")
                            for gmr_key, postes in gmr_postes.items():
                                gmr_alias, gmr_code, gmr_siege = gmr_key
                                st.info(f"📍 {', '.join(postes)}")
                                st.write(f"• **GMR :** {gmr_alias}")
                                st.write(f"• **Code GMR :** {gmr_code}")
                                st.write(f"• **Siège :** {gmr_siege}")
                        # Afficher les GDP
                        if not gdp_postes:
                            st.warning("Aucun GDP identifié pour les postes sélectionnés.")
                        else:
                            st.markdown("### 🟢 Groupements De Poste (GDP)")
                            for gdp_key, postes in gdp_postes.items():
                                gdp_poste, gdp_code, gdp_centre, gdp_siege = gdp_key
                                st.success(f"📍 {', '.join(postes)}")
                                st.write(f"• **GDP :** {gdp_poste}")
                                st.write(f"• **Code GDP :** {gdp_code}")
                                st.write(f"• **Centre :** {gdp_centre}")
                                st.write(f"• **Siège :** {gdp_siege}")

                with col_map:
                    st.subheader("🗺️ Carte des postes, GMR et GDP")
                    
                    with st.spinner("🗺️ Génération de la carte..."):
                        # Créer et afficher la carte
                        map_obj = create_map_with_gmr_gdp(filtered_result, gmr_df, gdp_df, show_all_gmr, show_all_gdp)
                        # Afficher la carte avec une clé unique pour éviter le re-rendu
                        map_key = f"map_{hash(search_nom)}_{len(filtered_result)}_{show_all_gmr}_{show_all_gdp}"
                        st_folium(
                            map_obj, 
                            width=700, 
                            height=500,
                            key=map_key
                        )
                    
                    # Légende
                    st.markdown("""
                    **Légende :**
                    - 🔴 **Marqueurs rouges** : Postes électriques trouvés
                    - 🔵 **Zones bleues** : Groupements de Maintenance Régionale (GMR)
                    - 🟢 **Zones vertes** : Groupements De Poste (GDP)
                    """)
                    
                    
            else:
                st.warning("❌ Aucun poste trouvé avec ce nom.")

    # Texte de fin et remerciements
    st.markdown("<hr style='margin-top:40px;margin-bottom:10px;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>v1.0.0 - DB and APP by Guillaume B. 🍔</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>Special thanks to PascaL B. , Kévin G. and Hervé G.</div>", unsafe_allow_html=True)
