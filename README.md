
# BURGER 🍔

## Fonctionnalités principales
- Authentification sécurisée via MongoDB (mot de passe hashé, gestion avancée)
- Recherche optimisée de postes RTE par nom (cache, tolérance orthographique)
- Visualisation cartographique interactive (Folium, KML, polygones GMR/GDP)
- Affichage détaillé des postes, zones des GMR et GDP avec popups enrichis
- Gestion intelligente du cache pour accélérer les recherches et l'affichage de la carte

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
└── utils/                     # Utilitaires divers
```

## ⚙️ Options de performance
- Précision des polygones GMR/GDP ajustable (rapide ou très précis mais très lent)
- Cache intelligent pour éviter les rechargements inutiles
- Affichage optimisé pour de nombreux postes ou polygones

## ℹ️ Conseils d'utilisation
- Pour une recherche efficace, saisissez au moins 2 caractères du nom du poste.
- Les résultats sont limités pour garantir la performance.

---
**Développé par Guillaume B.** 🍔  
*Remerciements spéciaux à Pascal B., Kévin G. et Hervé G.*

Version 1.1.0
