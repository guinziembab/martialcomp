#!/usr/bin/env python3
"""
Script pour extraire tous les grades par discipline et identifier les caractères spéciaux corrompus.
Usage: python extract_grades_by_discipline.py
"""

import os
import sys
import django
import csv
import json
from datetime import datetime
import re

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import Discipline

def detect_special_characters(text):
    """Détecte les caractères spéciaux et corrompus dans le texte."""
    if not text:
        return []
    
    # Caractères suspects courants
    suspicious_chars = [
        'Ã', 'Â', 'À', 'Á', 'Ä', 'Æ', 'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì', 'Í', 'Î', 'Ï',
        'Ð', 'Ñ', 'Ò', 'Ó', 'Ô', 'Õ', 'Ö', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý', 'Þ', 'ß',
        'à', 'á', 'â', 'ã', 'ä', 'å', 'æ', 'ç', 'è', 'é', 'ê', 'ë', 'ì', 'í', 'î', 'ï',
        'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', 'ø', 'ù', 'ú', 'û', 'ü', 'ý', 'þ', 'ÿ',
        '€', '‚', 'ƒ', '„', '…', '†', '‡', 'ˆ', '‰', 'Š', '‹', 'Œ', 'Ž', ''', ''',
        '"', '"', '•', '–', '—', '˜', '™', 'š', '›', 'œ', 'ž', 'Ÿ'
    ]
    
    found_chars = []
    for char in suspicious_chars:
        if char in text:
            found_chars.append(char)
    
    # Détection des séquences de caractères d'encodage corrompu
    encoding_patterns = [
        r'Ã\w+',  # Séquences UTF-8 corrompues
        r'â\w+',  # Autres séquences
        r'\w*[À-ÿ]{2,}',  # Séquences de caractères accentués
    ]
    
    for pattern in encoding_patterns:
        matches = re.findall(pattern, text)
        if matches:
            found_chars.extend(matches)
    
    return list(set(found_chars))

def clean_text_suggestion(text):
    """Propose une version nettoyée du texte."""
    if not text:
        return text
    
    # Mappings de correction courants
    corrections = {
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ã ': 'à',
        'Ã§': 'ç',
        'Ã´': 'ô',
        'Ã®': 'î',
        'Ã¯': 'ï',
        'Ã¢': 'â',
        'Ã¹': 'ù',
        'Ã»': 'û',
        'Ã«': 'ë',
        'Ã¤': 'ä',
        'Ã¶': 'ö',
        'Ã¼': 'ü',
        'Ã±': 'ñ',
        'â€™': "'",
        'â€œ': '"',
        'â€': '"',
        'â€¦': '...',
        'â€"': '-',
        'â€¢': '•',
        # Ajoutez d'autres corrections selon vos besoins
    }
    
    cleaned = text
    for corrupt, correct in corrections.items():
        cleaned = cleaned.replace(corrupt, correct)
    
    return cleaned

