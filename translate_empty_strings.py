#!/usr/bin/env python3
"""
Traduit automatiquement les chaînes vides dans le fichier .po anglais
"""

import polib
import re

# Dictionnaire de traduction étendu
TRANSLATIONS = {
    # Navigation & Actions
    'Accueil': 'Home',
    'Tableau de bord': 'Dashboard',
    'Connexion': 'Login',
    'Déconnexion': 'Logout',
    'Se connecter': 'Sign in',
    'Se déconnecter': 'Sign out',
    'S\'inscrire': 'Sign up',
    'Inscription': 'Registration',
    'Profil': 'Profile',
    'Mon profil': 'My profile',
    'Paramètres': 'Settings',
    'Configuration': 'Configuration',
    'Aide': 'Help',
    'Support': 'Support',
    'Rechercher': 'Search',
    'Filtrer': 'Filter',
    'Trier': 'Sort',
    'Exporter': 'Export',
    'Importer': 'Import',
    'Télécharger': 'Download',
    'Envoyer': 'Send',
    'Soumettre': 'Submit',
    'Enregistrer': 'Save',
    'Sauvegarder': 'Save',
    'Annuler': 'Cancel',
    'Fermer': 'Close',
    'Retour': 'Back',
    'Précédent': 'Previous',
    'Suivant': 'Next',
    'Terminer': 'Finish',
    'Confirmer': 'Confirm',
    'Valider': 'Validate',
    'Supprimer': 'Delete',
    'Modifier': 'Edit',
    'Ajouter': 'Add',
    'Créer': 'Create',
    'Nouveau': 'New',
    'Nouvelle': 'New',
    'Voir': 'View',
    'Afficher': 'Display',
    'Masquer': 'Hide',
    'Actualiser': 'Refresh',
    'Réinitialiser': 'Reset',
    'Appliquer': 'Apply',
    'Sélectionner': 'Select',
    'Choisir': 'Choose',
    'Télécharger': 'Download',
    'Charger': 'Load',
    'Ouvrir': 'Open',
    'Actions': 'Actions',
    'Options': 'Options',
    'Plus': 'More',
    'Moins': 'Less',
    'Tout': 'All',
    'Aucun': 'None',
    'Oui': 'Yes',
    'Non': 'No',
    
    # Membres & Utilisateurs
    'Membre': 'Member',
    'Membres': 'Members',
    'Utilisateur': 'User',
    'Utilisateurs': 'Users',
    'Pratiquant': 'Practitioner',
    'Pratiquants': 'Practitioners',
    'Entraîneur': 'Coach',
    'Entraîneurs': 'Coaches',
    'Arbitre': 'Referee',
    'Arbitres': 'Referees',
    'Juge': 'Judge',
    'Juges': 'Judges',
    'Administrateur': 'Administrator',
    'Administrateurs': 'Administrators',
    'Gestionnaire': 'Manager',
    'Gestionnaires': 'Managers',
    'Participant': 'Participant',
    'Participants': 'Participants',
    'Contact': 'Contact',
    'Contacts': 'Contacts',
    
    # Compétitions & Événements
    'Compétition': 'Competition',
    'Compétitions': 'Competitions',
    'Événement': 'Event',
    'Événements': 'Events',
    'Tournoi': 'Tournament',
    'Tournois': 'Tournaments',
    'Match': 'Match',
    'Matchs': 'Matches',
    'Combat': 'Fight',
    'Combats': 'Fights',
    'Catégorie': 'Category',
    'Catégories': 'Categories',
    'Poule': 'Pool',
    'Poules': 'Pools',
    'Tableau': 'Bracket',
    'Tableaux': 'Brackets',
    'Résultat': 'Result',
    'Résultats': 'Results',
    'Classement': 'Ranking',
    'Classements': 'Rankings',
    'Score': 'Score',
    'Scores': 'Scores',
    'Notation': 'Scoring',
    'Évaluation': 'Evaluation',
    'Performance': 'Performance',
    
    # Organisation & Structure
    'Club': 'Club',
    'Clubs': 'Clubs',
    'Organisation': 'Organization',
    'Organisations': 'Organizations',
    'Fédération': 'Federation',
    'Fédérations': 'Federations',
    'Association': 'Association',
    'Associations': 'Associations',
    'École': 'School',
    'Écoles': 'Schools',
    'Dojo': 'Dojo',
    'Dojos': 'Dojos',
    'Salle': 'Gym',
    'Salles': 'Gyms',
    'Lieu': 'Venue',
    'Lieux': 'Venues',
    'Adresse': 'Address',
    'Ville': 'City',
    'Pays': 'Country',
    'Région': 'Region',
    'Département': 'Department',
    
    # Grades & Examens
    'Grade': 'Grade',
    'Grades': 'Grades',
    'Examen': 'Exam',
    'Examens': 'Exams',
    'Ceinture': 'Belt',
    'Ceintures': 'Belts',
    'Dan': 'Dan',
    'Kyu': 'Kyu',
    'Niveau': 'Level',
    'Niveaux': 'Levels',
    'Certification': 'Certification',
    'Diplôme': 'Diploma',
    'Passage de grade': 'Grading',
    'Évaluation technique': 'Technical evaluation',
    
    # Dates & Temps
    'Date': 'Date',
    'Heure': 'Time',
    'Début': 'Start',
    'Fin': 'End',
    'Durée': 'Duration',
    'Jour': 'Day',
    'Semaine': 'Week',
    'Mois': 'Month',
    'Année': 'Year',
    'Aujourd\'hui': 'Today',
    'Demain': 'Tomorrow',
    'Hier': 'Yesterday',
    'Maintenant': 'Now',
    'Horaire': 'Schedule',
    'Planning': 'Planning',
    'Calendrier': 'Calendar',
    
    # États & Statuts
    'Statut': 'Status',
    'État': 'State',
    'Actif': 'Active',
    'Inactif': 'Inactive',
    'En cours': 'In progress',
    'Terminé': 'Completed',
    'En attente': 'Pending',
    'Validé': 'Validated',
    'Refusé': 'Rejected',
    'Brouillon': 'Draft',
    'Publié': 'Published',
    'Archivé': 'Archived',
    'Ouvert': 'Open',
    'Fermé': 'Closed',
    'Disponible': 'Available',
    'Indisponible': 'Unavailable',
    'Complet': 'Full',
    'Incomplet': 'Incomplete',
    
    # Finance & Paiement
    'Paiement': 'Payment',
    'Paiements': 'Payments',
    'Facture': 'Invoice',
    'Factures': 'Invoices',
    'Montant': 'Amount',
    'Prix': 'Price',
    'Tarif': 'Rate',
    'Total': 'Total',
    'Devise': 'Currency',
    'Transaction': 'Transaction',
    'Adhésion': 'Membership',
    'Adhésions': 'Memberships',
    'Abonnement': 'Subscription',
    'Cotisation': 'Fee',
    'Remise': 'Discount',
    'Réduction': 'Reduction',
    
    # Documents & Fichiers
    'Document': 'Document',
    'Documents': 'Documents',
    'Fichier': 'File',
    'Fichiers': 'Files',
    'Pièce jointe': 'Attachment',
    'Photo': 'Photo',
    'Image': 'Image',
    'Certificat': 'Certificate',
    'Certificat médical': 'Medical certificate',
    'Licence': 'License',
    'Autorisation': 'Authorization',
    'Formulaire': 'Form',
    'Modèle': 'Template',
    
    # Informations
    'Nom': 'Name',
    'Prénom': 'First name',
    'Nom de famille': 'Last name',
    'Email': 'Email',
    'Téléphone': 'Phone',
    'Mobile': 'Mobile',
    'Adresse email': 'Email address',
    'Numéro de téléphone': 'Phone number',
    'Date de naissance': 'Date of birth',
    'Âge': 'Age',
    'Genre': 'Gender',
    'Sexe': 'Sex',
    'Nationalité': 'Nationality',
    'Description': 'Description',
    'Commentaire': 'Comment',
    'Remarque': 'Note',
    'Information': 'Information',
    'Détails': 'Details',
    
    # Messages & Notifications
    'Message': 'Message',
    'Messages': 'Messages',
    'Notification': 'Notification',
    'Notifications': 'Notifications',
    'Alerte': 'Alert',
    'Avertissement': 'Warning',
    'Erreur': 'Error',
    'Succès': 'Success',
    'Information': 'Information',
    'Confirmation': 'Confirmation',
    
    # Statistiques
    'Statistiques': 'Statistics',
    'Rapport': 'Report',
    'Rapports': 'Reports',
    'Graphique': 'Chart',
    'Tableau': 'Table',
    'Total': 'Total',
    'Moyenne': 'Average',
    'Minimum': 'Minimum',
    'Maximum': 'Maximum',
    'Pourcentage': 'Percentage',
    'Évolution': 'Evolution',
    'Progression': 'Progress',
    
    # Actions spécifiques
    'Gérer': 'Manage',
    'Administrer': 'Administer',
    'Configurer': 'Configure',
    'Paramétrer': 'Set up',
    'Organiser': 'Organize',
    'Planifier': 'Plan',
    'Programmer': 'Schedule',
    'Assigner': 'Assign',
    'Attribuer': 'Allocate',
    'Associer': 'Associate',
    'Lier': 'Link',
    'Délier': 'Unlink',
    'Activer': 'Enable',
    'Désactiver': 'Disable',
    'Autoriser': 'Authorize',
    'Interdire': 'Forbid',
    'Approuver': 'Approve',
    'Rejeter': 'Reject',
    'Archiver': 'Archive',
    'Restaurer': 'Restore',
    'Dupliquer': 'Duplicate',
    'Cloner': 'Clone',
    'Fusionner': 'Merge',
    'Diviser': 'Split',
    'Synchroniser': 'Synchronize',
    'Actualiser': 'Update',
    'Rafraîchir': 'Refresh',
    'Recharger': 'Reload',
}

