#!/usr/bin/env python
"""
Script pour ajouter les traductions manquantes aux fichiers PO.
"""

import os

# Nouvelles chaînes à ajouter (msgid -> msgstr pour FR, msgid -> msgstr pour EN)
NEW_TRANSLATIONS_FR = {
    # organization_sites.py
    "Organisation non trouvée": "Organisation non trouvée",
    "Erreur génération QR codes": "Erreur génération QR codes",
    "Type de QR code non trouvé": "Type de QR code non trouvé",
    "Permissions insuffisantes": "Permissions insuffisantes",
    "Méthode non autorisée": "Méthode non autorisée",
    "Méthode POST requise": "Méthode POST requise",
    "Données QR manquantes": "Données QR manquantes",
    "Message envoyé avec succès!": "Message envoyé avec succès!",
    "Check-in effectué avec succès!": "Check-in effectué avec succès!",
    "QR code invalide ou membre non trouvé": "QR code invalide ou membre non trouvé",
    "Erreur lors du check-in": "Erreur lors du check-in",
    "Erreur serveur": "Erreur serveur",

    # schedule_api.py
    "Non authentifié": "Non authentifié",
    "Permission refusée": "Permission refusée",
    "Données manquantes": "Données manquantes",
    "JSON invalide": "JSON invalide",
    "category_id requis": "category_id requis",
    "Catégorie retirée du tatami": "Catégorie retirée du tatami",
    "Données invalides": "Données invalides",
    "Catégorie non assignée": "Catégorie non assignée",
    "Déjà en première position": "Déjà en première position",
    "Déjà en dernière position": "Déjà en dernière position",
    "Horaire mis à jour": "Horaire mis à jour",
    "Aucune catégorie à programmer": "Aucune catégorie à programmer",
    "Format d'heure invalide (HH:MM)": "Format d'heure invalide (HH:MM)",

    # practitioners.py
    "Paramètres manquants": "Paramètres manquants",
    "Action non reconnue": "Action non reconnue",
    "Erreur lors de l'opération": "Erreur lors de l'opération",
    "Club non trouvé": "Club non trouvé",

    # import_export templates
    "Import/Export de données": "Import/Export de données",
    "Gestion des données de votre club": "Gestion des données de votre club",
    "Cette page vous permet d'importer et d'exporter les données de votre club au format Excel. Vous pouvez ainsi gérer facilement vos pratiquants et optimiser votre organisation.": "Cette page vous permet d'importer et d'exporter les données de votre club au format Excel. Vous pouvez ainsi gérer facilement vos pratiquants et optimiser votre organisation.",
    "Exporter les données": "Exporter les données",
    "Téléchargez toutes les données de vos pratiquants au format Excel pour les consulter hors ligne ou les modifier dans un tableur.": "Téléchargez toutes les données de vos pratiquants au format Excel pour les consulter hors ligne ou les modifier dans un tableur.",
    "Exporter en Excel": "Exporter en Excel",
    "Importer des données": "Importer des données",
    "Importez de nouveaux pratiquants ou mettez à jour les existants en uploadant un fichier Excel au format approprié.": "Importez de nouveaux pratiquants ou mettez à jour les existants en uploadant un fichier Excel au format approprié.",
    "Commencer l'import": "Commencer l'import",
    "Importation de données": "Importation de données",
    "Téléchargez le modèle": "Téléchargez le modèle",
    "Utilisez notre modèle Excel pour vous assurer que vos données sont au bon format.": "Utilisez notre modèle Excel pour vous assurer que vos données sont au bon format.",
    "Télécharger le modèle": "Télécharger le modèle",
    "Remplissez le fichier": "Remplissez le fichier",
    "Complétez le fichier Excel avec les informations de vos pratiquants. Veillez à respecter le format des colonnes.": "Complétez le fichier Excel avec les informations de vos pratiquants. Veillez à respecter le format des colonnes.",
    "Importez le fichier": "Importez le fichier",
    "Uploadez votre fichier Excel complété pour importer les données dans le système.": "Uploadez votre fichier Excel complété pour importer les données dans le système.",
    "Déposez votre fichier ici": "Déposez votre fichier ici",
    "Choisir un fichier...": "Choisir un fichier...",
    "Formats acceptés: .xlsx, .xls": "Formats acceptés: .xlsx, .xls",
    "Importer les données": "Importer les données",
    "Structure attendue du fichier Excel": "Structure attendue du fichier Excel",
    "Colonne A:": "Colonne A :",
    "Colonne B:": "Colonne B :",
    "Colonne C:": "Colonne C :",
    "Colonne D:": "Colonne D :",
    "Colonne E:": "Colonne E :",
    "Colonne F:": "Colonne F :",
    "Date de naissance (AAAA-MM-JJ)": "Date de naissance (AAAA-MM-JJ)",
    "Numéro de licence": "Numéro de licence",
    "Retour au tableau de bord": "Retour au tableau de bord",
    "Gérer les pratiquants": "Gérer les pratiquants",

    # import_export_v2.html
    "Exporter les pratiquants": "Exporter les pratiquants",
    "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.",
    "Format: Excel (.xlsx)": "Format : Excel (.xlsx)",
    "Importer des pratiquants": "Importer des pratiquants",
    "Modèle de fichier": "Modèle de fichier",
    "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.",
    "Télécharger le modèle Excel": "Télécharger le modèle Excel",
    "Format attendu:": "Format attendu :",
    "Prénom": "Prénom",
    "NOM": "NOM",
    "Date de naissance": "Date de naissance",
    "adresse mail": "adresse mail",
    "Glissez votre fichier ici": "Glissez votre fichier ici",
    "ou cliquez pour sélectionner": "ou cliquez pour sélectionner",
    "Choisir un fichier": "Choisir un fichier",
    "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Formats acceptés : CSV, Excel (.xlsx, .xls) - Max 10MB",
    "Importation en cours...": "Importation en cours...",
    "Résultats de l'importation": "Résultats de l'importation",
    "Aide et conseils": "Aide et conseils",
    "Formats de date acceptés": "Formats de date acceptés",
    "JJ/MM/AAAA (ex: 15/03/2010)": "JJ/MM/AAAA (ex : 15/03/2010)",
    "JJ-MM-AAAA (ex: 15-03-2010)": "JJ-MM-AAAA (ex : 15-03-2010)",
    "JJ.MM.AAAA (ex: 15.03.2010)": "JJ.MM.AAAA (ex : 15.03.2010)",
    "Conseils pour l'import": "Conseils pour l'import",
    "Vérifiez que les noms de colonnes correspondent": "Vérifiez que les noms de colonnes correspondent",
    "Assurez-vous que les dates sont au bon format": "Assurez-vous que les dates sont au bon format",
    "Les doublons seront automatiquement ignorés": "Les doublons seront automatiquement ignorés",
}

