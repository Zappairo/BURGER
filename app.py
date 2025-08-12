import streamlit as st
import pandas as pd
import folium
import pymongo
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
from src.performance_config import (
    CACHE_TTL_DATA, CACHE_TTL_SEARCH, MIN_SEARCH_LENGTH, 
    MAX_SEARCH_RESULTS, AUTO_SELECT_COUNT, DISPLAY_COLUMNS, HELP_MESSAGES,
    MAP_RETURN_ON_HOVER, MAP_RETURNED_OBJECTS, MAP_USE_CONTAINER_WIDTH
)

# Configuration de la page doit être la première commande Streamlit
st.set_page_config(layout="wide", page_icon="🍔", page_title="BURGER - Recherche Postes RTE")

# Cache global pour les données KML - évite les rechargements intempestifs
@st.cache_data(ttl=CACHE_TTL_DATA, show_spinner="🔄 Chargement initial des données...")
def load_postes_data():
    """Charge et met en cache les données des postes"""
    return parse_postes_kml_optimized()

@st.cache_data(ttl=CACHE_TTL_DATA, show_spinner="🔄 Chargement des données GMR...")
def load_gmr_data(high_precision=False):
    """Charge et met en cache les données GMR"""
    return parse_gmr_kml_optimized(high_precision)

@st.cache_data(ttl=CACHE_TTL_DATA, show_spinner="🔄 Chargement des données GDP...")
def load_gdp_data(high_precision=False):
    """Charge et met en cache les données GDP"""
    return parse_gdp_kml_optimized(high_precision)

# Cache pour les fonctions de recherche - évite les recalculs
@st.cache_data(ttl=CACHE_TTL_SEARCH)
def prepare_search_data(postes_df):
    """Prépare les données de recherche optimisées"""
    import re
    import unicodedata
    
    nom_col = 'Nom poste' if 'Nom poste' in postes_df.columns else 'Nom_du_pos'
    ARTICLES = {"le", "la", "les", "l"}
    
    def clean_and_split(s):
        if pd.isna(s):
            return []
        s = str(s).lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join([c for c in s if not unicodedata.combining(c)])
        s = re.sub(r"[-()]+", " ", s)
        words = [w for w in s.split() if w not in ARTICLES]
        return sorted(words)
    
    search_df = postes_df.copy()
    search_df["_nom_clean_list"] = search_df[nom_col].apply(clean_and_split)
    return search_df

@st.cache_data(ttl=CACHE_TTL_SEARCH)
def search_postes(search_df, search_nom):
    """Effectue la recherche de postes de manière optimisée"""
    import re
    import unicodedata
    
    ARTICLES = {"le", "la", "les", "l"}
    
    def clean_and_split(s):
        if pd.isna(s):
            return []
        s = str(s).lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join([c for c in s if not unicodedata.combining(c)])
        s = re.sub(r"[-()]+", " ", s)
        words = [w for w in s.split() if w not in ARTICLES]
        return sorted(words)
    
    search_nom_clean_list = clean_and_split(search_nom)
    
    def match_words(row_words, search_words):
        return set(search_words) <= set(row_words)
    
    result = search_df[search_df["_nom_clean_list"].apply(lambda x: match_words(x, search_nom_clean_list))]
    return result.drop(columns=["_nom_clean_list"], errors='ignore')

