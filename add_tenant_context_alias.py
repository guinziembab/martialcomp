"""
Script pour ajouter un alias tenant_context pour la compatibilité
"""

def add_alias():
    middleware_file = 'multitenant/middleware.py'
    
    # Lire le fichier
    with open(middleware_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si l'alias existe déjà
    if 'tenant_context = TenantContext' in content:
        print("L'alias tenant_context existe déjà")
        return
    
    # Ajouter l'alias à la fin du fichier
    content += '\n\n# Alias pour la compatibilité avec l\'ancien code\ntenant_context = TenantContext\n'
    
    # Écrire le fichier modifié
    with open(middleware_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Alias tenant_context ajouté dans middleware.py")

if __name__ == "__main__":
    add_alias()