#!/usr/bin/env python
"""
Script pour mettre à jour les fichiers PO avec les chaînes manquantes.
Analyse les templates et Python files, puis ajoute les traductions absentes.
"""
import os
import re
from pathlib import Path
from datetime import datetime

# Chaînes à ajouter avec leurs traductions FR et EN
MISSING_TRANSLATIONS = {
    # Formulaires
    "Format de couleur invalide (ex: #FF0000)": {
        "fr": "Format de couleur invalide (ex: #FF0000)",
        "en": "Invalid color format (e.g. #FF0000)"
    },
    "URL de vidéo invalide (YouTube/Vimeo uniquement)": {
        "fr": "URL de vidéo invalide (YouTube/Vimeo uniquement)",
        "en": "Invalid video URL (YouTube/Vimeo only)"
    },
    "Format JSON invalide pour les sections personnalisées": {
        "fr": "Format JSON invalide pour les sections personnalisées",
        "en": "Invalid JSON format for custom sections"
    },

    # Compétitions
    "Aucune compétition": {
        "fr": "Aucune compétition",
        "en": "No competition"
    },
    "LIVE": {
        "fr": "EN DIRECT",
        "en": "LIVE"
    },
    "Officiel": {
        "fr": "Officiel",
        "en": "Official"
    },
    "Modifier": {
        "fr": "Modifier",
        "en": "Edit"
    },
    "En stock": {
        "fr": "En stock",
        "en": "In stock"
    },
    "Rupture": {
        "fr": "Rupture",
        "en": "Out of stock"
    },
    "Aucun grade disponible": {
        "fr": "Aucun grade disponible",
        "en": "No grade available"
    },
    "Erreur de chargement": {
        "fr": "Erreur de chargement",
        "en": "Loading error"
    },
    "Demander fusion": {
        "fr": "Demander fusion",
        "en": "Request merge"
    },

    # Import/Export
    "Gestion des données de votre club": {
        "fr": "Gestion des données de votre club",
        "en": "Managing your club data"
    },
    "Exporter les données": {
        "fr": "Exporter les données",
        "en": "Export data"
    },
    "Importer des données": {
        "fr": "Importer des données",
        "en": "Import data"
    },
    "Importation de données": {
        "fr": "Importation de données",
        "en": "Data import"
    },
    "Téléchargez le modèle": {
        "fr": "Téléchargez le modèle",
        "en": "Download the template"
    },
    "Remplissez le fichier": {
        "fr": "Remplissez le fichier",
        "en": "Fill in the file"
    },
    "Importez le fichier": {
        "fr": "Importez le fichier",
        "en": "Import the file"
    },
    "Déposez votre fichier ici": {
        "fr": "Déposez votre fichier ici",
        "en": "Drop your file here"
    },
    "Glissez votre fichier ici": {
        "fr": "Glissez votre fichier ici",
        "en": "Drag your file here"
    },
    "Formats de date acceptés": {
        "fr": "Formats de date acceptés",
        "en": "Accepted date formats"
    },
    "Vérifiez que les noms de colonnes correspondent": {
        "fr": "Vérifiez que les noms de colonnes correspondent",
        "en": "Make sure column names match"
    },
    "Les doublons seront automatiquement ignorés": {
        "fr": "Les doublons seront automatiquement ignorés",
        "en": "Duplicates will be automatically ignored"
    },
    "Fichier sélectionné": {
        "fr": "Fichier sélectionné",
        "en": "Selected file"
    },

    # QR Code
    "QR Code": {
        "fr": "QR Code",
        "en": "QR Code"
    },
    "QR Code Site": {
        "fr": "QR Code Site",
        "en": "Site QR Code"
    },
    "QR Code Inscription": {
        "fr": "QR Code Inscription",
        "en": "Registration QR Code"
    },
    "QR Code Activité": {
        "fr": "QR Code Activité",
        "en": "Activity QR Code"
    },
    "QR Code du profil": {
        "fr": "QR Code du profil",
        "en": "Profile QR Code"
    },

    # Pratiquants
    "Inscription en masse": {
        "fr": "Inscription en masse",
        "en": "Bulk registration"
    },
    "Sélectionner une compétition": {
        "fr": "Sélectionner une compétition",
        "en": "Select a competition"
    },
    "Prêt": {
        "fr": "Prêt",
        "en": "Ready"
    },
    "Aucun pratiquant": {
        "fr": "Aucun pratiquant",
        "en": "No practitioner"
    },
    "Liste des Pratiquants": {
        "fr": "Liste des Pratiquants",
        "en": "List of Practitioners"
    },

    # Combats
    "Kata": {
        "fr": "Kata",
        "en": "Kata"
    },
    "Kumite": {
        "fr": "Kumite",
        "en": "Kumite"
    },
    "Kata par équipe": {
        "fr": "Kata par équipe",
        "en": "Team Kata"
    },
    "Rouge": {
        "fr": "Rouge",
        "en": "Red"
    },
    "Blanc": {
        "fr": "Blanc",
        "en": "White"
    },
    "GONG": {
        "fr": "GONG",
        "en": "GONG"
    },
    "Historique des Actions": {
        "fr": "Historique des Actions",
        "en": "Action History"
    },
    "Prêt à démarrer": {
        "fr": "Prêt à démarrer",
        "en": "Ready to start"
    },
    "Pénalité": {
        "fr": "Pénalité",
        "en": "Penalty"
    },
    "Sortie": {
        "fr": "Sortie",
        "en": "Exit"
    },
    "Retrait": {
        "fr": "Retrait",
        "en": "Withdrawal"
    },
    "Gestion Poule": {
        "fr": "Gestion Poule",
        "en": "Pool Management"
    },
    "Refresh": {
        "fr": "Actualiser",
        "en": "Refresh"
    },
    "Plein écran": {
        "fr": "Plein écran",
        "en": "Full screen"
    },
    "Club ROUGE": {
        "fr": "Club ROUGE",
        "en": "RED Club"
    },
    "Club BLANC": {
        "fr": "Club BLANC",
        "en": "WHITE Club"
    },
    "Pays": {
        "fr": "Pays",
        "en": "Country"
    },

    # Tableaux et formulaires
    "Nom Prénom": {
        "fr": "Nom Prénom",
        "en": "Name"
    },
    "Age": {
        "fr": "Âge",
        "en": "Age"
    },
    "Grade": {
        "fr": "Grade",
        "en": "Grade"
    },
    "Contact": {
        "fr": "Contact",
        "en": "Contact"
    },
    "Licence": {
        "fr": "Licence",
        "en": "License"
    },
    "Discipline": {
        "fr": "Discipline",
        "en": "Discipline"
    },
    "Inscription": {
        "fr": "Inscription",
        "en": "Registration"
    },
    "Statut": {
        "fr": "Statut",
        "en": "Status"
    },
    "Rôle": {
        "fr": "Rôle",
        "en": "Role"
    },
    "Actif": {
        "fr": "Actif",
        "en": "Active"
    },
    "Inactif": {
        "fr": "Inactif",
        "en": "Inactive"
    },
    "INSTRUCTEUR": {
        "fr": "INSTRUCTEUR",
        "en": "INSTRUCTOR"
    },
    "Document généré automatiquement par MartialComp": {
        "fr": "Document généré automatiquement par MartialComp",
        "en": "Document automatically generated by MartialComp"
    },
    "Total": {
        "fr": "Total",
        "en": "Total"
    },
    "Dans cette liste": {
        "fr": "Dans cette liste",
        "en": "In this list"
    },
    "Actifs": {
        "fr": "Actifs",
        "en": "Active"
    },
    "Instructeurs": {
        "fr": "Instructeurs",
        "en": "Instructors"
    },
    "Compte utilisateur": {
        "fr": "Compte utilisateur",
        "en": "User account"
    },

    # Dashboard
    "Fermer": {
        "fr": "Fermer",
        "en": "Close"
    },
    "Retirer": {
        "fr": "Retirer",
        "en": "Remove"
    },
    "Ouvert": {
        "fr": "Ouvert",
        "en": "Open"
    },
    "Pratiquants": {
        "fr": "Pratiquants",
        "en": "Practitioners"
    },
    "Compétitions": {
        "fr": "Compétitions",
        "en": "Competitions"
    },
    "Inscriptions": {
        "fr": "Inscriptions",
        "en": "Registrations"
    },
    "Juges": {
        "fr": "Juges",
        "en": "Judges"
    },
    "Solde": {
        "fr": "Solde",
        "en": "Balance"
    },
    "Recettes": {
        "fr": "Recettes",
        "en": "Revenue"
    },
    "Dépenses": {
        "fr": "Dépenses",
        "en": "Expenses"
    },
    "Factures en attente": {
        "fr": "Factures en attente",
        "en": "Pending invoices"
    },
    "Compétitions organisées": {
        "fr": "Compétitions organisées",
        "en": "Organized competitions"
    },
    "Inscriptions actives": {
        "fr": "Inscriptions actives",
        "en": "Active registrations"
    },
    "Avatar": {
        "fr": "Avatar",
        "en": "Avatar"
    },
    "Trophy": {
        "fr": "Trophée",
        "en": "Trophy"
    },

    # Documentation
    "Bouton test": {
        "fr": "Bouton test",
        "en": "Test button"
    },
    "Bouton vert": {
        "fr": "Bouton vert",
        "en": "Green button"
    },
    "Bouton jaune": {
        "fr": "Bouton jaune",
        "en": "Yellow button"
    },
    "Diagnostic": {
        "fr": "Diagnostic",
        "en": "Diagnostic"
    },
    "Documentation Content Test": {
        "fr": "Test de contenu de documentation",
        "en": "Documentation Content Test"
    },
    "Contenu de test normal": {
        "fr": "Contenu de test normal",
        "en": "Normal test content"
    },
    "Autre contenu de test": {
        "fr": "Autre contenu de test",
        "en": "Other test content"
    },
    "Troisième contenu": {
        "fr": "Troisième contenu",
        "en": "Third content"
    },
    "Voir Documentation": {
        "fr": "Voir Documentation",
        "en": "View Documentation"
    },
    "Navigation": {
        "fr": "Navigation",
        "en": "Navigation"
    },
    "Documentation MartialComp": {
        "fr": "Documentation MartialComp",
        "en": "MartialComp Documentation"
    },
    "Dashboard Participant": {
        "fr": "Dashboard Participant",
        "en": "Participant Dashboard"
    },
    "Dashboard Club": {
        "fr": "Dashboard Club",
        "en": "Club Dashboard"
    },
    "Contenu de documentation": {
        "fr": "Contenu de documentation",
        "en": "Documentation content"
    },
    "Interface pour les participants": {
        "fr": "Interface pour les participants",
        "en": "Interface for participants"
    },
    "Gestion des clubs": {
        "fr": "Gestion des clubs",
        "en": "Club management"
    },
    "Introduction": {
        "fr": "Introduction",
        "en": "Introduction"
    },
    "Organisateur": {
        "fr": "Organisateur",
        "en": "Organizer"
    },

    # Fédérations
    "Informations de la Fédération": {
        "fr": "Informations de la Fédération",
        "en": "Federation Information"
    },
    "Statistiques": {
        "fr": "Statistiques",
        "en": "Statistics"
    },
    "Aucun club trouvé": {
        "fr": "Aucun club trouvé",
        "en": "No club found"
    },
    "Actions de Test": {
        "fr": "Actions de Test",
        "en": "Test Actions"
    },
    "Nom": {
        "fr": "Nom",
        "en": "Name"
    },
    "Ville": {
        "fr": "Ville",
        "en": "City"
    },
    "Organisation ID": {
        "fr": "Organisation ID",
        "en": "Organization ID"
    },
    "Propriétaire": {
        "fr": "Propriétaire",
        "en": "Owner"
    },
    "Championnat National": {
        "fr": "Championnat National",
        "en": "National Championship"
    },
    "Coupe Régionale": {
        "fr": "Coupe Régionale",
        "en": "Regional Cup"
    },

    # Modales fédérations
    "Annuler": {
        "fr": "Annuler",
        "en": "Cancel"
    },
    "Couleur principale": {
        "fr": "Couleur principale",
        "en": "Primary color"
    },
    "Couleur secondaire": {
        "fr": "Couleur secondaire",
        "en": "Secondary color"
    },
    "Couleur du texte": {
        "fr": "Couleur du texte",
        "en": "Text color"
    },
    "Police": {
        "fr": "Police",
        "en": "Font"
    },
    "Style de mise en page": {
        "fr": "Style de mise en page",
        "en": "Layout style"
    },
    "Arial": {
        "fr": "Arial",
        "en": "Arial"
    },
    "Helvetica": {
        "fr": "Helvetica",
        "en": "Helvetica"
    },
    "Georgia": {
        "fr": "Georgia",
        "en": "Georgia"
    },
    "Times New Roman": {
        "fr": "Times New Roman",
        "en": "Times New Roman"
    },
    "Générer": {
        "fr": "Générer",
        "en": "Generate"
    },
    "Paiement": {
        "fr": "Paiement",
        "en": "Payment"
    },
    "Taille des QR codes": {
        "fr": "Taille des QR codes",
        "en": "QR codes size"
    },
    "Format": {
        "fr": "Format",
        "en": "Format"
    },
    "Titre principal": {
        "fr": "Titre principal",
        "en": "Main title"
    },
    "Contenu principal": {
        "fr": "Contenu principal",
        "en": "Main content"
    },
    "Histoire": {
        "fr": "Histoire",
        "en": "History"
    },
    "Mission": {
        "fr": "Mission",
        "en": "Mission"
    },
    "Valeurs": {
        "fr": "Valeurs",
        "en": "Values"
    },
    "Réalisations": {
        "fr": "Réalisations",
        "en": "Achievements"
    },
    "Email de contact": {
        "fr": "Email de contact",
        "en": "Contact email"
    },
    "Téléphone": {
        "fr": "Téléphone",
        "en": "Phone"
    },
    "Adresse": {
        "fr": "Adresse",
        "en": "Address"
    },
    "Nom de la fédération": {
        "fr": "Nom de la fédération",
        "en": "Federation name"
    },
    "Acronyme": {
        "fr": "Acronyme",
        "en": "Acronym"
    },
    "Description": {
        "fr": "Description",
        "en": "Description"
    },
    "Email": {
        "fr": "Email",
        "en": "Email"
    },
    "Site web": {
        "fr": "Site web",
        "en": "Website"
    },
    "Catégorie": {
        "fr": "Catégorie",
        "en": "Category"
    },
    "Logo": {
        "fr": "Logo",
        "en": "Logo"
    },
    "Bannière": {
        "fr": "Bannière",
        "en": "Banner"
    },
    "Galerie": {
        "fr": "Galerie",
        "en": "Gallery"
    },
    "Description des photos": {
        "fr": "Description des photos",
        "en": "Photos description"
    },

    # Scoring
    "Dossard": {
        "fr": "Dossard",
        "en": "Bib number"
    },
    "Pratiquant": {
        "fr": "Pratiquant",
        "en": "Practitioner"
    },
    "Note": {
        "fr": "Note",
        "en": "Score"
    },
    "Action": {
        "fr": "Action",
        "en": "Action"
    },
    "Orange": {
        "fr": "Orange",
        "en": "Orange"
    },
    "Jaune": {
        "fr": "Jaune",
        "en": "Yellow"
    },
    "Vert": {
        "fr": "Vert",
        "en": "Green"
    },

    # Welcome/Login
    "Créer un compte": {
        "fr": "Créer un compte",
        "en": "Create account"
    },
    "Mot de passe": {
        "fr": "Mot de passe",
        "en": "Password"
    },
    "Connexion à votre compte": {
        "fr": "Connexion à votre compte",
        "en": "Login to your account"
    },
    "MartialComp Logo": {
        "fr": "Logo MartialComp",
        "en": "MartialComp Logo"
    },
    "MartialComp Platform": {
        "fr": "Plateforme MartialComp",
        "en": "MartialComp Platform"
    },
    "Plateforme de Gestion des Arts Martiaux": {
        "fr": "Plateforme de Gestion des Arts Martiaux",
        "en": "Martial Arts Management Platform"
    },

    # Organisation templates
    "QR Codes": {
        "fr": "QR Codes",
        "en": "QR Codes"
    },
    "Rechercher": {
        "fr": "Rechercher",
        "en": "Search"
    },
    "Prévisualiser": {
        "fr": "Prévisualiser",
        "en": "Preview"
    },
    "Précédent": {
        "fr": "Précédent",
        "en": "Previous"
    },
    "Suivant": {
        "fr": "Suivant",
        "en": "Next"
    },
    "Administration des organisations": {
        "fr": "Administration des organisations",
        "en": "Organizations administration"
    },
    "Type": {
        "fr": "Type",
        "en": "Type"
    },
    "Date de création": {
        "fr": "Date de création",
        "en": "Creation date"
    },
    "Actions": {
        "fr": "Actions",
        "en": "Actions"
    },
    "Sauvegarder": {
        "fr": "Sauvegarder",
        "en": "Save"
    },
    "Supprimer": {
        "fr": "Supprimer",
        "en": "Delete"
    },
    "Prévisualisation": {
        "fr": "Prévisualisation",
        "en": "Preview"
    },
    "Afficher les liens sociaux": {
        "fr": "Afficher les liens sociaux",
        "en": "Show social links"
    },
    "Afficher la section vidéos": {
        "fr": "Afficher la section vidéos",
        "en": "Show videos section"
    },
    "Activer la lightbox pour les images": {
        "fr": "Activer la lightbox pour les images",
        "en": "Enable lightbox for images"
    },
    "Activer les animations CSS": {
        "fr": "Activer les animations CSS",
        "en": "Enable CSS animations"
    },
    "Activer le mode sombre": {
        "fr": "Activer le mode sombre",
        "en": "Enable dark mode"
    },
    "Texte simple": {
        "fr": "Texte simple",
        "en": "Plain text"
    },
    "Image": {
        "fr": "Image",
        "en": "Image"
    },
    "Nos vidéos": {
        "fr": "Nos vidéos",
        "en": "Our videos"
    },
    "Accueil": {
        "fr": "Accueil",
        "en": "Home"
    },
    "Services": {
        "fr": "Services",
        "en": "Services"
    },
    "Accès Rapide": {
        "fr": "Accès Rapide",
        "en": "Quick Access"
    },
    "Ce que nous offrons": {
        "fr": "Ce que nous offrons",
        "en": "What we offer"
    },

    # Emails
    "Se connecter à MartialComp": {
        "fr": "Se connecter à MartialComp",
        "en": "Login to MartialComp"
    },
    "Vos identifiants de connexion": {
        "fr": "Vos identifiants de connexion",
        "en": "Your login credentials"
    },
    "Consulter vos informations personnelles": {
        "fr": "Consulter vos informations personnelles",
        "en": "View your personal information"
    },
    "Voir vos inscriptions aux compétitions": {
        "fr": "Voir vos inscriptions aux compétitions",
        "en": "View your competition registrations"
    },
    "Suivre vos résultats et performances": {
        "fr": "Suivre vos résultats et performances",
        "en": "Track your results and performances"
    },
    "Accéder à votre QR code personnel": {
        "fr": "Accéder à votre QR code personnel",
        "en": "Access your personal QR code"
    },
    "Recevoir des notifications importantes": {
        "fr": "Recevoir des notifications importantes",
        "en": "Receive important notifications"
    },
    "Modification importante": {
        "fr": "Modification importante",
        "en": "Important change"
    },
    "Détails de la compétition": {
        "fr": "Détails de la compétition",
        "en": "Competition details"
    },
    "Informations importantes": {
        "fr": "Informations importantes",
        "en": "Important information"
    },
    "Votre facture est disponible": {
        "fr": "Votre facture est disponible",
        "en": "Your invoice is available"
    },
    "Détails de la facture": {
        "fr": "Détails de la facture",
        "en": "Invoice details"
    },
    "Paiement automatique": {
        "fr": "Paiement automatique",
        "en": "Automatic payment"
    },
    "Réinitialiser mon mot de passe": {
        "fr": "Réinitialiser mon mot de passe",
        "en": "Reset my password"
    },
    "Réinitialisation de votre mot de passe": {
        "fr": "Réinitialisation de votre mot de passe",
        "en": "Reset your password"
    },
    "Créer un nouveau mot de passe": {
        "fr": "Créer un nouveau mot de passe",
        "en": "Create a new password"
    },
    "Détails du paiement": {
        "fr": "Détails du paiement",
        "en": "Payment details"
    },
    "Rappel de paiement": {
        "fr": "Rappel de paiement",
        "en": "Payment reminder"
    },
    "Détails du paiement en attente": {
        "fr": "Détails du paiement en attente",
        "en": "Pending payment details"
    },
    "Pour finaliser votre paiement": {
        "fr": "Pour finaliser votre paiement",
        "en": "To complete your payment"
    },
    "Confirmation de paiement": {
        "fr": "Confirmation de paiement",
        "en": "Payment confirmation"
    },
    "Confirmation de remboursement": {
        "fr": "Confirmation de remboursement",
        "en": "Refund confirmation"
    },
    "Détails du remboursement": {
        "fr": "Détails du remboursement",
        "en": "Refund details"
    },
    "Délai de traitement": {
        "fr": "Délai de traitement",
        "en": "Processing time"
    },
    "Reçu de paiement": {
        "fr": "Reçu de paiement",
        "en": "Payment receipt"
    },
    "Gestion de votre abonnement": {
        "fr": "Gestion de votre abonnement",
        "en": "Manage your subscription"
    },
    "Confirmer mon compte": {
        "fr": "Confirmer mon compte",
        "en": "Confirm my account"
    },
    "Confirmez votre compte": {
        "fr": "Confirmez votre compte",
        "en": "Confirm your account"
    },

    # Factures
    "Destinataire": {
        "fr": "Destinataire",
        "en": "Recipient"
    },
    "Article": {
        "fr": "Article",
        "en": "Item"
    },
    "Prix unitaire": {
        "fr": "Prix unitaire",
        "en": "Unit price"
    },
    "Qté": {
        "fr": "Qté",
        "en": "Qty"
    },
    "Choisissez le format CSV": {
        "fr": "Choisissez le format CSV",
        "en": "Choose CSV format"
    },
    "Sélectionnez la période": {
        "fr": "Sélectionnez la période",
        "en": "Select the period"
    },
    "Téléchargez le fichier": {
        "fr": "Téléchargez le fichier",
        "en": "Download the file"
    },

    # Grades
    "CERTIFICAT DE GRADE": {
        "fr": "CERTIFICAT DE GRADE",
        "en": "GRADE CERTIFICATE"
    },

    # Onboarding
    "Créer ma compétition": {
        "fr": "Créer ma compétition",
        "en": "Create my competition"
    },
    "Complétez les informations de votre organisation": {
        "fr": "Complétez les informations de votre organisation",
        "en": "Complete your organization information"
    },
    "Mes compétitions": {
        "fr": "Mes compétitions",
        "en": "My competitions"
    },
    "Créer une nouvelle compétition": {
        "fr": "Créer une nouvelle compétition",
        "en": "Create a new competition"
    },
    "Gérer les participants": {
        "fr": "Gérer les participants",
        "en": "Manage participants"
    },
    "Gérer les scores": {
        "fr": "Gérer les scores",
        "en": "Manage scores"
    },
    "Support": {
        "fr": "Support",
        "en": "Support"
    },
    "QR Management": {
        "fr": "Gestion QR",
        "en": "QR Management"
    },

    # Organisations
    "Créez votre organisation et obtenez automatiquement un site web et des QR codes": {
        "fr": "Créez votre organisation et obtenez automatiquement un site web et des QR codes",
        "en": "Create your organization and automatically get a website and QR codes"
    },
    "Visiter le site": {
        "fr": "Visiter le site",
        "en": "Visit website"
    },
    "Administration": {
        "fr": "Administration",
        "en": "Administration"
    },
    "Votre organisation a été créée avec succès": {
        "fr": "Votre organisation a été créée avec succès",
        "en": "Your organization has been successfully created"
    },

    # Messages Python
    "Impossible de déterminer votre organisation. Contactez l": {
        "fr": "Impossible de déterminer votre organisation. Contactez l'administrateur.",
        "en": "Unable to determine your organization. Contact administrator."
    },
    "Aucune organisation trouvée": {
        "fr": "Aucune organisation trouvée",
        "en": "No organization found"
    },
    "Dashboard Coach (Mode dégradé)": {
        "fr": "Dashboard Coach (Mode dégradé)",
        "en": "Coach Dashboard (Fallback Mode)"
    },
    "Nouveau cours créé avec succès!": {
        "fr": "Nouveau cours créé avec succès!",
        "en": "New course created successfully!"
    },
    "Nouvel élève ajouté avec succès!": {
        "fr": "Nouvel élève ajouté avec succès!",
        "en": "New student added successfully!"
    },
    "Nouvelle discipline ajoutée avec succès!": {
        "fr": "Nouvelle discipline ajoutée avec succès!",
        "en": "New discipline added successfully!"
    },
    "Fédération introuvable.": {
        "fr": "Fédération introuvable.",
        "en": "Federation not found."
    },
    "Paramètres mis à jour avec succès.": {
        "fr": "Paramètres mis à jour avec succès.",
        "en": "Settings updated successfully."
    },
    "Notifications de test créées avec succès!": {
        "fr": "Notifications de test créées avec succès!",
        "en": "Test notifications created successfully!"
    },
    "Scoring configuration updated successfully.": {
        "fr": "Configuration de scoring mise à jour avec succès.",
        "en": "Scoring configuration updated successfully."
    },
    "Default criteria generated based on discipline.": {
        "fr": "Critères par défaut générés en fonction de la discipline.",
        "en": "Default criteria generated based on discipline."
    },
    "Performance removed successfully.": {
        "fr": "Performance supprimée avec succès.",
        "en": "Performance removed successfully."
    },
    "Could not start performance. It may already be in progress.": {
        "fr": "Impossible de démarrer la performance. Elle est peut-être déjà en cours.",
        "en": "Could not start performance. It may already be in progress."
    },
    "Could not end performance. It may not be in progress.": {
        "fr": "Impossible de terminer la performance. Elle n'est peut-être pas en cours.",
        "en": "Could not end performance. It may not be in progress."
    },
    "Results published successfully.": {
        "fr": "Résultats publiés avec succès.",
        "en": "Results published successfully."
    },
    "Settings updated successfully.": {
        "fr": "Paramètres mis à jour avec succès.",
        "en": "Settings updated successfully."
    },
    "Scores submitted successfully.": {
        "fr": "Scores soumis avec succès.",
        "en": "Scores submitted successfully."
    },

    # Tests
    "Page de test de traduction": {
        "fr": "Page de test de traduction",
        "en": "Translation test page"
    },
    "Exemple": {
        "fr": "Exemple",
        "en": "Example"
    },
    "Français": {
        "fr": "Français",
        "en": "French"
    },
    "English": {
        "fr": "Anglais",
        "en": "English"
    },
    "Deutsch": {
        "fr": "Allemand",
        "en": "German"
    },
}