NEW_TRANSLATIONS_EN = {
    # organization_sites.py
    "Organisation non trouvée": "Organization not found",
    "Erreur génération QR codes": "QR codes generation error",
    "Type de QR code non trouvé": "QR code type not found",
    "Permissions insuffisantes": "Insufficient permissions",
    "Méthode non autorisée": "Method not allowed",
    "Méthode POST requise": "POST method required",
    "Données QR manquantes": "Missing QR data",
    "Message envoyé avec succès!": "Message sent successfully!",
    "Check-in effectué avec succès!": "Check-in completed successfully!",
    "QR code invalide ou membre non trouvé": "Invalid QR code or member not found",
    "Erreur lors du check-in": "Error during check-in",
    "Erreur serveur": "Server error",

    # schedule_api.py
    "Non authentifié": "Not authenticated",
    "Permission refusée": "Permission denied",
    "Données manquantes": "Missing data",
    "JSON invalide": "Invalid JSON",
    "category_id requis": "category_id required",
    "Catégorie retirée du tatami": "Category removed from tatami",
    "Données invalides": "Invalid data",
    "Catégorie non assignée": "Category not assigned",
    "Déjà en première position": "Already in first position",
    "Déjà en dernière position": "Already in last position",
    "Horaire mis à jour": "Schedule updated",
    "Aucune catégorie à programmer": "No category to schedule",
    "Format d'heure invalide (HH:MM)": "Invalid time format (HH:MM)",

    # practitioners.py
    "Paramètres manquants": "Missing parameters",
    "Action non reconnue": "Unrecognized action",
    "Erreur lors de l'opération": "Error during operation",
    "Club non trouvé": "Club not found",

    # import_export templates
    "Import/Export de données": "Data Import/Export",
    "Gestion des données de votre club": "Manage your club's data",
    "Cette page vous permet d'importer et d'exporter les données de votre club au format Excel. Vous pouvez ainsi gérer facilement vos pratiquants et optimiser votre organisation.": "This page allows you to import and export your club's data in Excel format. This way you can easily manage your practitioners and optimize your organization.",
    "Exporter les données": "Export data",
    "Téléchargez toutes les données de vos pratiquants au format Excel pour les consulter hors ligne ou les modifier dans un tableur.": "Download all your practitioners' data in Excel format to view offline or edit in a spreadsheet.",
    "Exporter en Excel": "Export to Excel",
    "Importer des données": "Import data",
    "Importez de nouveaux pratiquants ou mettez à jour les existants en uploadant un fichier Excel au format approprié.": "Import new practitioners or update existing ones by uploading an Excel file in the appropriate format.",
    "Commencer l'import": "Start import",
    "Importation de données": "Data import",
    "Téléchargez le modèle": "Download template",
    "Utilisez notre modèle Excel pour vous assurer que vos données sont au bon format.": "Use our Excel template to ensure your data is in the correct format.",
    "Télécharger le modèle": "Download template",
    "Remplissez le fichier": "Fill in the file",
    "Complétez le fichier Excel avec les informations de vos pratiquants. Veillez à respecter le format des colonnes.": "Complete the Excel file with your practitioners' information. Make sure to respect the column format.",
    "Importez le fichier": "Import the file",
    "Uploadez votre fichier Excel complété pour importer les données dans le système.": "Upload your completed Excel file to import the data into the system.",
    "Déposez votre fichier ici": "Drop your file here",
    "Choisir un fichier...": "Choose a file...",
    "Formats acceptés: .xlsx, .xls": "Accepted formats: .xlsx, .xls",
    "Importer les données": "Import data",
    "Structure attendue du fichier Excel": "Expected Excel file structure",
    "Colonne A:": "Column A:",
    "Colonne B:": "Column B:",
    "Colonne C:": "Column C:",
    "Colonne D:": "Column D:",
    "Colonne E:": "Column E:",
    "Colonne F:": "Column F:",
    "Date de naissance (AAAA-MM-JJ)": "Date of birth (YYYY-MM-DD)",
    "Numéro de licence": "License number",
    "Retour au tableau de bord": "Back to dashboard",
    "Gérer les pratiquants": "Manage practitioners",

    # import_export_v2.html
    "Exporter les pratiquants": "Export practitioners",
    "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Download the complete list of your practitioners in Excel format for backup or offline editing.",
    "Format: Excel (.xlsx)": "Format: Excel (.xlsx)",
    "Importer des pratiquants": "Import practitioners",
    "Modèle de fichier": "File template",
    "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Download this template to ensure your file is in the correct format.",
    "Télécharger le modèle Excel": "Download Excel template",
    "Format attendu:": "Expected format:",
    "Prénom": "First name",
    "NOM": "LAST NAME",
    "Date de naissance": "Date of birth",
    "adresse mail": "email address",
    "Glissez votre fichier ici": "Drop your file here",
    "ou cliquez pour sélectionner": "or click to select",
    "Choisir un fichier": "Choose a file",
    "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Accepted formats: CSV, Excel (.xlsx, .xls) - Max 10MB",
    "Importation en cours...": "Import in progress...",
    "Résultats de l'importation": "Import results",
    "Aide et conseils": "Help and tips",
    "Formats de date acceptés": "Accepted date formats",
    "JJ/MM/AAAA (ex: 15/03/2010)": "DD/MM/YYYY (ex: 15/03/2010)",
    "JJ-MM-AAAA (ex: 15-03-2010)": "DD-MM-YYYY (ex: 15-03-2010)",
    "JJ.MM.AAAA (ex: 15.03.2010)": "DD.MM.YYYY (ex: 15.03.2010)",
    "Conseils pour l'import": "Import tips",
    "Vérifiez que les noms de colonnes correspondent": "Check that column names match",
    "Assurez-vous que les dates sont au bon format": "Make sure dates are in the correct format",
    "Les doublons seront automatiquement ignorés": "Duplicates will be automatically ignored",

    # Common terms
    "Nom": "Last name",
    "Email": "Email",
    "Grade": "Grade",
}


