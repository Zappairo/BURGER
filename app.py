import streamlit as st
import pandas as pd
import pymongo
import bcrypt
import os
import xml.etree.ElementTree as ET
import folium
from streamlit_folium import st_folium
import pickle
from datetime import datetime

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

# Cache pour les données KML
@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def load_and_cache_kml_data(high_precision=False):
    """Charge et met en cache les données KML optimisées"""
    postes_df = parse_postes_kml_optimized()
    gmr_df = parse_gmr_kml_optimized(high_precision)
    gdp_df = parse_gdp_kml_optimized(high_precision)
    return postes_df, gmr_df, gdp_df

# Version optimisée du parser de postes
def parse_postes_kml_optimized():
    """Parse le fichier Poste.kml de manière optimisée"""
    try:
        # Vérifier si un cache local existe
        cache_file = "postes_cache.pkl"
        kml_file = "Poste.kml"
        
        # Vérifier si le cache est plus récent que le fichier KML
        if (os.path.exists(cache_file) and os.path.exists(kml_file) and 
            os.path.getmtime(cache_file) > os.path.getmtime(kml_file)):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        # Parser le KML avec optimisations
        tree = ET.parse(kml_file)
        root = tree.getroot()
        
        # Namespace KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        postes_data = []
        
        # Parcourir tous les Placemark avec limitation
        placemarks = root.findall('.//kml:Placemark', ns)
        
        for placemark in placemarks:
            # Récupérer les données étendues
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                poste_info = {}
                
                # Extraire seulement les données essentielles
                essential_fields = ['Nom_du_pos', 'Identifian', 'Tension_d', 'Tension_00']
                
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name in essential_fields and value:
                        poste_info[name] = value
                
                # Récupérer les coordonnées
                coordinates = placemark.find('.//kml:coordinates', ns)
                if coordinates is not None and coordinates.text:
                    coords = coordinates.text.strip().split(',')
                    if len(coords) >= 2:
                        try:
                            poste_info['longitude'] = float(coords[0])
                            poste_info['latitude'] = float(coords[1])
                        except ValueError:
                            continue
                
                # Ne garder que les postes avec coordonnées et nom
                if 'longitude' in poste_info and 'latitude' in poste_info and 'Nom_du_pos' in poste_info:
                    postes_data.append(poste_info)
        
        df = pd.DataFrame(postes_data)
        
        # Renommer les colonnes pour compatibilité
        if 'Nom_du_pos' in df.columns:
            df['Nom poste'] = df['Nom_du_pos']
        
        # Sauvegarder en cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            pass
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du parsing du fichier Poste.kml : {e}")
        return pd.DataFrame()

# Fonction pour parser le KML des postes
def parse_postes_kml():
    """Parse le fichier Poste.kml et retourne un DataFrame avec les postes"""
    try:
        tree = ET.parse("Poste.kml")
        root = tree.getroot()
        
        # Namespace KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        postes_data = []
        
        # Parcourir tous les Placemark
        for placemark in root.findall('.//kml:Placemark', ns):
            # Récupérer les données étendues
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                poste_info = {}
                
                # Extraire les données
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        poste_info[name] = value
                
                # Récupérer les coordonnées
                coordinates = placemark.find('.//kml:coordinates', ns)
                if coordinates is not None and coordinates.text:
                    coords = coordinates.text.strip().split(',')
                    if len(coords) >= 2:
                        poste_info['longitude'] = float(coords[0])
                        poste_info['latitude'] = float(coords[1])
                        poste_info['Geo Point'] = f"{coords[1]},{coords[0]}"  # Format lat,lon pour compatibilité
                
                if poste_info:
                    postes_data.append(poste_info)
        
        df = pd.DataFrame(postes_data)
        
        # Renommer les colonnes pour compatibilité avec l'ancien code
        if 'Nom_du_pos' in df.columns:
            df['Nom poste'] = df['Nom_du_pos']
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du parsing du fichier Poste.kml : {e}")
        return pd.DataFrame()