def escape_po_string(s):
    """Escape special characters for PO file format."""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    return s


def get_existing_msgids(po_file):
    """Extract existing msgids from PO file."""
    existing = set()
    try:
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all msgid entries
            matches = re.findall(r'msgid\s+"([^"]+)"', content)
            for match in matches:
                existing.add(match.replace('\\"', '"'))
    except Exception as e:
        print(f"Error reading {po_file}: {e}")
    return existing


def append_translations_to_po(po_file, lang, translations, existing):
    """Append missing translations to PO file."""
    added = []

    with open(po_file, 'a', encoding='utf-8') as f:
        f.write(f"\n# === Added by update_po_translations.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

        for msgid, trans in translations.items():
            # Check if already exists
            if msgid in existing or escape_po_string(msgid) in existing:
                continue

            msgstr = trans.get(lang, msgid)

            f.write(f'msgid "{escape_po_string(msgid)}"\n')
            f.write(f'msgstr "{escape_po_string(msgstr)}"\n\n')
            added.append(msgid)

    return added


def main():
    base_dir = Path('.')
    locale_dir = base_dir / 'locale'

    print("=" * 80)
    print("MISE À JOUR DES FICHIERS PO")
    print("=" * 80)

    for lang in ['fr', 'en']:
        po_file = locale_dir / lang / 'LC_MESSAGES' / 'django.po'

        if not po_file.exists():
            print(f"\n[WARNING] Fichier non trouvé: {po_file}")
            continue

        print(f"\n--- Traitement de {lang.upper()} ---")
        print(f"Fichier: {po_file}")

        # Get existing msgids
        existing = get_existing_msgids(po_file)
        print(f"Chaînes existantes: {len(existing)}")

        # Append missing translations
        added = append_translations_to_po(po_file, lang, MISSING_TRANSLATIONS, existing)
        print(f"Chaînes ajoutées: {len(added)}")

        if added[:5]:
            print("Exemples ajoutés:")
            for msgid in added[:5]:
                print(f"  - {msgid[:50]}...")

    print("\n" + "=" * 80)
    print("TERMINÉ!")
    print("=" * 80)
    print("\nPour compiler les fichiers PO en MO, exécutez:")
    print("  python manage.py compilemessages")


if __name__ == '__main__':
    main()
