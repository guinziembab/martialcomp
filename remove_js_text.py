#!/usr/bin/env python
"""Supprimer le JavaScript qui s'affiche comme texte"""

print("=== Suppression du JavaScript affiché comme texte ===\n")

template_file = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/club.html'

# Lire le fichier
with open(template_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
import datetime
backup_path = template_file + f'.backup_remove_js_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✓ Backup créé: {backup_path}")

original_size = len(content)

# Chercher et supprimer le JavaScript problématique
# D'après le message de l'utilisateur, le JS commence par "function calculateAges()"

# Méthode 1: Supprimer tout après le dernier {% endblock %}
endblock_tag = '{% endblock %}'
last_endblock = content.rfind(endblock_tag)
if last_endblock > 0:
    after_endblock = content[last_endblock + len(endblock_tag):]
    if after_endblock.strip():
        print(f"\n⚠️  Contenu trouvé après endblock: {len(after_endblock.strip())} caractères")
        content = content[:last_endblock + len(endblock_tag)]
        print("✓ Contenu supprimé après endblock")

# Méthode 2: Chercher spécifiquement "function calculateAges()" qui pourrait être mal placé
calc_start = content.find('function calculateAges()')
if calc_start > 0:
    print(f"\n'function calculateAges()' trouvé à la position {calc_start}")
    
    # Vérifier si c'est dans une balise script
    before = content[:calc_start]
    last_script_open = before.rfind('<script')
    last_script_close = before.rfind('</script>')
    
    if last_script_close > last_script_open:
        print("⚠️  JavaScript trouvé HORS des balises <script>!")
        
        # Chercher la fin de ce bloc JavaScript
        # Le JavaScript semble se terminer avec "processBulkRegistration"
        js_end = content.find('processBulkRegistration', calc_start)
        if js_end > 0:
            # Chercher la fin de la fonction processBulkRegistration
            # Elle se termine probablement avec "}, 2000);"
            func_end = content.find('}, 2000);', js_end)
            if func_end > 0:
                func_end += len('}, 2000);')
                # Peut-être qu'il y a encore du code après
                next_bracket = content.find('}', func_end)
                if next_bracket > 0 and next_bracket - func_end < 50:
                    func_end = next_bracket + 1
            else:
                func_end = js_end + 200  # Estimation
                
            # Supprimer tout ce bloc
            print(f"Suppression du JavaScript de la position {calc_start} à {func_end}")
            content = content[:calc_start] + content[func_end:]
            print("✓ JavaScript parasite supprimé")

# Méthode 3: Nettoyer tout JavaScript qui apparaît après </script>{% endblock %}
import re
pattern = r'</script>\s*\{% endblock %\}'
matches = list(re.finditer(pattern, content))
if matches:
    last_match = matches[-1]
    end_pos = last_match.end()
    if end_pos < len(content) - 10:  # S'il y a du contenu après
        remaining = content[end_pos:].strip()
        if remaining and any(js_pattern in remaining for js_pattern in ['function', 'document.', 'const ', 'let ', 'var ']):
            print("\n⚠️  JavaScript trouvé après </script> et endblock")
            content = content[:end_pos]
            print("✓ JavaScript supprimé après la fin du template")

# Sauvegarder
with open(template_file, 'w', encoding='utf-8') as f:
    f.write(content)

new_size = len(content)
print(f"\n✅ Correction terminée!")
print(f"Taille avant: {original_size} caractères")
print(f"Taille après: {new_size} caractères")
print(f"Supprimé: {original_size - new_size} caractères")

# Vérification finale
if content.count('function calculateAges') > 1:
    print("\n⚠️  ATTENTION: Il reste encore des occurrences de 'function calculateAges'")