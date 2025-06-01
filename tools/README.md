# Outils de test pour MartialComp

Ce répertoire contient des outils pour tester diverses fonctionnalités de l'application MartialComp.

## Test de compatibilité mobile

### `test_mobile_compatibility.py`

Ce script teste la compatibilité mobile des pages de profil hors-ligne en simulant différents appareils mobiles.

#### Prérequis

1. Python 3.6 ou supérieur
2. Selenium
3. Chrome WebDriver

Installation des dépendances :

```bash
pip install selenium
```

Vous devez également installer Chrome WebDriver. Consultez [la documentation de Selenium](https://selenium-python.readthedocs.io/installation.html#drivers) pour plus d'informations.

#### Utilisation

```bash
python test_mobile_compatibility.py [URL_BASE]
```

Exemple :

```bash
python test_mobile_compatibility.py http://localhost:8000
python test_mobile_compatibility.py https://martialcomp.example.com
```

Le script va :
1. Simuler différents appareils mobiles (iPhone X, Galaxy S10, iPad Pro, Nexus 7)
2. Tester les URLs liées au profil hors-ligne
3. Prendre des captures d'écran
4. Vérifier que les éléments responsives s'affichent correctement

Les captures d'écran sont sauvegardées dans le répertoire `screenshots` par défaut.

#### Options

- `--screenshots` ou `-s`: Spécifier un autre répertoire pour les captures d'écran

```bash
python test_mobile_compatibility.py http://localhost:8000 --screenshots /chemin/vers/dossier
```

## Test de taille maximale du QR code

### `test_qr_max_size.py`

Ce script vérifie la taille maximale des données pouvant être stockées dans un QR code tout en restant scannable.

#### Utilisation

```bash
python test_qr_max_size.py
```

Ce script va :
1. Générer des profils de tailles différentes
2. Créer les QR codes correspondants
3. Analyser la taille des données et la qualité du QR code
4. Produire un rapport sur la taille maximale recommandée