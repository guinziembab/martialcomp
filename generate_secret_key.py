#!/usr/bin/env python3
import secrets

# Générer une clé secrète forte de 50 caractères
secret_key = secrets.token_urlsafe(50)
print(f"Nouvelle clé secrète générée :")
print(secret_key)
print(f"\nLongueur : {len(secret_key)} caractères") 