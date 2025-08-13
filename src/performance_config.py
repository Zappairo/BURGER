"""
Configuration des paramètres de performance pour l'application BURGER
"""

# Paramètres de cache
CACHE_TTL_DATA = 300  # 5 minutes pour les données KML
CACHE_TTL_SEARCH = 180  # 3 minutes pour les recherches
CACHE_TTL_MAP = 180  # 3 minutes pour les cartes

# Paramètres de recherche
MIN_SEARCH_LENGTH = 2  # Minimum de caractères pour déclencher une recherche
MAX_SEARCH_RESULTS = 50  # Maximum de résultats affichés
AUTO_SELECT_COUNT = 1  # Nombre de résultats automatiquement sélectionnés

# Paramètres de carte
MAP_DEFAULT_ZOOM = 6
MAP_SINGLE_POSTE_ZOOM = 10
MAP_CANVAS_OPTIMIZATION = True  # Utiliser prefer_canvas pour de meilleures performances

# Paramètres anti-reload pour st_folium
MAP_RETURN_ON_HOVER = False  # Désactiver les événements de survol
MAP_RETURNED_OBJECTS = []  # Ne retourner aucun objet pour éviter les reloads
MAP_USE_CONTAINER_WIDTH = False  # Largeur fixe pour plus de stabilité

# Paramètres de polygones
POLYGON_SIMPLIFICATION_STEPS = {
    'low': {'small': 1, 'medium': 2, 'large': 4, 'huge': 8},
    'medium': {'small': 1, 'medium': 1, 'large': 2, 'huge': 4},
    'high': {'small': 1, 'medium': 1, 'large': 1, 'huge': 2}
}

# Seuils de taille pour la simplification des polygones
POLYGON_SIZE_THRESHOLDS = {
    'small': 100,
    'medium': 500,
    'large': 2000,
    'huge': float('inf')
}

# Configuration d'affichage
DISPLAY_COLUMNS = ['Nom_du_pos', 'Identifian', 'Tension_d', 'latitude', 'longitude']
POPUP_MAX_WIDTH = 350
TABLE_MAX_WIDTH = None  # Use container width

# Messages d'aide
HELP_MESSAGES = {
    'search_placeholder': "Ex: Marmande, Soullans...",
    'search_min_chars': "💡 Veuillez saisir au moins 2 caractères pour lancer la recherche.",
    'search_no_input': "🔍 Saisissez le nom d'un poste pour commencer la recherche.",
    'too_many_results': "⚠️ {} résultats trouvés. Seuls les {} premiers sont affichés. Précisez votre recherche.",
    'no_results': "❌ Aucun poste trouvé pour '{}'. Essayez un autre terme.",
    'select_postes': "⚠️ Veuillez sélectionner au moins un poste dans le tableau pour afficher les détails.",
    'precision_info': "💡 La précision maximale améliore les contours mais augmente le temps de chargement."
}
