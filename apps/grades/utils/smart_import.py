import pandas as pd
import json
import xml.etree.ElementTree as ET
import os
from django.core.exceptions import ValidationError

def detect_file_format(file_path):
    """Détecte automatiquement le format du fichier."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.xlsx', '.xls']:
        return 'excel'
    elif ext == '.csv':
        return 'csv'
    elif ext == '.json':
        return 'json'
    elif ext == '.xml':
        return 'xml'
    else:
        # Analyse du contenu pour tenter une détection plus fine
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Lire les premiers 1024 octets
                
                if content.strip().startswith('{') and '}' in content:
                    return 'json'
                elif content.strip().startswith('<'):
                    return 'xml'
                elif ',' in content or ';' in content:
                    return 'csv'
        except:
            pass
            
    raise ValidationError(f"Format de fichier non reconnu pour {file_path}")

def read_file(file_path):
    """Lit le contenu du fichier selon son format détecté."""
    format_type = detect_file_format(file_path)
    
    if format_type == 'excel':
        return pd.read_excel(file_path)
    elif format_type == 'csv':
        # Détection automatique du séparateur
        with open(file_path, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
        
        if ',' in sample:
            sep = ','
        elif ';' in sample:
            sep = ';'
        elif '\t' in sample:
            sep = '\t'
        else:
            sep = ','
            
        return pd.read_csv(file_path, sep=sep)
    elif format_type == 'json':
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif format_type == 'xml':
        tree = ET.parse(file_path)
        root = tree.getroot()
        data = []
        
        # Conversion simple XML vers dictionnaire
        for child in root:
            item = {}
            for subchild in child:
                item[subchild.tag] = subchild.text
            data.append(item)
            
        return pd.DataFrame(data)
