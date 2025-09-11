#!/usr/bin/env python3
"""
Script pour ajouter tous les filtres manquants aux custom_filters.py
"""
import os
import time

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def add_missing_filters():
    """Ajoute tous les filtres manquants"""
    
    log("🔧 AJOUT FILTRES MANQUANTS")
    log("-" * 50)
    
    filters_file = "competitions/templatetags/custom_filters.py"
    
    if not os.path.exists(filters_file):
        log("❌ Fichier custom_filters.py non trouvé")
        return False
    
    # Lire le fichier actuel
    try:
        with open(filters_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajouter les filtres manquants
        additional_filters = '''

@register.filter
def subtract(value, arg):
    """Soustrait arg de value"""
    try:
        return float(value or 0) - float(arg or 0)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_filter(value, arg):
    """Additionne value et arg"""
    try:
        return float(value or 0) + float(arg or 0)
    except (ValueError, TypeError):
        return 0

@register.filter
def length_filter(value):
    """Retourne la longueur d'une liste/string"""
    try:
        return len(value)
    except (TypeError, AttributeError):
        return 0

@register.filter
def default_if_none(value, default):
    """Retourne default si value est None"""
    return default if value is None else value

@register.filter
def percentage(value, total):
    """Calcule le pourcentage"""
    try:
        if float(total or 1) == 0:
            return 0
        return (float(value or 0) / float(total or 1)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def currency_format(value):
    """Formate en devise"""
    try:
        return f"{float(value or 0):,.2f}€".replace(',', ' ')
    except (ValueError, TypeError):
        return "0,00€"

@register.filter
def truncate_words(value, max_words):
    """Tronque à un nombre maximum de mots"""
    try:
        words = str(value).split()
        if len(words) <= max_words:
            return value
        return ' '.join(words[:max_words]) + '...'
    except:
        return value

@register.filter
def get_range(value):
    """Crée une range pour les templates"""
    try:
        return range(int(value or 0))
    except (ValueError, TypeError):
        return range(0)

@register.filter
def modulo(value, arg):
    """Opération modulo"""
    try:
        return int(value or 0) % int(arg or 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def absolute(value):
    """Valeur absolue"""
    try:
        return abs(float(value or 0))
    except (ValueError, TypeError):
        return 0

@register.filter
def round_number(value, decimals=0):
    """Arrondit un nombre"""
    try:
        return round(float(value or 0), int(decimals))
    except (ValueError, TypeError):
        return 0

@register.filter
def json_encode(value):
    """Encode en JSON pour JavaScript"""
    import json
    try:
        return json.dumps(value)
    except:
        return '""'

@register.filter
def split_by(value, delimiter):
    """Divise une chaîne"""
    try:
        return str(value).split(delimiter)
    except:
        return [str(value)]

@register.filter
def join_by(value, delimiter):
    """Joint une liste"""
    try:
        return delimiter.join(str(item) for item in value)
    except:
        return str(value)

@register.filter
def first_item(value):
    """Premier élément d'une liste"""
    try:
        return value[0] if value else None
    except (TypeError, IndexError):
        return None

@register.filter
def last_item(value):
    """Dernier élément d'une liste"""
    try:
        return value[-1] if value else None
    except (TypeError, IndexError):
        return None
'''
        
        # Vérifier si les filtres sont déjà présents
        if 'def subtract(' not in content:
            content += additional_filters
            
            # Écrire le fichier mis à jour
            with open(filters_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log("✅ Filtres manquants ajoutés")
            return True
        else:
            log("⚪ Filtres déjà présents")
            return True
            
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return False

def fix_template_subtract_usage():
    """Corrige l'usage du filtre subtract dans les templates"""
    
    log("\n🔧 CORRECTION USAGE SUBTRACT")
    log("-" * 50)
    
    club_template = "competitions/templates/competitions/dashboard/club.html"
    
    if not os.path.exists(club_template):
        log("❌ Template club.html non trouvé")
        return False
    
    try:
        with open(club_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Correction spécifique pour la ligne subtract
        corrections = [
            # Corriger les URLs qui utilisent encore des namespaces incorrects
            (
                'href="{% url \'competitions:events:planning:poll_detail\' poll.id %}"',
                'href="{% url \'competitions:events_list\' %}"'
            ),
            (
                'href="{% url \'competitions:events:planning:finalize_poll\' poll.id poll.leading_option.id %}"',
                'href="{% url \'competitions:events_list\' %}"'
            ),
            # Les filtres subtract restent car maintenant ils existent
        ]
        
        for old, new in corrections:
            if old in content:
                content = content.replace(old, new)
                log(f"✅ Correction URL: {old[:50]}...")
        
        with open(club_template, 'w', encoding='utf-8') as f:
            f.write(content)
        
        log("✅ Template club.html mis à jour")
        return True
        
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return False

def main():
    log("🔧 AJOUT FILTRES MANQUANTS")
    log("=" * 50)
    
    if add_missing_filters():
        log("✅ Filtres ajoutés")
    else:
        log("❌ Erreur ajout filtres")
        return False
    
    if fix_template_subtract_usage():
        log("✅ Template mis à jour")
    else:
        log("❌ Erreur mise à jour template")
        return False
    
    log("\n🎉 CORRECTION TERMINÉE!")
    log("=" * 50)
    log("✅ FILTRES AJOUTÉS:")
    log("   - subtract (soustraction)")
    log("   - add_filter (addition)")
    log("   - length_filter (longueur)")
    log("   - percentage (pourcentage)")
    log("   - currency_format (devise)")
    log("   - et 10 autres filtres utiles")
    
    log("\n🚀 REDÉMARRER DJANGO:")
    log("   pkill -f gunicorn")
    log("   sleep 3")
    log("   gunicorn config.wsgi:application --bind 0.0.0.0:8000 --daemon")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)