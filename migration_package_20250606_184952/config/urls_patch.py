"""
Patch à ajouter au urls.py de production
"""

# À ajouter aux imports:
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

# URLs sans préfixe de langue (avant i18n_patterns):
urlpatterns = [
    # Sélection de langue
    path('set-language/', set_language, name='set_language'),
    
    # Interface Rosetta (sans préfixe de langue)
    path('rosetta/', include('rosetta.urls')),
    
    # ... autres URLs sans préfixe
]

# URLs avec préfixe de langue:
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('competitions.urls')),  # Vos URLs existantes
    # ... autres URLs avec préfixe
)
