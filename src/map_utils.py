"""
Fonctions utilitaires pour la carte (folium, polygones, etc.)
"""
import folium
import pandas as pd

def point_in_polygon(point_lat, point_lon, polygon_coords):
    """Vérifie si un point est à l'intérieur d'un polygone - version optimisée"""
    try:
        x, y = float(point_lon), float(point_lat)
        n = len(polygon_coords)
        inside = False
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

def create_map_with_gmr_gdp(postes_result, gmr_df, gdp_df, show_all_gmr=False, show_all_gdp=False):
    # ...existing code...
    m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
    if show_all_gmr:
        gmr_to_show = gmr_df
    else:
        relevant_gmr_indices = set()
        for idx, poste in postes_result.iterrows():
            if 'latitude' in poste and 'longitude' in poste:
                for gmr_idx, gmr in gmr_df.iterrows():
                    if 'coordinates' in gmr and gmr['coordinates']:
                        if point_in_polygon(poste['latitude'], poste['longitude'], gmr['coordinates']):
                            relevant_gmr_indices.add(gmr_idx)
                            break
        gmr_to_show = gmr_df.loc[list(relevant_gmr_indices)] if relevant_gmr_indices else pd.DataFrame()
    if show_all_gdp:
        gdp_to_show = gdp_df
    else:
        relevant_gdp_indices = set()
        for idx, poste in postes_result.iterrows():
            if 'latitude' in poste and 'longitude' in poste:
                for gdp_idx, gdp in gdp_df.iterrows():
                    if 'coordinates' in gdp and gdp['coordinates']:
                        if point_in_polygon(poste['latitude'], poste['longitude'], gdp['coordinates']):
                            relevant_gdp_indices.add(gdp_idx)
                            break
        gdp_to_show = gdp_df.loc[list(relevant_gdp_indices)] if relevant_gdp_indices else pd.DataFrame()
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
    for idx, poste in postes_result.iterrows():
        if 'latitude' in poste and 'longitude' in poste:
            gmr_info = find_gmr_for_poste(poste['latitude'], poste['longitude'], gmr_df)
            gmr_text = ""
            if gmr_info is not None:
                gmr_text = f"<br><b>GMR:</b> {gmr_info.get('GMR_alias', 'N/A')}<br><b>Siège GMR:</b> {gmr_info.get('Siège_du_', 'N/A')}"
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
