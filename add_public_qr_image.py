#!/usr/bin/env python3
"""
Script pour ajouter une URL publique pour l'image QR
"""

def add_public_qr_image():
    """Ajoute une vue publique pour l'image QR"""
    
    qr_scanner_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/qr_scanner.py"
    
    # Lire le fichier
    with open(qr_scanner_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter une vue publique pour l'image QR après la fonction qr_code_image existante
    public_image_view = '''
def qr_code_image_public(request, practitioner_id):
    """Retourne l'image du QR code d'un pratiquant (accès public)"""
    practitioner = get_object_or_404(Practitioner, id=practitioner_id)
    
    # Obtenir ou créer le QR code
    qr_code, created = PractitionerQRCode.objects.get_or_create(practitioner=practitioner)
    
    # Générer le QR code si nécessaire
    if not qr_code.qr_image:
        qr_code.generate_qr_code()
        qr_code.save()
    
    # Retourner l'image
    if qr_code.qr_image:
        return HttpResponse(qr_code.qr_image.read(), content_type="image/png")
    else:
        return HttpResponse("QR code non disponible", status=404)


'''
    
    # Trouver la fin de la fonction qr_code_image et insérer la nouvelle fonction
    qr_image_end = content.find('    return HttpResponse(qr_code.qr_image.read(), content_type="image/png")')
    if qr_image_end != -1:
        # Trouver la fin de la fonction
        next_line = content.find('\n', qr_image_end)
        if next_line != -1:
            # Insérer la nouvelle fonction
            new_content = content[:next_line + 1] + public_image_view + content[next_line + 1:]
            
            # Écrire le fichier modifié
            with open(qr_scanner_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Vue publique qr_code_image_public ajoutée")
        else:
            print("❌ Impossible de trouver la fin de la fonction qr_code_image")
    else:
        print("❌ Impossible de trouver la fonction qr_code_image")

def update_qr_urls_for_image():
    """Met à jour les URLs pour inclure la vue publique de l'image"""
    
    qr_urls_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/qr.py"
    
    # Lire le fichier
    with open(qr_urls_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter l'import de la nouvelle vue
    new_import = "from apps.competitions.views.qr_scanner import (\n    scan_practitioner_qr, \n    scan_history, \n    mark_attendance_ajax, \n    process_qr_scan,\n    view_qr,\n    view_qr_public,\n    qr_code_image,\n    qr_code_image_public\n)"
    
    # Remplacer l'import existant
    import_start = content.find("from apps.competitions.views.qr_scanner import (")
    if import_start != -1:
        import_end = content.find(")", import_start) + 1
        new_content = content[:import_start] + new_import + content[import_end:]
        
        # Ajouter l'URL publique pour l'image
        url_patterns_end = new_content.find("]")
        if url_patterns_end != -1:
            new_url = "    \n    # Image du QR code (accès public)\n    path('image/public/<int:practitioner_id>/', qr_code_image_public, name='qr_image_public'),\n"
            new_content = new_content[:url_patterns_end] + new_url + new_content[url_patterns_end:]
            
            # Écrire le fichier modifié
            with open(qr_urls_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ URL publique pour l'image QR ajoutée")
        else:
            print("❌ Impossible de trouver urlpatterns")
    else:
        print("❌ Impossible de trouver l'import")

def update_template_for_public_image():
    """Met à jour le template pour utiliser l'URL publique de l'image"""
    
    template_path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/qr_scanner/view_qr.html"
    
    # Lire le fichier
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer l'URL de l'image QR par une version conditionnelle
    old_image_url = "{% url 'competitions:qr:qr_image' practitioner.id %}"
    new_image_url = "{% if is_public %}{% url 'competitions:qr:qr_image_public' practitioner.id %}{% else %}{% url 'competitions:qr:qr_image' practitioner.id %}{% endif %}"
    
    # Remplacer l'occurrence
    new_content = content.replace(old_image_url, new_image_url)
    
    # Écrire le fichier modifié
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Template mis à jour pour utiliser l'URL publique de l'image")

if __name__ == "__main__":
    print("🔧 AJOUT DE L'URL PUBLIQUE POUR L'IMAGE QR")
    print("=" * 50)
    
    add_public_qr_image()
    update_qr_urls_for_image()
    update_template_for_public_image()
    
    print("✅ Correction terminée")