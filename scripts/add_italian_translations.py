#!/usr/bin/env python
"""
Script pour ajouter les traductions italiennes manquantes au fichier PO.
"""

import os

# Nouvelles chaînes à ajouter (msgid -> msgstr IT)
NEW_TRANSLATIONS_IT = {
    # organization_sites.py
    "Organisation non trouvée": "Organizzazione non trovata",
    "Erreur génération QR codes": "Errore generazione codici QR",
    "Type de QR code non trouvé": "Tipo di codice QR non trovato",
    "Permissions insuffisantes": "Permessi insufficienti",
    "Méthode non autorisée": "Metodo non autorizzato",
    "Méthode POST requise": "Metodo POST richiesto",
    "Données QR manquantes": "Dati QR mancanti",
    "Message envoyé avec succès!": "Messaggio inviato con successo!",
    "Check-in effectué avec succès!": "Check-in effettuato con successo!",
    "QR code invalide ou membre non trouvé": "Codice QR non valido o membro non trovato",
    "Erreur lors du check-in": "Errore durante il check-in",
    "Erreur serveur": "Errore del server",

    # schedule_api.py
    "Non authentifié": "Non autenticato",
    "Permission refusée": "Permesso negato",
    "Données manquantes": "Dati mancanti",
    "JSON invalide": "JSON non valido",
    "category_id requis": "category_id richiesto",
    "Catégorie retirée du tatami": "Categoria rimossa dal tatami",
    "Données invalides": "Dati non validi",
    "Catégorie non assignée": "Categoria non assegnata",
    "Déjà en première position": "Già in prima posizione",
    "Déjà en dernière position": "Già in ultima posizione",
    "Horaire mis à jour": "Orario aggiornato",
    "Aucune catégorie à programmer": "Nessuna categoria da programmare",
    "Format d'heure invalide (HH:MM)": "Formato orario non valido (HH:MM)",

    # practitioners.py
    "Paramètres manquants": "Parametri mancanti",
    "Action non reconnue": "Azione non riconosciuta",
    "Erreur lors de l'opération": "Errore durante l'operazione",
    "Club non trouvé": "Club non trovato",

    # import_export templates
    "Import/Export de données": "Import/Export dati",
    "Gestion des données de votre club": "Gestione dei dati del vostro club",
    "Cette page vous permet d'importer et d'exporter les données de votre club au format Excel. Vous pouvez ainsi gérer facilement vos pratiquants et optimiser votre organisation.": "Questa pagina consente di importare ed esportare i dati del vostro club in formato Excel. In questo modo potete gestire facilmente i vostri praticanti e ottimizzare la vostra organizzazione.",
    "Exporter les données": "Esporta dati",
    "Téléchargez toutes les données de vos pratiquants au format Excel pour les consulter hors ligne ou les modifier dans un tableur.": "Scaricate tutti i dati dei vostri praticanti in formato Excel per consultarli offline o modificarli in un foglio di calcolo.",
    "Exporter en Excel": "Esporta in Excel",
    "Importer des données": "Importa dati",
    "Importez de nouveaux pratiquants ou mettez à jour les existants en uploadant un fichier Excel au format approprié.": "Importate nuovi praticanti o aggiornate quelli esistenti caricando un file Excel nel formato appropriato.",
    "Commencer l'import": "Inizia importazione",
    "Importation de données": "Importazione dati",
    "Téléchargez le modèle": "Scarica il modello",
    "Utilisez notre modèle Excel pour vous assurer que vos données sont au bon format.": "Utilizzate il nostro modello Excel per assicurarvi che i vostri dati siano nel formato corretto.",
    "Télécharger le modèle": "Scarica il modello",
    "Remplissez le fichier": "Compilate il file",
    "Complétez le fichier Excel avec les informations de vos pratiquants. Veillez à respecter le format des colonnes.": "Completate il file Excel con le informazioni dei vostri praticanti. Assicuratevi di rispettare il formato delle colonne.",
    "Importez le fichier": "Importate il file",
    "Uploadez votre fichier Excel complété pour importer les données dans le système.": "Caricate il vostro file Excel completato per importare i dati nel sistema.",
    "Déposez votre fichier ici": "Trascinate il vostro file qui",
    "Choisir un fichier...": "Scegli un file...",
    "Formats acceptés: .xlsx, .xls": "Formati accettati: .xlsx, .xls",
    "Importer les données": "Importa dati",
    "Structure attendue du fichier Excel": "Struttura prevista del file Excel",
    "Colonne A:": "Colonna A:",
    "Colonne B:": "Colonna B:",
    "Colonne C:": "Colonna C:",
    "Colonne D:": "Colonna D:",
    "Colonne E:": "Colonna E:",
    "Colonne F:": "Colonna F:",
    "Nom": "Cognome",
    "Prénom": "Nome",
    "Date de naissance (AAAA-MM-JJ)": "Data di nascita (AAAA-MM-GG)",
    "Grade": "Grado",
    "Email": "Email",
    "Numéro de licence": "Numero di licenza",
    "Retour au tableau de bord": "Torna alla dashboard",
    "Gérer les pratiquants": "Gestisci praticanti",

    # import_export_v2.html
    "Exporter les pratiquants": "Esporta praticanti",
    "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Scaricate l'elenco completo dei vostri praticanti in formato Excel per backup o modifica offline.",
    "Format: Excel (.xlsx)": "Formato: Excel (.xlsx)",
    "Importer des pratiquants": "Importa praticanti",
    "Modèle de fichier": "Modello di file",
    "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Scaricate questo modello per assicurarvi che il vostro file sia nel formato corretto.",
    "Télécharger le modèle Excel": "Scarica modello Excel",
    "Format attendu:": "Formato previsto:",
    "NOM": "COGNOME",
    "Date de naissance": "Data di nascita",
    "adresse mail": "indirizzo email",
    "Glissez votre fichier ici": "Trascinate il vostro file qui",
    "ou cliquez pour sélectionner": "o cliccate per selezionare",
    "Choisir un fichier": "Scegli un file",
    "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Formati accettati: CSV, Excel (.xlsx, .xls) - Max 10MB",
    "Importation en cours...": "Importazione in corso...",
    "Résultats de l'importation": "Risultati dell'importazione",
    "Aide et conseils": "Aiuto e consigli",
    "Formats de date acceptés": "Formati data accettati",
    "JJ/MM/AAAA (ex: 15/03/2010)": "GG/MM/AAAA (es: 15/03/2010)",
    "JJ-MM-AAAA (ex: 15-03-2010)": "GG-MM-AAAA (es: 15-03-2010)",
    "JJ.MM.AAAA (ex: 15.03.2010)": "GG.MM.AAAA (es: 15.03.2010)",
    "Conseils pour l'import": "Consigli per l'importazione",
    "Vérifiez que les noms de colonnes correspondent": "Verificate che i nomi delle colonne corrispondano",
    "Assurez-vous que les dates sont au bon format": "Assicuratevi che le date siano nel formato corretto",
    "Les doublons seront automatiquement ignorés": "I duplicati saranno automaticamente ignorati",
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
            f.write('\n# New Italian translations added by script\n')
            for entry in new_entries:
                f.write(entry)
        print(f"Added {len(new_entries)} new translations to {po_file_path}")
    else:
        print(f"No new translations needed for {po_file_path}")

    return len(new_entries)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Italian PO file
    it_po_path = os.path.join(base_dir, 'locale', 'it', 'LC_MESSAGES', 'django.po')
    print(f"\n=== Updating Italian translations ===")
    count = add_translations_to_po(it_po_path, NEW_TRANSLATIONS_IT)

    print(f"\n=== Done! Added {count} translations ===")
    print("Run 'python manage.py compilemessages' to compile the .mo files")


if __name__ == '__main__':
    main()