# Vérifier l'authentification
if check_password():
    # Header avec info utilisateur et déconnexion
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("BURGER 🍔 : Base Unifiée de Référencement des Grands Equipements RTE")
    with col3:
        st.markdown(f"👤 Connecté : **{st.session_state['current_user']}**")
        if st.button("🚪 Se déconnecter"):
            # Vider le cache utilisateur pour forcer la reconnexion
            for key in list(st.session_state.keys()):
                if key.startswith(('password', 'current_user', 'precision_')):
                    del st.session_state[key]
            st.rerun()

    # Initialisation des variables de session pour éviter les rechargements
    if 'precision_gmr' not in st.session_state:
        st.session_state.precision_gmr = False
    if 'precision_gdp' not in st.session_state:
        st.session_state.precision_gdp = False

    # Options de performance avec session state pour éviter les rechargements
    with st.expander("⚙️ Options de performance", expanded=False):
        col_gmr_prec, col_gdp_prec = st.columns(2)
        with col_gmr_prec:
            new_precision_gmr = st.checkbox(
                "🔵 Précision maximale des polygones GMR", 
                value=st.session_state.precision_gmr,
                key="precision_gmr_checkbox"
            )
        with col_gdp_prec:
            new_precision_gdp = st.checkbox(
                "🟢 Précision maximale des polygones GDP", 
                value=st.session_state.precision_gdp,
                key="precision_gdp_checkbox"
            )
        
        # Détecter les changements et mettre à jour le session state
        if new_precision_gmr != st.session_state.precision_gmr:
            st.session_state.precision_gmr = new_precision_gmr
            # Vider le cache pour forcer le rechargement avec nouvelle précision
            st.cache_data.clear()
            
        if new_precision_gdp != st.session_state.precision_gdp:
            st.session_state.precision_gdp = new_precision_gdp
            # Vider le cache pour forcer le rechargement avec nouvelle précision
            st.cache_data.clear()
            
            st.info(HELP_MESSAGES['precision_info'])

    # Chargement optimisé des données avec gestion d'erreurs
    try:
        # Chargement des postes (toujours nécessaire)
        postes_df = load_postes_data()
        
        # Préparation des données de recherche
        search_df = prepare_search_data(postes_df)
        
        # Chargement conditionnel des GMR et GDP selon les options
        gmr_df = load_gmr_data(st.session_state.precision_gmr)
        gdp_df = load_gdp_data(st.session_state.precision_gdp)
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {e}")
        st.stop()

    # Vérification de la validité des données
    if postes_df.empty:
        st.error("❌ Impossible de charger les données des postes")
        st.stop()
    elif gmr_df.empty:
        st.error("❌ Impossible de charger les données des GMR")
        st.stop()
    elif gdp_df.empty:
        st.error("❌ Impossible de charger les données des GDP")
        st.stop()
    # Interface de recherche optimisée
    col1, col2, col3, col4, col5 = st.columns([1,2,3,2,1])
    with col3:
        # Utilisation d'une clé unique pour éviter les rechargements intempestifs
        search_nom = st.text_input(
            "🔎 Entrez le nom du poste:", 
            key="search_input_main",
            placeholder=HELP_MESSAGES['search_placeholder']
        )

        # Options d'affichage avec session state stable
        if 'show_gmr' not in st.session_state:
            st.session_state.show_gmr = False
        if 'show_gdp' not in st.session_state:
            st.session_state.show_gdp = False
            
        col_gmr, col_gdp = st.columns(2)
        with col_gmr:
            new_show_gmr = st.checkbox(
                "🔵 Afficher tous les GMR", 
                value=st.session_state.show_gmr,
                key="show_gmr_checkbox"
            )
            # Mise à jour silencieuse du session state
            st.session_state.show_gmr = new_show_gmr
            show_all_gmr = st.session_state.show_gmr
                
        with col_gdp:
            new_show_gdp = st.checkbox(
                "🟢 Afficher tous les GDP", 
                value=st.session_state.show_gdp,
                key="show_gdp_checkbox"
            )
            # Mise à jour silencieuse du session state
            st.session_state.show_gdp = new_show_gdp
            show_all_gdp = st.session_state.show_gdp

    # Traitement de la recherche avec optimisations
    if search_nom and len(search_nom.strip()) >= MIN_SEARCH_LENGTH:
        try:
            # Recherche optimisée avec cache
            result = search_postes(search_df, search_nom)
            
            if not result.empty:
                # Limiter le nombre de résultats pour les performances
                if len(result) > MAX_SEARCH_RESULTS:
                    st.warning(HELP_MESSAGES['too_many_results'].format(len(result), MAX_SEARCH_RESULTS))
                    result = result.head(MAX_SEARCH_RESULTS)
                
                # Interface optimisée avec cache de l'état de sélection
                result_key = f"result_{hash(search_nom)}_{len(result)}"
                
                # Créer deux colonnes : tableau et carte
                col_table, col_map = st.columns([1, 1])
                
                with col_table:
                    st.subheader(f"📋 {len(result)} résultat(s) trouvé(s)")
                    
                    # Préparation optimisée des données d'affichage
                    result_for_editor = result[DISPLAY_COLUMNS].copy()
                    result_for_editor["Sélectionner"] = False
                    
                    # Sélection automatique intelligente (premiers résultats)
                    auto_select_count = min(AUTO_SELECT_COUNT, len(result_for_editor))
                    if auto_select_count > 0:
                        result_for_editor.loc[result_for_editor.index[:auto_select_count], "Sélectionner"] = True
                    
                    # Éditeur de données avec optimisations
                    selected_result = st.data_editor(
                        result_for_editor,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Sélectionner": st.column_config.CheckboxColumn(
                                "Sélectionner",
                                help="Cochez pour afficher sur la carte"
                            ),
                            "Nom_du_pos": st.column_config.TextColumn("Nom du poste"),
                            "Identifian": st.column_config.TextColumn("Identifiant"),
                            "Tension_d": st.column_config.TextColumn("Tension"),
                            "latitude": st.column_config.NumberColumn("Latitude", format="%.6f"),
                            "longitude": st.column_config.NumberColumn("Longitude", format="%.6f")
                        },
                        key=result_key
                    )
                    
                    # Filtrer pour ne garder que les lignes sélectionnées
                    filtered_result = selected_result[selected_result["Sélectionner"] == True].drop(columns=["Sélectionner"])

                    if not filtered_result.empty:
                        # Optimisation des liens de navigation
                        st.subheader("🗺️ Liens de navigation")
                        for idx, row in filtered_result.iterrows():
                            if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                                lat_str = f"{row['latitude']:.6f}"
                                lon_str = f"{row['longitude']:.6f}"
                                google_url = f"https://www.google.com/maps/search/?api=1&query={lat_str},{lon_str}"
                                waze_url = f"https://waze.com/ul?ll={lat_str}%2C{lon_str}&navigate=yes"
                                poste_name = row.get('Nom_du_pos', 'Poste inconnu')
                                st.markdown(f"📍 **{poste_name}** : [🗺️ Google Maps]({google_url}) | [🚗 Waze]({waze_url})")
                        
                        # Informations GMR et GDP optimisées avec cache
                        with st.expander("🏢 Informations GMR et GDP", expanded=True):
                            gmr_info_cache = {}
                            gdp_info_cache = {}
                            
                            for idx, row in filtered_result.iterrows():
                                if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                                    coord_key = (row['latitude'], row['longitude'])
                                    
                                    # Cache GMR
                                    if coord_key not in gmr_info_cache:
                                        gmr_info_cache[coord_key] = find_gmr_for_poste(row['latitude'], row['longitude'], gmr_df)
                                    
                                    # Cache GDP
                                    if coord_key not in gdp_info_cache:
                                        gdp_info_cache[coord_key] = find_gdp_for_poste(row['latitude'], row['longitude'], gdp_df)
                            
                            # Affichage optimisé des informations
                            unique_gmr = set()
                            unique_gdp = set()
                            
                            for coord_key in gmr_info_cache:
                                gmr_info = gmr_info_cache[coord_key]
                                if gmr_info is not None:
                                    gmr_tuple = (gmr_info.get('GMR_alias', 'N/A'), gmr_info.get('GMR', 'N/A'), gmr_info.get('Siège_du_', 'N/A'))
                                    unique_gmr.add(gmr_tuple)
                            
                            for coord_key in gdp_info_cache:
                                gdp_info = gdp_info_cache[coord_key]
                                if gdp_info is not None:
                                    gdp_tuple = (gdp_info.get('Poste', 'N/A'), gdp_info.get('Code', 'N/A'), gdp_info.get('Nom_du_cen', 'N/A'))
                                    unique_gdp.add(gdp_tuple)
                            
                            if unique_gmr:
                                st.markdown("#### 🔵 GMR identifiés")
                                for gmr_alias, gmr_code, gmr_siege in unique_gmr:
                                    st.info(f"**{gmr_alias}** (Code: {gmr_code}) - Siège: {gmr_siege}")
                            
                            if unique_gdp:
                                st.markdown("#### 🟢 GDP identifiés")
                                for gdp_poste, gdp_code, gdp_centre in unique_gdp:
                                    st.success(f"**{gdp_poste}** (Code: {gdp_code}) - Centre: {gdp_centre}")
                    else:
                        st.warning(HELP_MESSAGES['select_postes'])

                with col_map:
                    if not filtered_result.empty:
                        st.subheader("🗺️ Carte interactive")
                        
                        # Création optimisée de la carte avec cache stable
                        # Utiliser un hash du contenu pour éviter les regenerations intempestives
                        postes_hash = hash(tuple(sorted(filtered_result.index.tolist())))
                        options_hash = hash((show_all_gmr, show_all_gdp, st.session_state.precision_gmr, st.session_state.precision_gdp))
                        map_cache_key = f"stable_map_{postes_hash}_{options_hash}"
                        
                        with st.spinner("🗺️ Génération de la carte..."):
                            map_obj = create_map_with_gmr_gdp(filtered_result, gmr_df, gdp_df, show_all_gmr, show_all_gdp)
                            
                            # Affichage de la carte avec configuration anti-reload
                            map_data = st_folium(
                                map_obj, 
                                width=700, 
                                height=500,
                                key=map_cache_key,
                                returned_objects=MAP_RETURNED_OBJECTS,  # Configuration anti-reload
                                return_on_hover=MAP_RETURN_ON_HOVER,  # Désactiver les événements de survol
                                use_container_width=MAP_USE_CONTAINER_WIDTH  # Largeur fixe pour stabilité
                            )
                        
                        # Légende
                        st.markdown("""
                        **Légende :**
                        - 🔴 **Marqueurs rouges** : Postes sélectionnés
                        - 🔵 **Zones bleues** : GMR (Groupements de Maintenance Régionale)
                        - 🟢 **Zones vertes** : GDP (Groupements De Poste)
                        """)
                    else:
                        st.info("🗺️ Sélectionnez des postes dans le tableau pour afficher la carte.")
                        
            else:
                st.warning(HELP_MESSAGES['no_results'].format(search_nom))
                
        except Exception as e:
            st.error(f"❌ Erreur lors de la recherche : {e}")
            
    elif search_nom and len(search_nom.strip()) < MIN_SEARCH_LENGTH:
        st.info(HELP_MESSAGES['search_min_chars'])
    else:
        st.info(HELP_MESSAGES['search_no_input'])

    # Texte de fin et remerciements
    st.markdown("<hr style='margin-top:40px;margin-bottom:10px;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>v1.0.2 - DB and APP by Guillaume B. 🍔</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>Special thanks to PascaL B. , Kévin G. and Hervé G.</div>", unsafe_allow_html=True)
