"""
Admin principal pour competitions
NE PAS importer Practitioner pour éviter l'erreur en production
"""
from django.contrib import admin

# Importer uniquement depuis le répertoire admin/
try:
  from .admin.competition import *
  from .admin.category import *
  from .admin.discipline import *
  from .admin.judge import *
  from .admin.registration import *
  from .admin.club import *
  from .admin.federation import *
  # NE PAS importer practitioner !
  print("Admin competitions chargé (sans Practitioner)")
except ImportError as e:
  print(f"Erreur import admin: {e}")