# Version optimisée du parser GMR
def parse_gmr_kml_optimized(high_precision=False):
    """Parse le fichier GMR.kml de manière optimisée"""
    try:
        # Vérifier si un cache local existe (avec clé de précision)
        cache_suffix = "_hq" if high_precision else ""
        cache_file = f"gmr_cache{cache_suffix}.pkl"
        kml_file = "GMR.kml"
        
        # Vérifier si le cache est plus récent que le fichier KML
        if (os.path.exists(cache_file) and os.path.exists(kml_file) and 
            os.path.getmtime(cache_file) > os.path.getmtime(kml_file)):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        tree = ET.parse(kml_file)
        root = tree.getroot()
        
        # Namespace KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        gmr_data = []
        
        # Parcourir tous les Placemark
        for placemark in root.findall('.//kml:Placemark', ns):
            # Récupérer les données étendues
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                gmr_info = {}
                
                # Extraire seulement les données essentielles
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        gmr_info[name] = value
                
                # Récupérer la géométrie (avec précision variable)
                geometry = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if geometry is not None and geometry.text:
                    # Parser les coordonnées du polygone
                    coords_text = geometry.text.strip()
                    coord_pairs = []
                    coords_list = coords_text.split()
                    
                    if high_precision:
                        # Mode haute précision : garder beaucoup plus de points
                        step = 1  # Garder tous les points
                    else:
                        # Mode optimisé : simplification adaptative
                        if len(coords_list) <= 100:
                            step = 1  # Garder tous les points pour les petits polygones
                        elif len(coords_list) <= 500:
                            step = max(1, len(coords_list) // 200)  # Jusqu'à 200 points
                        elif len(coords_list) <= 2000:
                            step = max(1, len(coords_list) // 300)  # Jusqu'à 300 points
                        else:
                            step = max(1, len(coords_list) // 400)  # Jusqu'à 400 points max
                    
                    for i in range(0, len(coords_list), step):
                        coord = coords_list[i]
                        if ',' in coord:
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                try:
                                    coord_pairs.append([float(parts[1]), float(parts[0])])  # [lat, lon]
                                except ValueError:
                                    continue
                    
                    if coord_pairs:
                        gmr_info['coordinates'] = coord_pairs
                
                if gmr_info and 'Siège_du_' in gmr_info:
                    gmr_data.append(gmr_info)
        
        df = pd.DataFrame(gmr_data)
        
        # Sauvegarder en cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            pass
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du parsing du fichier GMR.kml : {e}")
        return pd.DataFrame()

# Version optimisée du parser GDP
def parse_gdp_kml_optimized(high_precision=False):
    """Parse le fichier GDP.kml de manière optimisée"""
    try:
        # Vérifier si un cache local existe (avec clé de précision)
        cache_suffix = "_hq" if high_precision else ""
        cache_file = f"gdp_cache{cache_suffix}.pkl"
        kml_file = "GDP.kml"
        
        # Vérifier si le cache est plus récent que le fichier KML
        if (os.path.exists(cache_file) and os.path.exists(kml_file) and 
            os.path.getmtime(cache_file) > os.path.getmtime(kml_file)):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        tree = ET.parse(kml_file)
        root = tree.getroot()
        
        # Namespace KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        gdp_data = []
        
        # Parcourir tous les Placemark
        for placemark in root.findall('.//kml:Placemark', ns):
            # Récupérer les données étendues
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                gdp_info = {}
                
                # Extraire seulement les données essentielles
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        gdp_info[name] = value
                
                # Récupérer la géométrie (avec précision variable)
                geometry = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if geometry is None:
                    # Essayer MultiGeometry pour les GDP
                    geometry = placemark.find('.//kml:MultiGeometry/kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                
                if geometry is not None and geometry.text:
                    # Parser les coordonnées du polygone
                    coords_text = geometry.text.strip()
                    coord_pairs = []
                    coords_list = coords_text.split()
                    
                    if high_precision:
                        # Mode haute précision : garder beaucoup plus de points
                        if len(coords_list) <= 200:
                            step = 1  # Tous les points
                        elif len(coords_list) <= 1000:
                            step = max(1, len(coords_list) // 500)  # Jusqu'à 500 points
                        else:
                            step = max(1, len(coords_list) // 800)  # Jusqu'à 800 points
                    else:
                        # Mode optimisé : simplification adaptative
                        if len(coords_list) <= 100:
                            step = 1  # Garder tous les points pour les petits polygones
                        elif len(coords_list) <= 500:
                            step = max(1, len(coords_list) // 200)  # Jusqu'à 200 points
                        elif len(coords_list) <= 2000:
                            step = max(1, len(coords_list) // 300)  # Jusqu'à 300 points
                        else:
                            step = max(1, len(coords_list) // 400)  # Jusqu'à 400 points max
                    
                    for i in range(0, len(coords_list), step):
                        coord = coords_list[i]
                        if ',' in coord:
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                try:
                                    coord_pairs.append([float(parts[1]), float(parts[0])])  # [lat, lon]
                                except ValueError:
                                    continue
                    
                    if coord_pairs:
                        gdp_info['coordinates'] = coord_pairs
                
                if gdp_info and 'Poste' in gdp_info:
                    gdp_data.append(gdp_info)
        
        df = pd.DataFrame(gdp_data)
        
        # Sauvegarder en cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            pass
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du parsing du fichier GDP.kml : {e}")
        return pd.DataFrame()

# Fonction pour parser le KML des GMR
def parse_gmr_kml():
    """Parse le fichier GMR.kml et retourne un DataFrame avec les GMR"""
    try:
        tree = ET.parse("GMR.kml")
        root = tree.getroot()
        
        # Namespace KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        gmr_data = []
        
        # Parcourir tous les Placemark
        for placemark in root.findall('.//kml:Placemark', ns):
            # Récupérer les données étendues
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                gmr_info = {}
                
                # Extraire les données
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    name = simple_data.get('name')
                    value = simple_data.text
                    if name and value:
                        gmr_info[name] = value
                
                # Récupérer la géométrie (Polygon ou autres)
                geometry = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if geometry is not None and geometry.text:
                    # Parser les coordonnées du polygone
                    coords_text = geometry.text.strip()
                    coord_pairs = []
                    for coord in coords_text.split():
                        if ',' in coord:
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                coord_pairs.append([float(parts[1]), float(parts[0])])  # [lat, lon]
                    
                    if coord_pairs:
                        gmr_info['coordinates'] = coord_pairs
                
                if gmr_info:
                    gmr_data.append(gmr_info)
        
        return pd.DataFrame(gmr_data)
        
    except Exception as e:
        st.error(f"Erreur lors du parsing du fichier GMR.kml : {e}")
        return pd.DataFrame()

# Fonction pour vérifier si un point est dans un polygone (optimisée)
def point_in_polygon(point_lat, point_lon, polygon_coords):
    """Vérifie si un point est à l'intérieur d'un polygone - version optimisée"""
    try:
        x, y = float(point_lon), float(point_lat)
        n = len(polygon_coords)
        inside = False
        
        # Vérification rapide des limites pour éviter les calculs inutiles
        lats = [coord[0] for coord in polygon_coords]
        lons = [coord[1] for coord in polygon_coords]
        if not (min(lats) <= y <= max(lats) and min(lons) <= x <= max(lons)):
            return False
        
        p1x, p1y = polygon_coords[0][1], polygon_coords[0][0]
        for i in range(1, n + 1):
            p2x, p2y = polygon_coords[i % n][1], polygon_coords[i % n][0]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    except:
        return False

# Cache pour les recherches GMR
@st.cache_data(ttl=1800)  # Cache pendant 30 minutes
def find_gmr_for_poste(poste_lat, poste_lon, gmr_df):
    """Trouve le GMR qui contient le poste donné - version avec cache"""
    try:
        for idx, gmr in gmr_df.iterrows():
            if 'coordinates' in gmr and gmr['coordinates']:
                if point_in_polygon(poste_lat, poste_lon, gmr['coordinates']):
                    return gmr
        return None
    except:
        return None

# Cache pour les recherches GDP
@st.cache_data(ttl=1800)  # Cache pendant 30 minutes
def find_gdp_for_poste(poste_lat, poste_lon, gdp_df):
    """Trouve le GDP qui contient le poste donné - version avec cache"""
    try:
        for idx, gdp in gdp_df.iterrows():
            if 'coordinates' in gdp and gdp['coordinates']:
                if point_in_polygon(poste_lat, poste_lon, gdp['coordinates']):
                    return gdp
        return None
    except:
        return None

# Fonction pour créer la carte avec GMR, GDP et postes (optimisée)
def create_map_with_gmr_gdp(postes_result, gmr_df, gdp_df, show_all_gmr=False, show_all_gdp=False):
    """Crée une carte avec les GMR, GDP et les postes trouvés - version optimisée"""
    # Créer la carte centrée sur la France
    m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
    
    # Ajouter seulement les GMR pertinents si show_all_gmr=False
    if show_all_gmr:
        gmr_to_show = gmr_df
    else:
        # Ne montrer que les GMR qui contiennent des postes recherchés
        relevant_gmr_indices = set()
        for idx, poste in postes_result.iterrows():
            if 'latitude' in poste and 'longitude' in poste:
                for gmr_idx, gmr in gmr_df.iterrows():
                    if 'coordinates' in gmr and gmr['coordinates']:
                        if point_in_polygon(poste['latitude'], poste['longitude'], gmr['coordinates']):
                            relevant_gmr_indices.add(gmr_idx)
                            break
        
        gmr_to_show = gmr_df.loc[list(relevant_gmr_indices)] if relevant_gmr_indices else pd.DataFrame()
    
    # Ajouter seulement les GDP pertinents si show_all_gdp=False
    if show_all_gdp:
        gdp_to_show = gdp_df
    else:
        # Ne montrer que les GDP qui contiennent des postes recherchés
        relevant_gdp_indices = set()
        for idx, poste in postes_result.iterrows():
            if 'latitude' in poste and 'longitude' in poste:
                for gdp_idx, gdp in gdp_df.iterrows():
                    if 'coordinates' in gdp and gdp['coordinates']:
                        if point_in_polygon(poste['latitude'], poste['longitude'], gdp['coordinates']):
                            relevant_gdp_indices.add(gdp_idx)
                            break
        
        gdp_to_show = gdp_df.loc[list(relevant_gdp_indices)] if relevant_gdp_indices else pd.DataFrame()
    
    # Ajouter les GMR (polygones en bleu)
    for idx, gmr in gmr_to_show.iterrows():
        if 'coordinates' in gmr and gmr['coordinates']:
            popup_text = f"""
            <b>GMR:</b> {gmr.get('GMR_alias', 'N/A')}<br>
            <b>Code:</b> {gmr.get('GMR', 'N/A')}<br>
            <b>Siège:</b> {gmr.get('Siège_du_', 'N/A')}
            """
            
            folium.Polygon(
                locations=gmr['coordinates'],
                popup=folium.Popup(popup_text, max_width=300),
                color='blue',
                weight=2,
                fillColor='lightblue',
                fillOpacity=0.3
            ).add_to(m)
    
    # Ajouter les GDP (polygones en vert)
    for idx, gdp in gdp_to_show.iterrows():
        if 'coordinates' in gdp and gdp['coordinates']:
            popup_text = f"""
            <b>GDP - Poste:</b> {gdp.get('Poste', 'N/A')}<br>
            <b>Code:</b> {gdp.get('Code', 'N/A')}<br>
            <b>Centre:</b> {gdp.get('Nom_du_cen', 'N/A')}<br>
            <b>GMR:</b> {gdp.get('GMR', 'N/A')}<br>
            <b>Siège:</b> {gdp.get('Siège_du_', 'N/A')}
            """
            
            folium.Polygon(
                locations=gdp['coordinates'],
                popup=folium.Popup(popup_text, max_width=300),
                color='green',
                weight=2,
                fillColor='lightgreen',
                fillOpacity=0.2
            ).add_to(m)
    
    # Ajouter les postes trouvés
    for idx, poste in postes_result.iterrows():
        if 'latitude' in poste and 'longitude' in poste:
            # Trouver le GMR correspondant
            gmr_info = find_gmr_for_poste(poste['latitude'], poste['longitude'], gmr_df)
            gmr_text = ""
            if gmr_info is not None:
                gmr_text = f"<br><b>GMR:</b> {gmr_info.get('GMR_alias', 'N/A')}<br><b>Siège GMR:</b> {gmr_info.get('Siège_du_', 'N/A')}"
            
            # Trouver le GDP correspondant
            gdp_info = find_gdp_for_poste(poste['latitude'], poste['longitude'], gdp_df)
            gdp_text = ""
            if gdp_info is not None:
                gdp_text = f"<br><b>GDP:</b> {gdp_info.get('Poste', 'N/A')}<br><b>Code GDP:</b> {gdp_info.get('Code', 'N/A')}<br><b>Centre GDP:</b> {gdp_info.get('Nom_du_cen', 'N/A')}"
            
            popup_text = f"""
            <b>Poste:</b> {poste.get('Nom poste', poste.get('Nom_du_pos', 'N/A'))}<br>
            <b>ID:</b> {poste.get('Identifian', 'N/A')}<br>
            <b>Tension:</b> {poste.get('Tension_d', 'N/A')}{gmr_text}{gdp_text}
            """
            
            folium.Marker(
                location=[poste['latitude'], poste['longitude']],
                popup=folium.Popup(popup_text, max_width=350),
                icon=folium.Icon(color='red', icon='bolt')
            ).add_to(m)
    
    return m

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
        high_precision = st.checkbox("🎯 Précision maximale des polygones GMR (plus lent au chargement)", value=False)
        st.info("💡 La précision maximale améliore les contours des GMR mais augmente le temps de chargement initial.")

    # Charger les données KML avec cache et indicateur de progression
    cache_key = f"data_loaded_{high_precision}"
    if cache_key not in st.session_state:
        with st.spinner("🔄 Chargement initial des données (mis en cache pour les prochaines utilisations)..."):
            postes_df, gmr_df, gdp_df = load_and_cache_kml_data(high_precision)
            st.session_state[cache_key] = True
            st.session_state['current_precision'] = high_precision
    else:
        # Vérifier si la précision a changé
        if st.session_state.get('current_precision', False) != high_precision:
            with st.spinner("🔄 Rechargement avec nouvelle précision..."):
                postes_df, gmr_df, gdp_df = load_and_cache_kml_data(high_precision)
                st.session_state['current_precision'] = high_precision
        else:
            # Chargement rapide depuis le cache
            postes_df, gmr_df, gdp_df = load_and_cache_kml_data(high_precision)
    
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
            nom_col = 'Nom poste' if 'Nom poste' in postes_df.columns else 'Nom_du_pos'
            result = postes_df[postes_df[nom_col].str.lower().str.contains(search_nom.lower(), na=False)]
            
            if not result.empty:
                # Créer deux colonnes : tableau et carte
                col_table, col_map = st.columns([1, 1])
                
                with col_table:
                    st.subheader("📋 Résultats de la recherche")
                    # Afficher le tableau des résultats
                    display_cols = [col for col in result.columns if col in ['Nom poste', 'Nom_du_pos', 'Identifian', 'Tension_d', 'latitude', 'longitude']]
                    st.dataframe(result[display_cols], use_container_width=True)

                    # Afficher les liens Google Maps et Waze pour chaque résultat
                    st.subheader("🗺️ Liens de navigation")
                    for idx, row in result.iterrows():
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
                    for idx, row in result.iterrows():
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
                    if gmr_postes:
                        st.markdown("### 🔵 Groupements de Maintenance Régionale (GMR)")
                        for gmr_key, postes in gmr_postes.items():
                            gmr_alias, gmr_code, gmr_siege = gmr_key
                            st.info(f"📍 {', '.join(postes)}")
                            st.write(f"• **GMR :** {gmr_alias}")
                            st.write(f"• **Code GMR :** {gmr_code}")
                            st.write(f"• **Siège :** {gmr_siege}")
                    else:
                        st.warning("Aucun GMR identifié pour les postes trouvés.")
                    # Afficher les GDP
                    if gdp_postes:
                        st.markdown("### 🟢 Groupements De Poste (GDP)")
                        for gdp_key, postes in gdp_postes.items():
                            gdp_poste, gdp_code, gdp_centre, gdp_siege = gdp_key
                            st.success(f"📍 {', '.join(postes)}")
                            st.write(f"• **GDP :** {gdp_poste}")
                            st.write(f"• **Code GDP :** {gdp_code}")
                            st.write(f"• **Centre :** {gdp_centre}")
                            st.write(f"• **Siège :** {gdp_siege}")
                    else:
                        st.warning("Aucun GDP identifié pour les postes trouvés.")
                
                with col_map:
                    st.subheader("🗺️ Carte des postes, GMR et GDP")
                    
                    with st.spinner("🗺️ Génération de la carte..."):
                        # Créer et afficher la carte
                        map_obj = create_map_with_gmr_gdp(result, gmr_df, gdp_df, show_all_gmr, show_all_gdp)
                        
                        # Afficher la carte avec une clé unique pour éviter le re-rendu
                        map_key = f"map_{hash(search_nom)}_{len(result)}_{show_all_gmr}_{show_all_gdp}"
                        
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
    st.markdown("<div style='text-align:center; color:gray;'>v0.4.0 - DB and APP by Guillaume B. 🍔</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>Special thanks to PascaL B. , Kévin G. and Hervé G.</div>", unsafe_allow_html=True)
