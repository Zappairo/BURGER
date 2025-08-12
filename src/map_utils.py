"""
Fonctions utilitaires pour la carte (folium, polygones, etc.) - Version optimisée
"""
import folium
import pandas as pd
import streamlit as st
from .performance_config import CACHE_TTL_SEARCH, MAP_DEFAULT_ZOOM, MAP_SINGLE_POSTE_ZOOM, POPUP_MAX_WIDTH

@st.cache_data(ttl=CACHE_TTL_SEARCH)
def point_in_polygon(point_lat, point_lon, polygon_coords):
    """Vérifie si un point est à l'intérieur d'un polygone - version optimisée avec cache"""
    try:
        x, y = float(point_lon), float(point_lat)
        n = len(polygon_coords)
        inside = False
        
        # Optimisation préliminaire : vérification de la bounding box
        lats = [coord[0] for coord in polygon_coords]
        lons = [coord[1] for coord in polygon_coords]
        if not (min(lats) <= y <= max(lats) and min(lons) <= x <= max(lons)):
            return False
        
        # Algorithme ray casting optimisé
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
    except Exception:
        return False

@st.cache_data(ttl=CACHE_TTL_SEARCH, show_spinner=False)
def create_map_with_gmr_gdp(postes_result, gmr_df, gdp_df, show_all_gmr=False, show_all_gdp=False):
    """Crée une carte Folium optimisée avec postes, GMR et GDP - Version stable anti-reload"""
    
    # Créer la carte centrée sur la France avec options de stabilité
    m = folium.Map(
        location=[46.603354, 1.888334], 
        zoom_start=MAP_DEFAULT_ZOOM,
        tiles='OpenStreetMap',
        prefer_canvas=True,  # Optimisation pour de nombreux éléments
        # Options pour réduire les interactions problématiques
        zoom_control=True,
        scrollWheelZoom=True,
        doubleClickZoom=True,
        dragging=True
    )
    
    # Optimisation : déterminer les polygones à afficher en fonction des options
    if show_all_gmr:
        gmr_to_show = gmr_df
    else:
        # Ne montrer que les GMR pertinents pour les postes sélectionnés
        relevant_gmr_indices = set()
        for idx, poste in postes_result.iterrows():
            if pd.notna(poste.get('latitude')) and pd.notna(poste.get('longitude')):
                for gmr_idx, gmr in gmr_df.iterrows():
                    if 'coordinates' in gmr and gmr['coordinates']:
                        if point_in_polygon(poste['latitude'], poste['longitude'], gmr['coordinates']):
                            relevant_gmr_indices.add(gmr_idx)
                            break  # Un poste ne peut être que dans un GMR
        gmr_to_show = gmr_df.loc[list(relevant_gmr_indices)] if relevant_gmr_indices else pd.DataFrame()

    if show_all_gdp:
        gdp_to_show = gdp_df
    else:
        # Ne montrer que les GDP pertinents pour les postes sélectionnés
        relevant_gdp_indices = set()
        for idx, poste in postes_result.iterrows():
            if pd.notna(poste.get('latitude')) and pd.notna(poste.get('longitude')):
                for gdp_idx, gdp in gdp_df.iterrows():
                    if 'coordinates' in gdp and gdp['coordinates']:
                        if point_in_polygon(poste['latitude'], poste['longitude'], gdp['coordinates']):
                            relevant_gdp_indices.add(gdp_idx)
                            break  # Un poste ne peut être que dans un GDP
        gdp_to_show = gdp_df.loc[list(relevant_gdp_indices)] if relevant_gdp_indices else pd.DataFrame()

    # Ajouter les polygones GMR avec popups améliorés
    for idx, gmr in gmr_to_show.iterrows():
        if 'coordinates' in gmr and gmr['coordinates'] and len(gmr['coordinates']) > 2:
            popup_text = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 13px; max-width: 280px; padding: 10px; line-height: 1.4; background-color: white; border-radius: 5px;">
                <div style="color: #1f4e79; font-weight: bold; font-size: 15px; margin-bottom: 8px; border-bottom: 2px solid #1f4e79; padding-bottom: 4px;">
                    &#x1F535; GMR
                </div>
                <div style="color: #333;">
                    <div style="font-weight: bold; margin-bottom: 2px;">{gmr.get('GMR_alias', 'N/A')}</div>
                    <div style="color: #666; font-size: 12px;">
                        <span style="font-weight: 600;">Code:</span> {gmr.get('GMR', 'N/A')}<br>
                        <span style="font-weight: 600;">Siège:</span> {gmr.get('Siège_du_', 'N/A')}
                    </div>
                </div>
            </div>
            """
            folium.Polygon(
                locations=gmr['coordinates'],
                popup=folium.Popup(popup_text, max_width=320, parse_html=False),
                color='blue',
                weight=2,
                fillColor='lightblue',
                fillOpacity=0.3,
                tooltip=folium.Tooltip(f"GMR: {gmr.get('GMR_alias', 'N/A')}", sticky=False)
            ).add_to(m)

    # Ajouter les polygones GDP avec popups améliorés
    for idx, gdp in gdp_to_show.iterrows():
        if 'coordinates' in gdp and gdp['coordinates'] and len(gdp['coordinates']) > 2:
            popup_text = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 13px; max-width: 280px; padding: 10px; line-height: 1.4; background-color: white; border-radius: 5px;">
                <div style="color: #2d5016; font-weight: bold; font-size: 15px; margin-bottom: 8px; border-bottom: 2px solid #2d5016; padding-bottom: 4px;">
                    &#x1F7E2; GDP
                </div>
                <div style="color: #333;">
                    <div style="font-weight: bold; margin-bottom: 2px;">{gdp.get('Poste', 'N/A')}</div>
                    <div style="color: #666; font-size: 12px;">
                        <span style="font-weight: 600;">Code:</span> {gdp.get('Code', 'N/A')}<br>
                        <span style="font-weight: 600;">Centre:</span> {gdp.get('Nom_du_cen', 'N/A')}<br>
                        <span style="font-weight: 600;">GMR:</span> {gdp.get('GMR', 'N/A')}
                    </div>
                </div>
            </div>
            """
            folium.Polygon(
                locations=gdp['coordinates'],
                popup=folium.Popup(popup_text, max_width=320, parse_html=False),
                color='green',
                weight=2,
                fillColor='lightgreen',
                fillOpacity=0.2,
                tooltip=folium.Tooltip(f"GDP: {gdp.get('Poste', 'N/A')}", sticky=False)
            ).add_to(m)

    # Ajouter les marqueurs de postes avec informations optimisées
    coordinates_for_centering = []
    
    for idx, poste in postes_result.iterrows():
        if pd.notna(poste.get('latitude')) and pd.notna(poste.get('longitude')):
            lat, lon = float(poste['latitude']), float(poste['longitude'])
            coordinates_for_centering.append([lat, lon])
            
            # Informations contextuelles optimisées
            gmr_info = find_gmr_for_poste(lat, lon, gmr_df)
            gdp_info = find_gdp_for_poste(lat, lon, gdp_df)
            
            # Construction du popup compatible cloud avec styles inline robustes
            popup_content = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 13px; max-width: 280px; padding: 10px; line-height: 1.4; background-color: white; border-radius: 5px;">
                <div style="color: #d73027; font-weight: bold; font-size: 15px; margin-bottom: 8px; border-bottom: 2px solid #d73027; padding-bottom: 4px;">
                    &#x1F534; POSTE RTE
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="font-weight: bold; color: #333; margin-bottom: 2px;">{poste.get('Nom_du_pos', 'N/A')}</div>
                    <div style="color: #666; font-size: 12px;">
                        <span style="font-weight: 600;">ID:</span> {poste.get('Identifian', 'N/A')}<br>
                        <span style="font-weight: 600;">Tension:</span> {poste.get('Tension_d', 'N/A')}<br>
                        <span style="font-weight: 600;">Coordonnées:</span> {lat:.4f}, {lon:.4f}
                    </div>
                </div>
            """
            
            if gmr_info is not None:
                popup_content += f"""
                <div style="border-top: 1px solid #e0e0e0; padding-top: 8px; margin-bottom: 8px;">
                    <div style="color: #1f4e79; font-weight: bold; font-size: 13px; margin-bottom: 3px;">
                        &#x1F535; GMR - {gmr_info.get('GMR_alias', 'N/A')}
                    </div>
                    <div style="color: #666; font-size: 12px;">
                        <span style="font-weight: 600;">Siège:</span> {gmr_info.get('Siège_du_', 'N/A')}
                    </div>
                </div>
                """
            
            if gdp_info is not None:
                popup_content += f"""
                <div style="border-top: 1px solid #e0e0e0; padding-top: 8px;">
                    <div style="color: #2d5016; font-weight: bold; font-size: 13px; margin-bottom: 3px;">
                        &#x1F7E2; GDP - {gdp_info.get('Poste', 'N/A')}
                    </div>
                    <div style="color: #666; font-size: 12px;">
                        <span style="font-weight: 600;">Centre:</span> {gdp_info.get('Nom_du_cen', 'N/A')}
                    </div>
                </div>
                """
            
            popup_content += "</div>"
            
            # Marqueur optimisé avec événements contrôlés
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=320, parse_html=False),
                tooltip=folium.Tooltip(f"Poste: {poste.get('Nom_du_pos', 'N/A')}", sticky=False),
                icon=folium.Icon(
                    color='red', 
                    icon='bolt',
                    prefix='fa'
                )
            ).add_to(m)

    # Centrage automatique optimisé sur les postes sélectionnés
    if coordinates_for_centering:
        if len(coordinates_for_centering) == 1:
            # Un seul poste : centrer dessus avec zoom approprié
            m.location = coordinates_for_centering[0]
            m.zoom_start = MAP_SINGLE_POSTE_ZOOM
        else:
            # Plusieurs postes : ajuster la vue pour tous les voir
            m.fit_bounds(coordinates_for_centering, padding=(20, 20))

    return m

@st.cache_data(ttl=CACHE_TTL_SEARCH)
def find_gmr_for_poste(poste_lat, poste_lon, gmr_df):
    """Trouve le GMR qui contient le poste donné - version optimisée avec cache"""
    try:
        for idx, gmr in gmr_df.iterrows():
            if 'coordinates' in gmr and gmr['coordinates']:
                if point_in_polygon(poste_lat, poste_lon, gmr['coordinates']):
                    return gmr
        return None
    except Exception:
        return None

@st.cache_data(ttl=CACHE_TTL_SEARCH)
def find_gdp_for_poste(poste_lat, poste_lon, gdp_df):
    """Trouve le GDP qui contient le poste donné - version optimisée avec cache"""
    try:
        for idx, gdp in gdp_df.iterrows():
            if 'coordinates' in gdp and gdp['coordinates']:
                if point_in_polygon(poste_lat, poste_lon, gdp['coordinates']):
                    return gdp
        return None
    except Exception:
        return None
