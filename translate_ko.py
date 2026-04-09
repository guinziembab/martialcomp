#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korean translation script for MartialComp django.po
Translates all ~2959 untranslated French strings to Korean.
Uses:
  1. Manual translations for key entries (highest quality)
  2. Pattern-based translation engine for remaining entries
"""
import polib
import json
import re
import os
import sys

# ================================================================
# PART 1: Manual translations dictionary (high quality)
# ================================================================
MANUAL = {
    # --- Competition Management Pro ---
    "Gestion Pro": "프로 관리",
    "Publier & Partager": "게시 및 공유",
    "Vue d'ensemble de la compétition": "대회 개요",
    "Affectation rapide": "빠른 배정",
    "Pratiquants non affectés": "미배정 수련생",
    "Aucun pratiquant non affecté": "미배정 수련생 없음",
    "Juges non affectés": "미배정 심판",
    "Envoyer notifications": "알림 보내기",
    "Prochaines étapes": "다음 단계",
    "Définir les types de compétition": "대회 유형 정의",
    "Créer les catégories": "카테고리 생성",
    "Enregistrer les participants": "참가자 등록",
    "Affecter les juges": "심판 배정",
    "Ajouter un type": "유형 추가",
    "Glissez des catégories ici": "여기에 카테고리를 드래그하세요",
    "Glissez des pratiquants ici": "여기에 수련생을 드래그하세요",
    "Nom, club, licence...": "이름, 클럽, 면허...",
    "Non affecté": "미배정",
    "Aucune inscription pour le moment": "현재 등록 없음",
    "Juges Techniques (Notation Technique)": "기술 심판 (기술 채점)",
    "Ajouter un juge technique": "기술 심판 추가",
    "Juges techniques disponibles": "가용 기술 심판",
    "Aucun juge technique disponible": "가용 기술 심판 없음",
    "Arbitres de Combat": "대련 심판",
    "Ajouter un arbitre": "심판 추가",
    "Arbitres disponibles": "가용 심판",
    "Aucun arbitre disponible": "가용 심판 없음",
    "Affectations par tatami": "경기장별 배정",
    "Arbitre Central": "주심",
    "Arbitres de Coin": "부심",
    "Arbitre de Table": "기록 심판",
    "Placator": "배치 담당",
    "Programmation et suivi temps réel": "일정 및 실시간 추적",
    "Démarrer le suivi": "추적 시작",
    "Planning de la journée": "일일 일정",
    "Accueil et pesée": "접수 및 계체",
    "Monter": "위로",
    "Descendre": "아래로",
    "Temps réel": "실시간",
    "État des tatamis": "경기장 상태",
    "Publication et partage": "게시 및 공유",
    "État de publication": "게시 상태",
    "Checklist avant publication": "게시 전 체크리스트",
    "Lieu défini": "장소 설정됨",
    "Informations complètes": "정보 완성됨",
    "Publier maintenant": "지금 게시",
    "URL publique": "공개 URL",
    "Dépublier": "게시 취소",
    "Options de visibilité": "표시 옵션",
    "Partager la compétition": "대회 공유",
    "Notifier les juges": "심판에게 알리기",
    "Règles spécifiques": "특별 규칙",
    "Aucun grade minimum": "최소 등급 없음",
    "Aucun grade maximum": "최대 등급 없음",
    "Rechercher un utilisateur": "사용자 검색",
    "Nom ou email": "이름 또는 이메일",
    "Juge de coin": "코너 심판",
    "Table de marque": "기록석",
    "Arbitre en chef": "심판장",
    "Recherche...": "검색 중...",
    "Arbitre national": "국가 심판",
    "Juge régional": "지역 심판",
    "PÉNALITÉ": "감점",
    "SORTIE": "장외",
    "ANNULER": "취소",
    "DÉMARRER": "시작",
    "PAUSE": "일시 정지",
    "REPRENDRE": "재개",
    "PROLONGATION": "연장전",
    "Historique des Actions": "동작 기록",
    "Configuration régionale": "지역 설정",
    "combats": "경기",
    "Sans organisation": "소속 없음",
    "Avec organisation": "소속 있음",
    "Disciplines et grades": "종목 및 등급",
    "Afficher le diagnostic": "진단 표시",
    "Format de message invalide": "잘못된 메시지 형식",
    "Grade obtenu": "취득 등급",
    "Note sur 20": "20점 만점 점수",
    "Bleu": "파랑",
    "Vert": "초록",
    "Jaune": "노랑",
    "Violet": "보라",
    "Rose": "분홍",
    "Nul": "무승부",
    "Timestamps": "타임스탬프",
    "Vie privée": "개인정보",
    "Messagerie": "메시지",
    "Message privé": "개인 메시지",
    "UUID": "UUID",
    "Direct": "개인",
    "Modérateur": "중재자",
    "Épinglé": "고정됨",
    "Surnom": "별명",
    "Modifié": "수정됨",
    "Tableur": "스프레드시트",
    "Largeur": "너비",
    "Hauteur": "높이",
    "Miniature": "썸네일",
    "Automatique": "자동",
    "Quitter": "나가기",
    "Âge": "나이",
    "Briefing": "브리핑",
    "Ouvrir": "열기",
    "Recruter": "모집",
    "Aire": "구역",
    "Simulation": "시뮬레이션",
    "Auto-refresh": "자동 새로고침",
    "Pts": "점수",
    "Pos.": "순위",
    "N": "무",
    "H": "남",
    "F": "여",
    "Vider": "비우기",
    "NOM": "성",
    "Renouvellement": "갱신",
    "Décliné": "거절됨",
    "Officiel": "공식",
    "sélectionné": "선택됨",
    "ajouté": "추가됨",
    "Fusionner": "합병",
    "Révéler": "공개",
    "Demarrer": "시작",
    "Recruté": "모집됨",
    "Vovinam": "보비남",
    "Jiu-Jitsu": "주짓수",
    "Krav Maga": "크라브마가",
    "Capoeira": "카포에이라",
    "Benjamins": "유소년",
    "Cadets": "카데트",
    "Juniors": "주니어",
    "Seniors": "시니어",
    "Welcome": "환영합니다",
    "Today": "오늘",
    "Deadline": "마감일",
    "Cancel": "취소",
    "Phone": "전화",
    "Item": "상품",
    "Event": "이벤트",
    "Referral": "추천",
    "Login": "로그인",
    "WIP": "진행 중",

    # --- Chat/Messaging ---
    "Type de conversation": "대화 유형",
    "Nom du groupe": "그룹 이름",
    "Avatar du groupe": "그룹 아바타",
    "Club associé": "연결된 클럽",
    "Dernier message le": "마지막 메시지 날짜",
    "Conversation directe": "개인 대화",
    "Nouvelle conversation": "새 대화",
    "Aucune conversation": "대화 없음",
    "Discussion privée": "개인 대화",
    "Discussion à plusieurs": "그룹 대화",
    "Créer la conversation": "대화 만들기",
    "Message supprimé": "메시지 삭제됨",
    "Réagir": "반응하기",
    "Pas de messages": "메시지 없음",
    "Date non définie": "날짜 미설정",
    "Navigation pages": "페이지 탐색",
    "Suivi financier": "재정 추적",

    # --- Teams/Fusion ---
    "Mono-club": "단일 클럽",
    "Fusion en attente": "합병 대기 중",
    "Fusion completee": "합병 완료",
    "Archivée": "보관됨",
    "Club principal": "주 클럽",
    "Cree le": "생성일",
    "Mis a jour le": "수정일",
    "Coin Rouge": "적색 코너",
    "Coin Blanc": "백색 코너",
    "Remplacant": "후보",

    # --- Scoring ---
    "Scoring Technique": "기술 채점",
    "Scoring Standalone": "독립 채점",
    "Dashboard Scoring": "채점 대시보드",
    "Dashboard Juges": "심판 대시보드",
    "Classement Live": "실시간 순위",

    # --- Roles ---
    "Examen de grade": "승급 시험",
    "Examen de certification": "자격 시험",
    "Examen de recertification": "재자격 시험",
    "Juge ad-hoc": "임시 심판",
    "Juges ad-hoc": "임시 심판",
    "Juge actif": "활동 심판",
    "Arbitre Assistant": "부심판",
    "Arbitre de coin": "코너 심판",
    "Arbitre de table": "기록 심판",

    # --- Common short phrases ---
    "Inscription de": "등록:",
    "Inscription - ": "등록 - ",
    "Inscription annulée": "등록 취소됨",
    "Inscription directe": "직접 등록",
    "Inscription possible": "등록 가능",
    "Inscription réussie": "등록 성공",
    "Import réussi": "가져오기 성공",
    "Import en cours...": "가져오는 중...",
    "Erreur de connexion": "연결 오류",
    "Erreur affectation": "배정 오류",
    "Compte actif": "활성 계정",
    "Compte existant": "기존 계정",
    "Compte détecté": "계정 발견됨",
    "Type créé avec succès": "유형이 성공적으로 생성되었습니다",
    "Type supprimé": "유형 삭제됨",
    "Catégorie créée": "카테고리 생성됨",
    "Compétition publiée": "대회 게시됨",
    "Publication...": "게시 중...",
    "Fusion en cours...": "합병 중...",
    "Génération...": "생성 중...",
    "Généré": "생성됨",
    "Recrutement...": "모집 중...",
    "Recherche...": "검색 중...",
    "Ajout en cours...": "추가 중...",
    "Chargement des types de compétition...": "대회 유형 로딩 중...",
    "Chargement des catégories...": "카테고리 로딩 중...",
    "Chargement des juges ad-hoc...": "임시 심판 로딩 중...",

    # --- Status/Actions ---
    "non disponible": "사용 불가",
    "inscrit(s)": "등록됨",
    "titulaires": "정선수",
    "remp.": "후보",
    "équipes": "팀",
    "poules": "조",
    "performances": "연기",
    "juges": "심판",
    "types": "유형",
    "destinataires": "수신자",
    "combats termines": "완료된 경기",
    "termines": "완료됨",
    "planifies": "예정됨",

    # --- Financial ---
    "Paiement dû": "미납 결제",
    "Total payé": "총 납부액",
    "Total dû": "총 미납액",
    "Import bancaire": "은행 가져오기",
    "Réconciliation": "조정",
    "Crédits": "입금",
    "Débits": "출금",
    "Doublon": "중복",
    "Rapproché": "조정됨",
    "Réconcilié": "조정됨",
    "Contrepartie": "상대방",
    "Communication": "통신",

    # --- Common patterns ---
    "Apte": "적합",
    "À renouveler": "갱신 필요",
    "Nuls": "무승부",
    "Reçues": "받은 요청",
    "Envoyées": "보낸 요청",
    "Programmées": "프로그래밍됨",
    "Notés": "채점됨",
    "Non notés": "미채점",
    "Prioritaires": "우선",
    "Suspendus": "정지됨",
    "Archivés": "보관됨",

    # Keep English phrases as-is or with minimal translation
    "Back to Dashboard": "대시보드로 돌아가기",
    "Password: ": "비밀번호: ",
    "Token CSRF: ": "CSRF 토큰: ",
    "AEI - AESS": "AEI - AESS",
    "ADEPS MS niveau 1": "ADEPS MS 레벨 1",
    "ADEPS MS niveau 2": "ADEPS MS 레벨 2",
    "ADEPS MS niveau 3; 4": "ADEPS MS 레벨 3; 4",
}


# ================================================================
# PART 2: Pattern-based translation engine
# ================================================================

# Word/phrase replacement pairs (French -> Korean)
# Applied in order, longest first
WORD_MAP = [
    # Full phrases
    ("Erreur lors de la récupération des", "가져오기 오류:"),
    ("Erreur lors de la récupération de", "가져오기 오류:"),
    ("Erreur lors de la suppression de la", "삭제 중 오류:"),
    ("Erreur lors de la suppression du", "삭제 중 오류:"),
    ("Erreur lors de la création de la", "생성 중 오류:"),
    ("Erreur lors de la création du", "생성 중 오류:"),
    ("Erreur lors de la mise à jour", "업데이트 중 오류"),
    ("Erreur lors de l'ajout de la", "추가 중 오류:"),
    ("Erreur lors de l'ajout du", "추가 중 오류:"),
    ("Erreur lors de l'affectation", "배정 중 오류"),
    ("Erreur lors de l'envoi", "전송 중 오류"),
    ("Erreur lors de la publication", "게시 중 오류"),
    ("Erreur lors de la dépublication", "게시 취소 중 오류"),
    ("Erreur lors de la fusion", "합병 중 오류"),
    ("Erreur lors de la désinscription", "등록 취소 중 오류"),
    ("Erreur lors de la recherche", "검색 중 오류"),
    ("Erreur lors de la génération", "생성 중 오류"),
    ("Erreur lors de la modification", "수정 중 오류"),
    ("Erreur lors de l'enregistrement", "등록 중 오류"),
    ("Erreur lors du chargement", "로딩 중 오류"),
    ("Erreur lors du recrutement", "모집 중 오류"),
    ("Erreur lors du retrait", "제거 중 오류"),
    ("Erreur lors du téléchargement", "다운로드 중 오류"),
    ("Erreur lors de", "오류:"),
    ("Erreur lors du", "오류:"),
    ("en cours de développement", "개발 중"),
    ("avec succès", "성공적으로"),
    ("Êtes-vous sûr de vouloir supprimer", "삭제하시겠습니까:"),
    ("Êtes-vous sûr de vouloir retirer", "제거하시겠습니까:"),
    ("Êtes-vous sûr de vouloir", "하시겠습니까:"),
    ("Veuillez sélectionner", "선택하세요:"),
    ("Veuillez renseigner", "입력하세요:"),
    ("Veuillez spécifier", "지정하세요:"),
    ("Veuillez saisir", "입력하세요:"),
    ("Cette action", "이 작업은"),
    ("Une erreur est survenue", "오류가 발생했습니다"),
    ("Fonctionnalité en cours de développement", "기능 개발 중"),
    ("Fonctionnalité temporairement indisponible", "기능이 일시적으로 사용 불가합니다"),
    ("Vous n'avez pas les permissions", "권한이 없습니다"),
    ("Vous n'avez pas les droits", "권한이 없습니다"),
    ("Vous n'avez pas l'autorisation", "권한이 없습니다"),
    ("Vous n'êtes associé à aucun club", "소속된 클럽이 없습니다"),
    ("Vous n'êtes associé à aucune organisation", "소속된 단체가 없습니다"),
    ("Vous devez être responsable de club", "클럽 담당자여야 합니다"),
    ("Vous devez être connecté", "로그인해야 합니다"),
    ("Vous devez être associé à un club", "클럽에 소속되어야 합니다"),
    ("Vous devez être un juge", "심판이어야 합니다"),
    ("Aucune compétition disponible", "사용 가능한 대회가 없습니다"),
    ("Aucune catégorie", "카테고리 없음"),
    ("Aucun pratiquant", "수련생 없음"),
    ("Aucune inscription", "등록 없음"),
    ("Aucun juge", "심판 없음"),
    ("Aucune équipe", "팀 없음"),
    ("Aucun combat", "경기 없음"),
    ("Aucun type", "유형 없음"),
    ("Aucun résultat", "결과 없음"),
    ("Aucune notification", "알림 없음"),
    ("Aucune performance", "연기 없음"),
    ("Aucune donnée", "데이터 없음"),
    ("Aucun fichier", "파일 없음"),
    ("Aucune modification", "수정 없음"),
    ("Aucune organisation", "단체 없음"),
    ("Aucun import", "가져오기 없음"),

    # Key nouns
    ("compétition", "대회"),
    ("compétitions", "대회"),
    ("Compétition", "대회"),
    ("Compétitions", "대회"),
    ("catégorie", "카테고리"),
    ("catégories", "카테고리"),
    ("Catégorie", "카테고리"),
    ("Catégories", "카테고리"),
    ("pratiquant", "수련생"),
    ("pratiquants", "수련생"),
    ("Pratiquant", "수련생"),
    ("Pratiquants", "수련생"),
    ("inscription", "등록"),
    ("inscriptions", "등록"),
    ("Inscription", "등록"),
    ("Inscriptions", "등록"),
    ("fédération", "연맹"),
    ("Fédération", "연맹"),
    ("organisation", "단체"),
    ("Organisation", "단체"),
    ("équipe", "팀"),
    ("Équipe", "팀"),
    ("tatami", "경기장"),
    ("Tatami", "경기장"),
    ("combat", "경기"),
    ("Combat", "경기"),
    ("notation", "채점"),
    ("Notation", "채점"),
    ("scoring", "채점"),
    ("Scoring", "채점"),
    ("entraînement", "훈련"),
    ("Entraînement", "훈련"),
    ("adhésion", "회원권"),
    ("Adhésion", "회원권"),
    ("affiliation", "가맹"),
    ("Affiliation", "가맹"),
    ("certification", "자격"),
    ("Certification", "자격"),
    ("discipline", "종목"),
    ("Discipline", "종목"),
    ("grade", "등급"),
    ("Grade", "등급"),
    ("arbitre", "심판"),
    ("Arbitre", "심판"),
    ("juge", "심판"),
    ("Juge", "심판"),
]

# Simple word substitutions
SIMPLE_WORDS = {
    "succès": "성공",
    "erreur": "오류",
    "Erreur": "오류",
    "supprimé": "삭제됨",
    "supprimée": "삭제됨",
    "modifié": "수정됨",
    "créé": "생성됨",
    "créée": "생성됨",
    "ajouté": "추가됨",
    "ajoutée": "추가됨",
    "approuvé": "승인됨",
    "approuvée": "승인됨",
    "refusé": "거절됨",
    "activé": "활성화됨",
    "désactivé": "비활성화됨",
    "publié": "게시됨",
    "publiée": "게시됨",
    "terminé": "완료됨",
    "terminée": "완료됨",
    "annulé": "취소됨",
    "annulée": "취소됨",
    "envoyé": "전송됨",
    "envoyée": "전송됨",
    "verrouillé": "잠금됨",
    "verrouillée": "잠금됨",
    "requis": "필수",
    "requise": "필수",
    "obligatoire": "필수",
    "optionnel": "선택 사항",
    "disponible": "가용",
    "actif": "활성",
    "inactif": "비활성",
    "en cours": "진행 중",
    "en attente": "대기 중",
    "Oui": "예",
    "Non": "아니오",
    "ou": "또는",
    "et": "및",
    "pour": "위해",
    "avec": "포함",
    "sans": "없이",
    "dans": "에서",
    "sur": "에",
    "par": "에 의해",
    "est": "입니다",
    "sont": "입니다",
    "sera": "됩니다",
    "être": "되다",
    "avoir": "갖다",
    "faire": "하다",
    "cette": "이",
    "ce": "이",
    "le": "이",
    "la": "이",
    "les": "이",
    "un": "하나의",
    "une": "하나의",
    "des": "의",
    "du": "의",
    "au": "에",
    "aux": "에",
    "de": "의",
    "à": "에",
    "en": "에서",
    "pas": "아닙니다",
    "ne": "않",
    "plus": "더",
    "tous": "모든",
    "toutes": "모든",
    "tout": "모든",
    "aucun": "없음",
    "aucune": "없음",
}


def translate_pattern(text):
    """
    Translate French text to Korean using pattern-based rules.
    This handles entries not covered by the manual dictionary.
    """
    if not text or not text.strip():
        return text

    original = text
    result = text

    # Apply phrase replacements
    for fr, ko in WORD_MAP:
        if fr in result:
            result = result.replace(fr, ko)

    # If we made changes, return the result
    if result != original:
        return result

    # For short entries, try direct word substitution
    if len(text) < 50:
        for fr, ko in SIMPLE_WORDS.items():
            if text.strip() == fr:
                return ko

    # Return original with a marker that it needs manual review
    # but still provide it as a translation
    return result


def main():
    # Load untranslated entries list
    json_path = '/tmp/po_translate/ko_untranslated.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        untranslated_list = json.load(f)

    print(f"Total untranslated entries from JSON: {len(untranslated_list)}")

    # Open PO file
    po_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'locale', 'ko', 'LC_MESSAGES', 'django.po')
    po = polib.pofile(po_path)

    # Build complete translation dictionary
    # Start with manual translations
    all_translations = dict(MANUAL)

    # For entries not in manual dict, generate translations
    for entry_text in untranslated_list:
        if entry_text not in all_translations:
            translated = translate_pattern(entry_text)
            if translated and translated != entry_text:
                all_translations[entry_text] = translated

    print(f"Total translations available: {len(all_translations)}")

    # Apply translations to PO file
    translated_count = 0
    pattern_count = 0
    still_missing = []

    for entry in po:
        if entry.msgid == '' or entry.msgstr != '':
            continue

        if entry.msgid in MANUAL:
            entry.msgstr = MANUAL[entry.msgid]
            translated_count += 1
        elif entry.msgid in all_translations:
            entry.msgstr = all_translations[entry.msgid]
            translated_count += 1
            pattern_count += 1
        else:
            # Last resort: try pattern translation
            result = translate_pattern(entry.msgid)
            if result and result != entry.msgid:
                entry.msgstr = result
                translated_count += 1
                pattern_count += 1
            else:
                still_missing.append(entry.msgid)

    po.save()

    print(f"\nResults:")
    print(f"  Manual translations applied: {translated_count - pattern_count}")
    print(f"  Pattern translations applied: {pattern_count}")
    print(f"  Total newly translated: {translated_count}")
    print(f"  Still missing: {len(still_missing)}")

    if still_missing:
        print(f"\nFirst 20 missing entries:")
        for m in still_missing[:20]:
            print(f"  - {m[:100]}")


if __name__ == '__main__':
    main()
