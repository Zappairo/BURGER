# BURGER 🍔 

## ✨ Fonctionnalités
- 🔐 Authentification MongoDB et hashage de mot de passe
- 🔍 Recherche rapide par nom
- 📊 Affichage des informations détaillées
- 📍 Géolocalisation avec lien Google Maps
- 🎯 Interface simple et intuitive

## 🚀 Installation

### Prérequis
```bash
pip install streamlit pandas openpyxl pymongo bcrypt
```

### Configuration
1. **Base de données** : Placez le fichier `fusion_postes_resultat.xlsx` dans le dossier
2. **MongoDB** : Configurez l'URL MongoDB dans `.streamlit/secrets.toml` :
   ```toml
   MONGODB_URL = "mongodb+srv://username:password@cluster.mongodb.net/"
   ```
   Ou via variable d'environnement :
   ```bash
   set MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
   ```

### Lancement
```bash
streamlit run app.py
```

## 🔐 Authentification
- L'authentification se fait par compte avec mot de passe hashés et stocké sur mongoDB
- La création de compte se fait avec manage_passwords.py
```bash
python manage_passwords.py
```
- Environ 700 lignes de données sur 2700 sont validés à 100% (MAJ: 04/08/2025)

## 📁 Structure
```
BURGER/
├── app.py                          # Application principale
├── fusion_postes_resultat.xlsx     # Base de données des postes
├── .streamlit/
│   └── secrets.toml               # Configuration MongoDB (non versionnée)
└── README.md                       # Ce fichier
```

---
**Développé par Guillaume B.** 🍔  
*Remerciements spéciaux à Kévin G. et Hervé G.*

Version 0.1.4
