#!/usr/bin/env python3
"""
Script de configuration multilingue pour MartialComp
Crée la structure de base pour les traductions
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command

def create_locale_structure():
    """Crée la structure des répertoires locale"""
    print("🏗️ Création de la structure locale...")
    
    # Créer le répertoire locale principal
    locale_dir = os.path.join('.', 'locale')
    os.makedirs(locale_dir, exist_ok=True)
    
    # Créer les répertoires pour chaque langue
    for lang_code, lang_name in settings.LANGUAGES:
        if lang_code == settings.LANGUAGE_CODE:
            continue  # Ignorer la langue source
            
        lang_dir = os.path.join(locale_dir, lang_code, 'LC_MESSAGES')
        os.makedirs(lang_dir, exist_ok=True)
        print(f"  ✅ Répertoire créé: {lang_dir}")
        
        # Créer un fichier PO vide
        po_file = os.path.join(lang_dir, 'django.po')
        if not os.path.exists(po_file):
            with open(po_file, 'w', encoding='utf-8') as f:
                f.write(f'''# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: MartialComp\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-06-05 00:00+0000\\n"
"PO-Revision-Date: 2025-06-05 00:00+0000\\n"
"Last-Translator: Auto-generated\\n"
"Language-Team: {lang_name}\\n"
"Language: {lang_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

''')
            print(f"  ✅ Fichier PO créé: {po_file}")

def create_sample_translations():
    """Crée quelques traductions d'exemple"""
    print("📝 Création de traductions d'exemple...")
    
    # Exemples de traductions pour les termes communs de MartialComp
    sample_translations = {
        'en': {
            'Bienvenue': 'Welcome',
            'Tableau de bord': 'Dashboard',
            'Compétition': 'Competition',
            'Pratiquant': 'Practitioner',
            'Club': 'Club',
            'Grade': 'Grade',
            'Discipline': 'Discipline',
            'Arts martiaux': 'Martial Arts',
            'Se connecter': 'Login',
            'S\'inscrire': 'Sign up',
            'Déconnexion': 'Logout',
            'Gestion': 'Management',
            'Résultats': 'Results',
            'Inscription': 'Registration',
            'Participant': 'Participant',
            'Juge': 'Judge',
            'Arbitre': 'Referee',
            'Entraîneur': 'Coach',
            'Fédération': 'Federation',
            'Événement': 'Event',
            'Tournoi': 'Tournament',
        },
        'es': {
            'Bienvenue': 'Bienvenido',
            'Tableau de bord': 'Panel de control',
            'Compétition': 'Competición',
            'Pratiquant': 'Practicante',
            'Club': 'Club',
            'Grade': 'Grado',
            'Discipline': 'Disciplina',
            'Arts martiaux': 'Artes marciales',
            'Se connecter': 'Iniciar sesión',
            'S\'inscrire': 'Registrarse',
            'Déconnexion': 'Cerrar sesión',
            'Gestion': 'Gestión',
            'Résultats': 'Resultados',
            'Inscription': 'Inscripción',
            'Participant': 'Participante',
            'Juge': 'Juez',
            'Arbitre': 'Árbitro',
            'Entraîneur': 'Entrenador',
            'Fédération': 'Federación',
            'Événement': 'Evento',
            'Tournoi': 'Torneo',
        },
        'it': {
            'Bienvenue': 'Benvenuto',
            'Tableau de bord': 'Cruscotto',
            'Compétition': 'Competizione',
            'Pratiquant': 'Praticante',
            'Club': 'Club',
            'Grade': 'Grado',
            'Discipline': 'Disciplina',
            'Arts martiaux': 'Arti marziali',
            'Se connecter': 'Accedi',
            'S\'inscrire': 'Registrati',
            'Déconnexion': 'Disconnetti',
            'Gestion': 'Gestione',
            'Résultats': 'Risultati',
            'Inscription': 'Iscrizione',
            'Participant': 'Partecipante',
            'Juge': 'Giudice',
            'Arbitre': 'Arbitro',
            'Entraîneur': 'Allenatore',
            'Fédération': 'Federazione',
            'Événement': 'Evento',
            'Tournoi': 'Torneo',
        },
        'de': {
            'Bienvenue': 'Willkommen',
            'Tableau de bord': 'Dashboard',
            'Compétition': 'Wettkampf',
            'Pratiquant': 'Praktizierender',
            'Club': 'Verein',
            'Grade': 'Grad',
            'Discipline': 'Disziplin',
            'Arts martiaux': 'Kampfkünste',
            'Se connecter': 'Anmelden',
            'S\'inscrire': 'Registrieren',
            'Déconnexion': 'Abmelden',
            'Gestion': 'Verwaltung',
            'Résultats': 'Ergebnisse',
            'Inscription': 'Anmeldung',
            'Participant': 'Teilnehmer',
            'Juge': 'Richter',
            'Arbitre': 'Schiedsrichter',
            'Entraîneur': 'Trainer',
            'Fédération': 'Verband',
            'Événement': 'Veranstaltung',
            'Tournoi': 'Turnier',
        }
    }
    
    for lang_code, translations in sample_translations.items():
        po_file = os.path.join('locale', lang_code, 'LC_MESSAGES', 'django.po')
        if os.path.exists(po_file):
            with open(po_file, 'a', encoding='utf-8') as f:
                for french, translation in translations.items():
                    f.write(f'\nmsgid "{french}"\nmsgstr "{translation}"\n')
            print(f"  ✅ Traductions ajoutées à {po_file}")

def create_welcome_template_with_translations():
    """Met à jour le template welcome avec les balises de traduction"""
    print("🔄 Mise à jour du template welcome avec les traductions...")
    
    # Le template a déjà été créé avec les balises de traduction
    # Ajoutons quelques améliorations spécifiques aux arts martiaux
    
    martial_arts_css = """
/* Styles spéciaux pour les termes d'arts martiaux */
.martial-term {
    color: var(--accent);
    font-weight: 500;
    cursor: help;
    border-bottom: 1px dotted var(--accent);
}

.martial-term:hover {
    background-color: rgba(212, 175, 55, 0.1);
    padding: 2px;
    border-radius: 3px;
}

.translation-missing {
    background-color: rgba(255, 0, 0, 0.1);
    border: 1px dashed red;
    padding: 2px;
    border-radius: 3px;
}
"""
    
    # Ajouter les styles dans un fichier séparé
    css_file = 'static/css/martial_arts_translations.css'
    os.makedirs(os.path.dirname(css_file), exist_ok=True)
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(martial_arts_css)
    print(f"  ✅ Styles créés: {css_file}")

def main():
    """Fonction principale de configuration"""
    print("🥋 CONFIGURATION MULTILINGUE MARTIALCOMP")
    print("=" * 50)
    
    try:
        # 1. Créer la structure locale
        create_locale_structure()
        
        # 2. Créer des traductions d'exemple
        create_sample_translations()
        
        # 3. Améliorer les templates
        create_welcome_template_with_translations()
        
        print("\n✅ CONFIGURATION MULTILINGUE TERMINÉE")
        print("=" * 50)
        print("📋 Prochaines étapes:")
        print("1. Accédez à /rosetta/ pour gérer les traductions")
        print("2. Visitez /admin/translations/dashboard/ pour voir les statistiques")
        print("3. Utilisez {% load translation_helpers %} dans vos templates")
        print("4. Testez le changement de langue sur la page d'accueil")
        print("5. Exécutez: python manage.py compilemessages pour compiler")
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()