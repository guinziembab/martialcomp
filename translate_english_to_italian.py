#!/usr/bin/env python3
"""
Traduit automatiquement les entrées anglaises en italien et les marque fuzzy pour révision.
"""

import re

# Dictionnaire complet Français → Italien
FR_TO_IT = {
    # Navigation et actions
    "Accueil": "Home",
    "Retour": "Indietro",
    "Suivant": "Avanti",
    "Successivo": "Avanti",
    "Précédent": "Precedente",
    "Enregistrer": "Salva",
    "Sauvegarder": "Salva",
    "Annuler": "Annulla",
    "Supprimer": "Elimina",
    "Modifier": "Modifica",
    "Éditer": "Modifica",
    "Ajouter": "Aggiungi",
    "Créer": "Crea",
    "Nouveau": "Nuovo",
    "Nouvelle": "Nuova",
    "Rechercher": "Cerca",
    "Filtrer": "Filtra",
    "Valider": "Convalida",
    "Confirmer": "Conferma",
    "Fermer": "Chiudi",
    "Ouvrir": "Apri",
    "Voir": "Visualizza",
    "Afficher": "Mostra",
    "Masquer": "Nascondi",
    "Télécharger": "Scarica",
    "Importer": "Importa",
    "Exporter": "Esporta",
    "Actualiser": "Aggiorna",
    "Charger": "Carica",
    "Soumettre": "Invia",
    "Envoyer": "Invia",
    "Copier": "Copia",
    "Coller": "Incolla",
    "Couper": "Taglia",
    "Sélectionner": "Seleziona",
    "Désélectionner": "Deseleziona",
    "Tout sélectionner": "Seleziona tutto",
    "Appliquer": "Applica",
    "Réinitialiser": "Reimposta",
    "Par défaut": "Predefinito",
    "Gérer": "Gestisci",
    "Administrer": "Amministra",
    "Configurer": "Configura",
    "Continuer": "Continua",
    "Terminer": "Termina",
    "Commencer": "Inizia",
    "Démarrer": "Avvia",
    "Arrêter": "Ferma",
    "Pause": "Pausa",
    "Reprendre": "Riprendi",
    "Personnaliser": "Personalizza",
    "Imprimer": "Stampa",
    "Partager": "Condividi",
    "Publier": "Pubblica",
    "Archiver": "Archivia",
    "Restaurer": "Ripristina",
    "Dupliquer": "Duplica",
    "Cloner": "Clona",
    "Renommer": "Rinomina",
    "Déplacer": "Sposta",
    "Trier": "Ordina",
    "Grouper": "Raggruppa",

    # Compétitions et sports
    "Compétition": "Competizione",
    "Compétitions": "Competizioni",
    "Catégorie": "Categoria",
    "Catégories": "Categorie",
    "Sous-catégorie": "Sottocategoria",
    "Inscription": "Iscrizione",
    "Inscriptions": "Iscrizioni",
    "Inscrire": "Iscrivere",
    "S'inscrire": "Iscriversi",
    "Participant": "Partecipante",
    "Participants": "Partecipanti",
    "Équipe": "Squadra",
    "Équipes": "Squadre",
    "Combat": "Combattimento",
    "Combats": "Combattimenti",
    "Poule": "Girone",
    "Poules": "Gironi",
    "Match": "Incontro",
    "Matchs": "Incontri",
    "Résultat": "Risultato",
    "Résultats": "Risultati",
    "Classement": "Classifica",
    "Classements": "Classifiche",
    "Score": "Punteggio",
    "Scores": "Punteggi",
    "Point": "Punto",
    "Points": "Punti",
    "Victoire": "Vittoria",
    "Victoires": "Vittorie",
    "Défaite": "Sconfitta",
    "Défaites": "Sconfitte",
    "Égalité": "Pareggio",
    "Nul": "Pareggio",
    "Vainqueur": "Vincitore",
    "Gagnant": "Vincitore",
    "Perdant": "Perdente",
    "Podium": "Podio",
    "Médaille": "Medaglia",
    "Médailles": "Medaglie",
    "Or": "Oro",
    "Argent": "Argento",
    "Bronze": "Bronzo",
    "Champion": "Campione",
    "Championnat": "Campionato",
    "Tournoi": "Torneo",
    "Tournois": "Tornei",
    "Finale": "Finale",
    "Demi-finale": "Semifinale",
    "Quart de finale": "Quarto di finale",
    "Phase de poules": "Fase a gironi",
    "Éliminatoire": "Eliminatorio",
    "Round": "Round",
    "Tour": "Turno",
    "Manche": "Manche",
    "Repêchage": "Ripescaggio",
    "Qualification": "Qualificazione",
    "Qualifié": "Qualificato",
    "Qualifiée": "Qualificata",
    "Éliminé": "Eliminato",
    "Éliminée": "Eliminata",
    "Forfait": "Forfait",
    "Disqualifié": "Squalificato",
    "Disqualifiée": "Squalificata",
    "Blessé": "Infortunato",
    "Blessée": "Infortunata",
    "Absent": "Assente",
    "Absente": "Assente",
    "Présent": "Presente",
    "Présente": "Presente",
    "Présence": "Presenza",
    "Inscription validée": "Iscrizione convalidata",
    "Inscription refusée": "Iscrizione rifiutata",
    "En attente": "In attesa",
    "Liste d'attente": "Lista d'attesa",

    # Arts martiaux
    "Art martial": "Arte marziale",
    "Arts martiaux": "Arti marziali",
    "Discipline": "Disciplina",
    "Disciplines": "Discipline",
    "Technique": "Tecnica",
    "Techniques": "Tecniche",
    "Kata": "Kata",
    "Kumite": "Kumite",
    "Poomsae": "Poomsae",
    "Kyorugi": "Kyorugi",
    "Ceinture": "Cintura",
    "Ceintures": "Cinture",
    "Grade": "Grado",
    "Grades": "Gradi",
    "Dan": "Dan",
    "Kyu": "Kyu",
    "Kup": "Kup",
    "Niveau": "Livello",
    "Niveaux": "Livelli",
    "Débutant": "Principiante",
    "Débutants": "Principianti",
    "Intermédiaire": "Intermedio",
    "Avancé": "Avanzato",
    "Expert": "Esperto",
    "Maître": "Maestro",
    "Professeur": "Insegnante",
    "Tatami": "Tatami",
    "Aire": "Area",
    "Surface": "Superficie",
    "Dojo": "Dojo",
    "Karaté": "Karate",
    "Taekwondo": "Taekwondo",
    "Judo": "Judo",
    "Aikido": "Aikido",
    "Aïkido": "Aikido",
    "Kung-fu": "Kung fu",
    "Boxe": "Boxe",

    # Club et organisation
    "Club": "Club",
    "Clubs": "Club",
    "Organisation": "Organizzazione",
    "Organisations": "Organizzazioni",
    "Fédération": "Federazione",
    "Fédérations": "Federazioni",
    "Ligue": "Lega",
    "Ligues": "Leghe",
    "Association": "Associazione",
    "Associations": "Associazioni",
    "Membre": "Membro",
    "Membres": "Membri",
    "Adhérent": "Iscritto",
    "Adhérents": "Iscritti",
    "Pratiquant": "Praticante",
    "Pratiquants": "Praticanti",
    "Entraîneur": "Allenatore",
    "Entraîneurs": "Allenatori",
    "Coach": "Allenatore",
    "Arbitre": "Arbitro",
    "Arbitres": "Arbitri",
    "Juge": "Giudice",
    "Juges": "Giudici",
    "Jury": "Giuria",
    "Organisateur": "Organizzatore",
    "Organisateurs": "Organizzatori",
    "Responsable": "Responsabile",
    "Responsables": "Responsabili",
    "Président": "Presidente",
    "Secrétaire": "Segretario",
    "Trésorier": "Tesoriere",
    "Directeur technique": "Direttore tecnico",
    "Licence": "Licenza",
    "Licences": "Licenze",
    "Numéro de licence": "Numero di licenza",
    "Adhésion": "Adesione",
    "Adhésions": "Adesioni",
    "Cotisation": "Quota associativa",
    "Cotisations": "Quote associative",
    "Saison": "Stagione",
    "Saisons": "Stagioni",

    # Personnes et profil
    "Nom": "Nome",
    "Prénom": "Nome",
    "Nom de famille": "Cognome",
    "Nom complet": "Nome completo",
    "Email": "Email",
    "Courriel": "Email",
    "Téléphone": "Telefono",
    "Portable": "Cellulare",
    "Adresse": "Indirizzo",
    "Rue": "Via",
    "Ville": "Città",
    "Pays": "Paese",
    "Code postal": "CAP",
    "Date de naissance": "Data di nascita",
    "Lieu de naissance": "Luogo di nascita",
    "Âge": "Età",
    "Sexe": "Sesso",
    "Genre": "Genere",
    "Homme": "Uomo",
    "Femme": "Donna",
    "Masculin": "Maschile",
    "Féminin": "Femminile",
    "Mixte": "Misto",
    "Photo": "Foto",
    "Avatar": "Avatar",
    "Image": "Immagine",
    "Profil": "Profilo",
    "Mon profil": "Il mio profilo",
    "Compte": "Account",
    "Mon compte": "Il mio account",
    "Utilisateur": "Utente",
    "Utilisateurs": "Utenti",
    "Rôle": "Ruolo",
    "Rôles": "Ruoli",
    "Permission": "Permesso",
    "Permissions": "Permessi",
    "Droit": "Diritto",
    "Droits": "Diritti",
    "Accès": "Accesso",
    "Nationalité": "Nazionalità",

    # Dates et temps
    "Date": "Data",
    "Dates": "Date",
    "Heure": "Ora",
    "Heures": "Ore",
    "Horaire": "Orario",
    "Horaires": "Orari",
    "Jour": "Giorno",
    "Jours": "Giorni",
    "Semaine": "Settimana",
    "Semaines": "Settimane",
    "Mois": "Mese",
    "Année": "Anno",
    "Années": "Anni",
    "Début": "Inizio",
    "Fin": "Fine",
    "Durée": "Durata",
    "Période": "Periodo",
    "Aujourd'hui": "Oggi",
    "Demain": "Domani",
    "Hier": "Ieri",
    "Maintenant": "Adesso",
    "Bientôt": "Presto",
    "Plus tard": "Più tardi",
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
    "État": "Stato",
    "Actif": "Attivo",
    "Active": "Attiva",
    "Inactif": "Inattivo",
    "Inactive": "Inattiva",
    "En cours": "In corso",
    "Terminé": "Completato",
    "Terminée": "Completata",
    "Fini": "Finito",
    "Finie": "Finita",
    "Annulé": "Annullato",
    "Annulée": "Annullata",
    "Validé": "Convalidato",
    "Validée": "Convalidata",
    "Refusé": "Rifiutato",
    "Refusée": "Rifiutata",
    "Approuvé": "Approvato",
    "Approuvée": "Approvata",
    "Brouillon": "Bozza",
    "Publié": "Pubblicato",
    "Publiée": "Pubblicata",
    "Archivé": "Archiviato",
    "Archivée": "Archiviata",
    "Ouvert": "Aperto",
    "Ouverte": "Aperta",
    "Fermé": "Chiuso",
    "Fermée": "Chiusa",
    "Disponible": "Disponibile",
    "Indisponible": "Non disponibile",
    "Complet": "Completo",
    "Complète": "Completa",
    "Incomplet": "Incompleto",
    "Incomplète": "Incompleta",
    "Obligatoire": "Obbligatorio",
    "Optionnel": "Facoltativo",
    "Optionnelle": "Facoltativa",
    "Requis": "Richiesto",
    "Requise": "Richiesta",

    # Messages et notifications
    "Succès": "Successo",
    "Réussite": "Successo",
    "Erreur": "Errore",
    "Erreurs": "Errori",
    "Avertissement": "Avviso",
    "Avertissements": "Avvisi",
    "Information": "Informazione",
    "Informations": "Informazioni",
    "Info": "Info",
    "Attention": "Attenzione",
    "Confirmation": "Conferma",
    "Message": "Messaggio",
    "Messages": "Messaggi",
    "Notification": "Notifica",
    "Notifications": "Notifiche",
    "Alerte": "Avviso",
    "Alertes": "Avvisi",
    "Conseil": "Consiglio",
    "Conseils": "Consigli",
    "Aide": "Aiuto",
    "Support": "Supporto",
    "FAQ": "FAQ",

    # Formulaires
    "Formulaire": "Modulo",
    "Formulaires": "Moduli",
    "Champ": "Campo",
    "Champs": "Campi",
    "Valeur": "Valore",
    "Valeurs": "Valori",
    "Description": "Descrizione",
    "Commentaire": "Commento",
    "Commentaires": "Commenti",
    "Note": "Nota",
    "Notes": "Note",
    "Remarque": "Osservazione",
    "Titre": "Titolo",
    "Type": "Tipo",
    "Types": "Tipi",
    "Label": "Etichetta",
    "Options": "Opzioni",
    "Choix": "Scelta",
    "Sélection": "Selezione",
    "Liste": "Elenco",
    "Listes": "Elenchi",
    "Tableau": "Tabella",
    "Tableaux": "Tabelle",
    "Ligne": "Riga",
    "Lignes": "Righe",
    "Colonne": "Colonna",
    "Colonnes": "Colonne",
    "Cellule": "Cella",
    "Fichier": "File",
    "Fichiers": "File",
    "Document": "Documento",
    "Documents": "Documenti",
    "Pièce jointe": "Allegato",
    "Pièces jointes": "Allegati",

    # Finance
    "Finance": "Finanza",
    "Finances": "Finanze",
    "Paiement": "Pagamento",
    "Paiements": "Pagamenti",
    "Tarif": "Tariffa",
    "Tarifs": "Tariffe",
    "Prix": "Prezzo",
    "Coût": "Costo",
    "Montant": "Importo",
    "Total": "Totale",
    "Sous-total": "Subtotale",
    "TVA": "IVA",
    "Taxe": "Tassa",
    "Taxes": "Tasse",
    "Remise": "Sconto",
    "Remises": "Sconti",
    "Réduction": "Riduzione",
    "Facture": "Fattura",
    "Factures": "Fatture",
    "Reçu": "Ricevuta",
    "Reçus": "Ricevute",
    "Devis": "Preventivo",
    "Bon de commande": "Ordine",
    "Gratuit": "Gratuito",
    "Gratuite": "Gratuita",
    "Payé": "Pagato",
    "Payée": "Pagata",
    "Impayé": "Non pagato",
    "Impayée": "Non pagata",
    "En retard": "In ritardo",
    "Remboursé": "Rimborsato",
    "Remboursée": "Rimborsata",
    "Euro": "Euro",
    "Euros": "Euro",
    "Dollar": "Dollaro",
    "Dollars": "Dollari",

    # Technique/Scoring
    "Performance": "Prestazione",
    "Performances": "Prestazioni",
    "Évaluation": "Valutazione",
    "Évaluations": "Valutazioni",
    "Notation": "Valutazione",
    "Note technique": "Punteggio tecnico",
    "Critère": "Criterio",
    "Critères": "Criteri",
    "Pénalité": "Penalità",
    "Pénalités": "Penalità",
    "Bonus": "Bonus",
    "Malus": "Penalità",
    "Coefficient": "Coefficiente",
    "Moyenne": "Media",
    "Maximum": "Massimo",
    "Minimum": "Minimo",
    "Somme": "Somma",

    # Événements et planification
    "Événement": "Evento",
    "Événements": "Eventi",
    "Calendrier": "Calendario",
    "Planning": "Pianificazione",
    "Programme": "Programma",
    "Agenda": "Agenda",
    "Rendez-vous": "Appuntamento",
    "Réunion": "Riunione",
    "Entraînement": "Allenamento",
    "Entraînements": "Allenamenti",
    "Cours": "Corso",
    "Session": "Sessione",
    "Sessions": "Sessioni",
    "Séance": "Seduta",
    "Séances": "Sedute",
    "Lieu": "Luogo",
    "Lieux": "Luoghi",
    "Salle": "Sala",
    "Salles": "Sale",
    "Gymnase": "Palestra",
    "Stade": "Stadio",

    # Divers
    "Oui": "Sì",
    "Non": "No",
    "Tous": "Tutti",
    "Toutes": "Tutte",
    "Aucun": "Nessuno",
    "Aucune": "Nessuna",
    "Autre": "Altro",
    "Autres": "Altri",
    "Détail": "Dettaglio",
    "Détails": "Dettagli",
    "Résumé": "Riepilogo",
    "Aperçu": "Anteprima",
    "Vue d'ensemble": "Panoramica",
    "Statistiques": "Statistiche",
    "Stats": "Statistiche",
    "Paramètres": "Impostazioni",
    "Réglages": "Impostazioni",
    "Configuration": "Configurazione",
    "Préférences": "Preferenze",
    "À propos": "Informazioni",
    "Contact": "Contatto",
    "Connexion": "Accesso",
    "Se connecter": "Accedi",
    "Déconnexion": "Disconnetti",
    "Se déconnecter": "Esci",
    "Mot de passe": "Password",
    "Changer le mot de passe": "Cambia password",
    "Mot de passe oublié": "Password dimenticata",
    "Identifiant": "Nome utente",
    "Tableau de bord": "Dashboard",
    "Administration": "Amministrazione",
    "Admin": "Admin",
    "Gestion": "Gestione",
    "Poids": "Peso",
    "Taille": "Dimensione",
    "Hauteur": "Altezza",
    "Numéro": "Numero",
    "Version": "Versione",
    "Langue": "Lingua",
    "Langues": "Lingue",
    "Français": "Francese",
    "Anglais": "Inglese",
    "Allemand": "Tedesco",
    "Espagnol": "Spagnolo",
    "Italien": "Italiano",
    "Portugais": "Portoghese",
    "Chinois": "Cinese",
    "Japonais": "Giapponese",
    "Coréen": "Coreano",
    "Arabe": "Arabo",
    "Russe": "Russo",
    "Bienvenue": "Benvenuto",
    "Bonjour": "Buongiorno",
    "Merci": "Grazie",
    "S'il vous plaît": "Per favore",
    "Veuillez": "Per favore",

    # Phrases courantes
    "Aucun résultat": "Nessun risultato",
    "Aucune donnée": "Nessun dato",
    "Chargement": "Caricamento",
    "En cours de chargement": "Caricamento in corso",
    "Veuillez patienter": "Attendere prego",
    "Erreur de chargement": "Errore di caricamento",
    "Données non disponibles": "Dati non disponibili",
    "Non renseigné": "Non specificato",
    "Non défini": "Non definito",
    "Inconnu": "Sconosciuto",
    "Inconnue": "Sconosciuta",
    "Tout marquer comme lu": "Segna tutto come letto",
    "Marquer comme lu": "Segna come letto",
    "Marquer comme non lu": "Segna come non letto",
    "Supprimer définitivement": "Elimina definitivamente",
    "Êtes-vous sûr": "Sei sicuro",
    "Cette action est irréversible": "Questa azione è irreversibile",
    "Confirmer la suppression": "Conferma eliminazione",
    "Annuler les modifications": "Annulla modifiche",
    "Enregistrer les modifications": "Salva modifiche",
    "Modifications enregistrées": "Modifiche salvate",
    "Erreur lors de l'enregistrement": "Errore durante il salvataggio",
    "Opération réussie": "Operazione riuscita",
    "Opération échouée": "Operazione fallita",
    "Veuillez réessayer": "Riprova per favore",
    "Session expirée": "Sessione scaduta",
    "Connexion requise": "Accesso richiesto",
    "Accès refusé": "Accesso negato",
    "Page non trouvée": "Pagina non trovata",
    "Erreur serveur": "Errore server",
    "Erreur interne": "Errore interno",
    "Maintenance": "Manutenzione",
    "En maintenance": "In manutenzione",
    "Retour à l'accueil": "Torna alla home",
    "Voir plus": "Vedi altro",
    "Voir moins": "Vedi meno",
    "Afficher tout": "Mostra tutto",
    "Masquer tout": "Nascondi tutto",
    "Développer": "Espandi",
    "Réduire": "Riduci",
    "Plein écran": "Schermo intero",
    "Quitter le plein écran": "Esci da schermo intero",

    # Termes techniques
    "Multi-tenant": "Multi-tenant",
    "Tenant": "Tenant",
    "Tenants": "Tenant",
    "Audit": "Audit",
    "Audits": "Audit",
    "Sécurité": "Sicurezza",
    "Violation": "Violazione",
    "Violations": "Violazioni",
    "Détecté": "Rilevato",
    "Détectée": "Rilevata",
    "Détectés": "Rilevati",
    "Détectées": "Rilevate",
    "Global": "Globale",
    "Spécifique": "Specifico",
    "Composant": "Componente",
    "Composants": "Componenti",
    "Critique": "Critico",
    "Problème": "Problema",
    "Problèmes": "Problemi",
}

