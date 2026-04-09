#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Traduction etendue du fichier PO italien avec nettoyage mojibake complet.
"""

import re
import os

# Corrections mojibake completes
MOJIBAKE_MAP = [
    # Sequences les plus longues d'abord
    ('\\\\\\\\\\\\\\\\', ''),  # Backslashes multiples
    ("\\\\\\\\'", "'"),
    ("\\\\'", "'"),
    ("\\'", "'"),
    ('Ã©', 'é'),
    ('Ã¨', 'è'),
    ('Ãª', 'ê'),
    ('Ã«', 'ë'),
    ('Ã ', 'à'),
    ('Ã¢', 'â'),
    ('Ã¤', 'ä'),
    ('Ã¹', 'ù'),
    ('Ã»', 'û'),
    ('Ã¼', 'ü'),
    ('Ã´', 'ô'),
    ('Ã¶', 'ö'),
    ('Ã®', 'î'),
    ('Ã¯', 'ï'),
    ('Ã§', 'ç'),
    ('Å"', 'œ'),
    ('Ã€', 'À'),
    ('Ã‰', 'É'),
    ('Ãˆ', 'È'),
    ('Ã‡', 'Ç'),
    ('Ã"', 'Ô'),
    ('Ã›', 'Û'),
    ('Ã™', 'Ù'),
    ('â€™', "'"),
    ('â€"', '–'),
    ('â€"', '—'),
    ('â€œ', '"'),
    ('â€', '"'),
    ('â€¦', '…'),
    ('Â ', ' '),
    ('Â', ''),
]

# Dictionnaire etendu francais -> italien
FR_IT_EXTENDED = {
    # Messages et confirmations
    "Résultats en temps réel": "Risultati in tempo reale",
    "Partager la compétition": "Condividi la competizione",
    "Réseaux sociaux": "Social network",
    "Partager sur Facebook": "Condividi su Facebook",
    "Partager sur Twitter": "Condividi su Twitter",
    "Partager sur WhatsApp": "Condividi su WhatsApp",
    "Notifier les juges": "Notifica i giudici",
    "Ajouter un type de compétition": "Aggiungi un tipo di competizione",
    "Règles spécifiques": "Regole specifiche",
    "Démonstration": "Dimostrazione",
    "Personnalisé": "Personalizzato",
    "Sélectionner un type": "Seleziona un tipo",
    "Âge minimum": "Età minima",
    "Âge maximum": "Età massima",
    "âge minimum": "età minima",
    "âge maximum": "età massima",
    "ge minimum": "età minima",
    "ge maximum": "età massima",
    "Aucun grade minimum": "Nessun grado minimo",
    "Aucun grade maximum": "Nessun grado massimo",
    "Rechercher un utilisateur": "Cerca un utente",
    "Nom ou email": "Nome o email",
    "Juge de coin": "Giudice d'angolo",
    "Table de marque": "Tavolo di segnapunti",
    "Arbitre en chef": "Arbitro capo",
    "Pratiquant affecté avec succès": "Praticante assegnato con successo",
    "Erreur lors de l'affectation": "Errore durante l'assegnazione",
    "Erreur de connexion": "Errore di connessione",
    "Êtes-vous sûr de vouloir retirer ce pratiquant de cette catégorie ?": "Sei sicuro di voler rimuovere questo praticante da questa categoria?",
    "Pratiquant retiré de la catégorie": "Praticante rimosso dalla categoria",
    "Juge affecté avec succès": "Giudice assegnato con successo",
    "Création...": "Creazione...",
    "Catégorie créée avec succès": "Categoria creata con successo",
    "Erreur lors de la création": "Errore durante la creazione",
    "Type de compétition créé avec succès": "Tipo di competizione creato con successo",
    "Fonction en cours de développement": "Funzione in fase di sviluppo",
    "Recherche...": "Ricerca...",
    "Arbitre national": "Arbitro nazionale",
    "Juge régional": "Giudice regionale",
    "Êtes-vous sûr de vouloir supprimer la catégorie": "Sei sicuro di voler eliminare la categoria",
    "Catégorie supprimée avec succès": "Categoria eliminata con successo",
    "Compétition publiée avec succès !": "Competizione pubblicata con successo!",
    "Erreur lors de la publication": "Errore durante la pubblicazione",
    "Lien copié !": "Link copiato!",
    "Génération de la programmation en cours...": "Generazione della programmazione in corso...",
    "Suivi temps réel activé": "Monitoraggio in tempo reale attivato",
    "Progression sauvegardée": "Progresso salvato",
    "Êtes-vous sûr de vouloir supprimer ce type de compétition ?": "Sei sicuro di voler eliminare questo tipo di competizione?",
    "Type de compétition supprimé avec succès": "Tipo di competizione eliminato con successo",
    "Export PDF en cours de développement": "Esportazione PDF in fase di sviluppo",

    # Juges et arbitres
    "Les juges techniques effectuent la notation technique. Il peut y avoir plus de 5 juges par catégorie.": "I giudici tecnici effettuano la valutazione tecnica. Possono esserci più di 5 giudici per categoria.",
    "Juges Techniques (Notation Technique)": "Giudici Tecnici (Valutazione Tecnica)",
    "Ajouter un juge technique": "Aggiungi un giudice tecnico",
    "Juges techniques disponibles": "Giudici tecnici disponibili",
    "ans d'expérience": "anni di esperienza",
    "Aucun juge technique disponible": "Nessun giudice tecnico disponibile",
    "Affectations par catégorie": "Assegnazioni per categoria",
    "Glisser les juges techniques ici": "Trascina i giudici tecnici qui",
    "Aucune catégorie créée. Créez d'abord des catégories.": "Nessuna categoria creata. Crea prima le categorie.",
    "Arbitres de Combat": "Arbitri di Combattimento",
    "Ajouter un arbitre": "Aggiungi un arbitro",
    "Arbitres disponibles": "Arbitri disponibili",
    "Aucun arbitre disponible": "Nessun arbitro disponibile",
    "Affectations par tatami": "Assegnazioni per tatami",
    "Arbitre Central": "Arbitro Centrale",
    "Glisser 1 arbitre central": "Trascina 1 arbitro centrale",
    "Arbitres de Coin": "Arbitri d'Angolo",
    "Glisser 2-3 arbitres de coin": "Trascina 2-3 arbitri d'angolo",
    "Arbitre de Table": "Arbitro di Tavolo",
    "Glisser 1 arbitre de table": "Trascina 1 arbitro di tavolo",
    "Placator": "Placator",
    "Glisser 1 placator": "Trascina 1 placator",

    # Planning et programmation
    "Programmation et suivi temps réel": "Programmazione e monitoraggio in tempo reale",
    "Démarrer le suivi": "Avvia il monitoraggio",
    "Planning de la journée": "Pianificazione della giornata",
    "Accueil et pesée": "Accoglienza e pesatura",
    "Vérification des licences et pesée officielle": "Verifica delle licenze e pesatura ufficiale",
    "Cérémonie d'ouverture": "Cerimonia di apertura",
    "Présentation des juges et rappel des règles": "Presentazione dei giudici e promemoria delle regole",
    "Compétitions - Session 1": "Competizioni - Sessione 1",
    "Catégories jeunes et débutants": "Categorie giovani e principianti",
    "Temps réel": "Tempo reale",
    "État des tatamis": "Stato dei tatami",

    # Publication
    "Publication et partage": "Pubblicazione e condivisione",
    "État de publication": "Stato di pubblicazione",
    "Cette compétition n'est pas encore publiée. Elle n'est visible que par les organisateurs.": "Questa competizione non è ancora pubblicata. È visibile solo dagli organizzatori.",
    "Checklist avant publication": "Checklist prima della pubblicazione",
    "Lieu défini": "Luogo definito",
    "Au moins une catégorie créée": "Almeno una categoria creata",
    "Informations complètes": "Informazioni complete",
    "Publier maintenant": "Pubblica ora",
    "Cette compétition est publiée et visible publiquement.": "Questa competizione è pubblicata e visibile pubblicamente.",
    "URL publique": "URL pubblico",
    "Options de visibilité": "Opzioni di visibilità",
    "Autoriser les inscriptions en ligne": "Consenti le iscrizioni online",
    "Afficher la liste des participants": "Mostra l'elenco dei partecipanti",
    "Afficher le planning": "Mostra la pianificazione",
    "Partager sur les réseaux sociaux": "Condividi sui social network",

    # Actions et boutons
    "Monter": "Sali",
    "Descendre": "Scendi",
    "Glisser": "Trascina",
    "Déplacer": "Sposta",
    "Réorganiser": "Riorganizza",
    "Configurer": "Configura",
    "Personnaliser": "Personalizza",
    "Importer des données": "Importa dati",
    "Exporter les données": "Esporta dati",
    "Télécharger le fichier": "Scarica il file",
    "Charger un fichier": "Carica un file",
    "Sélectionner un fichier": "Seleziona un file",
    "Choisir un fichier": "Scegli un file",
    "Parcourir": "Sfoglia",
    "Aperçu": "Anteprima",
    "Prévisualisation": "Anteprima",
    "Zoom": "Zoom",
    "Agrandir": "Ingrandisci",
    "Réduire": "Riduci",
    "Plein écran": "Schermo intero",
    "Quitter le plein écran": "Esci dallo schermo intero",

    # Formulaires
    "Veuillez saisir": "Si prega di inserire",
    "Veuillez sélectionner": "Si prega di selezionare",
    "Veuillez choisir": "Si prega di scegliere",
    "Veuillez entrer": "Si prega di inserire",
    "Veuillez confirmer": "Si prega di confermare",
    "Veuillez vérifier": "Si prega di verificare",
    "Champ requis": "Campo richiesto",
    "Ce champ est requis": "Questo campo è richiesto",
    "Valeur minimale": "Valore minimo",
    "Valeur maximale": "Valore massimo",
    "Caractères minimum": "Caratteri minimi",
    "Caractères maximum": "Caratteri massimi",
    "Format incorrect": "Formato errato",
    "Email invalide": "Email non valida",
    "Numéro invalide": "Numero non valido",
    "Date invalide": "Data non valida",
    "Sélection invalide": "Selezione non valida",

    # Compétitions
    "Compétition créée avec succès": "Competizione creata con successo",
    "Compétition modifiée avec succès": "Competizione modificata con successo",
    "Compétition supprimée avec succès": "Competizione eliminata con successo",
    "Compétition annulée": "Competizione annullata",
    "Compétition reportée": "Competizione rinviata",
    "Compétition terminée": "Competizione terminata",
    "Compétition archivée": "Competizione archiviata",
    "Nouvelle compétition créée": "Nuova competizione creata",
    "Modifier les informations": "Modifica le informazioni",
    "Voir les détails": "Visualizza i dettagli",
    "Gérer les catégories": "Gestisci le categorie",
    "Gérer les inscriptions": "Gestisci le iscrizioni",
    "Gérer les combats": "Gestisci i combattimenti",
    "Voir les résultats": "Visualizza i risultati",
    "Exporter les résultats": "Esporta i risultati",
    "Imprimer les résultats": "Stampa i risultati",

    # Catégories
    "Catégorie créée": "Categoria creata",
    "Catégorie modifiée": "Categoria modificata",
    "Catégorie supprimée": "Categoria eliminata",
    "Ajouter des participants": "Aggiungi partecipanti",
    "Retirer des participants": "Rimuovi partecipanti",
    "Configurer la catégorie": "Configura la categoria",
    "Critères de la catégorie": "Criteri della categoria",
    "Participants de la catégorie": "Partecipanti della categoria",
    "Combats de la catégorie": "Combattimenti della categoria",

    # Inscriptions
    "Inscription réussie": "Iscrizione riuscita",
    "Inscription confirmée": "Iscrizione confermata",
    "Inscription annulée": "Iscrizione annullata",
    "Inscription refusée": "Iscrizione rifiutata",
    "Inscription en attente de validation": "Iscrizione in attesa di convalida",
    "Inscription validée": "Iscrizione convalidata",
    "Confirmer cette inscription": "Conferma questa iscrizione",
    "Refuser cette inscription": "Rifiuta questa iscrizione",
    "Annuler cette inscription": "Annulla questa iscrizione",
    "Modifier cette inscription": "Modifica questa iscrizione",
    "Détails de l'inscription": "Dettagli dell'iscrizione",
    "Historique des inscriptions": "Storico delle iscrizioni",
    "Aucune inscription": "Nessuna iscrizione",
    "Inscription gratuite": "Iscrizione gratuita",

    # Combats
    "Combat créé": "Combattimento creato",
    "Combat modifié": "Combattimento modificato",
    "Combat annulé": "Combattimento annullato",
    "Démarrer le combat": "Avvia il combattimento",
    "Terminer le combat": "Termina il combattimento",
    "Suspendre le combat": "Sospendi il combattimento",
    "Reprendre le combat": "Riprendi il combattimento",
    "Annuler le combat": "Annulla il combattimento",
    "Saisir le score": "Inserisci il punteggio",
    "Valider le score": "Convalida il punteggio",
    "Modifier le score": "Modifica il punteggio",
    "Score validé": "Punteggio convalidato",
    "Combat en attente": "Combattimento in attesa",
    "Combats terminés": "Combattimenti terminati",
    "Combats à venir": "Combattimenti imminenti",
    "Aucun combat": "Nessun combattimento",
    "Prochain combat dans": "Prossimo combattimento tra",
    "Résultat du combat": "Risultato del combattimento",

    # Résultats et classements
    "Classement final publié": "Classifica finale pubblicata",
    "Classement provisoire": "Classifica provvisoria",
    "Voir le classement": "Visualizza la classifica",
    "Exporter le classement": "Esporta la classifica",
    "Imprimer le classement": "Stampa la classifica",
    "Résultats publiés": "Risultati pubblicati",
    "Résultats validés": "Risultati convalidati",
    "Pas encore de résultats": "Ancora nessun risultato",
    "Résultats en attente": "Risultati in attesa",

    # Podium
    "Cérémonie de remise des prix": "Cerimonia di premiazione",
    "Afficher le podium": "Mostra il podio",
    "Masquer le podium": "Nascondi il podio",
    "Médailles attribuées": "Medaglie assegnate",
    "Attribution des médailles": "Assegnazione delle medaglie",
    "Félicitations aux vainqueurs": "Congratulazioni ai vincitori",

    # Équipes
    "Équipe créée": "Squadra creata",
    "Équipe modifiée": "Squadra modificata",
    "Équipe supprimée": "Squadra eliminata",
    "Ajouter des membres": "Aggiungi membri",
    "Retirer des membres": "Rimuovi membri",
    "Membres de l'équipe": "Membri della squadra",
    "Nom de l'équipe": "Nome della squadra",
    "Logo de l'équipe": "Logo della squadra",
    "Couleurs de l'équipe": "Colori della squadra",

    # Clubs
    "Club créé": "Club creato",
    "Club modifié": "Club modificato",
    "Club supprimé": "Club eliminato",
    "Informations du club": "Informazioni del club",
    "Statistiques du club": "Statistiche del club",
    "Pratiquants du club": "Praticanti del club",
    "Compétitions du club": "Competizioni del club",

    # Pratiquants
    "Pratiquant créé": "Praticante creato",
    "Pratiquant modifié": "Praticante modificato",
    "Pratiquant supprimé": "Praticante eliminato",
    "Informations du pratiquant": "Informazioni del praticante",
    "Historique du pratiquant": "Storico del praticante",
    "Compétitions du pratiquant": "Competizioni del praticante",
    "Résultats du pratiquant": "Risultati del praticante",

    # Utilisateurs et comptes
    "Compte créé": "Account creato",
    "Compte modifié": "Account modificato",
    "Compte supprimé": "Account eliminato",
    "Compte activé": "Account attivato",
    "Compte désactivé": "Account disattivato",
    "Connexion réussie": "Accesso riuscito",
    "Déconnexion réussie": "Disconnessione riuscita",
    "Mot de passe modifié": "Password modificata",
    "Email de confirmation envoyé": "Email di conferma inviata",
    "Lien de réinitialisation envoyé": "Link di reimpostazione inviato",

    # Erreurs
    "Une erreur s'est produite": "Si è verificato un errore",
    "Erreur serveur": "Errore del server",
    "Erreur de chargement": "Errore di caricamento",
    "Erreur de sauvegarde": "Errore di salvataggio",
    "Erreur de suppression": "Errore di eliminazione",
    "Erreur de validation": "Errore di convalida",
    "Erreur d'authentification": "Errore di autenticazione",
    "Session expirée": "Sessione scaduta",
    "Accès refusé": "Accesso negato",
    "Page non trouvée": "Pagina non trovata",
    "Ressource non trouvée": "Risorsa non trovata",
    "Action non autorisée": "Azione non autorizzata",
    "Opération impossible": "Operazione impossibile",
    "Données invalides": "Dati non validi",
    "Veuillez réessayer": "Si prega di riprovare",
    "Contacter le support": "Contatta il supporto",

    # Confirmations
    "Êtes-vous sûr de vouloir continuer ?": "Sei sicuro di voler continuare?",
    "Cette action ne peut pas être annulée": "Questa azione non può essere annullata",
    "Confirmer la suppression": "Conferma l'eliminazione",
    "Confirmer l'annulation": "Conferma l'annullamento",
    "Confirmer la modification": "Conferma la modifica",
    "Confirmer l'action": "Conferma l'azione",
    "Annuler et revenir": "Annulla e torna indietro",
    "Continuer quand même": "Continua comunque",
    "Oui, supprimer": "Sì, elimina",
    "Non, annuler": "No, annulla",
    "Oui, confirmer": "Sì, conferma",
    "Non, revenir": "No, torna indietro",

    # Chargement
    "Chargement des données": "Caricamento dei dati",
    "Chargement en cours...": "Caricamento in corso...",
    "Veuillez patienter...": "Attendere prego...",
    "Traitement en cours": "Elaborazione in corso",
    "Sauvegarde en cours": "Salvataggio in corso",
    "Envoi en cours": "Invio in corso",
    "Téléchargement en cours": "Scaricamento in corso",
    "Mise à jour en cours": "Aggiornamento in corso",
    "Suppression en cours": "Eliminazione in corso",

    # Divers
    "Aucun résultat trouvé": "Nessun risultato trovato",
    "Aucun élément à afficher": "Nessun elemento da visualizzare",
    "Liste vide": "Elenco vuoto",
    "Pas de données disponibles": "Nessun dato disponibile",
    "En savoir plus": "Scopri di più",
    "Voir tout": "Vedi tutto",
    "Voir moins": "Vedi meno",
    "Afficher plus": "Mostra di più",
    "Afficher moins": "Mostra meno",
    "Développer": "Espandi",
    "Réduire": "Riduci",
    "Copier le lien": "Copia il link",
    "Lien copié": "Link copiato",
    "Partager le lien": "Condividi il link",
    "Envoyer par email": "Invia per email",
    "Télécharger en PDF": "Scarica in PDF",
    "Imprimer la page": "Stampa la pagina",
    "Retour en haut": "Torna in alto",
    "Aller en bas": "Vai in basso",
    "Fermer cette fenêtre": "Chiudi questa finestra",
    "Ouvrir dans un nouvel onglet": "Apri in una nuova scheda",

    # Interface
    "Menu principal": "Menu principale",
    "Barre de navigation": "Barra di navigazione",
    "Barre latérale": "Barra laterale",
    "En-tête": "Intestazione",
    "Pied de page": "Piè di pagina",
    "Contenu principal": "Contenuto principale",
    "Section": "Sezione",
    "Onglet": "Scheda",
    "Onglets": "Schede",
    "Panneau": "Pannello",
    "Fenêtre": "Finestra",
    "Boîte de dialogue": "Finestra di dialogo",
    "Notification": "Notifica",
    "Message d'erreur": "Messaggio di errore",
    "Message de succès": "Messaggio di successo",
    "Indicateur de chargement": "Indicatore di caricamento",
}


def fix_text(text):
    """Nettoie un texte des caracteres mojibake."""
    for bad, good in MOJIBAKE_MAP:
        text = text.replace(bad, good)
    return text


def main():
    """Fonction principale."""
    po_path = 'locale/it/LC_MESSAGES/django.po'

    print("=" * 70)
    print("TRADUCTION ETENDUE DU PO ITALIEN")
    print("=" * 70)

    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Nettoyer le mojibake dans tout le fichier
    print("\n1. Nettoyage du mojibake...")
    content = fix_text(content)

    # 2. Appliquer les traductions
    print("2. Application des traductions...")
    translations_applied = 0

    for fr_term, it_term in FR_IT_EXTENDED.items():
        # Nettoyer le terme francais aussi
        fr_clean = fix_text(fr_term)
        fr_escaped = re.escape(fr_clean)

        # Pattern msgstr vide
        pattern1 = re.compile(
            rf'(msgid "{fr_escaped}"\n)(msgstr "")',
            re.MULTILINE | re.IGNORECASE
        )
        new_content, count1 = pattern1.subn(rf'\1msgstr "{it_term}"', content)
        if count1 > 0:
            content = new_content
            translations_applied += count1

        # Pattern msgstr = msgid
        pattern2 = re.compile(
            rf'(msgid "{fr_escaped}"\n)(msgstr "{fr_escaped}")',
            re.MULTILINE | re.IGNORECASE
        )
        new_content, count2 = pattern2.subn(rf'\1msgstr "{it_term}"', content)
        if count2 > 0:
            content = new_content
            translations_applied += count2

    print(f"   {translations_applied} traductions appliquees")

    # 3. Sauvegarder
    print("3. Sauvegarde...")
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n" + "=" * 70)
    print(f"TERMINE - {translations_applied} traductions")
    print("=" * 70)


if __name__ == '__main__':
    main()
