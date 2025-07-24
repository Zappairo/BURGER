import streamlit as st
import pandas as pd
# Utiliser toute la largeur de la fenêtre
st.set_page_config(layout="wide")

# Charger le fichier Excel
df = pd.read_excel("fusion_postes_resultat.xlsx")

st.title("BURGER 🍔 : Base Unifiée de Référencement des Grands Equipements RTE")

# Saisie du nom du poste
col1, col2, col3, col4, col5 = st.columns([1,2,3,2,1])
with col3:
    search_nom = st.text_input("Entrez le nom du poste:")

if search_nom:
    # Filtrer les lignes où le nom du poste correspond (insensible à la casse)
    result = df[df['Nom poste'].str.lower().str.contains(search_nom.lower(), na=False)]
    if not result.empty:
        st.write("Résultats trouvés :")
        st.dataframe(result)
        for idx, row in result.iterrows():
            # Récupérer les coordonnées
            lat = row.get('Geo Point', None)
            if lat:
                # Si la colonne Geo Point contient une chaîne comme 'lat,lon', séparer
                try:
                    lat_str, lon_str = str(lat).split(',')
                    lat_str = lat_str.strip()
                    lon_str = lon_str.strip()
                    url = f"https://www.google.com/maps/search/?api=1&query={lat_str},{lon_str}"
                    st.markdown(f"[Voir sur Google Maps]({url})")
                except Exception:
                    pass
    else:
        st.warning("Aucun poste trouvé avec ce nom.")

st.markdown("<hr style='margin-top:40px;margin-bottom:10px;'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:gray;'>DB and APP by Guillaume B. 🍔</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:gray;'>Special thanks to Kévin G. and Hervé G.</div>", unsafe_allow_html=True)