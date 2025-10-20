#!/bin/bash
# Script d'urgence pour corriger les problèmes en production

echo "🚨 Application des corrections d'urgence..."
echo "=========================================="

# 1. Corriger l'erreur 500 sur registrations
echo "1. Correction de la vue registrations..."
ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Corriger la ligne problématique dans competitions.py
sed -i '775,776s/.*/    if not request.user.is_staff:/' apps/competitions/views/competitions.py
sed -i '777s/.*/        return redirect("competitions:competitions:list")/' apps/competitions/views/competitions.py

# Vérifier
echo "Vérification de la correction:"
sed -n '775,777p' apps/competitions/views/competitions.py
EOF

# 2. Ajouter le patch JavaScript directement dans le template
echo ""
echo "2. Ajout du patch JavaScript pour l'AJAX..."
ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Créer une copie de sauvegarde
cp apps/competitions/templates/competitions/club/competition_management_detail.html \
   apps/competitions/templates/competitions/club/competition_management_detail.html.backup_emergency

# Ajouter le script juste après {% block content %}
sed -i '/{% block content %}/a\
<script>\
// PATCH AJAX URGENCE\
(function() {\
    if (document.readyState === "loading") {\
        document.addEventListener("DOMContentLoaded", setupCategoryAjax);\
    } else {\
        setupCategoryAjax();\
    }\
    \
    function setupCategoryAjax() {\
        setTimeout(function() {\
            const categoryForm = document.getElementById("categoryForm");\
            if (!categoryForm) return;\
            \
            const newForm = categoryForm.cloneNode(true);\
            categoryForm.parentNode.replaceChild(newForm, categoryForm);\
            \
            newForm.addEventListener("submit", function(e) {\
                e.preventDefault();\
                \
                const formData = new FormData(this);\
                const submitBtn = this.querySelector("button[type=submit]");\
                submitBtn.disabled = true;\
                \
                fetch(this.action, {\
                    method: "POST",\
                    body: formData,\
                    headers: {\
                        "X-CSRFToken": this.querySelector("[name=csrfmiddlewaretoken]").value,\
                        "X-Requested-With": "XMLHttpRequest"\
                    }\
                })\
                .then(response => response.json())\
                .then(data => {\
                    if (data.success) {\
                        alert("Catégorie créée avec succès !");\
                        window.location.reload();\
                    } else {\
                        alert("Erreur: " + data.message);\
                    }\
                })\
                .catch(error => {\
                    alert("Erreur de connexion");\
                })\
                .finally(() => {\
                    submitBtn.disabled = false;\
                });\
            });\
        }, 1000);\
    }\
})();\
</script>' apps/competitions/templates/competitions/club/competition_management_detail.html

echo "Patch JavaScript ajouté"
EOF

# 3. Redémarrer le service
echo ""
echo "3. Redémarrage du service..."
ssh martialcomp-production "sudo systemctl restart martialcomp.service && sleep 3"

# 4. Vérifier le statut
echo ""
echo "4. Vérification du statut..."
ssh martialcomp-production "sudo systemctl is-active martialcomp.service"

echo ""
echo "=========================================="
echo "✅ Corrections d'urgence appliquées"
echo ""
echo "Tests à effectuer:"
echo "1. Vérifier que /registrations/ ne donne plus d'erreur 500"
echo "2. Tester la création de catégorie (le JSON ne devrait plus s'afficher)"
echo "3. Si le problème persiste, vider le cache du navigateur"