def translate_string(french):
    """Traduit une chaîne française en anglais"""
    # Vérifier si c'est une traduction directe
    if french in TRANSLATIONS:
        return TRANSLATIONS[french]
    
    # Essayer avec la première lettre en minuscule
    if french and french[0].isupper():
        lower_french = french[0].lower() + french[1:]
        if lower_french in TRANSLATIONS:
            translation = TRANSLATIONS[lower_french]
            return translation[0].upper() + translation[1:]
    
    # Traduction mot par mot pour les phrases simples
    words = french.split()
    translated_words = []
    
    for word in words:
        # Chercher le mot exact
        if word in TRANSLATIONS:
            translated_words.append(TRANSLATIONS[word])
        # Chercher avec minuscule
        elif word.lower() in TRANSLATIONS:
            trans = TRANSLATIONS[word.lower()]
            if word[0].isupper():
                trans = trans[0].upper() + trans[1:]
            translated_words.append(trans)
        # Chercher sans ponctuation
        elif word.rstrip('.,!?:;') in TRANSLATIONS:
            punct = word[len(word.rstrip('.,!?:;')):]
            trans = TRANSLATIONS[word.rstrip('.,!?:;')]
            translated_words.append(trans + punct)
        else:
            # Garder le mot original si pas de traduction
            translated_words.append(word)
    
    return ' '.join(translated_words)

