#!/usr/bin/env python3
"""
Script pour traduire les messages vides et fuzzy dans le fichier PO anglais.
Utilise un dictionnaire de traductions français -> anglais.
"""

import re
import os

# Dictionnaire étendu de traductions français -> anglais
TRANSLATIONS = {
    # Navigation et actions de base
    "Accueil": "Home",
    "Retour": "Back",
    "Suivant": "Next",
    "Précédent": "Previous",
    "Enregistrer": "Save",
    "Sauvegarder": "Save",
    "Annuler": "Cancel",
    "Supprimer": "Delete",
    "Modifier": "Edit",
    "Éditer": "Edit",
    "Ajouter": "Add",
    "Créer": "Create",
    "Nouveau": "New",
    "Nouvelle": "New",
    "Rechercher": "Search",
    "Filtrer": "Filter",
    "Valider": "Validate",
    "Confirmer": "Confirm",
    "Fermer": "Close",
    "Ouvrir": "Open",
    "Voir": "View",
    "Afficher": "Display",
    "Masquer": "Hide",
    "Télécharger": "Download",
    "Importer": "Import",
    "Exporter": "Export",
    "Actualiser": "Refresh",
    "Charger": "Load",
    "Soumettre": "Submit",
    "Envoyer": "Send",
    "Copier": "Copy",
    "Coller": "Paste",
    "Couper": "Cut",
    "Sélectionner": "Select",
    "Désélectionner": "Deselect",
    "Tout sélectionner": "Select all",
    "Tout désélectionner": "Deselect all",
    "Appliquer": "Apply",
    "Réinitialiser": "Reset",
    "Par défaut": "Default",
    "Gérer": "Manage",
    "Administrer": "Administer",
    "Configurer": "Configure",

    # Compétitions et sports
    "Compétition": "Competition",
    "Compétitions": "Competitions",
    "Catégorie": "Category",
    "Catégories": "Categories",
    "Sous-catégorie": "Subcategory",
    "Inscription": "Registration",
    "Inscriptions": "Registrations",
    "Participant": "Participant",
    "Participants": "Participants",
    "Équipe": "Team",
    "Équipes": "Teams",
    "Combat": "Combat",
    "Combats": "Combats",
    "Poule": "Pool",
    "Poules": "Pools",
    "Match": "Match",
    "Matchs": "Matches",
    "Résultat": "Result",
    "Résultats": "Results",
    "Classement": "Ranking",
    "Classements": "Rankings",
    "Score": "Score",
    "Scores": "Scores",
    "Point": "Point",
    "Points": "Points",
    "Victoire": "Victory",
    "Victoires": "Victories",
    "Défaite": "Defeat",
    "Défaites": "Defeats",
    "Égalité": "Draw",
    "Nul": "Draw",
    "Vainqueur": "Winner",
    "Gagnant": "Winner",
    "Perdant": "Loser",
    "Podium": "Podium",
    "Médaille": "Medal",
    "Médailles": "Medals",
    "Or": "Gold",
    "Argent": "Silver",
    "Bronze": "Bronze",
    "Champion": "Champion",
    "Championnat": "Championship",
    "Tournoi": "Tournament",
    "Tournois": "Tournaments",
    "Finale": "Final",
    "Demi-finale": "Semi-final",
    "Quart de finale": "Quarter-final",
    "Phase de poules": "Pool phase",
    "Éliminatoire": "Knockout",
    "Éliminatoires": "Knockouts",
    "Round": "Round",
    "Manche": "Round",
    "Tour": "Round",
    "Repêchage": "Repechage",
    "Qualification": "Qualification",
    "Qualifié": "Qualified",
    "Qualifiée": "Qualified",
    "Éliminé": "Eliminated",
    "Éliminée": "Eliminated",
    "Forfait": "Forfeit",
    "Disqualifié": "Disqualified",
    "Disqualifiée": "Disqualified",
    "Blessé": "Injured",
    "Blessée": "Injured",
    "Absent": "Absent",
    "Absente": "Absent",
    "Présent": "Present",
    "Présente": "Present",
    "Présence": "Attendance",

    # Arts martiaux spécifiques
    "Technique": "Technical",
    "Techniques": "Techniques",
    "Kata": "Kata",
    "Kumite": "Kumite",
    "Poomsae": "Poomsae",
    "Kyorugi": "Kyorugi",
    "Ceinture": "Belt",
    "Ceintures": "Belts",
    "Grade": "Grade",
    "Grades": "Grades",
    "Dan": "Dan",
    "Kyu": "Kyu",
    "Niveau": "Level",
    "Niveaux": "Levels",
    "Débutant": "Beginner",
    "Débutants": "Beginners",
    "Intermédiaire": "Intermediate",
    "Avancé": "Advanced",
    "Expert": "Expert",
    "Maître": "Master",
    "Tatami": "Tatami",
    "Aire": "Area",
    "Surface": "Surface",
    "Dojo": "Dojo",
    "Discipline": "Discipline",
    "Disciplines": "Disciplines",
    "Art martial": "Martial art",
    "Arts martiaux": "Martial arts",
    "Karaté": "Karate",
    "Taekwondo": "Taekwondo",
    "Judo": "Judo",
    "Aikido": "Aikido",
    "Aïkido": "Aikido",
    "Kung-fu": "Kung fu",
    "Kung Fu": "Kung fu",
    "Boxe": "Boxing",
    "Kickboxing": "Kickboxing",

    # Club et organisation
    "Club": "Club",
    "Clubs": "Clubs",
    "Organisation": "Organization",
    "Organisations": "Organizations",
    "Fédération": "Federation",
    "Fédérations": "Federations",
    "Ligue": "League",
    "Ligues": "Leagues",
    "Association": "Association",
    "Associations": "Associations",
    "Membre": "Member",
    "Membres": "Members",
    "Adhérent": "Member",
    "Adhérents": "Members",
    "Pratiquant": "Practitioner",
    "Pratiquants": "Practitioners",
    "Entraîneur": "Coach",
    "Entraîneurs": "Coaches",
    "Coach": "Coach",
    "Arbitre": "Referee",
    "Arbitres": "Referees",
    "Juge": "Judge",
    "Juges": "Judges",
    "Organisateur": "Organizer",
    "Organisateurs": "Organizers",
    "Responsable": "Manager",
    "Responsables": "Managers",
    "Président": "President",
    "Secrétaire": "Secretary",
    "Trésorier": "Treasurer",
    "Directeur technique": "Technical director",
    "Licence": "License",
    "Licences": "Licenses",
    "Numéro de licence": "License number",
    "Adhésion": "Membership",
    "Adhésions": "Memberships",
    "Cotisation": "Subscription",
    "Cotisations": "Subscriptions",

    # Personnes et profil
    "Nom": "Name",
    "Prénom": "First name",
    "Nom de famille": "Last name",
    "Nom complet": "Full name",
    "Email": "Email",
    "Courriel": "Email",
    "Téléphone": "Phone",
    "Adresse": "Address",
    "Ville": "City",
    "Pays": "Country",
    "Code postal": "Postal code",
    "Date de naissance": "Date of birth",
    "Âge": "Age",
    "Sexe": "Gender",
    "Genre": "Gender",
    "Homme": "Male",
    "Femme": "Female",
    "Masculin": "Male",
    "Féminin": "Female",
    "Mixte": "Mixed",
    "Photo": "Photo",
    "Avatar": "Avatar",
    "Image": "Image",
    "Profil": "Profile",
    "Mon profil": "My profile",
    "Compte": "Account",
    "Mon compte": "My account",
    "Utilisateur": "User",
    "Utilisateurs": "Users",
    "Rôle": "Role",
    "Rôles": "Roles",
    "Permission": "Permission",
    "Permissions": "Permissions",
    "Droit": "Right",
    "Droits": "Rights",
    "Accès": "Access",

    # Dates et temps
    "Date": "Date",
    "Heure": "Time",
    "Horaire": "Schedule",
    "Horaires": "Schedules",
    "Jour": "Day",
    "Jours": "Days",
    "Semaine": "Week",
    "Semaines": "Weeks",
    "Mois": "Month",
    "Année": "Year",
    "Début": "Start",
    "Fin": "End",
    "Durée": "Duration",
    "Période": "Period",
    "Aujourd'hui": "Today",
    "Demain": "Tomorrow",
    "Hier": "Yesterday",
    "Maintenant": "Now",
    "Bientôt": "Soon",
    "Plus tard": "Later",
    "Lundi": "Monday",
    "Mardi": "Tuesday",
    "Mercredi": "Wednesday",
    "Jeudi": "Thursday",
    "Vendredi": "Friday",
    "Samedi": "Saturday",
    "Dimanche": "Sunday",
    "Janvier": "January",
    "Février": "February",
    "Mars": "March",
    "Avril": "April",
    "Mai": "May",
    "Juin": "June",
    "Juillet": "July",
    "Août": "August",
    "Septembre": "September",
    "Octobre": "October",
    "Novembre": "November",
    "Décembre": "December",

    # Statuts
    "Statut": "Status",
    "État": "State",
    "Actif": "Active",
    "Active": "Active",
    "Inactif": "Inactive",
    "Inactive": "Inactive",
    "En cours": "In progress",
    "Terminé": "Completed",
    "Terminée": "Completed",
    "Fini": "Finished",
    "Finie": "Finished",
    "En attente": "Pending",
    "Annulé": "Cancelled",
    "Annulée": "Cancelled",
    "Validé": "Validated",
    "Validée": "Validated",
    "Refusé": "Rejected",
    "Refusée": "Rejected",
    "Approuvé": "Approved",
    "Approuvée": "Approved",
    "Brouillon": "Draft",
    "Publié": "Published",
    "Publiée": "Published",
    "Archivé": "Archived",
    "Archivée": "Archived",
    "Ouvert": "Open",
    "Ouverte": "Open",
    "Fermé": "Closed",
    "Fermée": "Closed",
    "Disponible": "Available",
    "Indisponible": "Unavailable",
    "Complet": "Full",
    "Complète": "Complete",
    "Incomplet": "Incomplete",
    "Incomplète": "Incomplete",
    "Obligatoire": "Required",
    "Optionnel": "Optional",
    "Optionnelle": "Optional",
    "Requis": "Required",
    "Requise": "Required",

    # Messages et notifications
    "Succès": "Success",
    "Réussite": "Success",
    "Erreur": "Error",
    "Erreurs": "Errors",
    "Avertissement": "Warning",
    "Avertissements": "Warnings",
    "Information": "Information",
    "Informations": "Information",
    "Attention": "Attention",
    "Confirmation": "Confirmation",
    "Message": "Message",
    "Messages": "Messages",
    "Notification": "Notification",
    "Notifications": "Notifications",
    "Alerte": "Alert",
    "Alertes": "Alerts",
    "Conseil": "Tip",
    "Conseils": "Tips",
    "Aide": "Help",
    "Support": "Support",
    "FAQ": "FAQ",

    # Formulaires
    "Formulaire": "Form",
    "Champ": "Field",
    "Champs": "Fields",
    "Valeur": "Value",
    "Valeurs": "Values",
    "Description": "Description",
    "Commentaire": "Comment",
    "Commentaires": "Comments",
    "Note": "Note",
    "Notes": "Notes",
    "Titre": "Title",
    "Type": "Type",
    "Label": "Label",
    "Placeholder": "Placeholder",
    "Options": "Options",
    "Choix": "Choice",
    "Sélection": "Selection",
    "Liste": "List",
    "Listes": "Lists",
    "Tableau": "Table",
    "Tableaux": "Tables",
    "Ligne": "Row",
    "Lignes": "Rows",
    "Colonne": "Column",
    "Colonnes": "Columns",
    "Cellule": "Cell",
    "Fichier": "File",
    "Fichiers": "Files",
    "Document": "Document",
    "Documents": "Documents",
    "Pièce jointe": "Attachment",
    "Pièces jointes": "Attachments",

    # Finance
    "Finance": "Finance",
    "Finances": "Finances",
    "Paiement": "Payment",
    "Paiements": "Payments",
    "Tarif": "Rate",
    "Tarifs": "Rates",
    "Prix": "Price",
    "Coût": "Cost",
    "Montant": "Amount",
    "Total": "Total",
    "Sous-total": "Subtotal",
    "TVA": "VAT",
    "Taxe": "Tax",
    "Taxes": "Taxes",
    "Remise": "Discount",
    "Remises": "Discounts",
    "Réduction": "Reduction",
    "Facture": "Invoice",
    "Factures": "Invoices",
    "Reçu": "Receipt",
    "Reçus": "Receipts",
    "Devis": "Quote",
    "Bon de commande": "Purchase order",
    "Gratuit": "Free",
    "Payé": "Paid",
    "Payée": "Paid",
    "Impayé": "Unpaid",
    "Impayée": "Unpaid",
    "En retard": "Overdue",
    "Remboursé": "Refunded",
    "Remboursée": "Refunded",
    "Euro": "Euro",
    "Euros": "Euros",
    "Dollar": "Dollar",
    "Dollars": "Dollars",

    # Technique/Scoring
    "Performance": "Performance",
    "Performances": "Performances",
    "Évaluation": "Evaluation",
    "Évaluations": "Evaluations",
    "Notation": "Scoring",
    "Note technique": "Technical score",
    "Critère": "Criterion",
    "Critères": "Criteria",
    "Pénalité": "Penalty",
    "Pénalités": "Penalties",
    "Bonus": "Bonus",
    "Malus": "Penalty",
    "Coefficient": "Coefficient",
    "Moyenne": "Average",
    "Maximum": "Maximum",
    "Minimum": "Minimum",
    "Somme": "Sum",

    # Événements et planification
    "Événement": "Event",
    "Événements": "Events",
    "Calendrier": "Calendar",
    "Planning": "Schedule",
    "Programme": "Program",
    "Agenda": "Agenda",
    "Rendez-vous": "Appointment",
    "Réunion": "Meeting",
    "Entraînement": "Training",
    "Entraînements": "Trainings",
    "Cours": "Class",
    "Session": "Session",
    "Sessions": "Sessions",
    "Séance": "Session",
    "Séances": "Sessions",
    "Lieu": "Venue",
    "Lieux": "Venues",
    "Salle": "Room",
    "Salles": "Rooms",
    "Gymnase": "Gymnasium",
    "Stade": "Stadium",

    # Divers
    "Oui": "Yes",
    "Non": "No",
    "Tous": "All",
    "Toutes": "All",
    "Aucun": "None",
    "Aucune": "None",
    "Autre": "Other",
    "Autres": "Others",
    "Détail": "Detail",
    "Détails": "Details",
    "Résumé": "Summary",
    "Aperçu": "Preview",
    "Vue d'ensemble": "Overview",
    "Statistiques": "Statistics",
    "Stats": "Stats",
    "Paramètres": "Settings",
    "Réglages": "Settings",
    "Configuration": "Configuration",
    "Préférences": "Preferences",
    "À propos": "About",
    "Contact": "Contact",
    "Connexion": "Login",
    "Se connecter": "Log in",
    "Déconnexion": "Logout",
    "Se déconnecter": "Log out",
    "Mot de passe": "Password",
    "Changer le mot de passe": "Change password",
    "Mot de passe oublié": "Forgot password",
    "Identifiant": "Username",
    "Tableau de bord": "Dashboard",
    "Administration": "Administration",
    "Admin": "Admin",
    "Gestion": "Management",
    "Poids": "Weight",
    "Taille": "Size",
    "Numéro": "Number",
    "Version": "Version",
    "Langue": "Language",
    "Langues": "Languages",
    "Français": "French",
    "Anglais": "English",
    "Allemand": "German",
    "Espagnol": "Spanish",
    "Italien": "Italian",
    "Portugais": "Portuguese",
    "Chinois": "Chinese",
    "Japonais": "Japanese",
    "Coréen": "Korean",
    "Arabe": "Arabic",
    "Russe": "Russian",
    "Bienvenue": "Welcome",
    "Bonjour": "Hello",
    "Merci": "Thank you",
    "S'il vous plaît": "Please",
    "Veuillez": "Please",
    "Continuer": "Continue",
    "Précédent": "Previous",
    "Terminer": "Finish",
    "Commencer": "Start",
    "Démarrer": "Start",
    "Arrêter": "Stop",
    "Pause": "Pause",
    "Reprendre": "Resume",
    "Personnaliser": "Customize",
    "Imprimer": "Print",
    "Partager": "Share",
    "Publier": "Publish",
    "Archiver": "Archive",
    "Restaurer": "Restore",
    "Dupliquer": "Duplicate",
    "Cloner": "Clone",
    "Renommer": "Rename",
    "Déplacer": "Move",
    "Trier": "Sort",
    "Grouper": "Group",
    "Filtrer par": "Filter by",
    "Trier par": "Sort by",
    "Rechercher dans": "Search in",
    "Aller à": "Go to",
    "Retourner à": "Return to",
    "Actions": "Actions",
    "Plus d'actions": "More actions",
    "Voir plus": "See more",
    "Voir moins": "See less",
    "Afficher tout": "Show all",
    "Masquer tout": "Hide all",
    "Développer": "Expand",
    "Réduire": "Collapse",
    "Plein écran": "Full screen",
    "Quitter le plein écran": "Exit full screen",
    "Zoom avant": "Zoom in",
    "Zoom arrière": "Zoom out",
    "Téléversement": "Upload",
    "Téléchargement": "Download",
    "En cours de chargement": "Loading",
    "Chargement": "Loading",
    "Veuillez patienter": "Please wait",
    "Erreur de chargement": "Loading error",
    "Aucun résultat": "No results",
    "Aucune donnée": "No data",
    "Données non disponibles": "Data not available",
    "Non renseigné": "Not specified",
    "Non défini": "Not defined",
    "Inconnu": "Unknown",
    "Inconnue": "Unknown",
    "Récent": "Recent",
    "Récente": "Recent",
    "Récents": "Recent",
    "Récentes": "Recent",
    "Ancien": "Old",
    "Ancienne": "Old",
    "Populaire": "Popular",
    "Populaires": "Popular",
    "Favori": "Favorite",
    "Favoris": "Favorites",
    "Important": "Important",
    "Importants": "Important",
    "Urgent": "Urgent",
    "Urgents": "Urgent",
    "Nouveau message": "New message",
    "Nouvelles notifications": "New notifications",
    "Marquer comme lu": "Mark as read",
    "Marquer comme non lu": "Mark as unread",
    "Supprimer définitivement": "Delete permanently",
    "Êtes-vous sûr": "Are you sure",
    "Cette action est irréversible": "This action is irreversible",
    "Confirmer la suppression": "Confirm deletion",
    "Annuler les modifications": "Cancel changes",
    "Enregistrer les modifications": "Save changes",
    "Modifications enregistrées": "Changes saved",
    "Erreur lors de l'enregistrement": "Error saving",
    "Opération réussie": "Operation successful",
    "Opération échouée": "Operation failed",
    "Veuillez réessayer": "Please try again",
    "Session expirée": "Session expired",
    "Connexion requise": "Login required",
    "Accès refusé": "Access denied",
    "Page non trouvée": "Page not found",
    "Erreur serveur": "Server error",
    "Erreur interne": "Internal error",
    "Maintenance": "Maintenance",
    "En maintenance": "Under maintenance",
    "Retour à l'accueil": "Back to home",
}

