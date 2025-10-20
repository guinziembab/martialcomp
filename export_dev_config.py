import os
import json
import hashlib

# Collecter les informations importantes
config = {
  "INSTALLED_APPS": [],
  "MIDDLEWARE": [],
  "files": {},
  "migrations": {},
}

# Lire settings
try:
  from config.settings.base import INSTALLED_APPS, MIDDLEWARE
  config["INSTALLED_APPS"] = INSTALLED_APPS
  config["MIDDLEWARE"] = MIDDLEWARE
except:
  pass

# Lister tous les fichiers Python importants
for root, dirs, files in os.walk("apps"):
  for file in files:
	  if file.endswith(".py") and not file.startswith("__"):
		  path = os.path.join(root, file)
		  with open(path, "rb") as f:
			  config["files"][path] = hashlib.md5(f.read()).hexdigest()

# Sauvegarder
with open("dev_config.json", "w") as f:
  json.dump(config, f, indent=2)

print("Configuration exportée dans dev_config.json")
