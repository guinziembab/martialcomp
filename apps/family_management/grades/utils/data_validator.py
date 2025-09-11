import pandas as pd
import re
from datetime import datetime, date
from typing import Dict, List, Tuple, Any
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

class DataValidator:
    """Validateur intelligent de données avec scoring automatique."""
    
    def __init__(self):
        self.validation_rules = {
            'first_name': self._validate_name,
            'last_name': self._validate_name,
            'email': self._validate_email,
            'phone': self._validate_phone,
            'birth_date': self._validate_birth_date,
            'grade': self._validate_grade,
            'discipline': self._validate_discipline,
            'club': self._validate_club,
            'license_number': self._validate_license
        }
        
        # Grades valides pour différentes disciplines
        self.valid_grades = {
            'karate': [
                'blanche', 'jaune', 'orange', 'verte', 'bleue', 'marron', 'noire',
                '1er kyu', '2ème kyu', '3ème kyu', '4ème kyu', '5ème kyu',
                '1er dan', '2ème dan', '3ème dan', '4ème dan', '5ème dan'
            ],
            'judo': [
                'blanche', 'jaune', 'orange', 'verte', 'bleue', 'marron', 'noire',
                'shodan', 'nidan', 'sandan', 'yondan', 'godan'
            ],
            'taekwondo': [
                'blanche', 'jaune', 'orange', 'verte', 'bleue', 'rouge', 'noire',
                '1er poom', '2ème poom', '3ème poom',
                '1er dan', '2ème dan', '3ème dan', '4ème dan'
            ]
        }
        
        # Disciplines reconnues
        self.valid_disciplines = [
            'karate', 'judo', 'taekwondo', 'aikido', 'kung fu', 'krav maga',
            'capoeira', 'jiu-jitsu', 'muay thai', 'boxe', 'mma', 'tai chi'
        ]
    
    def validate_dataframe(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Valide un DataFrame complet selon le mapping de colonnes.
        
        Args:
            df: DataFrame Ã  valider
            column_mapping: Mapping {standard_column: input_column}
        
        Returns:
            Résultats de validation avec scores et erreurs
        """
        validation_results = {
            'overall_score': 0.0,
            'row_scores': [],
            'column_scores': {},
            'errors': [],
            'warnings': [],
            'statistics': {
                'total_rows': len(df),
                'valid_rows': 0,
                'warning_rows': 0,
                'error_rows': 0
            }
        }
        
        # Valider chaque colonne
        column_scores = {}
        for standard_col, input_col in column_mapping.items():
            if input_col in df.columns:
                col_result = self._validate_column(df[input_col], standard_col, input_col)
                column_scores[standard_col] = col_result
                validation_results['column_scores'][standard_col] = col_result
        
        # Valider chaque ligne
        for idx, row in df.iterrows():
            row_result = self._validate_row(row, column_mapping, idx)
            validation_results['row_scores'].append(row_result)
            
            # Compter les types de lignes
            if row_result['score'] >= 0.8:
                validation_results['statistics']['valid_rows'] += 1
            elif row_result['score'] >= 0.5:
                validation_results['statistics']['warning_rows'] += 1
            else:
                validation_results['statistics']['error_rows'] += 1
            
            # Collecter les erreurs et avertissements
            validation_results['errors'].extend(row_result['errors'])
            validation_results['warnings'].extend(row_result['warnings'])
        
        # Calculer le score global
        if validation_results['row_scores']:
            avg_row_score = sum(r['score'] for r in validation_results['row_scores']) / len(validation_results['row_scores'])
            avg_col_score = sum(c['score'] for c in column_scores.values()) / len(column_scores) if column_scores else 0
            validation_results['overall_score'] = (avg_row_score + avg_col_score) / 2
        
        return validation_results
    
    def _validate_column(self, series: pd.Series, standard_col: str, input_col: str) -> Dict[str, Any]:
        """Valide une colonne complète."""
        if standard_col not in self.validation_rules:
            return {
                'score': 0.5,
                'valid_count': 0,
                'total_count': len(series),
                'errors': [f"Type de colonne non reconnu: {standard_col}"]
            }
        
        validator = self.validation_rules[standard_col]
        valid_count = 0
        errors = []
        
        for idx, value in series.items():
            if pd.isna(value):
                continue
            
            is_valid, error_msg = validator(value)
            if is_valid:
                valid_count += 1
            elif error_msg:
                errors.append(f"Ligne {idx + 1}: {error_msg}")
        
        non_null_count = series.notna().sum()
        score = valid_count / non_null_count if non_null_count > 0 else 0
        
        return {
            'score': score,
            'valid_count': valid_count,
            'total_count': len(series),
            'non_null_count': non_null_count,
            'errors': errors[:10]  # Limiter Ã  10 erreurs par colonne
        }
    
    def _validate_row(self, row: pd.Series, column_mapping: Dict[str, str], row_idx: int) -> Dict[str, Any]:
        """Valide une ligne complète."""
        row_errors = []
        row_warnings = []
        valid_fields = 0
        total_fields = 0
        
        for standard_col, input_col in column_mapping.items():
            if input_col not in row.index:
                continue
            
            value = row[input_col]
            total_fields += 1
            
            if pd.isna(value):
                if standard_col in ['first_name', 'last_name', 'email']:  # Champs obligatoires
                    row_errors.append(f"Champ obligatoire manquant: {standard_col}")
                continue
            
            if standard_col in self.validation_rules:
                is_valid, error_msg = self.validation_rules[standard_col](value)
                if is_valid:
                    valid_fields += 1
                elif error_msg:
                    row_errors.append(f"{standard_col}: {error_msg}")
        
        # Validation croisée
        cross_validation = self._cross_validate_row(row, column_mapping)
        row_warnings.extend(cross_validation)
        
        score = valid_fields / total_fields if total_fields > 0 else 0
        
        return {
            'row_index': row_idx,
            'score': score,
            'valid_fields': valid_fields,
            'total_fields': total_fields,
            'errors': row_errors,
            'warnings': row_warnings
        }
    
    def _cross_validate_row(self, row: pd.Series, column_mapping: Dict[str, str]) -> List[str]:
        """Validation croisée entre les champs d'une ligne."""
        warnings = []
        
        # Vérifier cohérence nom/email
        if 'first_name' in column_mapping and 'last_name' in column_mapping and 'email' in column_mapping:
            first_name_col = column_mapping['first_name']
            last_name_col = column_mapping['last_name']
            email_col = column_mapping['email']
            
            if all(col in row.index and pd.notna(row[col]) for col in [first_name_col, last_name_col, email_col]):
                first_name = str(row[first_name_col]).lower()
                last_name = str(row[last_name_col]).lower()
                email = str(row[email_col]).lower()
                
                if first_name not in email and last_name not in email:
                    warnings.append("L'email ne semble pas correspondre au nom/prénom")
        
        # Vérifier cohérence grade/discipline
        if 'grade' in column_mapping and 'discipline' in column_mapping:
            grade_col = column_mapping['grade']
            discipline_col = column_mapping['discipline']
            
            if grade_col in row.index and discipline_col in row.index:
                grade = str(row[grade_col]).lower() if pd.notna(row[grade_col]) else ""
                discipline = str(row[discipline_col]).lower() if pd.notna(row[discipline_col]) else ""
                
                if grade and discipline:
                    discipline_key = self._find_discipline_key(discipline)
                    if discipline_key and discipline_key in self.valid_grades:
                        valid_grades = [g.lower() for g in self.valid_grades[discipline_key]]
                        if grade not in valid_grades:
                            warnings.append(f"Grade '{grade}' inhabituel pour la discipline '{discipline}'")
        
        return warnings
    
    def _validate_name(self, value: Any) -> Tuple[bool, str]:
        """Valide un nom ou prénom."""
        if not isinstance(value, str):
            return False, "Doit Ãªtre une chaÃ®ne de caractères"
        
        value = value.strip()
        if len(value) < 2:
            return False, "Trop court (minimum 2 caractères)"
        
        if len(value) > 50:
            return False, "Trop long (maximum 50 caractères)"
        
        # Accepter lettres, espaces, tirets et apostrophes
        if not re.match(r"^[a-zA-ZÃ€-Ã¿\s\-']+$", value):
            return False, "Caractères non autorisés"
        
        return True, ""
    
    def _validate_email(self, value: Any) -> Tuple[bool, str]:
        """Valide une adresse email."""
        if not isinstance(value, str):
            return False, "Doit Ãªtre une chaÃ®ne de caractères"
        
        try:
            validate_email(value.strip())
            return True, ""
        except ValidationError:
            return False, "Format d'email invalide"
    
    def _validate_phone(self, value: Any) -> Tuple[bool, str]:
        """Valide un numéro de téléphone."""
        if not isinstance(value, str):
            value = str(value)
        
        # Nettoyer le numéro
        cleaned = re.sub(r'[^\d+]', '', value.strip())
        
        if len(cleaned) < 8:
            return False, "Numéro trop court"
        
        if len(cleaned) > 15:
            return False, "Numéro trop long"
        
        # Vérifier format international ou français
        if cleaned.startswith('+'):
            if len(cleaned) < 10:
                return False, "Format international invalide"
        elif cleaned.startswith('0'):
            if len(cleaned) != 10:
                return False, "Format français invalide (doit contenir 10 chiffres)"
        
        return True, ""
    
    def _validate_birth_date(self, value: Any) -> Tuple[bool, str]:
        """Valide une date de naissance."""
        try:
            if isinstance(value, (date, datetime)):
                birth_date = value if isinstance(value, date) else value.date()
            else:
                birth_date = pd.to_datetime(str(value)).date()
            
            today = date.today()
            
            if birth_date > today:
                return False, "Date de naissance future"
            
            age = today.year - birth_date.year
            if age > 120:
                return False, "Ã‚ge irréaliste (plus de 120 ans)"
            
            if age < 3:
                return False, "Ã‚ge trop jeune pour la pratique"
            
            return True, ""
            
        except (ValueError, TypeError):
            return False, "Format de date invalide"
    
    def _validate_grade(self, value: Any) -> Tuple[bool, str]:
        """Valide un grade."""
        if not isinstance(value, str):
            return False, "Doit Ãªtre une chaÃ®ne de caractères"
        
        value = value.strip().lower()
        
        # Vérifier dans tous les systèmes de grades
        all_grades = []
        for grades_list in self.valid_grades.values():
            all_grades.extend([g.lower() for g in grades_list])
        
        if value in all_grades:
            return True, ""
        
        # Vérifier formats alternatifs (dan, kyu, etc.)
        if re.match(r'^\d+e?r?\s*(dan|kyu|poom)$', value):
            return True, ""
        
        if re.match(r'^ceinture\s+[a-zA-ZÃ€-Ã¿]+$', value):
            return True, ""
        
        return False, "Grade non reconnu"
    
    def _validate_discipline(self, value: Any) -> Tuple[bool, str]:
        """Valide une discipline."""
        if not isinstance(value, str):
            return False, "Doit Ãªtre une chaÃ®ne de caractères"
        
        value = value.strip().lower()
        
        if value in self.valid_disciplines:
            return True, ""
        
        # Vérifier similarité avec disciplines connues
        for discipline in self.valid_disciplines:
            if discipline in value or value in discipline:
                return True, ""
        
        return False, "Discipline non reconnue"
    
    def _validate_club(self, value: Any) -> Tuple[bool, str]:
        """Valide un nom de club."""
        if not isinstance(value, str):
            return False, "Doit Ãªtre une chaÃ®ne de caractères"
        
        value = value.strip()
        if len(value) < 3:
            return False, "Nom de club trop court"
        
        if len(value) > 100:
            return False, "Nom de club trop long"
        
        return True, ""
    
    def _validate_license(self, value: Any) -> Tuple[bool, str]:
        """Valide un numéro de licence."""
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        if len(value) < 4:
            return False, "Numéro de licence trop court"
        
        if len(value) > 20:
            return False, "Numéro de licence trop long"
        
        return True, ""
    
    def _find_discipline_key(self, discipline_name: str) -> str:
        """Trouve la clé de discipline correspondante."""
        discipline_name = discipline_name.lower()
        
        for key in self.valid_grades.keys():
            if key in discipline_name or discipline_name in key:
                return key
        
        return ""
