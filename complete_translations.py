#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour compléter tous les fichiers PO avec toutes les entrées du fichier français.
"""

import os
import re
from collections import defaultdict

# Traductions automatiques pour les langues principales
AUTO_TRANSLATIONS = {
    'es': {
        'Accueil': 'Inicio',
        'Se connecter': 'Iniciar sesión',
        'Inscription': 'Registro',
        'Déconnexion': 'Cerrar sesión',
        'Bienvenue': 'Bienvenido',
        'Profil': 'Perfil',
        'Compétitions': 'Competiciones',
        'Participants': 'Participantes',
        'Administration': 'Administración',
        'Utilisateur': 'Usuario',
        'Mot de passe': 'Contraseña',
        'Confirmer le mot de passe': 'Confirmar contraseña',
        'Email': 'Correo electrónico',
        'Nom': 'Nombre',
        'Prénom': 'Nombre',
        'Téléphone': 'Teléfono',
        'Adresse': 'Dirección',
        'Ville': 'Ciudad',
        'Code postal': 'Código postal',
        'Pays': 'País',
        'Date de naissance': 'Fecha de nacimiento',
        'Genre': 'Género',
        'Homme': 'Hombre',
        'Femme': 'Mujer',
        'Autre': 'Otro',
        'Sauvegarder': 'Guardar',
        'Annuler': 'Cancelar',
        'Modifier': 'Editar',
        'Supprimer': 'Eliminar',
        'Ajouter': 'Añadir',
        'Rechercher': 'Buscar',
        'Filtrer': 'Filtrar',
        'Trier': 'Ordenar',
        'Exporter': 'Exportar',
        'Importer': 'Importar',
        'Valider': 'Validar',
        'Rejeter': 'Rechazar',
        'Approuver': 'Aprobar',
        'Refuser': 'Rechazar',
        'Accepter': 'Aceptar',
        'Confirmer': 'Confirmar',
        'Oui': 'Sí',
        'Non': 'No',
        'Voir': 'Ver',
        'Voir plus': 'Ver más',
        'Voir moins': 'Ver menos',
        'Détails': 'Detalles',
        'Informations': 'Información',
        'Description': 'Descripción',
        'Commentaires': 'Comentarios',
        'Notes': 'Notas',
        'Remarques': 'Observaciones',
        'Erreur': 'Error',
        'Erreurs': 'Errores',
        'Attention': 'Atención',
        'Avertissement': 'Advertencia',
        'Succès': 'Éxito',
        'Échec': 'Fallo',
        'En cours': 'En progreso',
        'Terminé': 'Completado',
        'En attente': 'Pendiente',
        'Actif': 'Activo',
        'Inactif': 'Inactivo',
        'Activé': 'Activado',
        'Désactivé': 'Desactivado',
        'Visible': 'Visible',
        'Masqué': 'Oculto',
        'Public': 'Público',
        'Privé': 'Privado',
        'Confidentiel': 'Confidencial',
        'Secret': 'Secreto',
        'Nouveau': 'Nuevo',
        'Ancien': 'Viejo',
        'Récent': 'Reciente',
        'Ancien': 'Antiguo',
        'Premier': 'Primero',
        'Dernier': 'Último',
        'Suivant': 'Siguiente',
        'Précédent': 'Anterior',
        'Page': 'Página',
        'Pages': 'Páginas',
        'Résultats': 'Resultados',
        'Total': 'Total',
        'Moyenne': 'Promedio',
        'Maximum': 'Máximo',
        'Minimum': 'Mínimo',
        'Somme': 'Suma',
        'Compte': 'Cuenta',
        'Nombre': 'Número',
        'Quantité': 'Cantidad',
        'Prix': 'Precio',
        'Coût': 'Costo',
        'Montant': 'Monto',
        'Devise': 'Moneda',
        'Euro': 'Euro',
        'Dollar': 'Dólar',
        'Franc': 'Franco',
        'Date': 'Fecha',
        'Heure': 'Hora',
        'Durée': 'Duración',
        'Temps': 'Tiempo',
        'Jour': 'Día',
        'Jours': 'Días',
        'Semaine': 'Semana',
        'Semaines': 'Semanas',
        'Mois': 'Mes',
        'Mois': 'Meses',
        'Année': 'Año',
        'Années': 'Años',
        'Aujourd\'hui': 'Hoy',
        'Hier': 'Ayer',
        'Demain': 'Mañana',
        'Cette semaine': 'Esta semana',
        'Ce mois': 'Este mes',
        'Cette année': 'Este año',
        'Lundi': 'Lunes',
        'Mardi': 'Martes',
        'Mercredi': 'Miércoles',
        'Jeudi': 'Jueves',
        'Vendredi': 'Viernes',
        'Samedi': 'Sábado',
        'Dimanche': 'Domingo',
        'Janvier': 'Enero',
        'Février': 'Febrero',
        'Mars': 'Marzo',
        'Avril': 'Abril',
        'Mai': 'Mayo',
        'Juin': 'Junio',
        'Juillet': 'Julio',
        'Août': 'Agosto',
        'Septembre': 'Septiembre',
        'Octobre': 'Octubre',
        'Novembre': 'Noviembre',
        'Décembre': 'Diciembre',
    },
    'de': {
        'Accueil': 'Startseite',
        'Se connecter': 'Anmelden',
        'Inscription': 'Registrierung',
        'Déconnexion': 'Abmelden',
        'Bienvenue': 'Willkommen',
        'Profil': 'Profil',
        'Compétitions': 'Wettkämpfe',
        'Participants': 'Teilnehmer',
        'Administration': 'Verwaltung',
        'Utilisateur': 'Benutzer',
        'Mot de passe': 'Passwort',
        'Confirmer le mot de passe': 'Passwort bestätigen',
        'Email': 'E-Mail',
        'Nom': 'Name',
        'Prénom': 'Vorname',
        'Téléphone': 'Telefon',
        'Adresse': 'Adresse',
        'Ville': 'Stadt',
        'Code postal': 'Postleitzahl',
        'Pays': 'Land',
        'Date de naissance': 'Geburtsdatum',
        'Genre': 'Geschlecht',
        'Homme': 'Mann',
        'Femme': 'Frau',
        'Autre': 'Andere',
        'Sauvegarder': 'Speichern',
        'Annuler': 'Abbrechen',
        'Modifier': 'Bearbeiten',
        'Supprimer': 'Löschen',
        'Ajouter': 'Hinzufügen',
        'Rechercher': 'Suchen',
        'Filtrer': 'Filtern',
        'Trier': 'Sortieren',
        'Exporter': 'Exportieren',
        'Importer': 'Importieren',
        'Valider': 'Validieren',
        'Rejeter': 'Ablehnen',
        'Approuver': 'Genehmigen',
        'Refuser': 'Ablehnen',
        'Accepter': 'Akzeptieren',
        'Confirmer': 'Bestätigen',
        'Oui': 'Ja',
        'Non': 'Nein',
        'Voir': 'Anzeigen',
        'Voir plus': 'Mehr anzeigen',
        'Voir moins': 'Weniger anzeigen',
        'Détails': 'Details',
        'Informations': 'Informationen',
        'Description': 'Beschreibung',
        'Commentaires': 'Kommentare',
        'Notes': 'Notizen',
        'Remarques': 'Bemerkungen',
        'Erreur': 'Fehler',
        'Erreurs': 'Fehler',
        'Attention': 'Achtung',
        'Avertissement': 'Warnung',
        'Succès': 'Erfolg',
        'Échec': 'Fehler',
        'En cours': 'In Bearbeitung',
        'Terminé': 'Abgeschlossen',
        'En attente': 'Ausstehend',
        'Actif': 'Aktiv',
        'Inactif': 'Inaktiv',
        'Activé': 'Aktiviert',
        'Désactivé': 'Deaktiviert',
        'Visible': 'Sichtbar',
        'Masqué': 'Versteckt',
        'Public': 'Öffentlich',
        'Privé': 'Privat',
        'Confidentiel': 'Vertraulich',
        'Secret': 'Geheim',
        'Nouveau': 'Neu',
        'Ancien': 'Alt',
        'Récent': 'Kürzlich',
        'Ancien': 'Alt',
        'Premier': 'Erste',
        'Dernier': 'Letzte',
        'Suivant': 'Weiter',
        'Précédent': 'Zurück',
        'Page': 'Seite',
        'Pages': 'Seiten',
        'Résultats': 'Ergebnisse',
        'Total': 'Gesamt',
        'Moyenne': 'Durchschnitt',
        'Maximum': 'Maximum',
        'Minimum': 'Minimum',
        'Somme': 'Summe',
        'Compte': 'Anzahl',
        'Nombre': 'Nummer',
        'Quantité': 'Menge',
        'Prix': 'Preis',
        'Coût': 'Kosten',
        'Montant': 'Betrag',
        'Devise': 'Währung',
        'Euro': 'Euro',
        'Dollar': 'Dollar',
        'Franc': 'Franc',
        'Date': 'Datum',
        'Heure': 'Zeit',
        'Durée': 'Dauer',
        'Temps': 'Zeit',
        'Jour': 'Tag',
        'Jours': 'Tage',
        'Semaine': 'Woche',
        'Semaines': 'Wochen',
        'Mois': 'Monat',
        'Mois': 'Monate',
        'Année': 'Jahr',
        'Années': 'Jahre',
        'Aujourd\'hui': 'Heute',
        'Hier': 'Gestern',
        'Demain': 'Morgen',
        'Cette semaine': 'Diese Woche',
        'Ce mois': 'Dieser Monat',
        'Cette année': 'Dieses Jahr',
        'Lundi': 'Montag',
        'Mardi': 'Dienstag',
        'Mercredi': 'Mittwoch',
        'Jeudi': 'Donnerstag',
        'Vendredi': 'Freitag',
        'Samedi': 'Samstag',
        'Dimanche': 'Sonntag',
        'Janvier': 'Januar',
        'Février': 'Februar',
        'Mars': 'März',
        'Avril': 'April',
        'Mai': 'Mai',
        'Juin': 'Juni',
        'Juillet': 'Juli',
        'Août': 'August',
        'Septembre': 'September',
        'Octobre': 'Oktober',
        'Novembre': 'November',
        'Décembre': 'Dezember',
    },
    'it': {
        'Accueil': 'Home',
        'Se connecter': 'Accedi',
        'Inscription': 'Registrazione',
        'Déconnexion': 'Disconnetti',
        'Bienvenue': 'Benvenuto',
        'Profil': 'Profilo',
        'Compétitions': 'Competizioni',
        'Participants': 'Partecipanti',
        'Administration': 'Amministrazione',
        'Utilisateur': 'Utente',
        'Mot de passe': 'Password',
        'Confirmer le mot de passe': 'Conferma password',
        'Email': 'Email',
        'Nom': 'Nome',
        'Prénom': 'Nome',
        'Téléphone': 'Telefono',
        'Adresse': 'Indirizzo',
        'Ville': 'Città',
        'Code postal': 'Codice postale',
        'Pays': 'Paese',
        'Date de naissance': 'Data di nascita',
        'Genre': 'Genere',
        'Homme': 'Uomo',
        'Femme': 'Donna',
        'Autre': 'Altro',
        'Sauvegarder': 'Salva',
        'Annuler': 'Annulla',
        'Modifier': 'Modifica',
        'Supprimer': 'Elimina',
        'Ajouter': 'Aggiungi',
        'Rechercher': 'Cerca',
        'Filtrer': 'Filtra',
        'Trier': 'Ordina',
        'Exporter': 'Esporta',
        'Importer': 'Importa',
        'Valider': 'Valida',
        'Rejeter': 'Rifiuta',
        'Approuver': 'Approva',
        'Refuser': 'Rifiuta',
        'Accepter': 'Accetta',
        'Confirmer': 'Conferma',
        'Oui': 'Sì',
        'Non': 'No',
        'Voir': 'Vedi',
        'Voir plus': 'Vedi più',
        'Voir moins': 'Vedi meno',
        'Détails': 'Dettagli',
        'Informations': 'Informazioni',
        'Description': 'Descrizione',
        'Commentaires': 'Commenti',
        'Notes': 'Note',
        'Remarques': 'Osservazioni',
        'Erreur': 'Errore',
        'Erreurs': 'Errori',
        'Attention': 'Attenzione',
        'Avertissement': 'Avviso',
        'Succès': 'Successo',
        'Échec': 'Fallimento',
        'En cours': 'In corso',
        'Terminé': 'Completato',
        'En attente': 'In attesa',
        'Actif': 'Attivo',
        'Inactif': 'Inattivo',
        'Activé': 'Attivato',
        'Désactivé': 'Disattivato',
        'Visible': 'Visibile',
        'Masqué': 'Nascosto',
        'Public': 'Pubblico',
        'Privé': 'Privato',
        'Confidentiel': 'Riservato',
        'Secret': 'Segreto',
        'Nouveau': 'Nuovo',
        'Ancien': 'Vecchio',
        'Récent': 'Recente',
        'Ancien': 'Antico',
        'Premier': 'Primo',
        'Dernier': 'Ultimo',
        'Suivant': 'Successivo',
        'Précédent': 'Precedente',
        'Page': 'Pagina',
        'Pages': 'Pagine',
        'Résultats': 'Risultati',
        'Total': 'Totale',
        'Moyenne': 'Media',
        'Maximum': 'Massimo',
        'Minimum': 'Minimo',
        'Somme': 'Somma',
        'Compte': 'Conteggio',
        'Nombre': 'Numero',
        'Quantité': 'Quantità',
        'Prix': 'Prezzo',
        'Coût': 'Costo',
        'Montant': 'Importo',
        'Devise': 'Valuta',
        'Euro': 'Euro',
        'Dollar': 'Dollaro',
        'Franc': 'Franco',
        'Date': 'Data',
        'Heure': 'Ora',
        'Durée': 'Durata',
        'Temps': 'Tempo',
        'Jour': 'Giorno',
        'Jours': 'Giorni',
        'Semaine': 'Settimana',
        'Semaines': 'Settimane',
        'Mois': 'Mese',
        'Mois': 'Mesi',
        'Année': 'Anno',
        'Années': 'Anni',
        'Aujourd\'hui': 'Oggi',
        'Hier': 'Ieri',
        'Demain': 'Domani',
        'Cette semaine': 'Questa settimana',
        'Ce mois': 'Questo mese',
        'Cette année': 'Quest\'anno',
        'Lundi': 'Lunedì',
        'Mardi': 'Martedì',
        'Mercredi': 'Mercoledì',
        'Jeudi': 'Giovedì',
        'Vendredi': 'Venerdì',
        'Samedi': 'Sabato',
        'Dimanche': 'Domenica',
        'Janvier': 'Gennaio',
        'Février': 'Febbraio',
        'Mars': 'Marzo',
        'Avril': 'Aprile',
        'Mai': 'Maggio',
        'Juin': 'Giugno',
        'Juillet': 'Luglio',
        'Août': 'Agosto',
        'Septembre': 'Settembre',
        'Octobre': 'Ottobre',
        'Novembre': 'Novembre',
        'Décembre': 'Dicembre',
    }
}

def parse_po_file(file_path):
    """Parse un fichier PO et retourne un dictionnaire des traductions."""
    translations = {}
    
    if not os.path.exists(file_path):
        return translations
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour extraire msgid et msgstr
    pattern = r'msgid\s+"([^"]*)"\s*\nmsgstr\s+"([^"]*)"'
    matches = re.findall(pattern, content)
    
    for msgid, msgstr in matches:
        if msgid:  # Ignorer les entrées vides
            translations[msgid] = msgstr
    
    return translations

def create_complete_po_file(lang, french_translations, auto_translations):
    """Crée un fichier PO complet pour une langue donnée."""
    
    # Lire les traductions existantes pour cette langue
    po_file = f"locale/{lang}/LC_MESSAGES/django.po"
    existing_translations = parse_po_file(po_file)
    
    # Créer le contenu du fichier PO
    header = f'''# {lang.upper()} translations for MartialComp project.
# Copyright (C) 2025 MartialComp
# This file is distributed under the same license as the MartialComp package.
msgid ""
msgstr "Project-Id-Version: MartialComp 1.0\\n"
"Language: {lang}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n > 1);\\n"
"X-Generator: Poedit 3.6\\n"

'''
    
    content = header
    
    # Pour chaque traduction française
    for french_msgid, french_msgstr in french_translations.items():
        # Chercher une traduction existante
        if french_msgid in existing_translations and existing_translations[french_msgid]:
            translation = existing_translations[french_msgid]
        # Chercher une traduction automatique
        elif french_msgid in auto_translations.get(lang, {}):
            translation = auto_translations[lang][french_msgid]
        # Sinon, garder le français
        else:
            translation = french_msgstr
        
        content += f'msgid "{french_msgid}"\n'
        content += f'msgstr "{translation}"\n\n'
    
    # Écrire le fichier
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return len(french_translations)

def main():
    """Fonction principale."""
    
    print("🔄 Complétion des fichiers PO avec toutes les entrées françaises")
    print("=" * 70)
    
    # Lire le fichier PO français comme référence
    french_po = "locale/fr/LC_MESSAGES/django.po"
    french_translations = parse_po_file(french_po)
    
    print(f"📊 Fichier français contient {len(french_translations)} entrées")
    
    # Langues à traiter
    languages = ['es', 'de', 'it', 'pt', 'ja', 'ko', 'zh-hans', 'ar', 'hi', 'no', 'sw', 'am', 'yo', 'zu']
    
    for lang in languages:
        if lang in AUTO_TRANSLATIONS:
            count = create_complete_po_file(lang, french_translations, AUTO_TRANSLATIONS)
            print(f"✅ {lang.upper()}: {count} entrées créées avec traductions automatiques")
        else:
            count = create_complete_po_file(lang, french_translations, {})
            print(f"✅ {lang.upper()}: {count} entrées créées (français par défaut)")
    
    print("\n🎯 Tous les fichiers PO ont été complétés !")
    print("🌍 Vous pouvez maintenant compiler les fichiers MO.")

if __name__ == '__main__':
    main() 