def translate_french_to_italian(french_text):
    """Traduit un texte français en italien."""
    if not french_text or not french_text.strip():
        return french_text

    result = french_text

    # Trier par longueur décroissante pour éviter les remplacements partiels
    for fr, it in sorted(FR_TO_IT.items(), key=lambda x: -len(x[0])):
        # Utiliser des frontières de mots pour éviter les remplacements partiels
        pattern = re.compile(r'\b' + re.escape(fr) + r'\b', re.IGNORECASE | re.UNICODE)

        def replace_with_case(match):
            matched = match.group(0)
            if matched.isupper():
                return it.upper()
            elif matched[0].isupper():
                return it.capitalize() if len(it) > 0 else it
            return it.lower() if it.islower() else it

        result = pattern.sub(replace_with_case, result)

    return result

def is_english(text):
    """Vérifie si un texte est probablement en anglais."""
    if not text or len(text.strip()) < 3:
        return False

    english_words = {
        "the", "a", "an", "of", "to", "for", "with", "from", "by", "at", "in", "on",
        "is", "are", "was", "were", "be", "been", "being",
        "has", "have", "had", "you", "your", "he", "his", "she", "her", "it", "its",
        "we", "our", "they", "their", "this", "that", "these", "those",
        "click", "select", "submit", "delete", "manage", "view", "show", "hide",
        "user", "users", "member", "settings", "account", "password",
        "error", "warning", "success", "loading", "message",
    }

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words or len(words) < 2:
        return False

    english_count = sum(1 for w in words if w in english_words and len(w) > 2)
    ratio = english_count / len(words) if words else 0

    return ratio > 0.3

