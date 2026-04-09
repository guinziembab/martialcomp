#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Traduction complete du fichier PO italien.
Dictionnaire exhaustif francais -> italien.
"""

import re
import os
from datetime import datetime

# Dictionnaire complet francais -> italien
FR_TO_IT = {
    # Navigation et interface
    "Accueil": "Home",
    "Tableau de bord": "Dashboard",
    "Dashboard": "Dashboard",
    "Connexion": "Accesso",
    "Déconnexion": "Disconnessione",
    "Se déconnecter": "Disconnettersi",
    "Inscription": "Registrazione",
    "S'inscrire": "Registrati",
    "Profil": "Profilo",
    "Mon profil": "Il mio profilo",
    "Paramètres": "Impostazioni",
    "Configuration": "Configurazione",
    "Aide": "Aiuto",
    "Support": "Supporto",
    "Contact": "Contatto",
    "À propos": "Chi siamo",
    "Retour": "Indietro",
    "Suivant": "Avanti",
    "Précédent": "Precedente",
    "Menu": "Menu",
    "Fermer": "Chiudi",
    "Ouvrir": "Apri",

    # Actions communes
    "Ajouter": "Aggiungi",
    "Créer": "Crea",
    "Modifier": "Modifica",
    "Supprimer": "Elimina",
    "Éditer": "Modifica",
    "Sauvegarder": "Salva",
    "Enregistrer": "Salva",
    "Annuler": "Annulla",
    "Confirmer": "Conferma",
    "Valider": "Convalida",
    "Rechercher": "Cerca",
    "Filtrer": "Filtra",
    "Trier": "Ordina",
    "Exporter": "Esporta",
    "Importer": "Importa",
    "Télécharger": "Scarica",
    "Charger": "Carica",
    "Envoyer": "Invia",
    "Copier": "Copia",
    "Coller": "Incolla",
    "Actualiser": "Aggiorna",
    "Rafraîchir": "Aggiorna",
    "Voir": "Visualizza",
    "Afficher": "Mostra",
    "Masquer": "Nascondi",
    "Détails": "Dettagli",
    "Plus": "Di più",
    "Moins": "Meno",
    "Tout": "Tutto",
    "Aucun": "Nessuno",
    "Sélectionner": "Seleziona",
    "Désélectionner": "Deseleziona",
    "Tout sélectionner": "Seleziona tutto",
    "Appliquer": "Applica",
    "Réinitialiser": "Ripristina",
    "Publier": "Pubblica",
    "Dépublier": "Annulla pubblicazione",

    # Compétitions
    "Compétition": "Competizione",
    "Compétitions": "Competizioni",
    "Nouvelle compétition": "Nuova competizione",
    "Créer une compétition": "Crea una competizione",
    "Modifier la compétition": "Modifica competizione",
    "Supprimer la compétition": "Elimina competizione",
    "Détails de la compétition": "Dettagli competizione",
    "Liste des compétitions": "Elenco competizioni",
    "Mes compétitions": "Le mie competizioni",
    "Compétitions à venir": "Competizioni in arrivo",
    "Compétitions passées": "Competizioni passate",
    "Compétitions en cours": "Competizioni in corso",
    "Gestion de la compétition": "Gestione della competizione",
    "Gestion Pro": "Gestione Pro",
    "Vue d'ensemble de la compétition": "Panoramica della competizione",
    "Types de compétition": "Tipi di competizione",
    "Type de compétition": "Tipo di competizione",
    "Ajouter un type": "Aggiungi un tipo",
    "Publier la compétition": "Pubblica la competizione",
    "Publier & Partager": "Pubblica e Condividi",
    "Publiée": "Pubblicata",
    "Non publiée": "Non pubblicata",
    "Brouillon": "Bozza",
    "Prochaines étapes": "Prossimi passi",
    "Définir les types de compétition": "Definire i tipi di competizione",

    # Catégories
    "Catégorie": "Categoria",
    "Catégories": "Categorie",
    "catégories": "categorie",
    "Nouvelle catégorie": "Nuova categoria",
    "Créer une catégorie": "Crea una categoria",
    "Ajouter une catégorie": "Aggiungi una categoria",
    "Modifier la catégorie": "Modifica categoria",
    "Supprimer la catégorie": "Elimina categoria",
    "Catégories de la compétition": "Categorie della competizione",
    "Glissez des catégories ici": "Trascina le categorie qui",
    "Aucune catégorie définie. Créez des catégories pour organiser les participants.": "Nessuna categoria definita. Crea categorie per organizzare i partecipanti.",
    "Aucun type de compétition défini. Les types permettent d'organiser les catégories.": "Nessun tipo di competizione definito. I tipi permettono di organizzare le categorie.",
    "Toutes les catégories": "Tutte le categorie",

    # Participants et pratiquants
    "Participant": "Partecipante",
    "Participants": "Partecipanti",
    "Pratiquant": "Praticante",
    "Pratiquants": "Praticanti",
    "Nouveau pratiquant": "Nuovo praticante",
    "Ajouter un pratiquant": "Aggiungi un praticante",
    "Modifier le pratiquant": "Modifica praticante",
    "Liste des pratiquants": "Elenco dei praticanti",
    "Mes pratiquants": "I miei praticanti",
    "Pratiquants inscrits": "Praticanti iscritti",
    "Pratiquants non affectés": "Praticanti non assegnati",
    "Aucun pratiquant non affecté": "Nessun praticante non assegnato",
    "Glissez des pratiquants ici": "Trascina i praticanti qui",
    "Enregistrer les participants": "Registra i partecipanti",
    "Non affecté": "Non assegnato",
    "Affecté": "Assegnato",
    "Affectation": "Assegnazione",
    "Affectation rapide": "Assegnazione rapida",
    "Nom, club, licence...": "Nome, club, licenza...",

    # Inscriptions
    "Inscription": "Iscrizione",
    "Inscriptions": "Iscrizioni",
    "S'inscrire": "Iscriviti",
    "Inscrire": "Iscrivere",
    "Inscription à la compétition": "Iscrizione alla competizione",
    "Nouvelle inscription": "Nuova iscrizione",
    "Modifier l'inscription": "Modifica iscrizione",
    "Annuler l'inscription": "Annulla iscrizione",
    "Confirmer l'inscription": "Conferma iscrizione",
    "Aucune inscription pour le moment": "Nessuna iscrizione al momento",
    "Inscriptions ouvertes": "Iscrizioni aperte",
    "Inscriptions fermées": "Iscrizioni chiuse",

    # Clubs
    "Club": "Club",
    "Clubs": "Club",
    "Mon club": "Il mio club",
    "Nouveau club": "Nuovo club",
    "Créer un club": "Crea un club",
    "Modifier le club": "Modifica club",
    "Liste des clubs": "Elenco dei club",
    "Membres du club": "Membri del club",
    "Gestion du club": "Gestione del club",

    # Juges et arbitres
    "Juge": "Giudice",
    "Juges": "Giudici",
    "Arbitre": "Arbitro",
    "Arbitres": "Arbitri",
    "Nouveau juge": "Nuovo giudice",
    "Ajouter un juge": "Aggiungi un giudice",
    "Juges non affectés": "Giudici non assegnati",
    "Affecter les juges": "Assegna i giudici",
    "Liste des juges": "Elenco dei giudici",
    "Panel de juges": "Pannello giudici",

    # Combats et matchs
    "Combat": "Combattimento",
    "Combats": "Combattimenti",
    "Match": "Incontro",
    "Matchs": "Incontri",
    "Nouveau combat": "Nuovo combattimento",
    "Créer un combat": "Crea un combattimento",
    "Combat en cours": "Combattimento in corso",
    "Combat terminé": "Combattimento terminato",
    "Prochain combat": "Prossimo combattimento",
    "Aire de combat": "Area di combattimento",
    "Aires de combat": "Aree di combattimento",

    # Scores et résultats
    "Score": "Punteggio",
    "Scores": "Punteggi",
    "Points": "Punti",
    "Point": "Punto",
    "Résultat": "Risultato",
    "Résultats": "Risultati",
    "Classement": "Classifica",
    "Classements": "Classifiche",
    "Rang": "Posizione",
    "Position": "Posizione",
    "Premier": "Primo",
    "Deuxième": "Secondo",
    "Troisième": "Terzo",
    "Victoire": "Vittoria",
    "Défaite": "Sconfitta",
    "Égalité": "Pareggio",
    "Match nul": "Pareggio",
    "Gagnant": "Vincitore",
    "Perdant": "Perdente",
    "Vainqueur": "Vincitore",

    # Podium et cérémonies
    "Podium": "Podio",
    "Médaille": "Medaglia",
    "Médailles": "Medaglie",
    "Or": "Oro",
    "Argent": "Argento",
    "Bronze": "Bronzo",
    "Médaille d'or": "Medaglia d'oro",
    "Médaille d'argent": "Medaglia d'argento",
    "Médaille de bronze": "Medaglia di bronzo",
    "Cérémonie": "Cerimonia",
    "Remise des prix": "Premiazione",

    # Équipes
    "Équipe": "Squadra",
    "Équipes": "Squadre",
    "Nouvelle équipe": "Nuova squadra",
    "Créer une équipe": "Crea una squadra",
    "Membres de l'équipe": "Membri della squadra",
    "Chef d'équipe": "Caposquadra",
    "Capitaine": "Capitano",

    # Poules et tableaux
    "Poule": "Girone",
    "Poules": "Gironi",
    "Tableau": "Tabellone",
    "Tableaux": "Tabelloni",
    "Phase de poules": "Fase a gironi",
    "Phase finale": "Fase finale",
    "Demi-finale": "Semifinale",
    "Finale": "Finale",
    "Quart de finale": "Quarto di finale",
    "Huitième de finale": "Ottavo di finale",

    # Grades et ceintures
    "Grade": "Grado",
    "Grades": "Gradi",
    "Ceinture": "Cintura",
    "Ceintures": "Cinture",
    "Ceinture blanche": "Cintura bianca",
    "Ceinture jaune": "Cintura gialla",
    "Ceinture orange": "Cintura arancione",
    "Ceinture verte": "Cintura verde",
    "Ceinture bleue": "Cintura blu",
    "Ceinture marron": "Cintura marrone",
    "Ceinture noire": "Cintura nera",
    "Dan": "Dan",
    "Kyu": "Kyu",

    # Disciplines
    "Discipline": "Disciplina",
    "Disciplines": "Discipline",
    "Art martial": "Arte marziale",
    "Arts martiaux": "Arti marziali",
    "Karaté": "Karate",
    "Judo": "Judo",
    "Taekwondo": "Taekwondo",
    "Aikido": "Aikido",
    "Aïkido": "Aikido",
    "Kung-fu": "Kung-fu",
    "Boxe": "Pugilato",
    "MMA": "MMA",

    # Dates et temps
    "Date": "Data",
    "Heure": "Ora",
    "Horaire": "Orario",
    "Horaires": "Orari",
    "Début": "Inizio",
    "Fin": "Fine",
    "Durée": "Durata",
    "Jour": "Giorno",
    "Mois": "Mese",
    "Année": "Anno",
    "Aujourd'hui": "Oggi",
    "Demain": "Domani",
    "Hier": "Ieri",
    "Semaine": "Settimana",
    "Cette semaine": "Questa settimana",
    "Lundi": "Lunedì",
    "Mardi": "Martedì",
    "Mercredi": "Mercoledì",
    "Jeudi": "Giovedì",
    "Vendredi": "Venerdì",
    "Samedi": "Sabato",
    "Dimanche": "Domenica",
    "Janvier": "Gennaio",
    "Février": "Febbraio",
    "Mars": "Marzo",
    "Avril": "Aprile",
    "Mai": "Maggio",
    "Juin": "Giugno",
    "Juillet": "Luglio",
    "Août": "Agosto",
    "Septembre": "Settembre",
    "Octobre": "Ottobre",
    "Novembre": "Novembre",
    "Décembre": "Dicembre",

    # Statuts
    "Statut": "Stato",
    "Actif": "Attivo",
    "Inactif": "Inattivo",
    "En attente": "In attesa",
    "Validé": "Convalidato",
    "Refusé": "Rifiutato",
    "Annulé": "Annullato",
    "Terminé": "Terminato",
    "En cours": "In corso",
    "Planifié": "Pianificato",
    "Reporté": "Rinviato",
    "Suspendu": "Sospeso",
    "Confirmé": "Confermato",
    "Non confirmé": "Non confermato",
    "Approuvé": "Approvato",
    "Rejeté": "Rifiutato",
    "Ouvert": "Aperto",
    "Fermé": "Chiuso",
    "Disponible": "Disponibile",
    "Indisponible": "Non disponibile",

    # Informations personnelles
    "Nom": "Cognome",
    "Prénom": "Nome",
    "Nom complet": "Nome completo",
    "Date de naissance": "Data di nascita",
    "Âge": "Età",
    "Sexe": "Sesso",
    "Genre": "Genere",
    "Homme": "Uomo",
    "Femme": "Donna",
    "Masculin": "Maschile",
    "Féminin": "Femminile",
    "Mixte": "Misto",
    "Adresse": "Indirizzo",
    "Ville": "Città",
    "Code postal": "Codice postale",
    "Pays": "Paese",
    "Téléphone": "Telefono",
    "Email": "Email",
    "Licence": "Licenza",
    "Numéro de licence": "Numero di licenza",
    "Poids": "Peso",
    "Taille": "Altezza",
    "Catégorie de poids": "Categoria di peso",
    "Catégorie d'âge": "Categoria di età",

    # Messages et notifications
    "Message": "Messaggio",
    "Messages": "Messaggi",
    "Notification": "Notifica",
    "Notifications": "Notifiche",
    "Envoyer un message": "Invia un messaggio",
    "Nouveau message": "Nuovo messaggio",
    "Lire le message": "Leggi il messaggio",
    "Envoyer notifications": "Invia notifiche",
    "Aucune notification": "Nessuna notifica",

    # Erreurs et confirmations
    "Erreur": "Errore",
    "Succès": "Successo",
    "Attention": "Attenzione",
    "Information": "Informazione",
    "Avertissement": "Avviso",
    "Confirmation": "Conferma",
    "Êtes-vous sûr ?": "Sei sicuro?",
    "Cette action est irréversible": "Questa azione è irreversibile",
    "Opération réussie": "Operazione riuscita",
    "Une erreur est survenue": "Si è verificato un errore",
    "Champs obligatoires": "Campi obbligatori",
    "Veuillez remplir tous les champs": "Compila tutti i campi",
    "Formulaire invalide": "Modulo non valido",

    # Formulaires
    "Formulaire": "Modulo",
    "Champ": "Campo",
    "Champs": "Campi",
    "Obligatoire": "Obbligatorio",
    "Optionnel": "Opzionale",
    "Saisir": "Inserisci",
    "Entrer": "Inserisci",
    "Choisir": "Scegli",
    "Sélectionner une option": "Seleziona un'opzione",
    "Aucune option": "Nessuna opzione",
    "Mot de passe": "Password",
    "Confirmer le mot de passe": "Conferma password",
    "Mot de passe oublié": "Password dimenticata",
    "Se souvenir de moi": "Ricordami",
    "Rester connecté": "Resta connesso",

    # Tableaux et listes
    "Liste": "Elenco",
    "Tableau": "Tabella",
    "Colonne": "Colonna",
    "Ligne": "Riga",
    "Trier par": "Ordina per",
    "Ordre croissant": "Ordine crescente",
    "Ordre décroissant": "Ordine decrescente",
    "Afficher": "Mostra",
    "par page": "per pagina",
    "éléments": "elementi",
    "Aucun résultat": "Nessun risultato",
    "Aucune donnée": "Nessun dato",
    "Chargement...": "Caricamento...",
    "Chargement en cours": "Caricamento in corso",

    # Pagination
    "Page": "Pagina",
    "Pages": "Pagine",
    "Première page": "Prima pagina",
    "Dernière page": "Ultima pagina",
    "Page suivante": "Pagina successiva",
    "Page précédente": "Pagina precedente",
    "sur": "di",
    "de": "di",

    # Finances
    "Prix": "Prezzo",
    "Tarif": "Tariffa",
    "Tarifs": "Tariffe",
    "Paiement": "Pagamento",
    "Paiements": "Pagamenti",
    "Facture": "Fattura",
    "Factures": "Fatture",
    "Total": "Totale",
    "Montant": "Importo",
    "TVA": "IVA",
    "HT": "Netto",
    "TTC": "Lordo",
    "Gratuit": "Gratuito",
    "Payant": "A pagamento",
    "Payé": "Pagato",
    "Non payé": "Non pagato",
    "En attente de paiement": "In attesa di pagamento",

    # Planning et calendrier
    "Planning": "Pianificazione",
    "Calendrier": "Calendario",
    "Événement": "Evento",
    "Événements": "Eventi",
    "Agenda": "Agenda",
    "Rendez-vous": "Appuntamento",
    "Programmer": "Programmare",
    "Planifier": "Pianificare",
    "Activité": "Attività",
    "Activités": "Attività",
    "Activité récente": "Attività recente",
    "Aucune activité récente": "Nessuna attività recente",

    # Organisation
    "Organisation": "Organizzazione",
    "Organisations": "Organizzazioni",
    "Fédération": "Federazione",
    "Fédérations": "Federazioni",
    "Ligue": "Lega",
    "Ligues": "Leghe",
    "Comité": "Comitato",
    "Comités": "Comitati",
    "Association": "Associazione",
    "Associations": "Associazioni",

    # Rôles et permissions
    "Rôle": "Ruolo",
    "Rôles": "Ruoli",
    "Permission": "Permesso",
    "Permissions": "Permessi",
    "Administrateur": "Amministratore",
    "Gestionnaire": "Gestore",
    "Membre": "Membro",
    "Invité": "Ospite",
    "Propriétaire": "Proprietario",
    "Utilisateur": "Utente",
    "Utilisateurs": "Utenti",

    # Documents
    "Document": "Documento",
    "Documents": "Documenti",
    "Fichier": "File",
    "Fichiers": "File",
    "Télécharger": "Scarica",
    "Téléverser": "Carica",
    "Imprimer": "Stampa",
    "PDF": "PDF",
    "Excel": "Excel",
    "CSV": "CSV",

    # Oui/Non et options
    "Oui": "Sì",
    "Non": "No",
    "Vrai": "Vero",
    "Faux": "Falso",
    "Activer": "Attiva",
    "Désactiver": "Disattiva",
    "Activé": "Attivato",
    "Désactivé": "Disattivato",
    "Inclure": "Includi",
    "Exclure": "Escludi",

    # Interface combat
    "Rouge": "Rosso",
    "Bleu": "Blu",
    "Blanc": "Bianco",
    "Noir": "Nero",
    "Vert": "Verde",
    "Jaune": "Giallo",
    "Combattant": "Combattente",
    "Combattants": "Combattenti",
    "Coin rouge": "Angolo rosso",
    "Coin bleu": "Angolo blu",
    "Round": "Round",
    "Rounds": "Round",
    "Temps": "Tempo",
    "Chronomètre": "Cronometro",
    "Démarrer": "Avvia",
    "Arrêter": "Ferma",
    "Pause": "Pausa",
    "Reprendre": "Riprendi",
    "Réinitialiser": "Ripristina",

    # Descriptions et textes longs
    "Description": "Descrizione",
    "Commentaire": "Commento",
    "Commentaires": "Commenti",
    "Note": "Nota",
    "Notes": "Note",
    "Remarque": "Osservazione",
    "Remarques": "Osservazioni",
    "Observations": "Osservazioni",

    # Général
    "Général": "Generale",
    "Avancé": "Avanzato",
    "Options": "Opzioni",
    "Préférences": "Preferenze",
    "Réglages": "Impostazioni",
    "Langue": "Lingua",
    "Langues": "Lingue",
    "Version": "Versione",
    "Mise à jour": "Aggiornamento",
    "Nouveau": "Nuovo",
    "Nouvelle": "Nuova",
    "Ancien": "Vecchio",
    "Ancienne": "Vecchia",
    "Récent": "Recente",
    "Récente": "Recente",
    "Tous": "Tutti",
    "Toutes": "Tutte",
    "Autre": "Altro",
    "Autres": "Altri",
    "Et": "E",
    "Ou": "O",
    "Avec": "Con",
    "Sans": "Senza",
    "Pour": "Per",
    "Par": "Per",
    "Dans": "In",
    "Sur": "Su",
    "Sous": "Sotto",
    "Entre": "Tra",
    "Depuis": "Da",
    "Jusqu'à": "Fino a",
    "Avant": "Prima",
    "Après": "Dopo",
    "Pendant": "Durante",
    "Ici": "Qui",
    "Là": "Là",
    "Maintenant": "Ora",
    "Bientôt": "Presto",
    "Déjà": "Già",
    "Encore": "Ancora",
    "Toujours": "Sempre",
    "Jamais": "Mai",
    "Parfois": "A volte",
    "Souvent": "Spesso",
    "Rarement": "Raramente",
}


def translate_italian_po():
    """Traduit le fichier PO italien."""

    po_path = 'locale/it/LC_MESSAGES/django.po'

    if not os.path.exists(po_path):
        print("Fichier PO italien non trouve!")
        return

    print("=" * 70)
    print("TRADUCTION DU FICHIER PO ITALIEN")
    print("=" * 70)

    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    translations_applied = 0

    # Pour chaque terme francais, chercher et traduire
    for fr_term, it_term in FR_TO_IT.items():
        # Pattern pour trouver msgid avec ce terme et msgstr vide
        # Cas 1: msgstr vide
        pattern1 = re.compile(
            rf'(msgid\s+"{re.escape(fr_term)}"\s*\n)(msgstr\s+"")',
            re.MULTILINE
        )

        replacement1 = rf'\1msgstr "{it_term}"'
        new_content, count1 = pattern1.subn(replacement1, content)

        if count1 > 0:
            content = new_content
            translations_applied += count1

        # Cas 2: msgstr = msgid (non traduit)
        pattern2 = re.compile(
            rf'(msgid\s+"{re.escape(fr_term)}"\s*\n)(msgstr\s+"{re.escape(fr_term)}")',
            re.MULTILINE
        )

        replacement2 = rf'\1msgstr "{it_term}"'
        new_content, count2 = pattern2.subn(replacement2, content)

        if count2 > 0:
            content = new_content
            translations_applied += count2

    # Sauvegarder
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Traductions appliquees: {translations_applied}")

    return translations_applied


def main():
    """Fonction principale."""

    count = translate_italian_po()

    print("\n" + "=" * 70)
    print(f"TERMINE - {count} traductions appliquees")
    print("=" * 70)


if __name__ == '__main__':
    main()