def extract_grades_by_discipline():
    """Extrait tous les grades par discipline avec analyse des caractères spéciaux."""
    
    print("🔍 Extraction des grades par discipline...")
    print("=" * 60)
    
    # Données pour export
    grades_data = []
    corruption_summary = []
    
    # Récupération de toutes les disciplines (sans tri pour éviter les problèmes de colonnes)
    disciplines = Discipline.objects.all()
    
    for discipline in disciplines:
        print(f"\n📋 DISCIPLINE: {discipline.name}")
        print("-" * 40)
        
        # Grades de cette discipline
        grades = Grade.objects.filter(discipline=discipline).order_by('level', 'name')
        
        if not grades.exists():
            print("   ⚠️  Aucun grade trouvé")
            continue
        
        discipline_corrupted = False
        
        for grade in grades:
            # Analyse du nom du grade
            suspicious_chars = detect_special_characters(grade.name)
            color_suspicious = detect_special_characters(grade.color)
            
            is_corrupted = len(suspicious_chars) > 0 or len(color_suspicious) > 0
            
            if is_corrupted:
                discipline_corrupted = True
                
            # Affichage
            status = "🔴 CORROMPU" if is_corrupted else "✅ OK"
            print(f"   {status} | {grade.name} | {grade.color} | Niveau: {grade.level}")
            
            if suspicious_chars:
                print(f"        🚨 Caractères suspects dans le nom: {suspicious_chars}")
                print(f"        💡 Suggestion: {clean_text_suggestion(grade.name)}")
            
            if color_suspicious:
                print(f"        🚨 Caractères suspects dans la couleur: {color_suspicious}")
                print(f"        💡 Suggestion: {clean_text_suggestion(grade.color)}")
            
            # Stockage des données
            grade_data = {
                'discipline_id': discipline.id,
                'discipline_name': discipline.name,
                'grade_id': grade.id,
                'grade_name': grade.name,
                'grade_color': grade.color,
                'level': grade.level,
                'is_corrupted': is_corrupted,
                'suspicious_chars_name': suspicious_chars,
                'suspicious_chars_color': color_suspicious,
                'suggested_name': clean_text_suggestion(grade.name),
                'suggested_color': clean_text_suggestion(grade.color),
                'category_name': grade.category.name if grade.category else None,
                'is_active': grade.is_active,
                'is_dan_grade': grade.is_dan_grade,
            }
            grades_data.append(grade_data)
        
        # Résumé par discipline
        total_grades = grades.count()
        corrupted_grades = len([g for g in grades_data if g['discipline_id'] == discipline.id and g['is_corrupted']])
        
        corruption_summary.append({
            'discipline': discipline.name,
            'total_grades': total_grades,
            'corrupted_grades': corrupted_grades,
            'corruption_rate': (corrupted_grades / total_grades * 100) if total_grades > 0 else 0
        })
        
        print(f"   📊 Total: {total_grades} grades | Corrompus: {corrupted_grades}")
    
    # Génération des fichiers de sortie
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Fichier CSV détaillé
    csv_filename = f"grades_analysis_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['discipline_name', 'grade_name', 'grade_color', 'level', 'is_corrupted', 
                     'suspicious_chars_name', 'suspicious_chars_color', 'suggested_name', 
                     'suggested_color', 'category_name', 'is_active', 'is_dan_grade']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for grade in grades_data:
            writer.writerow({
                'discipline_name': grade['discipline_name'],
                'grade_name': grade['grade_name'],
                'grade_color': grade['grade_color'],
                'level': grade['level'],
                'is_corrupted': grade['is_corrupted'],
                'suspicious_chars_name': ', '.join(grade['suspicious_chars_name']),
                'suspicious_chars_color': ', '.join(grade['suspicious_chars_color']),
                'suggested_name': grade['suggested_name'],
                'suggested_color': grade['suggested_color'],
                'category_name': grade['category_name'],
                'is_active': grade['is_active'],
                'is_dan_grade': grade['is_dan_grade'],
            })
    
    # 2. Fichier JSON complet
    json_filename = f"grades_data_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump({
            'extraction_date': datetime.now().isoformat(),
            'total_disciplines': len(disciplines),
            'total_grades': len(grades_data),
            'corrupted_grades': len([g for g in grades_data if g['is_corrupted']]),
            'corruption_summary': corruption_summary,
            'grades_data': grades_data
        }, jsonfile, indent=2, ensure_ascii=False)
    
    # 3. Rapport de corruption
    report_filename = f"corruption_report_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as reportfile:
        reportfile.write("RAPPORT D'ANALYSE DES GRADES - CARACTÈRES CORROMPUS\n")
        reportfile.write("=" * 60 + "\n\n")
        reportfile.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        reportfile.write("RÉSUMÉ PAR DISCIPLINE:\n")
        reportfile.write("-" * 30 + "\n")
        for summary in corruption_summary:
            reportfile.write(f"• {summary['discipline']}: {summary['corrupted_grades']}/{summary['total_grades']} grades corrompus ({summary['corruption_rate']:.1f}%)\n")
        
        reportfile.write("\n\nGRADES CORROMPUS DÉTAILLÉS:\n")
        reportfile.write("-" * 30 + "\n")
        for grade in grades_data:
            if grade['is_corrupted']:
                reportfile.write(f"\n🔴 {grade['discipline_name']} - {grade['grade_name']}\n")
                if grade['suspicious_chars_name']:
                    reportfile.write(f"   Caractères suspects (nom): {', '.join(grade['suspicious_chars_name'])}\n")
                    reportfile.write(f"   Suggestion: {grade['suggested_name']}\n")
                if grade['suspicious_chars_color']:
                    reportfile.write(f"   Caractères suspects (couleur): {', '.join(grade['suspicious_chars_color'])}\n")
                    reportfile.write(f"   Suggestion couleur: {grade['suggested_color']}\n")
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DE L'EXTRACTION")
    print("=" * 60)
    print(f"📊 Total disciplines analysées: {len(disciplines)}")
    print(f"📊 Total grades analysés: {len(grades_data)}")
    print(f"🔴 Grades avec caractères corrompus: {len([g for g in grades_data if g['is_corrupted']])}")
    print(f"\n📁 Fichiers générés:")
    print(f"   • {csv_filename} (analyse détaillée CSV)")
    print(f"   • {json_filename} (données complètes JSON)")
    print(f"   • {report_filename} (rapport de corruption)")
    
    return grades_data, corruption_summary

if __name__ == "__main__":
    try:
        from grades.models import Grade, GradeCategory  # Import local pour éviter les problèmes d'ordre d'import
        extract_grades_by_discipline()
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
        import traceback
        traceback.print_exc()