def main():
    po_file = 'locale/it/LC_MESSAGES/django.po'

    print("Lecture du fichier PO italien...")
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    stats = {
        'total': 0,
        'translated': 0,
        'marked_fuzzy': 0,
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Collecter les commentaires
        comments = []
        while i < len(lines) and lines[i].startswith('#'):
            comments.append(lines[i])
            i += 1

        if i >= len(lines):
            result_lines.extend(comments)
            break

        # Détecter msgid
        if lines[i].startswith('msgid '):
            msgid_lines = [lines[i]]
            msgid_text = ''

            # Extraire msgid
            match = re.match(r'msgid "(.*)"', lines[i])
            if match:
                msgid_text = match.group(1)
            i += 1

            # Lignes de continuation msgid
            while i < len(lines) and lines[i].startswith('"'):
                msgid_lines.append(lines[i])
                content = lines[i].strip()[1:-1] if lines[i].strip().endswith('"') else lines[i].strip()[1:]
                msgid_text += content
                i += 1

            # msgid_plural
            msgid_plural_lines = []
            while i < len(lines) and lines[i].startswith('msgid_plural'):
                msgid_plural_lines.append(lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgid_plural_lines.append(lines[i])
                    i += 1

            # msgstr
            msgstr_lines = []
            msgstr_text = ''

            if i < len(lines) and lines[i].startswith('msgstr'):
                if lines[i].startswith('msgstr['):
                    # Pluriel - garder tel quel pour l'instant
                    while i < len(lines) and (lines[i].startswith('msgstr[') or lines[i].startswith('"')):
                        msgstr_lines.append(lines[i])
                        i += 1
                else:
                    # msgstr simple
                    match = re.match(r'msgstr "(.*)"', lines[i])
                    if match:
                        msgstr_text = match.group(1)
                    msgstr_lines.append(lines[i])
                    i += 1

                    # Lignes de continuation
                    while i < len(lines) and lines[i].startswith('"'):
                        content = lines[i].strip()[1:-1] if lines[i].strip().endswith('"') else lines[i].strip()[1:]
                        msgstr_text += content
                        msgstr_lines.append(lines[i])
                        i += 1

                    # Vérifier si c'est de l'anglais
                    if msgstr_text.strip() and is_english(msgstr_text):
                        stats['total'] += 1

                        # Traduire FR → IT
                        italian_translation = translate_french_to_italian(msgid_text)

                        if italian_translation and italian_translation != msgid_text:
                            # Remplacer le msgstr
                            new_msgstr = f'msgstr "{italian_translation}"\n'
                            msgstr_lines = [new_msgstr]
                            stats['translated'] += 1

                            # Marquer fuzzy
                            fuzzy_added = False
                            for idx, comment in enumerate(comments):
                                if comment.startswith('#,'):
                                    if 'fuzzy' not in comment:
                                        comments[idx] = comment.rstrip() + ', fuzzy\n'
                                        fuzzy_added = True
                                        stats['marked_fuzzy'] += 1
                                    break

                            if not fuzzy_added:
                                comments.append('#, fuzzy\n')
                                stats['marked_fuzzy'] += 1

            # Écrire l'entrée
            result_lines.extend(comments)
            result_lines.extend(msgid_lines)
            result_lines.extend(msgid_plural_lines)
            result_lines.extend(msgstr_lines)

            continue

        result_lines.append(lines[i])
        i += 1

    # Sauvegarder
    with open(po_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    print("\nTraduction terminee !")
    print(f"  - Entrees anglaises detectees : {stats['total']}")
    print(f"  - Traduites automatiquement FR->IT : {stats['translated']}")
    print(f"  - Marquees fuzzy pour revision : {stats['marked_fuzzy']}")
    print("\nVous pouvez maintenant ouvrir le fichier dans Poedit et")
    print("filtrer sur 'fuzzy' pour reviser toutes les traductions automatiques.")

if __name__ == '__main__':
    main()