def add_translations_to_po(po_file_path, translations):
    """Add missing translations to a PO file."""

    # Read existing content
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find existing msgids
    existing_msgids = set()
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('msgid "') and line != 'msgid ""':
            msgid = line[7:-1]  # Remove 'msgid "' and trailing '"'
            existing_msgids.add(msgid)

    # Add missing translations
    new_entries = []
    for msgid, msgstr in translations.items():
        if msgid not in existing_msgids:
            # Escape quotes in the string
            escaped_msgid = msgid.replace('"', '\\"')
            escaped_msgstr = msgstr.replace('"', '\\"')
            entry = f'\nmsgid "{escaped_msgid}"\nmsgstr "{escaped_msgstr}"\n'
            new_entries.append(entry)
            print(f"  + Adding: {msgid[:50]}...")

    if new_entries:
        # Append new entries
        with open(po_file_path, 'a', encoding='utf-8') as f:
            f.write('\n# New translations added by script\n')
            for entry in new_entries:
                f.write(entry)
        print(f"Added {len(new_entries)} new translations to {po_file_path}")
    else:
        print(f"No new translations needed for {po_file_path}")

    return len(new_entries)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # French PO file
    fr_po_path = os.path.join(base_dir, 'locale', 'fr', 'LC_MESSAGES', 'django.po')
    print(f"\n=== Updating French translations ===")
    add_translations_to_po(fr_po_path, NEW_TRANSLATIONS_FR)

    # English PO file
    en_po_path = os.path.join(base_dir, 'locale', 'en', 'LC_MESSAGES', 'django.po')
    print(f"\n=== Updating English translations ===")
    add_translations_to_po(en_po_path, NEW_TRANSLATIONS_EN)

    print("\n=== Done! ===")
    print("Run 'python manage.py compilemessages' to compile the .mo files")


if __name__ == '__main__':
    main()
