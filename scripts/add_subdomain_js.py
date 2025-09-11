#!/usr/bin/env python3
"""
Script pour ajouter le JavaScript de gestion des sous-domaines aux templates de création de fédération
"""

# Ce script ajoute le JavaScript nécessaire pour gérer l'affichage conditionnel 
# des champs de sous-domaine et site web externe

subdomain_javascript = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Éléments du formulaire
    const websiteTypeRadios = document.querySelectorAll('input[name="website_type"]');
    const customSubdomainGroup = document.querySelector('.field-custom_subdomain, .form-group:has(#id_custom_subdomain)');
    const externalWebsiteGroup = document.querySelector('.field-external_website, .form-group:has(#id_external_website)');
    const customSubdomainInput = document.getElementById('id_custom_subdomain');
    const externalWebsiteInput = document.getElementById('id_external_website');
    const previewDiv = document.getElementById('subdomain-preview');
    
    // Fonction pour mettre à jour l'affichage
    function updateDisplayBasedOnType() {
        const selectedType = document.querySelector('input[name="website_type"]:checked')?.value;
        
        if (selectedType === 'subdomain') {
            // Afficher les champs de sous-domaine
            if (customSubdomainGroup) customSubdomainGroup.style.display = 'block';
            if (externalWebsiteGroup) externalWebsiteGroup.style.display = 'none';
            
            // Rendre le site externe optionnel
            if (externalWebsiteInput) externalWebsiteInput.required = false;
            
            // Générer un aperçu du sous-domaine
            updateSubdomainPreview();
        } else if (selectedType === 'external') {
            // Afficher le champ site web externe
            if (customSubdomainGroup) customSubdomainGroup.style.display = 'none';
            if (externalWebsiteGroup) externalWebsiteGroup.style.display = 'block';
            
            // Rendre le site externe requis
            if (externalWebsiteInput) externalWebsiteInput.required = true;
            
            // Masquer l'aperçu du sous-domaine
            if (previewDiv) previewDiv.style.display = 'none';
        }
    }
    
    // Fonction pour générer un aperçu du sous-domaine
    function updateSubdomainPreview() {
        const nameInput = document.getElementById('id_name');
        const customInput = document.getElementById('id_custom_subdomain');
        
        if (!nameInput || !previewDiv) return;
        
        let subdomain = '';
        
        if (customInput && customInput.value.trim()) {
            // Utiliser le sous-domaine personnalisé
            subdomain = customInput.value.trim().toLowerCase();
        } else if (nameInput.value.trim()) {
            // Générer automatiquement depuis le nom
            subdomain = generateSubdomainFromName(nameInput.value);
        }
        
        if (subdomain) {
            // Nettoyer le sous-domaine
            subdomain = subdomain.replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
            
            if (subdomain.length > 50) {
                subdomain = subdomain.substring(0, 50).replace(/-[^-]*$/, '');
            }
            
            const fullUrl = `https://${subdomain}.martialcomp.com`;
            previewDiv.innerHTML = `
                <div class="alert alert-info">
                    <strong>Aperçu de votre site :</strong><br>
                    <a href="#" class="text-decoration-none">${fullUrl}</a>
                    <small class="d-block mt-1 text-muted">
                        Ce site sera créé automatiquement avec votre fédération
                    </small>
                </div>
            `;
            previewDiv.style.display = 'block';
        } else {
            previewDiv.style.display = 'none';
        }
    }
    
    // Fonction pour générer un sous-domaine depuis le nom
    function generateSubdomainFromName(name) {
        // Règles de génération simplifiées (côté client)
        return name.toLowerCase()
                   .replace(/[àáâãäå]/g, 'a')
                   .replace(/[èéêë]/g, 'e')
                   .replace(/[ìíîï]/g, 'i')
                   .replace(/[òóôõö]/g, 'o')
                   .replace(/[ùúûü]/g, 'u')
                   .replace(/[ç]/g, 'c')
                   .replace(/[ñ]/g, 'n')
                   .replace(/[^a-z0-9\\s-]/g, '')
                   .replace(/\\s+/g, '-')
                   .replace(/-+/g, '-')
                   .replace(/^-|-$/g, '');
    }
    
    // Écouter les changements de type de site web
    websiteTypeRadios.forEach(radio => {
        radio.addEventListener('change', updateDisplayBasedOnType);
    });
    
    // Écouter les changements dans les champs pour l'aperçu
    if (document.getElementById('id_name')) {
        document.getElementById('id_name').addEventListener('input', function() {
            const selectedType = document.querySelector('input[name="website_type"]:checked')?.value;
            if (selectedType === 'subdomain') {
                updateSubdomainPreview();
            }
        });
    }
    
    if (customSubdomainInput) {
        customSubdomainInput.addEventListener('input', updateSubdomainPreview);
    }
    
    // Initialiser l'affichage
    updateDisplayBasedOnType();
});
</script>

<style>
.field-custom_subdomain, .field-external_website {
    transition: all 0.3s ease;
}

#subdomain-preview {
    margin-top: 10px;
}

#subdomain-preview .alert {
    margin-bottom: 0;
}

.website-type-help {
    font-size: 0.875em;
    color: #6c757d;
    margin-top: 5px;
}

.form-check-input:checked + .form-check-label {
    font-weight: 500;
}
</style>
"""

print("JavaScript pour la gestion des sous-domaines:")
print("=" * 50)
print(subdomain_javascript)
print("=" * 50)
print("\n🎯 Ce JavaScript doit être ajouté au template de création de fédération")
print("📁 Emplacement suggéré: competitions/templates/competitions/federations/create.html")
print("📝 Fonctionnalités:")
print("   • Affichage conditionnel des champs selon le type de site")
print("   • Aperçu en temps réel du sous-domaine généré")
print("   • Validation côté client du sous-domaine personnalisé")
print("   • Interface utilisateur fluide avec transitions")