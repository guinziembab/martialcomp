from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from django.shortcuts import redirect

urlpatterns = [
  path('admin/', admin.site.urls),
  path('rosetta/', include('rosetta.urls')),
  path('i18n/', include('django.conf.urls.i18n')),
  path('accounts/', include('allauth.urls')),
]

# URLs avec support i18n (incluent le préfixe de langue /fr/, /en/, etc.)
urlpatterns += i18n_patterns(
  path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
  path('', include('competitions.urls')),
  prefix_default_language=False,
)

# Médias et statiques (sans i18n)
if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
  urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# URLs temporaires pour les modules non implémentés
urlpatterns += [
  path('grades/', lambda request: redirect('/dashboard/'), name='grades_temp'),
  path('finances/', lambda request: redirect('/dashboard/'), name='finances_temp'),
  path('shop/', lambda request: redirect('/dashboard/'), name='shop_temp'),
  path('documents/', lambda request: redirect('/dashboard/'), name='documents_temp'),        
]
