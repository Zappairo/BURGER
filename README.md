
# BURGER 🍔

## Fonctionnalités principales
- Authentification via MongoDB (mot de passe hashé, gestion avancée)
- Recherche de postes RTE par nom (cache, tolérance orthographique)
- Visualisation cartographique interactive (Folium, KML, polygones GMR/GDP)
- Affichage détaillé des postes, zones des GMR et GDP avec popups enrichis
- Gestion du cache pour accélérer les recherches et l'affichage de la carte

## 🚀 Installation

### Prérequis
```bash
pip install streamlit pandas openpyxl pymongo bcrypt folium streamlit_folium
```

### Fichiers nécessaires
- Placez les fichiers KML dans le dossier `kml/` :
  - `GDP.kml`, `GMR.kml`, `Poste.kml`
- Les fichiers de cache seront générés automatiquement dans `data/`.

### Configuration MongoDB
1. **Secrets Streamlit** :
   Créez `.streamlit/secrets.toml` et ajoutez :
   ```toml
   MONGODB_URL = "mongodb+srv://username:password@cluster.mongodb.net/"
   ```
2. **Ou variable d'environnement** :
   ```powershell
   $env:MONGODB_URL = "mongodb+srv://username:password@cluster.mongodb.net/"
   ```

### Lancement de l'application
```powershell
streamlit run app.py
```

## 🔐 Authentification & gestion des comptes
- L'authentification se fait par compte utilisateur, mot de passe hashé (bcrypt), stocké sur MongoDB.
- Pour créer ou modifier un compte :
```powershell
python manage_passwords.py
```

## 📁 Structure du projet
```
BURGER/
├── app.py                     # Application principale Streamlit
├── manage_passwords.py        # Script de gestion des comptes utilisateurs
├── requirements.txt           # Dépendances Python
├── README.md                  # Ce fichier
├── secrets.toml.example       # Exemple de configuration MongoDB
├── kml/                       # Fichiers KML (GDP.kml, GMR.kml, Poste.kml)
├── data/                      # Fichiers de cache générés automatiquement
├── src/
│   ├── config.py              # Configuration des chemins et secrets
│   ├── auth.py                # Authentification et gestion MongoDB
│   ├── map_utils.py           # Fonctions de cartographie et polygones
│   ├── parsers.py             # Parsers KML optimisés
│   ├── performance_config.py  # Paramètres de performance et d'affichage
│   └── __init__.py
├── pages/
│   └── _Planning_Equipes      # Import du planning en csv pour envoyer les points GPS et les infos des postes aux équipes 
└── utils/                     # Utilitaires divers

```

## ⚙️ Options de performance
- Précision des tracés polygones GMR/GDP ajustable (peu précis - rapide, très précis - lent)
- Création d'un cache à chaque recherche pour éviter des rechargements.

## ℹ️ Conseils d'utilisation
- Pour une recherche efficace, saisissez au moins le nom du poste au complet avec son article.
- La recherche va vous faire apparaître chaque tension du poste, une par ligne, ainsi que son code NAT sa latitude et sa longitude.
- Le poste va être situé sur une carte interactive, cela fera apparaître son GMR et son GDP.

---
**Développé par Guillaume B.** 🍔  
*Remerciements chaleureux à Pascal B., Kévin G. et Hervé G.*

Version 1.1.2