def translate_french_to_english(text):
    """Traduit un texte français en anglais."""
    if not text or not text.strip():
        return text

    result = text

    # Remplacements par ordre de longueur décroissante (pour éviter les remplacements partiels)
    for fr, en in sorted(TRANSLATIONS.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(r'\b' + re.escape(fr) + r'\b', re.IGNORECASE | re.UNICODE)

        def replace_with_case(match):
            matched = match.group(0)
            if matched.isupper():
                return en.upper()
            elif matched[0].isupper():
                return en.capitalize() if len(en) > 0 else en
            return en

        result = pattern.sub(replace_with_case, result)

    return result


def process_po_file(filepath):
    """Traite le fichier PO pour traduire les entrées vides et fuzzy."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    result_lines = []

    translated_count = 0
    fuzzy_cleaned = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Détection des entrées fuzzy
        if line.startswith('#, fuzzy'):
            # Regarder si on peut améliorer la traduction
            # On garde la ligne fuzzy pour le moment mais on pourrait la nettoyer si la traduction est bonne
            result_lines.append(line)
            i += 1
            continue

        # Détection msgid simple
        if line.startswith('msgid "') and not line.startswith('msgid ""'):
            msgid_content = line[7:-1]  # Extraire le contenu entre guillemets
            result_lines.append(line)
            i += 1

            # Vérifier si le prochain msgstr est vide
            if i < len(lines) and lines[i] == 'msgstr ""':
                # Traduire le msgid
                translation = translate_french_to_english(msgid_content)
                if translation != msgid_content:
                    result_lines.append(f'msgstr "{translation}"')
                    translated_count += 1
                else:
                    result_lines.append(lines[i])
                i += 1
            continue

        # Détection msgid multiligne
        if line == 'msgid ""':
            result_lines.append(line)
            msgid_parts = []
            i += 1

            # Collecter toutes les lignes du msgid
            while i < len(lines) and lines[i].startswith('"'):
                msgid_parts.append(lines[i][1:-1])  # Enlever les guillemets
                result_lines.append(lines[i])
                i += 1

            # Ignorer msgid_plural si présent
            if i < len(lines) and lines[i].startswith('msgid_plural'):
                while i < len(lines) and not lines[i].startswith('msgstr'):
                    result_lines.append(lines[i])
                    i += 1

            # Vérifier si le msgstr est vide
            if i < len(lines) and lines[i] == 'msgstr ""':
                next_line_idx = i + 1
                if next_line_idx < len(lines) and lines[next_line_idx].startswith('"'):
                    # msgstr multiligne non vide, on le garde
                    result_lines.append(lines[i])
                    i += 1
                elif next_line_idx < len(lines) and (lines[next_line_idx] == '' or lines[next_line_idx].startswith('#') or lines[next_line_idx].startswith('msgid')):
                    # msgstr vide - essayer de traduire
                    full_msgid = ''.join(msgid_parts)
                    translation = translate_french_to_english(full_msgid)

                    if translation != full_msgid and translation.strip():
                        # Vérifier s'il faut une traduction multiligne
                        if '\n' in full_msgid or len(translation) > 70:
                            result_lines.append('msgstr ""')
                            # Découper la traduction
                            result_lines.append(f'"{translation}"')
                        else:
                            result_lines.append(f'msgstr "{translation}"')
                        translated_count += 1
                        i += 1
                    else:
                        result_lines.append(lines[i])
                        i += 1
                else:
                    result_lines.append(lines[i])
                    i += 1
            continue

        result_lines.append(line)
        i += 1

    print(f"  Messages traduits: {translated_count}")

    return '\n'.join(result_lines)


def main():
    po_file = 'locale/en/LC_MESSAGES/django.po'

    print(f"Traitement de {po_file}...")

    # Lire et traiter le fichier
    result = process_po_file(po_file)

    # Écrire le résultat
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"Fichier mis à jour.")


if __name__ == '__main__':
    main()
