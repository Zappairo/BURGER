# BURGER 🍔 

**Base Unifiée de Référencement des Grands Equipements RTE**

Une application Streamlit sécurisée pour rechercher et localiser les postes électriques HTB de RTE et les postes HTB/HTA RTE/Enedis.

## ✨ Fonctionnalités
- 🔐 Authentification sécurisée via MongoDB
- 🔍 Recherche rapide par nom de poste
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
- L'accès nécessite un compte utilisateur MongoDB
- Contactez Guillaume B. pour obtenir vos identifiants
- Environ 100 postes sur 2700 sont validés à 100% (MAJ: 28/07/2025)

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

Version 0.1.1