import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import dedupe
from typing import List, Dict, Tuple, Any
import re
import unicodedata
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PractitionerDeduplicator:
    """Déduplicateur intelligent pour les pratiquants utilisant l'IA."""
    
    def __init__(self):
        # Initialiser le modèle de sentence transformers (léger et multilingue)
        try:
            self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            logger.warning(f"Impossible de charger sentence-transformers: {e}")
            self.sentence_model = None
        
        # Configuration pour dedupe
        self.dedupe_fields = [
            {'field': 'full_name', 'type': 'String'},
            {'field': 'email', 'type': 'Email', 'has missing': True},
            {'field': 'phone', 'type': 'String', 'has missing': True},
            {'field': 'birth_date', 'type': 'DateTime', 'has missing': True},
            {'field': 'club', 'type': 'String', 'has missing': True},
        ]
    
    def normalize_text(self, text: str) -> str:
        """Normalise le texte pour améliorer la comparaison."""
        if not isinstance(text, str):
            return ""
        
        # Convertir en minuscules
        text = text.lower().strip()
        
        # Supprimer les accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        # Nettoyer les caractères spéciaux
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def prepare_data_for_dedupe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Prépare les données pour la déduplication avec dedupe."""
        prepared_data = []
        
        for idx, row in df.iterrows():
            # Créer le nom complet
            first_name = str(row.get('first_name', '')).strip()
            last_name = str(row.get('last_name', '')).strip()
            full_name = f"{first_name} {last_name}".strip()
            
            # Normaliser les données
            record = {
                'id': idx,
                'full_name': self.normalize_text(full_name),
                'email': str(row.get('email', '')).lower().strip(),
                'phone': self.normalize_phone(str(row.get('phone', ''))),
                'birth_date': self.normalize_date(row.get('birth_date')),
                'club': self.normalize_text(str(row.get('club', ''))),
                'original_data': row.to_dict()
            }
            
            prepared_data.append((idx, record))
        
        return prepared_data
    
    def normalize_phone(self, phone: str) -> str:
        """Normalise un numéro de téléphone."""
        if not phone or phone == 'nan':
            return ""
        
        # Garder seulement les chiffres et le +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Normaliser format français
        if cleaned.startswith('0'):
            cleaned = '+33' + cleaned[1:]
        elif len(cleaned) == 9 and not cleaned.startswith('+'):
            cleaned = '+33' + cleaned
        
        return cleaned
    
    def normalize_date(self, date_val: Any) -> str:
        """Normalise une date."""
        if pd.isna(date_val):
            return ""
        
        try:
            if isinstance(date_val, str):
                parsed_date = pd.to_datetime(date_val)
            else:
                parsed_date = pd.to_datetime(str(date_val))
            
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return ""
    
    def find_duplicates_semantic(self, df: pd.DataFrame, threshold: float = 0.85) -> List[Dict[str, Any]]:
        """
        Trouve les doublons en utilisant la similarité sémantique.
        
        Args:
            df: DataFrame des pratiquants
            threshold: Seuil de similarité (0-1)
        
        Returns:
            Liste des groupes de doublons potentiels
        """
        if self.sentence_model is None:
            logger.warning("Sentence transformer non disponible, utilisation de la méthode de base")
            return self.find_duplicates_basic(df, threshold)
        
        duplicates = []
        
        # Créer les descriptions textuelles pour chaque personne
        descriptions = []
        for idx, row in df.iterrows():
            # Créer une description textuelle
            desc_parts = []
            
            if pd.notna(row.get('first_name')):
                desc_parts.append(f"prénom {row['first_name']}")
            if pd.notna(row.get('last_name')):
                desc_parts.append(f"nom {row['last_name']}")
            if pd.notna(row.get('email')):
                desc_parts.append(f"email {row['email']}")
            if pd.notna(row.get('club')):
                desc_parts.append(f"club {row['club']}")
            if pd.notna(row.get('birth_date')):
                desc_parts.append(f"né le {row['birth_date']}")
            
            description = " ".join(desc_parts)
            descriptions.append(description)
        
        try:
            # Encoder les descriptions
            embeddings = self.sentence_model.encode(descriptions)
            
            # Calculer la matrice de similarité
            similarity_matrix = cosine_similarity(embeddings)
            
            # Trouver les paires similaires
            processed_indices = set()
            
            for i in range(len(similarity_matrix)):
                if i in processed_indices:
                    continue
                
                similar_indices = []
                for j in range(i + 1, len(similarity_matrix)):
                    if j in processed_indices:
                        continue
                    
                    if similarity_matrix[i][j] >= threshold:
                        if not similar_indices:
                            similar_indices.append(i)
                        similar_indices.append(j)
                
                if similar_indices:
                    # Ajouter tous les indices similaires au groupe
                    group_data = []
                    for idx in similar_indices:
                        processed_indices.add(idx)
                        row_data = df.iloc[idx].to_dict()
                        row_data['original_index'] = idx
                        group_data.append(row_data)
                    
                    # Calculer les scores de similarité dans le groupe
                    similarity_scores = []
                    for k in range(len(similar_indices)):
                        for l in range(k + 1, len(similar_indices)):
                            score = similarity_matrix[similar_indices[k]][similar_indices[l]]
                            similarity_scores.append(score)
                    
                    avg_similarity = np.mean(similarity_scores) if similarity_scores else threshold
                    
                    duplicates.append({
                        'group_id': len(duplicates) + 1,
                        'similarity_score': float(avg_similarity),
                        'records': group_data,
                        'method': 'semantic'
                    })
        
        except Exception as e:
            logger.error(f"Erreur dans la déduplication sémantique: {e}")
            return self.find_duplicates_basic(df, threshold)
        
        return duplicates
    
    def find_duplicates_basic(self, df: pd.DataFrame, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Méthode de déduplication de base basée sur les correspondances exactes et fuzzy.
        """
        duplicates = []
        processed_indices = set()
        
        for i, row1 in df.iterrows():
            if i in processed_indices:
                continue
            
            similar_records = [row1.to_dict()]
            similar_records[0]['original_index'] = i
            similar_indices = {i}
            
            for j, row2 in df.iterrows():
                if j <= i or j in processed_indices:
                    continue
                
                similarity = self.calculate_record_similarity(row1, row2)
                
                if similarity >= threshold:
                    row2_dict = row2.to_dict()
                    row2_dict['original_index'] = j
                    similar_records.append(row2_dict)
                    similar_indices.add(j)
            
            if len(similar_records) > 1:
                processed_indices.update(similar_indices)
                
                duplicates.append({
                    'group_id': len(duplicates) + 1,
                    'similarity_score': threshold,
                    'records': similar_records,
                    'method': 'basic'
                })
        
        return duplicates
    
    def calculate_record_similarity(self, record1: pd.Series, record2: pd.Series) -> float:
        """Calcule la similarité entre deux enregistrements."""
        scores = []
        weights = {
            'name': 0.4,
            'email': 0.3,
            'phone': 0.2,
            'birth_date': 0.1
        }
        
        # Similarité des noms
        name1 = f"{record1.get('first_name', '')} {record1.get('last_name', '')}".strip().lower()
        name2 = f"{record2.get('first_name', '')} {record2.get('last_name', '')}".strip().lower()
        
        if name1 and name2:
            name_sim = self.fuzzy_string_similarity(name1, name2)
            scores.append(('name', name_sim))
        
        # Similarité des emails
        email1 = str(record1.get('email', '')).lower()
        email2 = str(record2.get('email', '')).lower()
        
        if email1 and email2 and email1 != 'nan' and email2 != 'nan':
            email_sim = 1.0 if email1 == email2 else 0.0
            scores.append(('email', email_sim))
        
        # Similarité des téléphones
        phone1 = self.normalize_phone(str(record1.get('phone', '')))
        phone2 = self.normalize_phone(str(record2.get('phone', '')))
        
        if phone1 and phone2:
            phone_sim = 1.0 if phone1 == phone2 else 0.0
            scores.append(('phone', phone_sim))
        
        # Similarité des dates de naissance
        date1 = self.normalize_date(record1.get('birth_date'))
        date2 = self.normalize_date(record2.get('birth_date'))
        
        if date1 and date2:
            date_sim = 1.0 if date1 == date2 else 0.0
            scores.append(('birth_date', date_sim))
        
        # Calculer la moyenne pondérée
        if not scores:
            return 0.0
        
        weighted_sum = sum(weights.get(field, 0.1) * score for field, score in scores)
        total_weight = sum(weights.get(field, 0.1) for field, _ in scores)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def fuzzy_string_similarity(self, str1: str, str2: str) -> float:
        """Calcule la similarité floue entre deux chaÃ®nes."""
        if not str1 or not str2:
            return 0.0
        
        if str1 == str2:
            return 1.0
        
        # Utiliser la distance de Levenshtein normalisée
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        max_len = max(len(str1), len(str2))
        distance = levenshtein_distance(str1, str2)
        
        return 1.0 - (distance / max_len)
    
    def merge_duplicates(self, duplicate_group: Dict[str, Any], merge_strategy: str = 'most_complete') -> Dict[str, Any]:
        """
        Fusionne un groupe de doublons selon la stratégie choisie.
        
        Args:
            duplicate_group: Groupe de doublons
            merge_strategy: 'most_complete', 'newest', 'manual'
        
        Returns:
            Enregistrement fusionné
        """
        records = duplicate_group['records']
        
        if merge_strategy == 'most_complete':
            # Choisir l'enregistrement avec le plus de champs remplis
            best_record = max(records, key=lambda r: sum(1 for v in r.values() if pd.notna(v) and str(v).strip()))
            
            # Compléter avec les données des autres enregistrements
            merged = best_record.copy()
            
            for record in records:
                for key, value in record.items():
                    if key == 'original_index':
                        continue
                    
                    # Si le champ est vide dans l'enregistrement principal, le remplir
                    if (pd.isna(merged.get(key)) or not str(merged.get(key)).strip()) and \
                       (pd.notna(value) and str(value).strip()):
                        merged[key] = value
            
            return merged
        
        elif merge_strategy == 'newest':
            # Retourner le premier enregistrement (supposé le plus récent)
            return records[0]
        
        else:  # manual
            # Retourner le groupe pour traitement manuel
            return duplicate_group
    
    def generate_merge_suggestions(self, duplicates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Génère des suggestions de fusion pour les doublons."""
        suggestions = []
        
        for group in duplicates:
            # Analyser le groupe pour faire des suggestions
            records = group['records']
            
            # Trouver l'enregistrement le plus complet
            completeness_scores = []
            for record in records:
                score = sum(1 for v in record.values() if pd.notna(v) and str(v).strip() and v != 'nan')
                completeness_scores.append(score)
            
            best_idx = completeness_scores.index(max(completeness_scores))
            suggested_master = records[best_idx]
            
            # Identifier les conflits
            conflicts = []
            for key in suggested_master.keys():
                if key == 'original_index':
                    continue
                
                values = [r.get(key) for r in records if pd.notna(r.get(key)) and str(r.get(key)).strip()]
                unique_values = list(set(str(v) for v in values))
                
                if len(unique_values) > 1:
                    conflicts.append({
                        'field': key,
                        'values': unique_values,
                        'suggested': str(suggested_master.get(key, ''))
                    })
            
            suggestion = {
                'group_id': group['group_id'],
                'similarity_score': group['similarity_score'],
                'suggested_master': suggested_master,
                'duplicates': [r for i, r in enumerate(records) if i != best_idx],
                'conflicts': conflicts,
                'auto_merge_safe': len(conflicts) == 0,
                'confidence': group['similarity_score'] * (1 - len(conflicts) * 0.1)
            }
            
            suggestions.append(suggestion)
        
        return suggestions
