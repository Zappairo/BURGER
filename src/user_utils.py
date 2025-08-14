import pymongo
from src.config import get_mongodb_url

def get_user_mail(username):
    """Récupère l'adresse mail d'un utilisateur MongoDB"""
    users_collection = None
    try:
        mongodb_url = get_mongodb_url()
        if not mongodb_url:
            return None
        client = pymongo.MongoClient(mongodb_url, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)
        db = client["burger_app"]
        users_collection = db["users"]
        user = users_collection.find_one({"username": username})
        if user and "mail" in user:
            return user["mail"]
    except Exception as e:
        print(f"Erreur MongoDB: {e}")
    return None

def get_all_users_mails():
    """Récupère tous les utilisateurs avec leurs mails depuis MongoDB"""
    users_collection = None
    try:
        mongodb_url = get_mongodb_url()
        if not mongodb_url:
            return {}
        client = pymongo.MongoClient(mongodb_url, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)
        db = client["burger_app"]
        users_collection = db["users"]
        users = users_collection.find({}, {"username": 1, "mail": 1})
        
        # Mapping entre les noms du planning et les usernames MongoDB
        name_mapping = {
            "Guillaume": "gbodin",
            "Corentin": "chervouet", 
            "Pascal": "pbrezel",
            "Hervé": "hgautreau",
            "Cyril": "cthibaud",
            "Florian": "florian",
            "Nathan": "nathan",
            "Romain": "romain",
            "Justine": "justine",
            "Emilien": "emilien",
            "Victorien": "victorien",
            "Razvan": "razvan",
            "Noah": "noah",
            "Fabio": "fabio",
            "Brady": "brady",
            "Stephane" : "stephane",
            "Franck" : "franck",
            "John" : "john",
            "Jordan" : "jordan",
            "Audry" : "audry",
            "Julien" : "julien",
        }
        
        # Créer un dictionnaire avec les usernames MongoDB et leurs mails
        users_dict = {user["username"]: user.get("mail", "") for user in users if "mail" in user}
        
        # Retourner un dictionnaire avec les noms du planning comme clés
        result = {}
        for planning_name, mongodb_username in name_mapping.items():
            if mongodb_username in users_dict:
                result[planning_name] = users_dict[mongodb_username]
        
        return result
    except Exception as e:
        print(f"Erreur MongoDB: {e}")
    return {}
