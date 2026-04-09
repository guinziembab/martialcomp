#!/usr/bin/env python
"""
Script pour synchroniser toutes les traductions dans les fichiers PO.
Ajoute les entrées manquantes pour DE, ES, PT.
"""

import os

# Nouvelles chaînes avec traductions pour chaque langue
NEW_TRANSLATIONS = {
    "de": {  # German
        "Organisation non trouvée": "Organisation nicht gefunden",
        "Erreur génération QR codes": "Fehler bei der QR-Code-Generierung",
        "Type de QR code non trouvé": "QR-Code-Typ nicht gefunden",
        "Permissions insuffisantes": "Unzureichende Berechtigungen",
        "Méthode non autorisée": "Methode nicht erlaubt",
        "Méthode POST requise": "POST-Methode erforderlich",
        "Données QR manquantes": "Fehlende QR-Daten",
        "Message envoyé avec succès!": "Nachricht erfolgreich gesendet!",
        "Check-in effectué avec succès!": "Check-in erfolgreich durchgeführt!",
        "QR code invalide ou membre non trouvé": "Ungültiger QR-Code oder Mitglied nicht gefunden",
        "Erreur lors du check-in": "Fehler beim Check-in",
        "Erreur serveur": "Serverfehler",
        "Non authentifié": "Nicht authentifiziert",
        "Permission refusée": "Berechtigung verweigert",
        "Données manquantes": "Fehlende Daten",
        "JSON invalide": "Ungültiges JSON",
        "category_id requis": "category_id erforderlich",
        "Catégorie retirée du tatami": "Kategorie vom Tatami entfernt",
        "Données invalides": "Ungültige Daten",
        "Catégorie non assignée": "Kategorie nicht zugewiesen",
        "Déjà en première position": "Bereits an erster Position",
        "Déjà en dernière position": "Bereits an letzter Position",
        "Horaire mis à jour": "Zeitplan aktualisiert",
        "Aucune catégorie à programmer": "Keine Kategorie zu planen",
        "Format d'heure invalide (HH:MM)": "Ungültiges Zeitformat (HH:MM)",
        "Paramètres manquants": "Fehlende Parameter",
        "Action non reconnue": "Aktion nicht erkannt",
        "Erreur lors de l'opération": "Fehler bei der Operation",
        "Club non trouvé": "Club nicht gefunden",
        "Import/Export de données": "Daten Import/Export",
        "Gestion des données de votre club": "Verwaltung Ihrer Clubdaten",
        "Cette page vous permet d'importer et d'exporter les données de votre club au format Excel. Vous pouvez ainsi gérer facilement vos pratiquants et optimiser votre organisation.": "Auf dieser Seite können Sie die Daten Ihres Clubs im Excel-Format importieren und exportieren. So können Sie Ihre Praktizierenden einfach verwalten und Ihre Organisation optimieren.",
        "Exporter les données": "Daten exportieren",
        "Téléchargez toutes les données de vos pratiquants au format Excel pour les consulter hors ligne ou les modifier dans un tableur.": "Laden Sie alle Daten Ihrer Praktizierenden im Excel-Format herunter, um sie offline anzuzeigen oder in einer Tabelle zu bearbeiten.",
        "Exporter en Excel": "Nach Excel exportieren",
        "Importer des données": "Daten importieren",
        "Importez de nouveaux pratiquants ou mettez à jour les existants en uploadant un fichier Excel au format approprié.": "Importieren Sie neue Praktizierende oder aktualisieren Sie bestehende durch Hochladen einer Excel-Datei im entsprechenden Format.",
        "Commencer l'import": "Import starten",
        "Importation de données": "Datenimport",
        "Téléchargez le modèle": "Vorlage herunterladen",
        "Utilisez notre modèle Excel pour vous assurer que vos données sont au bon format.": "Verwenden Sie unsere Excel-Vorlage, um sicherzustellen, dass Ihre Daten im richtigen Format sind.",
        "Télécharger le modèle": "Vorlage herunterladen",
        "Remplissez le fichier": "Datei ausfüllen",
        "Complétez le fichier Excel avec les informations de vos pratiquants. Veillez à respecter le format des colonnes.": "Vervollständigen Sie die Excel-Datei mit den Informationen Ihrer Praktizierenden. Achten Sie auf das Spaltenformat.",
        "Importez le fichier": "Datei importieren",
        "Uploadez votre fichier Excel complété pour importer les données dans le système.": "Laden Sie Ihre ausgefüllte Excel-Datei hoch, um die Daten ins System zu importieren.",
        "Déposez votre fichier ici": "Datei hier ablegen",
        "Choisir un fichier...": "Datei auswählen...",
        "Formats acceptés: .xlsx, .xls": "Akzeptierte Formate: .xlsx, .xls",
        "Importer les données": "Daten importieren",
        "Structure attendue du fichier Excel": "Erwartete Excel-Dateistruktur",
        "Colonne A:": "Spalte A:",
        "Colonne B:": "Spalte B:",
        "Colonne C:": "Spalte C:",
        "Colonne D:": "Spalte D:",
        "Colonne E:": "Spalte E:",
        "Colonne F:": "Spalte F:",
        "Nom": "Nachname",
        "Prénom": "Vorname",
        "Date de naissance (AAAA-MM-JJ)": "Geburtsdatum (JJJJ-MM-TT)",
        "Grade": "Grad",
        "Email": "E-Mail",
        "Numéro de licence": "Lizenznummer",
        "Retour au tableau de bord": "Zurück zum Dashboard",
        "Gérer les pratiquants": "Praktizierende verwalten",
        "Exporter les pratiquants": "Praktizierende exportieren",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Laden Sie die vollständige Liste Ihrer Praktizierenden im Excel-Format zur Sicherung oder Offline-Bearbeitung herunter.",
        "Format: Excel (.xlsx)": "Format: Excel (.xlsx)",
        "Importer des pratiquants": "Praktizierende importieren",
        "Modèle de fichier": "Dateivorlage",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Laden Sie diese Vorlage herunter, um sicherzustellen, dass Ihre Datei das richtige Format hat.",
        "Télécharger le modèle Excel": "Excel-Vorlage herunterladen",
        "Format attendu:": "Erwartetes Format:",
        "NOM": "NACHNAME",
        "Date de naissance": "Geburtsdatum",
        "adresse mail": "E-Mail-Adresse",
        "Glissez votre fichier ici": "Datei hier ablegen",
        "ou cliquez pour sélectionner": "oder klicken zum Auswählen",
        "Choisir un fichier": "Datei auswählen",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Akzeptierte Formate: CSV, Excel (.xlsx, .xls) - Max 10MB",
        "Importation en cours...": "Import läuft...",
        "Résultats de l'importation": "Importergebnisse",
        "Aide et conseils": "Hilfe und Tipps",
        "Formats de date acceptés": "Akzeptierte Datumsformate",
        "JJ/MM/AAAA (ex: 15/03/2010)": "TT/MM/JJJJ (z.B.: 15/03/2010)",
        "JJ-MM-AAAA (ex: 15-03-2010)": "TT-MM-JJJJ (z.B.: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "TT.MM.JJJJ (z.B.: 15.03.2010)",
        "Conseils pour l'import": "Import-Tipps",
        "Vérifiez que les noms de colonnes correspondent": "Überprüfen Sie, ob die Spaltennamen übereinstimmen",
        "Assurez-vous que les dates sont au bon format": "Stellen Sie sicher, dass die Daten im richtigen Format sind",
        "Les doublons seront automatiquement ignorés": "Duplikate werden automatisch ignoriert",
    },
    "es": {  # Spanish
        "Organisation non trouvée": "Organización no encontrada",
        "Erreur génération QR codes": "Error en la generación de códigos QR",
        "Type de QR code non trouvé": "Tipo de código QR no encontrado",
        "Permissions insuffisantes": "Permisos insuficientes",
        "Méthode non autorisée": "Método no autorizado",
        "Méthode POST requise": "Se requiere método POST",
        "Données QR manquantes": "Datos QR faltantes",
        "Message envoyé avec succès!": "¡Mensaje enviado con éxito!",
        "Check-in effectué avec succès!": "¡Check-in realizado con éxito!",
        "QR code invalide ou membre non trouvé": "Código QR inválido o miembro no encontrado",
        "Erreur lors du check-in": "Error durante el check-in",
        "Erreur serveur": "Error del servidor",
        "Non authentifié": "No autenticado",
        "Permission refusée": "Permiso denegado",
        "Données manquantes": "Datos faltantes",
        "JSON invalide": "JSON inválido",
        "category_id requis": "category_id requerido",
        "Catégorie retirée du tatami": "Categoría retirada del tatami",
        "Données invalides": "Datos inválidos",
        "Catégorie non assignée": "Categoría no asignada",
        "Déjà en première position": "Ya en primera posición",
        "Déjà en dernière position": "Ya en última posición",
        "Horaire mis à jour": "Horario actualizado",
        "Aucune catégorie à programmer": "Ninguna categoría para programar",
        "Format d'heure invalide (HH:MM)": "Formato de hora inválido (HH:MM)",
        "Paramètres manquants": "Parámetros faltantes",
        "Action non reconnue": "Acción no reconocida",
        "Erreur lors de l'opération": "Error durante la operación",
        "Club non trouvé": "Club no encontrado",
        "Import/Export de données": "Importar/Exportar datos",
        "Gestion des données de votre club": "Gestión de datos de su club",
        "Cette page vous permet d'importer et d'exporter les données de votre club au format Excel. Vous pouvez ainsi gérer facilement vos pratiquants et optimiser votre organisation.": "Esta página le permite importar y exportar los datos de su club en formato Excel. Así puede gestionar fácilmente sus practicantes y optimizar su organización.",
        "Exporter les données": "Exportar datos",
        "Téléchargez toutes les données de vos pratiquants au format Excel pour les consulter hors ligne ou les modifier dans un tableur.": "Descargue todos los datos de sus practicantes en formato Excel para consultarlos sin conexión o modificarlos en una hoja de cálculo.",
        "Exporter en Excel": "Exportar a Excel",
        "Importer des données": "Importar datos",
        "Importez de nouveaux pratiquants ou mettez à jour les existants en uploadant un fichier Excel au format approprié.": "Importe nuevos practicantes o actualice los existentes subiendo un archivo Excel en el formato apropiado.",
        "Commencer l'import": "Iniciar importación",
        "Importation de données": "Importación de datos",
        "Téléchargez le modèle": "Descargar plantilla",
        "Utilisez notre modèle Excel pour vous assurer que vos données sont au bon format.": "Use nuestra plantilla Excel para asegurarse de que sus datos están en el formato correcto.",
        "Télécharger le modèle": "Descargar plantilla",
        "Remplissez le fichier": "Complete el archivo",
        "Complétez le fichier Excel avec les informations de vos pratiquants. Veillez à respecter le format des colonnes.": "Complete el archivo Excel con la información de sus practicantes. Asegúrese de respetar el formato de las columnas.",
        "Importez le fichier": "Importe el archivo",
        "Uploadez votre fichier Excel complété pour importer les données dans le système.": "Suba su archivo Excel completado para importar los datos al sistema.",
        "Déposez votre fichier ici": "Suelte su archivo aquí",
        "Choisir un fichier...": "Elegir un archivo...",
        "Formats acceptés: .xlsx, .xls": "Formatos aceptados: .xlsx, .xls",
        "Importer les données": "Importar datos",
        "Structure attendue du fichier Excel": "Estructura esperada del archivo Excel",
        "Colonne A:": "Columna A:",
        "Colonne B:": "Columna B:",
        "Colonne C:": "Columna C:",
        "Colonne D:": "Columna D:",
        "Colonne E:": "Columna E:",
        "Colonne F:": "Columna F:",
        "Nom": "Apellido",
        "Prénom": "Nombre",
        "Date de naissance (AAAA-MM-JJ)": "Fecha de nacimiento (AAAA-MM-DD)",
        "Grade": "Grado",
        "Email": "Correo electrónico",
        "Numéro de licence": "Número de licencia",
        "Retour au tableau de bord": "Volver al panel",
        "Gérer les pratiquants": "Gestionar practicantes",
        "Exporter les pratiquants": "Exportar practicantes",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Descargue la lista completa de sus practicantes en formato Excel para respaldo o edición sin conexión.",
        "Format: Excel (.xlsx)": "Formato: Excel (.xlsx)",
        "Importer des pratiquants": "Importar practicantes",
        "Modèle de fichier": "Plantilla de archivo",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Descargue esta plantilla para asegurarse de que su archivo tiene el formato correcto.",
        "Télécharger le modèle Excel": "Descargar plantilla Excel",
        "Format attendu:": "Formato esperado:",
        "NOM": "APELLIDO",
        "Date de naissance": "Fecha de nacimiento",
        "adresse mail": "dirección de correo",
        "Glissez votre fichier ici": "Suelte su archivo aquí",
        "ou cliquez pour sélectionner": "o haga clic para seleccionar",
        "Choisir un fichier": "Elegir un archivo",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Formatos aceptados: CSV, Excel (.xlsx, .xls) - Máx 10MB",
        "Importation en cours...": "Importación en curso...",
        "Résultats de l'importation": "Resultados de la importación",
        "Aide et conseils": "Ayuda y consejos",
        "Formats de date acceptés": "Formatos de fecha aceptados",
        "JJ/MM/AAAA (ex: 15/03/2010)": "DD/MM/AAAA (ej: 15/03/2010)",
        "JJ-MM-AAAA (ex: 15-03-2010)": "DD-MM-AAAA (ej: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "DD.MM.AAAA (ej: 15.03.2010)",
        "Conseils pour l'import": "Consejos para la importación",
        "Vérifiez que les noms de colonnes correspondent": "Verifique que los nombres de columnas coincidan",
        "Assurez-vous que les dates sont au bon format": "Asegúrese de que las fechas estén en el formato correcto",
        "Les doublons seront automatiquement ignorés": "Los duplicados serán ignorados automáticamente",
    },
    "pt": {  # Portuguese
        "Organisation non trouvée": "Organização não encontrada",
        "Erreur génération QR codes": "Erro na geração de códigos QR",
        "Type de QR code non trouvé": "Tipo de código QR não encontrado",
        "Permissions insuffisantes": "Permissões insuficientes",
        "Méthode non autorisée": "Método não autorizado",
        "Méthode POST requise": "Método POST necessário",
        "Données QR manquantes": "Dados QR em falta",
        "Message envoyé avec succès!": "Mensagem enviada com sucesso!",
        "Check-in effectué avec succès!": "Check-in efetuado com sucesso!",
        "QR code invalide ou membre non trouvé": "Código QR inválido ou membro não encontrado",
        "Erreur lors du check-in": "Erro durante o check-in",
        "Erreur serveur": "Erro do servidor",
        "Non authentifié": "Não autenticado",
        "Permission refusée": "Permissão recusada",
        "Données manquantes": "Dados em falta",
        "JSON invalide": "JSON inválido",
        "category_id requis": "category_id obrigatório",
        "Catégorie retirée du tatami": "Categoria removida do tatami",
        "Données invalides": "Dados inválidos",
        "Catégorie non assignée": "Categoria não atribuída",
        "Déjà en première position": "Já na primeira posição",
        "Déjà en dernière position": "Já na última posição",
        "Horaire mis à jour": "Horário atualizado",
        "Aucune catégorie à programmer": "Nenhuma categoria para programar",
        "Format d'heure invalide (HH:MM)": "Formato de hora inválido (HH:MM)",
        "Paramètres manquants": "Parâmetros em falta",
        "Action non reconnue": "Ação não reconhecida",
        "Erreur lors de l'opération": "Erro durante a operação",
        "Club non trouvé": "Clube não encontrado",
        "Import/Export de données": "Importar/Exportar dados",
        "Gestion des données de votre club": "Gestão de dados do seu clube",
        "Cette page vous permet d'importer et d'exporter les données de votre club au format Excel. Vous pouvez ainsi gérer facilement vos pratiquants et optimiser votre organisation.": "Esta página permite-lhe importar e exportar os dados do seu clube em formato Excel. Assim pode gerir facilmente os seus praticantes e otimizar a sua organização.",
        "Exporter les données": "Exportar dados",
        "Téléchargez toutes les données de vos pratiquants au format Excel pour les consulter hors ligne ou les modifier dans un tableur.": "Descarregue todos os dados dos seus praticantes em formato Excel para os consultar offline ou modificar numa folha de cálculo.",
        "Exporter en Excel": "Exportar para Excel",
        "Importer des données": "Importar dados",
        "Importez de nouveaux pratiquants ou mettez à jour les existants en uploadant un fichier Excel au format approprié.": "Importe novos praticantes ou atualize os existentes carregando um ficheiro Excel no formato apropriado.",
        "Commencer l'import": "Iniciar importação",
        "Importation de données": "Importação de dados",
        "Téléchargez le modèle": "Descarregar modelo",
        "Utilisez notre modèle Excel pour vous assurer que vos données sont au bon format.": "Use o nosso modelo Excel para garantir que os seus dados estão no formato correto.",
        "Télécharger le modèle": "Descarregar modelo",
        "Remplissez le fichier": "Preencha o ficheiro",
        "Complétez le fichier Excel avec les informations de vos pratiquants. Veillez à respecter le format des colonnes.": "Complete o ficheiro Excel com as informações dos seus praticantes. Certifique-se de respeitar o formato das colunas.",
        "Importez le fichier": "Importe o ficheiro",
        "Uploadez votre fichier Excel complété pour importer les données dans le système.": "Carregue o seu ficheiro Excel completo para importar os dados no sistema.",
        "Déposez votre fichier ici": "Largue o seu ficheiro aqui",
        "Choisir un fichier...": "Escolher um ficheiro...",
        "Formats acceptés: .xlsx, .xls": "Formatos aceites: .xlsx, .xls",
        "Importer les données": "Importar dados",
        "Structure attendue du fichier Excel": "Estrutura esperada do ficheiro Excel",
        "Colonne A:": "Coluna A:",
        "Colonne B:": "Coluna B:",
        "Colonne C:": "Coluna C:",
        "Colonne D:": "Coluna D:",
        "Colonne E:": "Coluna E:",
        "Colonne F:": "Coluna F:",
        "Nom": "Apelido",
        "Prénom": "Nome",
        "Date de naissance (AAAA-MM-JJ)": "Data de nascimento (AAAA-MM-DD)",
        "Grade": "Grau",
        "Email": "Email",
        "Numéro de licence": "Número de licença",
        "Retour au tableau de bord": "Voltar ao painel",
        "Gérer les pratiquants": "Gerir praticantes",
        "Exporter les pratiquants": "Exportar praticantes",
        "Téléchargez la liste complète de vos pratiquants au format Excel pour sauvegarde ou modification hors ligne.": "Descarregue a lista completa dos seus praticantes em formato Excel para backup ou edição offline.",
        "Format: Excel (.xlsx)": "Formato: Excel (.xlsx)",
        "Importer des pratiquants": "Importar praticantes",
        "Modèle de fichier": "Modelo de ficheiro",
        "Téléchargez ce modèle pour vous assurer que votre fichier est au bon format.": "Descarregue este modelo para garantir que o seu ficheiro está no formato correto.",
        "Télécharger le modèle Excel": "Descarregar modelo Excel",
        "Format attendu:": "Formato esperado:",
        "NOM": "APELIDO",
        "Date de naissance": "Data de nascimento",
        "adresse mail": "endereço de email",
        "Glissez votre fichier ici": "Largue o seu ficheiro aqui",
        "ou cliquez pour sélectionner": "ou clique para selecionar",
        "Choisir un fichier": "Escolher um ficheiro",
        "Formats acceptés: CSV, Excel (.xlsx, .xls) - Max 10MB": "Formatos aceites: CSV, Excel (.xlsx, .xls) - Máx 10MB",
        "Importation en cours...": "Importação em curso...",
        "Résultats de l'importation": "Resultados da importação",
        "Aide et conseils": "Ajuda e dicas",
        "Formats de date acceptés": "Formatos de data aceites",
        "JJ/MM/AAAA (ex: 15/03/2010)": "DD/MM/AAAA (ex: 15/03/2010)",
        "JJ-MM-AAAA (ex: 15-03-2010)": "DD-MM-AAAA (ex: 15-03-2010)",
        "JJ.MM.AAAA (ex: 15.03.2010)": "DD.MM.AAAA (ex: 15.03.2010)",
        "Conseils pour l'import": "Dicas para importação",
        "Vérifiez que les noms de colonnes correspondent": "Verifique se os nomes das colunas correspondem",
        "Assurez-vous que les dates sont au bon format": "Certifique-se de que as datas estão no formato correto",
        "Les doublons seront automatiquement ignorés": "Os duplicados serão automaticamente ignorados",
    },
}


def add_translations_to_po(po_file_path, translations, lang_name):
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

    if new_entries:
        # Append new entries
        with open(po_file_path, 'a', encoding='utf-8') as f:
            f.write(f'\n# New {lang_name} translations added by sync script\n')
            for entry in new_entries:
                f.write(entry)
        print(f"  Added {len(new_entries)} new translations to {lang_name}")
    else:
        print(f"  No new translations needed for {lang_name}")

    return len(new_entries)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lang_names = {
        "de": "German",
        "es": "Spanish",
        "pt": "Portuguese"
    }

    total_added = 0

    for lang, translations in NEW_TRANSLATIONS.items():
        po_path = os.path.join(base_dir, 'locale', lang, 'LC_MESSAGES', 'django.po')
        print(f"\n=== Processing {lang_names[lang]} ({lang}) ===")
        if os.path.exists(po_path):
            count = add_translations_to_po(po_path, translations, lang_names[lang])
            total_added += count
        else:
            print(f"  File not found: {po_path}")

    print(f"\n=== Done! Total translations added: {total_added} ===")
    print("Run 'python manage.py compilemessages' to compile the .mo files")


if __name__ == '__main__':
    main()
