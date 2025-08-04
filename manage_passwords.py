"""
Script pour créer des mots de passe hashés et les ajouter à MongoDB
"""
import pymongo
import bcrypt
import getpass
from datetime import datetime

def hash_password(password):
    """Hashe un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def update_user_password():
    """Met à jour le mot de passe d'un utilisateur existant"""
    
    # URL MongoDB - À CONFIGURER
    mongodb_url = input("Entrez l'URL MongoDB : ")
    
    try:
        # Connexion à MongoDB
        client = pymongo.MongoClient(mongodb_url)
        db = client["burger_app"]
        users_collection = db["users"]
        
        print("🍔 BURGER - Mise à jour des mots de passe")
        print("=" * 50)
        
        # Lister les utilisateurs existants
        print("📋 Utilisateurs existants:")
        for user in users_collection.find({}, {"username": 1, "role": 1}):
            print(f"  - {user['username']} ({user.get('role', 'N/A')})")
        
        print()
        username = input("Nom d'utilisateur à mettre à jour: ")
        
        # Vérifier si l'utilisateur existe
        user = users_collection.find_one({"username": username})
        if not user:
            print(f"❌ Utilisateur '{username}' non trouvé")
            return
        
        # Demander le nouveau mot de passe
        password = getpass.getpass("Nouveau mot de passe: ")
        confirm_password = getpass.getpass("Confirmer le mot de passe: ")
        
        if password != confirm_password:
            print("❌ Les mots de passe ne correspondent pas")
            return
        
        # Hasher le mot de passe
        password_hash = hash_password(password)
        
        # Mettre à jour l'utilisateur
        result = users_collection.update_one(
            {"username": username},
            {"$set": {"password_hash": password_hash}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Mot de passe mis à jour pour '{username}'")
        else:
            print(f"❌ Échec de la mise à jour pour '{username}'")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")

def test_password():
    """Teste un mot de passe contre un utilisateur"""
    
    mongodb_url = input("Entrez l'URL MongoDB : ")
    
    try:
        client = pymongo.MongoClient(mongodb_url)
        db = client["burger_app"]
        users_collection = db["users"]
        
        username = input("Nom d'utilisateur: ")
        password = getpass.getpass("Mot de passe à tester: ")
        
        user = users_collection.find_one({"username": username})
        if not user:
            print(f"❌ Utilisateur '{username}' non trouvé")
            return
        
        # Vérifier le mot de passe
        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            print("✅ Mot de passe correct !")
        else:
            print("❌ Mot de passe incorrect")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")

def create_user():
    """Crée un nouveau compte utilisateur"""
    
    mongodb_url = input("Entrez l'URL MongoDB : ")
    
    try:
        # Connexion à MongoDB
        client = pymongo.MongoClient(mongodb_url)
        db = client["burger_app"]
        users_collection = db["users"]
        
        print("🍔 BURGER - Création d'un nouveau compte")
        print("=" * 50)
        
        # Lister les utilisateurs existants
        print("📋 Utilisateurs existants:")
        for user in users_collection.find({}, {"username": 1, "role": 1}):
            print(f"  - {user['username']} ({user.get('role', 'N/A')})")
        
        print()
        username = input("Nom d'utilisateur: ")
        
        # Vérifier si l'utilisateur existe déjà
        if users_collection.find_one({"username": username}):
            print(f"❌ L'utilisateur '{username}' existe déjà")
            return
        
        # Demander le rôle
        print("\nRôles disponibles:")
        print("1. admin - Accès complet")
        print("2. employee - Accès employé")
        print("3. user - Accès client")
        
        role_choice = input("Choisissez le rôle (1, 2 ou 3): ")
        role_map = {"1": "admin", "2": "employee", "3": "user"}
        role = role_map.get(role_choice, "user")
        
        # Demander le mot de passe
        password = getpass.getpass("Mot de passe: ")
        confirm_password = getpass.getpass("Confirmer le mot de passe: ")
        
        if password != confirm_password:
            print("❌ Les mots de passe ne correspondent pas")
            return
        
        if len(password) < 6:
            print("❌ Le mot de passe doit contenir au moins 6 caractères")
            return
        
        # Hasher le mot de passe
        password_hash = hash_password(password)
        
        # Créer l'utilisateur
        user_data = {
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        
        result = users_collection.insert_one(user_data)
        
        if result.inserted_id:
            print(f"✅ Utilisateur '{username}' créé avec succès (rôle: {role})")
        else:
            print(f"❌ Échec de la création de l'utilisateur '{username}'")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    print("🍔 BURGER - Gestionnaire de mots de passe")
    print("1. Mettre à jour un mot de passe")
    print("2. Tester un mot de passe")
    print("3. Créer le mot de passe par défaut pour admin")
    print("4. Créer un nouveau compte utilisateur")
    
    choice = input("Votre choix (1, 2, 3 ou 4): ")
    
    if choice == "1":
        update_user_password()
    elif choice == "2":
        test_password()
    elif choice == "3":
        # Créer le mot de passe hashé pour admin
        mongodb_url = input("Entrez l'URL MongoDB : ")
        admin_password = getpass.getpass("Entrez le mot de passe pour admin : ")
        try:
            client = pymongo.MongoClient(mongodb_url)
            db = client["burger_app"]
            users_collection = db["users"]
            
            password_hash = hash_password(admin_password)
            result = users_collection.update_one(
                {"username": "admin"},
                {"$set": {"password_hash": password_hash}}
            )
            
            if result.modified_count > 0:
                print("✅ Mot de passe configuré pour admin")
            else:
                print("❌ Échec de la mise à jour")
                
        except Exception as e:
            print(f"❌ Erreur : {e}")
    elif choice == "4":
        create_user()
    else:
        print("❌ Choix invalide")
    
    input("\nAppuyez sur Entrée pour continuer...")
