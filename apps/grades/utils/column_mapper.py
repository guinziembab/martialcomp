from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple

class IntelligentColumnMapper:
    """Mappeur intelligent de colonnes utilisant TF-IDF et similarité cosinus."""
    
    def __init__(self):
        # Mapping des colonnes standard vers leurs variantes possibles
        self.standard_columns = {
            'first_name': [
                'prénom', 'prenom', 'firstname', 'first_name', 'nom_prenom', 
                'givenname', 'given_name', 'fname', 'forename'
            ],
            'last_name': [
                'nom', 'lastname', 'last_name', 'nom_famille', 'surname', 
                'family_name', 'lname', 'nom_de_famille'
            ],
            'email': [
                'email', 'e-mail', 'mail', 'adresse_email', 'courriel', 
                'electronic_mail', 'email_address'
            ],
            'phone': [
                'téléphone', 'telephone', 'phone', 'tel', 'mobile', 'portable',
                'numero_telephone', 'phone_number', 'cellphone'
            ],
            'birth_date': [
                'date_naissance', 'naissance', 'birth_date', 'birthdate', 
                'dob', 'date_of_birth', 'birthday', 'age'
            ],
            'grade': [
                'grade', 'niveau', 'ceinture', 'belt', 'rank', 'dan', 'kyu',
                'grade_actuel', 'current_grade', 'niveau_actuel'
            ],
            'discipline': [
                'discipline', 'art_martial', 'martial_art', 'sport', 'activity',
                'pratique', 'specialite', 'specialty'
            ],
            'club': [
                'club', 'dojo', 'école', 'ecole', 'school', 'gym', 'academy',
                'association', 'federation'
            ],
            'license_number': [
                'licence', 'license', 'numero_licence', 'license_number',
                'registration_number', 'membership_number', 'id_member'
            ]
        }
        
        # Initialiser le vectoriseur TF-IDF
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=None,
            lowercase=True,
            analyzer='word'
        )
    
    def preprocess_column_name(self, column_name: str) -> str:
        """Préprocesse le nom de colonne pour améliorer la correspondance."""
        # Convertir en minuscules
        column_name = column_name.lower()
        
        # Remplacer les caractères spéciaux par des espaces
        column_name = re.sub(r'[_\-\.\s]+', ' ', column_name)
        
        # Supprimer les accents
        accent_map = {
            'é': 'e', 'è': 'e', 'Ãª': 'e', 'Ã«': 'e',
            'Ã ': 'a', 'Ã¢': 'a', 'Ã¤': 'a',
            'Ã´': 'o', 'Ã¶': 'o',
            'Ã¹': 'u', 'Ã»': 'u', 'Ã¼': 'u',
            'Ã®': 'i', 'Ã¯': 'i',
            'ç': 'c'
        }
        
        for accented, plain in accent_map.items():
            column_name = column_name.replace(accented, plain)
        
        return column_name.strip()
    
    def calculate_similarity_score(self, input_column: str, standard_variants: List[str]) -> float:
        """Calcule le score de similarité entre une colonne et ses variantes standard."""
        processed_input = self.preprocess_column_name(input_column)
        processed_variants = [self.preprocess_column_name(variant) for variant in standard_variants]
        
        # Créer le corpus pour TF-IDF
        corpus = [processed_input] + processed_variants
        
        try:
            # Calculer les vecteurs TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Calculer la similarité cosinus entre l'input et chaque variante
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Retourner le score maximum
            return float(np.max(similarities))
        except:
            # Fallback: correspondance exacte ou partielle
            for variant in processed_variants:
                if processed_input == variant:
                    return 1.0
                elif processed_input in variant or variant in processed_input:
                    return 0.8
            
            return 0.0
    
    def map_columns(self, input_columns: List[str], confidence_threshold: float = 0.3) -> Dict[str, Tuple[str, float]]:
        """
        Mappe les colonnes d'entrée vers les colonnes standard.
        
        Args:
            input_columns: Liste des noms de colonnes d'entrée
            confidence_threshold: Seuil de confiance minimum pour accepter un mapping
        
        Returns:
            Dictionnaire {standard_column: (input_column, confidence_score)}
        """
        mapping_results = {}
        used_input_columns = set()
        
        # Pour chaque colonne standard
        for standard_col, variants in self.standard_columns.items():
            best_match = None
            best_score = 0.0
            
            # Tester chaque colonne d'entrée
            for input_col in input_columns:
                if input_col in used_input_columns:
                    continue
                
                score = self.calculate_similarity_score(input_col, variants)
                
                if score > best_score and score >= confidence_threshold:
                    best_score = score
                    best_match = input_col
            
            # Si on a trouvé une correspondance acceptable
            if best_match:
                mapping_results[standard_col] = (best_match, best_score)
                used_input_columns.add(best_match)
        
        return mapping_results
    
    def suggest_mappings(self, dataframe: pd.DataFrame) -> Dict[str, Dict]:
        """
        Suggère des mappings pour un DataFrame avec analyse des données.
        
        Returns:
            Dictionnaire avec les suggestions de mapping et statistiques
        """
        input_columns = list(dataframe.columns)
        mappings = self.map_columns(input_columns)
        
        # Analyser les données pour renforcer les suggestions
        enhanced_mappings = {}
        
        for standard_col, (input_col, score) in mappings.items():
            column_data = dataframe[input_col].dropna()
            
            # Analyse spécifique par type de colonne
            data_analysis = self._analyze_column_data(standard_col, column_data)
            
            # Ajuster le score basé sur l'analyse des données
            adjusted_score = min(score + data_analysis['confidence_boost'], 1.0)
            
            enhanced_mappings[standard_col] = {
                'input_column': input_col,
                'confidence_score': adjusted_score,
                'original_score': score,
                'data_analysis': data_analysis,
                'sample_values': column_data.head(3).tolist()
            }
        
        # Identifier les colonnes non mappées
        unmapped_columns = [col for col in input_columns if col not in [m['input_column'] for m in enhanced_mappings.values()]]
        
        return {
            'mappings': enhanced_mappings,
            'unmapped_columns': unmapped_columns,
            'total_columns': len(input_columns),
            'mapped_columns': len(enhanced_mappings)
        }
    
    def _analyze_column_data(self, standard_col: str, data: pd.Series) -> Dict:
        """Analyse les données d'une colonne pour valider le mapping."""
        analysis = {
            'confidence_boost': 0.0,
            'data_type': str(data.dtype),
            'sample_count': len(data),
            'validation_notes': []
        }
        
        if len(data) == 0:
            return analysis
        
        # Analyse spécifique par type de colonne
        if standard_col == 'email':
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            valid_emails = data.astype(str).apply(lambda x: bool(email_pattern.match(x))).sum()
            email_ratio = valid_emails / len(data)
            
            if email_ratio > 0.8:
                analysis['confidence_boost'] = 0.3
                analysis['validation_notes'].append(f"{email_ratio:.1%} d'emails valides")
            elif email_ratio > 0.5:
                analysis['confidence_boost'] = 0.1
                analysis['validation_notes'].append(f"Quelques emails valides ({email_ratio:.1%})")
        
        elif standard_col == 'phone':
            # Détecter les numéros de téléphone
            phone_pattern = re.compile(r'[\+]?[\d\s\-\(\)\.]{8,}')
            valid_phones = data.astype(str).apply(lambda x: bool(phone_pattern.match(x))).sum()
            phone_ratio = valid_phones / len(data)
            
            if phone_ratio > 0.7:
                analysis['confidence_boost'] = 0.2
                analysis['validation_notes'].append(f"{phone_ratio:.1%} de numéros valides")
        
        elif standard_col == 'birth_date':
            # Essayer de parser les dates
            try:
                parsed_dates = pd.to_datetime(data, errors='coerce').notna().sum()
                date_ratio = parsed_dates / len(data)
                
                if date_ratio > 0.8:
                    analysis['confidence_boost'] = 0.3
                    analysis['validation_notes'].append(f"{date_ratio:.1%} de dates valides")
                elif date_ratio > 0.5:
                    analysis['confidence_boost'] = 0.1
                    analysis['validation_notes'].append(f"Quelques dates valides ({date_ratio:.1%})")
            except:
                pass
        
        elif standard_col in ['first_name', 'last_name']:
            # Vérifier que ce sont des chaÃ®nes de caractères alphabétiques
            alpha_ratio = data.astype(str).apply(lambda x: x.replace(' ', '').replace('-', '').isalpha()).sum() / len(data)
            
            if alpha_ratio > 0.8:
                analysis['confidence_boost'] = 0.2
                analysis['validation_notes'].append(f"{alpha_ratio:.1%} de noms valides")
        
        return analysis
