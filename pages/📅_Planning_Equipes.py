import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.user_utils import get_user_mail, get_all_users_mails
from src.parsers import parse_postes_kml_optimized
from difflib import get_close_matches
from src.auth import check_password

# Configuration de la page - doit être en premier
st.set_page_config(
    page_title="BURGER - Planning Équipes",
    page_icon="📅",
    layout="wide"
)

# Vérifier l'authentification
if check_password():
    # Header avec info utilisateur et déconnexion
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📅 Envoi du planning par mail aux équipes")
    with col3:
        st.markdown(f"👤 Connecté : **{st.session_state['current_user']}**")
        if st.button("🚪 Se déconnecter", key="logout_planning"):
            # Vider le cache utilisateur pour forcer la reconnexion
            for key in list(st.session_state.keys()):
                if key.startswith(('password', 'current_user')):
                    del st.session_state[key]
            st.rerun()

    uploaded_file = st.file_uploader("Importer le planning CSV", type=["csv"])

    # Cache des postes pour éviter de recharger à chaque fois
    @st.cache_data
    def load_postes_data():
        """Charge les données des postes depuis Poste.kml"""
        return parse_postes_kml_optimized()

    def get_poste_coords(nom_poste):
        """Recherche les coordonnées d'un poste dans le fichier Poste.kml"""
        postes_df = load_postes_data()
        
        if postes_df.empty:
            st.error("Impossible de charger les données de Poste.kml")
            return None, None
        
        # Nettoyage du nom recherché
        nom_poste_clean = str(nom_poste).strip().lower()
        
        # Recherche exacte d'abord
        poste_exact = postes_df[postes_df["Nom_du_pos"].str.strip().str.lower() == nom_poste_clean]
        if not poste_exact.empty:
            lat = poste_exact.iloc[0].get("latitude", None)
            lon = poste_exact.iloc[0].get("longitude", None)
            if lat and lon:
                return float(lat), float(lon)
        
        # Recherche approximative si pas de correspondance exacte
        noms_disponibles = postes_df["Nom_du_pos"].astype(str).str.strip().str.lower().tolist()
        matches = get_close_matches(nom_poste_clean, noms_disponibles, n=1, cutoff=0.4)
        
        if matches:
            poste = postes_df[postes_df["Nom_du_pos"].str.strip().str.lower() == matches[0]]
            if not poste.empty:
                lat = poste.iloc[0].get("latitude", None)
                lon = poste.iloc[0].get("longitude", None)
                if lat and lon:
                    return float(lat), float(lon)
        
        return None, None

    def send_mail(to_email, subject, body):
        """Envoie un mail via SMTP (Gmail, Outlook, etc.)"""
        from_email = st.secrets.get("MAIL_FROM", "")
        password = st.secrets.get("MAIL_PASSWORD", "")
        
        if not from_email or not password:
            st.error("⚠️ Configurez MAIL_FROM et MAIL_PASSWORD dans .streamlit/secrets.toml")
            st.info("💡 Voir les instructions de configuration ci-dessous")
            return False
        
        # Détection automatique du serveur SMTP selon le domaine
        if "@gmail.com" in from_email.lower():
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
        elif "@outlook.com" in from_email.lower() or "@hotmail.com" in from_email.lower():
            smtp_server = "smtp-mail.outlook.com"
            smtp_port = 587
        elif "@yahoo.com" in from_email.lower() or "@yahoo.fr" in from_email.lower():
            smtp_server = "smtp.mail.yahoo.com"
            smtp_port = 587
        elif "@orange.fr" in from_email.lower():
            smtp_server = "smtp.orange.fr"
            smtp_port = 587
        elif "@free.fr" in from_email.lower():
            smtp_server = "smtp.free.fr"
            smtp_port = 587
        else:
            st.error(f"❌ Serveur SMTP non reconnu pour {from_email}")
            st.info("💡 Fournisseurs supportés : Gmail, Outlook, Yahoo, Orange, Free")
            return False
        
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg.attach(MIMEText(body, 'html'))
        
        try:
            with st.spinner(f"📤 Envoi du mail à {to_email}..."):
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(from_email, password)
                server.sendmail(from_email, [to_email], msg.as_string())
                server.quit()
            return True
        except smtplib.SMTPAuthenticationError:
            st.error("❌ Erreur d'authentification SMTP")
            st.error("💡 Vérifiez votre email et mot de passe d'application")
            return False
        except smtplib.SMTPException as e:
            st.error(f"❌ Erreur SMTP: {e}")
            return False
        except Exception as e:
            st.error(f"❌ Erreur envoi mail: {e}")
            return False

    def format_planning_for_mail(df):
        """Formate le planning en texte pour l'email à Guillaume"""
        txt = "<h2>Planning de la semaine</h2><br>"
        for day in df.index:
            txt += f"<b>{day}:</b> "
            for col in df.columns:
                val = str(df.loc[day, col]) if not pd.isna(df.loc[day, col]) else ""
                if val:
                    txt += f"{col} → {val}; "
            txt += "<br>"
        return txt

    def create_individual_mail(person_name, assignments):
        """Crée un mail personnalisé pour une personne avec ses affectations"""
        html = f"""
        <html>
        <body>
            <h2>🏗️ Planning de la semaine</h2>
            <p>Bonjour <b>{person_name}</b>,</p>
            <p>Voici votre planning pour la semaine :</p>
            <ul>
        """
        
        for day, poste in assignments.items():
            if poste and str(poste).strip() and str(poste).strip().upper() not in ['NAN', '']:
                poste_clean = str(poste).strip().upper()
                
                # Liste des valeurs qui ne nécessitent pas de liens GPS
                no_gps_values = ['FORMATION', 'ATELIER', 'CP', 'REPOS', 'CONGE', 'ARRET', 'MALADIE']
                
                if poste_clean in no_gps_values:
                    # Affichage simple sans liens GPS pour les formations, ateliers, etc.
                    if poste_clean == 'FORMATION':
                        html += f"<li><b>{day}</b> : 📚 {poste}</li>"
                    elif poste_clean == 'ATELIER':
                        html += f"<li><b>{day}</b> : 🔧 {poste}</li>"
                    elif poste_clean == 'CP':
                        html += f"<li><b>{day}</b> : 🏖️ Congés payés</li>"
                    else:
                        html += f"<li><b>{day}</b> : {poste}</li>"
                else:
                    # Recherche GPS uniquement pour les vrais postes
                    lat, lon = get_poste_coords(poste)
                    if lat and lon:
                        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                        waze_link = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
                        html += f"""
                        <li><b>{day}</b> : {poste}
                            <br>📍 <a href="{google_maps_link}" target="_blank">Google Maps</a> | 
                            🚗 <a href="{waze_link}" target="_blank">Waze</a>
                        </li>
                        """
                    else:
                        html += f"<li><b>{day}</b> : {poste}</li>"
            else:
                html += f"<li><b>{day}</b> : Repos / Non affecté</li>"
        
        html += """
            </ul>
            <p>Bonne semaine de travail !</p>
            <p><i>Mail automatique - Planning Cap Solar</i></p>
        </body>
        </html>
        """
        return html

    if uploaded_file:
        try:
            # Essai de différents encodages et séparateurs pour lire le CSV
            planning_df = None
            encodings = ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin-1']
            separators = [',', ';', '\t']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        # Lecture du planning - LIGNES 2 à 6 SEULEMENT (skiprows=1, nrows=5)
                        uploaded_file.seek(0)  # Reset file pointer
                        planning_df = pd.read_csv(uploaded_file, sep=sep, encoding=encoding, skiprows=1, nrows=5)
                        
                        # Vérifier si on a des colonnes valides
                        if len(planning_df.columns) > 1 and not planning_df.empty:
                            st.success(f"✅ Fichier lu avec l'encodage: {encoding} et séparateur: '{sep}' (lignes 2-6)")
                            break
                    except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError):
                        continue
                    except Exception:
                        continue
                if planning_df is not None and len(planning_df.columns) > 1:
                    break
            
            if planning_df is None or len(planning_df.columns) <= 1:
                st.error("❌ Impossible de lire le fichier avec les encodages et séparateurs testés")
                st.info("🔍 Contenu brut du fichier (premières lignes):")
                uploaded_file.seek(0)
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                st.text(content[:500] + "..." if len(content) > 500 else content)
                st.stop()
            
            # Afficher le dataframe brut pour debug
            st.write("📋 Données détectées (lignes 2-6):")
            st.dataframe(planning_df)
            
            # Essayer de détecter automatiquement les colonnes noms
            if len(planning_df.columns) > 5:  # Si on a plusieurs colonnes
                # Prendre la première colonne comme index (jours)
                planning_df = planning_df.set_index(planning_df.columns[0])
                # Supprimer les colonnes vides
                planning_df = planning_df.dropna(axis=1, how='all')
                planning_df = planning_df.dropna(axis=0, how='all')
            
            st.subheader("📊 Planning restructuré")
            st.dataframe(planning_df)
            
            if planning_df.empty:
                st.warning("⚠️ Aucune donnée trouvée après restructuration")
                st.stop()
            
            # Bouton pour envoyer à Guillaume
            col1, col2 = st.columns(2)
            
            with col2:
                if st.button("📨 Envoyer les plannings individuels à tous"):
                    users_mails = get_all_users_mails()
                    
                    if not users_mails:
                        st.error("Aucun utilisateur avec mail trouvé dans MongoDB.")
                    else:
                        sent_count = 0
                        total_count = 0
                        
                        # Pour chaque personne dans les colonnes du planning
                        for person_name in planning_df.columns:
                            person_name_clean = str(person_name).strip()
                            
                            # Ignorer les colonnes "Unnamed" ou vides
                            if person_name_clean.startswith("Unnamed") or not person_name_clean:
                                st.info(f"⏭️ Colonne ignorée : {person_name_clean}")
                                continue
                            
                            # Rechercher le mail de cette personne directement dans le mapping
                            person_mail = users_mails.get(person_name_clean)
                            
                            if person_mail:
                                total_count += 1
                                
                                # Extraire les affectations de cette personne
                                assignments = {}
                                for day in planning_df.index:
                                    if day and str(day).strip():  # Ignorer les lignes vides
                                        day_clean = str(day).strip()
                                        if not day_clean.upper().startswith('SEMAINE'):  # Ignorer la ligne titre semaine
                                            poste = planning_df.loc[day, person_name]
                                            assignments[day_clean] = poste
                                
                                if assignments:
                                    # Créer le mail personnalisé
                                    subject = f"Votre planning - Cap Solar"
                                    body = create_individual_mail(person_name_clean, assignments)
                                    
                                    success = send_mail(person_mail, subject, body)
                                    if success:
                                        st.success(f"✅ Mail envoyé à {person_name_clean} ({person_mail})")
                                        sent_count += 1
                                    else:
                                        st.error(f"❌ Échec pour {person_name_clean}")
                            else:
                                st.warning(f"⚠️ Mail non trouvé pour {person_name_clean}")
                        
                        st.info(f"📊 Envoi terminé : {sent_count}/{total_count} mails envoyés")
            
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
            st.info("💡 Vérifiez que le fichier CSV est bien formaté avec les noms en colonnes et les jours en lignes")
            
            # Essai avec d'autres paramètres
            try:
                st.write("Tentative de lecture alternative...")
                uploaded_file.seek(0)
                for encoding in ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin-1']:
                    for sep in [',', ';', '\t']:
                        try:
                            planning_df_alt = pd.read_csv(uploaded_file, sep=sep, encoding=encoding, skiprows=1, nrows=6)
                            if len(planning_df_alt.columns) > 1:
                                st.write(f"Format alternatif détecté avec {encoding} et séparateur '{sep}' (lignes 2-7):")
                                st.dataframe(planning_df_alt)
                                break
                        except Exception:
                            continue
                    if 'planning_df_alt' in locals() and len(planning_df_alt.columns) > 1:
                        break
            except Exception as e2:
                st.error(f"Lecture alternative échouée : {e2}")
    else:
        st.info("Importez un fichier CSV pour commencer.")

    # Section d'aide pour la configuration SMTP
    with st.expander("🔧 Configuration SMTP - Test"):
        
        # Test de configuration SMTP
        st.subheader("🧪 Test de configuration")
        test_email = st.text_input("Email de test :", value="test@example.com")
        if st.button("🚀 Tester l'envoi SMTP"):
            if test_email and "@" in test_email:
                success = send_mail(
                    test_email, 
                    "Test SMTP - Planning BURGER", 
                    "<h2>🎉 Test réussi !</h2><p>Votre configuration SMTP fonctionne parfaitement.</p>"
                )
                if success:
                    st.success("✅ Test SMTP réussi ! Configuration OK")
                else:
                    st.error("❌ Test SMTP échoué. Vérifiez votre configuration.")
            else:
                st.warning("⚠️ Veuillez saisir un email valide")

    # Texte de fin et remerciements
    st.markdown("<hr style='margin-top:40px;margin-bottom:10px;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:gray;'>v1.1.0 - APP by Guillaume B. </div>", unsafe_allow_html=True)