def main():
    print("=== Traduction automatique des chaînes vides ===\n")
    
    # Charger le fichier .po
    po_file = 'locale/en/LC_MESSAGES/django.po'
    print(f"Chargement de {po_file}...")
    po = polib.pofile(po_file)
    
    # Compter les entrées vides
    empty_entries = [entry for entry in po if not entry.msgstr and not entry.obsolete]
    print(f"Entrées vides trouvées: {len(empty_entries)}")
    
    # Traduire les entrées vides
    translated = 0
    examples = []
    
    for entry in empty_entries:
        translation = translate_string(entry.msgid)
        
        # Si on a trouvé une traduction différente du msgid
        if translation != entry.msgid:
            entry.msgstr = translation
            translated += 1
            
            if len(examples) < 10:
                examples.append((entry.msgid, translation))
    
    print(f"\nTraductions effectuées: {translated}/{len(empty_entries)}")
    
    if examples:
        print("\nExemples de traductions:")
        print("-" * 70)
        for fr, en in examples:
            print(f'"{fr}" → "{en}"')
    
    if translated > 0:
        print("\nSauvegarde du fichier .po...")
        po.save()
        
        print("Compilation du fichier .mo...")
        po.save_as_mofile(po_file.replace('.po', '.mo'))
        
        print("\n✅ Traduction terminée!")
        print(f"   - Traduites: {translated}")
        print(f"   - Restantes: {len(empty_entries) - translated}")
    else:
        print("\n⚠️  Aucune traduction automatique possible")
    
    # Statistiques finales
    still_empty = sum(1 for entry in po if not entry.msgstr and not entry.obsolete)
    print(f"\n📊 Total des traductions vides restantes: {still_empty}")

if __name__ == '__main__':
    main()