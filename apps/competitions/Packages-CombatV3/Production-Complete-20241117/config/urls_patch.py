# Patch pour config/urls.py
# Ajouter l'inclusion des URLs API Combat V3

# Dans la section des URLs sans préfixe de langue, ajouter :
# API Combat V3 - IMPORTANT: Placer après api.urls pour éviter les conflits
# Les URLs de combat_api_urls commencent par 'combat/', donc pas de conflit
path('api/', include('apps.competitions.combat_api_urls')),

# Cette ligne doit être ajoutée après :
# path('api/', include('api.urls')),
# path('api/v1/auth/', include('api_auth.urls', namespace='api_auth')),
