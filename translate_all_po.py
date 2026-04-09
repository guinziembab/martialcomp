#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour traduire les textes manquants dans tous les fichiers PO.
Utilise un dictionnaire multilingue de traductions.
"""

import re
import os
from datetime import datetime

# Dictionnaire multilingue de traductions
# Format: { 'francais': {'en': 'english', 'de': 'german', 'es': 'spanish', ...} }
TRANSLATIONS = {
    # Navigation et interface
    "Accueil": {"en": "Home", "de": "Startseite", "es": "Inicio", "it": "Home", "pt": "Início", "ja": "ホーム", "zh": "首页", "ko": "홈", "ar": "الرئيسية", "ru": "Главная", "vi": "Trang chủ", "hi": "होम", "sw": "Nyumbani", "no": "Hjem", "am": "መነሻ", "yo": "Ile", "zu": "Ikhaya"},
    "Tableau de bord": {"en": "Dashboard", "de": "Dashboard", "es": "Panel de control", "it": "Cruscotto", "pt": "Painel", "ja": "ダッシュボード", "zh": "仪表板", "ko": "대시보드", "ar": "لوحة التحكم", "ru": "Панель управления", "vi": "Bảng điều khiển", "hi": "डैशबोर्ड", "sw": "Dashibodi", "no": "Dashbord", "am": "ዳሽቦርድ", "yo": "Dasibodu", "zu": "Ideshibhodi"},
    "Connexion": {"en": "Login", "de": "Anmeldung", "es": "Iniciar sesión", "it": "Accesso", "pt": "Login", "ja": "ログイン", "zh": "登录", "ko": "로그인", "ar": "تسجيل الدخول", "ru": "Вход", "vi": "Đăng nhập", "hi": "लॉगिन", "sw": "Ingia", "no": "Logg inn", "am": "ግባ", "yo": "Wọle", "zu": "Ngena"},
    "Déconnexion": {"en": "Logout", "de": "Abmelden", "es": "Cerrar sesión", "it": "Disconnetti", "pt": "Sair", "ja": "ログアウト", "zh": "登出", "ko": "로그아웃", "ar": "تسجيل الخروج", "ru": "Выход", "vi": "Đăng xuất", "hi": "लॉगआउट", "sw": "Ondoka", "no": "Logg ut", "am": "ውጣ", "yo": "Jade", "zu": "Phuma"},
    "Profil": {"en": "Profile", "de": "Profil", "es": "Perfil", "it": "Profilo", "pt": "Perfil", "ja": "プロフィール", "zh": "个人资料", "ko": "프로필", "ar": "الملف الشخصي", "ru": "Профиль", "vi": "Hồ sơ", "hi": "प्रोफ़ाइल", "sw": "Wasifu", "no": "Profil", "am": "መገለጫ", "yo": "Profaili", "zu": "Iphrofayela"},
    "Paramètres": {"en": "Settings", "de": "Einstellungen", "es": "Configuración", "it": "Impostazioni", "pt": "Configurações", "ja": "設定", "zh": "设置", "ko": "설정", "ar": "الإعدادات", "ru": "Настройки", "vi": "Cài đặt", "hi": "सेटिंग्स", "sw": "Mipangilio", "no": "Innstillinger", "am": "ቅንብሮች", "yo": "Eto", "zu": "Izilungiselelo"},
    "Rechercher": {"en": "Search", "de": "Suchen", "es": "Buscar", "it": "Cerca", "pt": "Pesquisar", "ja": "検索", "zh": "搜索", "ko": "검색", "ar": "بحث", "ru": "Поиск", "vi": "Tìm kiếm", "hi": "खोजें", "sw": "Tafuta", "no": "Søk", "am": "ፈልግ", "yo": "Wa", "zu": "Sesha"},
    "Recherche": {"en": "Search", "de": "Suche", "es": "Búsqueda", "it": "Ricerca", "pt": "Pesquisa", "ja": "検索", "zh": "搜索", "ko": "검색", "ar": "بحث", "ru": "Поиск", "vi": "Tìm kiếm", "hi": "खोज", "sw": "Utafutaji", "no": "Søk", "am": "ፍለጋ", "yo": "Wiwa", "zu": "Usesho"},
    "Aide": {"en": "Help", "de": "Hilfe", "es": "Ayuda", "it": "Aiuto", "pt": "Ajuda", "ja": "ヘルプ", "zh": "帮助", "ko": "도움말", "ar": "مساعدة", "ru": "Помощь", "vi": "Trợ giúp", "hi": "सहायता", "sw": "Msaada", "no": "Hjelp", "am": "እገዛ", "yo": "Iranlọwọ", "zu": "Usizo"},

    # Actions
    "Ajouter": {"en": "Add", "de": "Hinzufügen", "es": "Añadir", "it": "Aggiungi", "pt": "Adicionar", "ja": "追加", "zh": "添加", "ko": "추가", "ar": "إضافة", "ru": "Добавить", "vi": "Thêm", "hi": "जोड़ें", "sw": "Ongeza", "no": "Legg til", "am": "ጨምር", "yo": "Fi kun", "zu": "Engeza"},
    "Créer": {"en": "Create", "de": "Erstellen", "es": "Crear", "it": "Crea", "pt": "Criar", "ja": "作成", "zh": "创建", "ko": "생성", "ar": "إنشاء", "ru": "Создать", "vi": "Tạo", "hi": "बनाएं", "sw": "Unda", "no": "Opprett", "am": "ፍጠር", "yo": "Ṣẹda", "zu": "Dala"},
    "Modifier": {"en": "Edit", "de": "Bearbeiten", "es": "Editar", "it": "Modifica", "pt": "Editar", "ja": "編集", "zh": "编辑", "ko": "편집", "ar": "تعديل", "ru": "Редактировать", "vi": "Chỉnh sửa", "hi": "संपादित करें", "sw": "Hariri", "no": "Rediger", "am": "አርትዕ", "yo": "Ṣatunkọ", "zu": "Hlela"},
    "Supprimer": {"en": "Delete", "de": "Löschen", "es": "Eliminar", "it": "Elimina", "pt": "Excluir", "ja": "削除", "zh": "删除", "ko": "삭제", "ar": "حذف", "ru": "Удалить", "vi": "Xóa", "hi": "हटाएं", "sw": "Futa", "no": "Slett", "am": "ሰርዝ", "yo": "Paarẹ", "zu": "Susa"},
    "Enregistrer": {"en": "Save", "de": "Speichern", "es": "Guardar", "it": "Salva", "pt": "Salvar", "ja": "保存", "zh": "保存", "ko": "저장", "ar": "حفظ", "ru": "Сохранить", "vi": "Lưu", "hi": "सहेजें", "sw": "Hifadhi", "no": "Lagre", "am": "አስቀምጥ", "yo": "Fi pamọ", "zu": "Gcina"},
    "Annuler": {"en": "Cancel", "de": "Abbrechen", "es": "Cancelar", "it": "Annulla", "pt": "Cancelar", "ja": "キャンセル", "zh": "取消", "ko": "취소", "ar": "إلغاء", "ru": "Отмена", "vi": "Hủy", "hi": "रद्द करें", "sw": "Ghairi", "no": "Avbryt", "am": "ሰርዝ", "yo": "Fagilee", "zu": "Khansela"},
    "Valider": {"en": "Validate", "de": "Bestätigen", "es": "Validar", "it": "Convalida", "pt": "Validar", "ja": "検証", "zh": "验证", "ko": "확인", "ar": "تأكيد", "ru": "Подтвердить", "vi": "Xác nhận", "hi": "मान्य करें", "sw": "Thibitisha", "no": "Bekreft", "am": "አረጋግጥ", "yo": "Fọwọsi", "zu": "Qinisekisa"},
    "Confirmer": {"en": "Confirm", "de": "Bestätigen", "es": "Confirmar", "it": "Conferma", "pt": "Confirmar", "ja": "確認", "zh": "确认", "ko": "확인", "ar": "تأكيد", "ru": "Подтвердить", "vi": "Xác nhận", "hi": "पुष्टि करें", "sw": "Thibitisha", "no": "Bekreft", "am": "አረጋግጥ", "yo": "Jẹrisi", "zu": "Qinisekisa"},
    "Fermer": {"en": "Close", "de": "Schließen", "es": "Cerrar", "it": "Chiudi", "pt": "Fechar", "ja": "閉じる", "zh": "关闭", "ko": "닫기", "ar": "إغلاق", "ru": "Закрыть", "vi": "Đóng", "hi": "बंद करें", "sw": "Funga", "no": "Lukk", "am": "ዝጋ", "yo": "Pa", "zu": "Vala"},
    "Ouvrir": {"en": "Open", "de": "Öffnen", "es": "Abrir", "it": "Apri", "pt": "Abrir", "ja": "開く", "zh": "打开", "ko": "열기", "ar": "فتح", "ru": "Открыть", "vi": "Mở", "hi": "खोलें", "sw": "Fungua", "no": "Åpne", "am": "ክፈት", "yo": "Ṣii", "zu": "Vula"},
    "Voir": {"en": "View", "de": "Ansehen", "es": "Ver", "it": "Visualizza", "pt": "Ver", "ja": "表示", "zh": "查看", "ko": "보기", "ar": "عرض", "ru": "Просмотр", "vi": "Xem", "hi": "देखें", "sw": "Tazama", "no": "Vis", "am": "ተመልከት", "yo": "Wo", "zu": "Buka"},
    "Retour": {"en": "Back", "de": "Zurück", "es": "Volver", "it": "Indietro", "pt": "Voltar", "ja": "戻る", "zh": "返回", "ko": "뒤로", "ar": "رجوع", "ru": "Назад", "vi": "Quay lại", "hi": "वापस", "sw": "Rudi", "no": "Tilbake", "am": "ተመለስ", "yo": "Pada", "zu": "Emuva"},
    "Suivant": {"en": "Next", "de": "Weiter", "es": "Siguiente", "it": "Avanti", "pt": "Próximo", "ja": "次へ", "zh": "下一步", "ko": "다음", "ar": "التالي", "ru": "Далее", "vi": "Tiếp theo", "hi": "अगला", "sw": "Ifuatayo", "no": "Neste", "am": "ቀጣይ", "yo": "Tẹle", "zu": "Okulandelayo"},
    "Précédent": {"en": "Previous", "de": "Zurück", "es": "Anterior", "it": "Precedente", "pt": "Anterior", "ja": "前へ", "zh": "上一步", "ko": "이전", "ar": "السابق", "ru": "Назад", "vi": "Trước", "hi": "पिछला", "sw": "Iliyotangulia", "no": "Forrige", "am": "ያለፈው", "yo": "Tẹlẹ", "zu": "Okwedlule"},
    "Télécharger": {"en": "Download", "de": "Herunterladen", "es": "Descargar", "it": "Scarica", "pt": "Baixar", "ja": "ダウンロード", "zh": "下载", "ko": "다운로드", "ar": "تحميل", "ru": "Скачать", "vi": "Tải xuống", "hi": "डाउनलोड", "sw": "Pakua", "no": "Last ned", "am": "አውርድ", "yo": "Gba silẹ", "zu": "Landa"},
    "Importer": {"en": "Import", "de": "Importieren", "es": "Importar", "it": "Importa", "pt": "Importar", "ja": "インポート", "zh": "导入", "ko": "가져오기", "ar": "استيراد", "ru": "Импорт", "vi": "Nhập", "hi": "आयात", "sw": "Ingiza", "no": "Importer", "am": "አስመጣ", "yo": "Gbe wọle", "zu": "Ngenisa"},
    "Exporter": {"en": "Export", "de": "Exportieren", "es": "Exportar", "it": "Esporta", "pt": "Exportar", "ja": "エクスポート", "zh": "导出", "ko": "내보내기", "ar": "تصدير", "ru": "Экспорт", "vi": "Xuất", "hi": "निर्यात", "sw": "Hamisha", "no": "Eksporter", "am": "ላክ", "yo": "Gbe jade", "zu": "Thumela"},
    "Imprimer": {"en": "Print", "de": "Drucken", "es": "Imprimir", "it": "Stampa", "pt": "Imprimir", "ja": "印刷", "zh": "打印", "ko": "인쇄", "ar": "طباعة", "ru": "Печать", "vi": "In", "hi": "प्रिंट", "sw": "Chapisha", "no": "Skriv ut", "am": "አትም", "yo": "Tẹ jade", "zu": "Phrinta"},
    "Actualiser": {"en": "Refresh", "de": "Aktualisieren", "es": "Actualizar", "it": "Aggiorna", "pt": "Atualizar", "ja": "更新", "zh": "刷新", "ko": "새로고침", "ar": "تحديث", "ru": "Обновить", "vi": "Làm mới", "hi": "रिफ्रेश", "sw": "Onyesha upya", "no": "Oppdater", "am": "አድስ", "yo": "Tunse", "zu": "Vuselela"},

    # Compétitions
    "Compétition": {"en": "Competition", "de": "Wettbewerb", "es": "Competición", "it": "Competizione", "pt": "Competição", "ja": "大会", "zh": "比赛", "ko": "대회", "ar": "مسابقة", "ru": "Соревнование", "vi": "Cuộc thi", "hi": "प्रतियोगिता", "sw": "Mashindano", "no": "Konkurranse", "am": "ውድድር", "yo": "Idije", "zu": "Umncintiswano"},
    "Compétitions": {"en": "Competitions", "de": "Wettbewerbe", "es": "Competiciones", "it": "Competizioni", "pt": "Competições", "ja": "大会", "zh": "比赛", "ko": "대회", "ar": "مسابقات", "ru": "Соревнования", "vi": "Cuộc thi", "hi": "प्रतियोगिताएं", "sw": "Mashindano", "no": "Konkurranser", "am": "ውድድሮች", "yo": "Awọn idije", "zu": "Imincintiswano"},
    "Catégorie": {"en": "Category", "de": "Kategorie", "es": "Categoría", "it": "Categoria", "pt": "Categoria", "ja": "カテゴリー", "zh": "类别", "ko": "카테고리", "ar": "فئة", "ru": "Категория", "vi": "Danh mục", "hi": "श्रेणी", "sw": "Jamii", "no": "Kategori", "am": "ምድብ", "yo": "Ẹka", "zu": "Isigaba"},
    "Catégories": {"en": "Categories", "de": "Kategorien", "es": "Categorías", "it": "Categorie", "pt": "Categorias", "ja": "カテゴリー", "zh": "类别", "ko": "카테고리", "ar": "فئات", "ru": "Категории", "vi": "Danh mục", "hi": "श्रेणियां", "sw": "Makundi", "no": "Kategorier", "am": "ምድቦች", "yo": "Awọn ẹka", "zu": "Izigaba"},
    "Pratiquant": {"en": "Practitioner", "de": "Teilnehmer", "es": "Practicante", "it": "Praticante", "pt": "Praticante", "ja": "練習生", "zh": "练习者", "ko": "수련생", "ar": "ممارس", "ru": "Практикующий", "vi": "Người tập", "hi": "अभ्यासी", "sw": "Mfanyaji", "no": "Utøver", "am": "ተለማማጅ", "yo": "Olukọni", "zu": "Umzileli"},
    "Pratiquants": {"en": "Practitioners", "de": "Teilnehmer", "es": "Practicantes", "it": "Praticanti", "pt": "Praticantes", "ja": "練習生", "zh": "练习者", "ko": "수련생", "ar": "ممارسون", "ru": "Практикующие", "vi": "Người tập", "hi": "अभ्यासी", "sw": "Wafanyaji", "no": "Utøvere", "am": "ተለማማጆች", "yo": "Awọn olukọni", "zu": "Abazileli"},
    "Juge": {"en": "Judge", "de": "Richter", "es": "Juez", "it": "Giudice", "pt": "Juiz", "ja": "審判", "zh": "裁判", "ko": "심판", "ar": "حكم", "ru": "Судья", "vi": "Trọng tài", "hi": "न्यायाधीश", "sw": "Hakimu", "no": "Dommer", "am": "ዳኛ", "yo": "Onidajọ", "zu": "Ijaji"},
    "Juges": {"en": "Judges", "de": "Richter", "es": "Jueces", "it": "Giudici", "pt": "Juízes", "ja": "審判", "zh": "裁判", "ko": "심판", "ar": "حكام", "ru": "Судьи", "vi": "Trọng tài", "hi": "न्यायाधीश", "sw": "Mahakimu", "no": "Dommere", "am": "ዳኞች", "yo": "Awọn onidajọ", "zu": "Amajaji"},
    "Arbitre": {"en": "Referee", "de": "Schiedsrichter", "es": "Árbitro", "it": "Arbitro", "pt": "Árbitro", "ja": "審判員", "zh": "裁判员", "ko": "심판원", "ar": "حكم", "ru": "Рефери", "vi": "Trọng tài", "hi": "रेफरी", "sw": "Refa", "no": "Dommer", "am": "ዳኛ", "yo": "Adajọ", "zu": "Unrefereli"},
    "Équipe": {"en": "Team", "de": "Team", "es": "Equipo", "it": "Squadra", "pt": "Equipe", "ja": "チーム", "zh": "团队", "ko": "팀", "ar": "فريق", "ru": "Команда", "vi": "Đội", "hi": "टीम", "sw": "Timu", "no": "Lag", "am": "ቡድን", "yo": "Ẹgbẹ", "zu": "Ithimu"},
    "Équipes": {"en": "Teams", "de": "Teams", "es": "Equipos", "it": "Squadre", "pt": "Equipes", "ja": "チーム", "zh": "团队", "ko": "팀", "ar": "فرق", "ru": "Команды", "vi": "Đội", "hi": "टीमें", "sw": "Timu", "no": "Lag", "am": "ቡድኖች", "yo": "Awọn ẹgbẹ", "zu": "Amathimu"},
    "Résultat": {"en": "Result", "de": "Ergebnis", "es": "Resultado", "it": "Risultato", "pt": "Resultado", "ja": "結果", "zh": "结果", "ko": "결과", "ar": "نتيجة", "ru": "Результат", "vi": "Kết quả", "hi": "परिणाम", "sw": "Matokeo", "no": "Resultat", "am": "ውጤት", "yo": "Abajade", "zu": "Umphumela"},
    "Résultats": {"en": "Results", "de": "Ergebnisse", "es": "Resultados", "it": "Risultati", "pt": "Resultados", "ja": "結果", "zh": "结果", "ko": "결과", "ar": "نتائج", "ru": "Результаты", "vi": "Kết quả", "hi": "परिणाम", "sw": "Matokeo", "no": "Resultater", "am": "ውጤቶች", "yo": "Awọn abajade", "zu": "Imiphumela"},
    "Classement": {"en": "Ranking", "de": "Rangliste", "es": "Clasificación", "it": "Classifica", "pt": "Classificação", "ja": "ランキング", "zh": "排名", "ko": "순위", "ar": "تصنيف", "ru": "Рейтинг", "vi": "Xếp hạng", "hi": "रैंकिंग", "sw": "Nafasi", "no": "Rangering", "am": "ደረጃ", "yo": "Ipo", "zu": "Ukuhlela"},
    "Score": {"en": "Score", "de": "Punktzahl", "es": "Puntuación", "it": "Punteggio", "pt": "Pontuação", "ja": "スコア", "zh": "分数", "ko": "점수", "ar": "نقاط", "ru": "Счёт", "vi": "Điểm", "hi": "स्कोर", "sw": "Alama", "no": "Poeng", "am": "ነጥብ", "yo": "Dimegilio", "zu": "Amaphuzu"},
    "Point": {"en": "Point", "de": "Punkt", "es": "Punto", "it": "Punto", "pt": "Ponto", "ja": "ポイント", "zh": "分", "ko": "점", "ar": "نقطة", "ru": "Очко", "vi": "Điểm", "hi": "अंक", "sw": "Pointi", "no": "Poeng", "am": "ነጥብ", "yo": "Ojuami", "zu": "Iphuzu"},
    "Points": {"en": "Points", "de": "Punkte", "es": "Puntos", "it": "Punti", "pt": "Pontos", "ja": "ポイント", "zh": "分", "ko": "점", "ar": "نقاط", "ru": "Очки", "vi": "Điểm", "hi": "अंक", "sw": "Pointi", "no": "Poeng", "am": "ነጥቦች", "yo": "Awọn ojuami", "zu": "Amaphuzu"},
    "Victoire": {"en": "Victory", "de": "Sieg", "es": "Victoria", "it": "Vittoria", "pt": "Vitória", "ja": "勝利", "zh": "胜利", "ko": "승리", "ar": "فوز", "ru": "Победа", "vi": "Chiến thắng", "hi": "जीत", "sw": "Ushindi", "no": "Seier", "am": "ድል", "yo": "Iṣẹgun", "zu": "Ukunqoba"},
    "Défaite": {"en": "Defeat", "de": "Niederlage", "es": "Derrota", "it": "Sconfitta", "pt": "Derrota", "ja": "敗北", "zh": "失败", "ko": "패배", "ar": "هزيمة", "ru": "Поражение", "vi": "Thất bại", "hi": "हार", "sw": "Kushindwa", "no": "Tap", "am": "ሽንፈት", "yo": "Ijatil", "zu": "Ukwehlulwa"},
    "Podium": {"en": "Podium", "de": "Podium", "es": "Podio", "it": "Podio", "pt": "Pódio", "ja": "表彰台", "zh": "领奖台", "ko": "시상대", "ar": "منصة", "ru": "Подиум", "vi": "Bục", "hi": "पोडियम", "sw": "Jukwaa", "no": "Podium", "am": "መድረክ", "yo": "Pẹpẹ", "zu": "Ipulatifomu"},

    # Club et organisation
    "Club": {"en": "Club", "de": "Verein", "es": "Club", "it": "Club", "pt": "Clube", "ja": "クラブ", "zh": "俱乐部", "ko": "클럽", "ar": "نادي", "ru": "Клуб", "vi": "Câu lạc bộ", "hi": "क्लब", "sw": "Klabu", "no": "Klubb", "am": "ክለብ", "yo": "Ẹgbẹ", "zu": "Iklabhu"},
    "Organisation": {"en": "Organization", "de": "Organisation", "es": "Organización", "it": "Organizzazione", "pt": "Organização", "ja": "組織", "zh": "组织", "ko": "조직", "ar": "منظمة", "ru": "Организация", "vi": "Tổ chức", "hi": "संगठन", "sw": "Shirika", "no": "Organisasjon", "am": "ድርጅት", "yo": "Ẹgbẹ", "zu": "Inhlangano"},
    "Fédération": {"en": "Federation", "de": "Verband", "es": "Federación", "it": "Federazione", "pt": "Federação", "ja": "連盟", "zh": "联合会", "ko": "연맹", "ar": "اتحاد", "ru": "Федерация", "vi": "Liên đoàn", "hi": "संघ", "sw": "Shirikisho", "no": "Forbund", "am": "ፌዴሬሽን", "yo": "Ajọṣepọ", "zu": "Inhlangano"},
    "Membre": {"en": "Member", "de": "Mitglied", "es": "Miembro", "it": "Membro", "pt": "Membro", "ja": "会員", "zh": "成员", "ko": "회원", "ar": "عضو", "ru": "Член", "vi": "Thành viên", "hi": "सदस्य", "sw": "Mwanachama", "no": "Medlem", "am": "አባል", "yo": "Ọmọ ẹgbẹ", "zu": "Ilungu"},
    "Membres": {"en": "Members", "de": "Mitglieder", "es": "Miembros", "it": "Membri", "pt": "Membros", "ja": "会員", "zh": "成员", "ko": "회원", "ar": "أعضاء", "ru": "Члены", "vi": "Thành viên", "hi": "सदस्य", "sw": "Wanachama", "no": "Medlemmer", "am": "አባላት", "yo": "Awọn ọmọ ẹgbẹ", "zu": "Amalungu"},
    "Entraîneur": {"en": "Coach", "de": "Trainer", "es": "Entrenador", "it": "Allenatore", "pt": "Treinador", "ja": "コーチ", "zh": "教练", "ko": "코치", "ar": "مدرب", "ru": "Тренер", "vi": "Huấn luyện viên", "hi": "कोच", "sw": "Kocha", "no": "Trener", "am": "አሰልጣኝ", "yo": "Olukọni", "zu": "Umqeqeshi"},

    # Personnes
    "Nom": {"en": "Name", "de": "Name", "es": "Nombre", "it": "Nome", "pt": "Nome", "ja": "名前", "zh": "姓名", "ko": "이름", "ar": "اسم", "ru": "Имя", "vi": "Tên", "hi": "नाम", "sw": "Jina", "no": "Navn", "am": "ስም", "yo": "Orukọ", "zu": "Igama"},
    "Prénom": {"en": "First name", "de": "Vorname", "es": "Nombre", "it": "Nome", "pt": "Nome", "ja": "名", "zh": "名", "ko": "이름", "ar": "الاسم الأول", "ru": "Имя", "vi": "Tên", "hi": "पहला नाम", "sw": "Jina la kwanza", "no": "Fornavn", "am": "የመጀመሪያ ስም", "yo": "Orukọ akọkọ", "zu": "Igama lokuqala"},
    "Email": {"en": "Email", "de": "E-Mail", "es": "Correo electrónico", "it": "Email", "pt": "Email", "ja": "メール", "zh": "电子邮件", "ko": "이메일", "ar": "البريد الإلكتروني", "ru": "Электронная почта", "vi": "Email", "hi": "ईमेल", "sw": "Barua pepe", "no": "E-post", "am": "ኢሜይል", "yo": "Imeeli", "zu": "I-imeyili"},
    "Téléphone": {"en": "Phone", "de": "Telefon", "es": "Teléfono", "it": "Telefono", "pt": "Telefone", "ja": "電話", "zh": "电话", "ko": "전화", "ar": "هاتف", "ru": "Телефон", "vi": "Điện thoại", "hi": "फोन", "sw": "Simu", "no": "Telefon", "am": "ስልክ", "yo": "Foonu", "zu": "Ucingo"},
    "Adresse": {"en": "Address", "de": "Adresse", "es": "Dirección", "it": "Indirizzo", "pt": "Endereço", "ja": "住所", "zh": "地址", "ko": "주소", "ar": "عنوان", "ru": "Адрес", "vi": "Địa chỉ", "hi": "पता", "sw": "Anwani", "no": "Adresse", "am": "አድራሻ", "yo": "Adirẹsi", "zu": "Ikheli"},
    "Ville": {"en": "City", "de": "Stadt", "es": "Ciudad", "it": "Città", "pt": "Cidade", "ja": "市", "zh": "城市", "ko": "도시", "ar": "مدينة", "ru": "Город", "vi": "Thành phố", "hi": "शहर", "sw": "Mji", "no": "By", "am": "ከተማ", "yo": "Ilu", "zu": "Idolobha"},
    "Pays": {"en": "Country", "de": "Land", "es": "País", "it": "Paese", "pt": "País", "ja": "国", "zh": "国家", "ko": "국가", "ar": "بلد", "ru": "Страна", "vi": "Quốc gia", "hi": "देश", "sw": "Nchi", "no": "Land", "am": "ሀገር", "yo": "Orílẹ̀-èdè", "zu": "Izwe"},
    "Date de naissance": {"en": "Date of birth", "de": "Geburtsdatum", "es": "Fecha de nacimiento", "it": "Data di nascita", "pt": "Data de nascimento", "ja": "生年月日", "zh": "出生日期", "ko": "생년월일", "ar": "تاريخ الميلاد", "ru": "Дата рождения", "vi": "Ngày sinh", "hi": "जन्म तिथि", "sw": "Tarehe ya kuzaliwa", "no": "Fødselsdato", "am": "የልደት ቀን", "yo": "Ọjọ ibi", "zu": "Usuku lokuzalwa"},
    "Âge": {"en": "Age", "de": "Alter", "es": "Edad", "it": "Età", "pt": "Idade", "ja": "年齢", "zh": "年龄", "ko": "나이", "ar": "العمر", "ru": "Возраст", "vi": "Tuổi", "hi": "उम्र", "sw": "Umri", "no": "Alder", "am": "ዕድሜ", "yo": "Ọjọ ori", "zu": "Iminyaka"},
    "Sexe": {"en": "Gender", "de": "Geschlecht", "es": "Sexo", "it": "Sesso", "pt": "Sexo", "ja": "性別", "zh": "性别", "ko": "성별", "ar": "الجنس", "ru": "Пол", "vi": "Giới tính", "hi": "लिंग", "sw": "Jinsia", "no": "Kjønn", "am": "ጾታ", "yo": "Akọ tabi abo", "zu": "Ubulili"},
    "Masculin": {"en": "Male", "de": "Männlich", "es": "Masculino", "it": "Maschile", "pt": "Masculino", "ja": "男性", "zh": "男", "ko": "남성", "ar": "ذكر", "ru": "Мужской", "vi": "Nam", "hi": "पुरुष", "sw": "Kiume", "no": "Mann", "am": "ወንድ", "yo": "Ọkunrin", "zu": "Owesilisa"},
    "Féminin": {"en": "Female", "de": "Weiblich", "es": "Femenino", "it": "Femminile", "pt": "Feminino", "ja": "女性", "zh": "女", "ko": "여성", "ar": "أنثى", "ru": "Женский", "vi": "Nữ", "hi": "महिला", "sw": "Kike", "no": "Kvinne", "am": "ሴት", "yo": "Obinrin", "zu": "Owesifazane"},
    "Poids": {"en": "Weight", "de": "Gewicht", "es": "Peso", "it": "Peso", "pt": "Peso", "ja": "体重", "zh": "体重", "ko": "체중", "ar": "الوزن", "ru": "Вес", "vi": "Cân nặng", "hi": "वजन", "sw": "Uzito", "no": "Vekt", "am": "ክብደት", "yo": "Iwuwo", "zu": "Isisindo"},
    "Grade": {"en": "Grade", "de": "Grad", "es": "Grado", "it": "Grado", "pt": "Graduação", "ja": "段位", "zh": "段位", "ko": "단", "ar": "درجة", "ru": "Степень", "vi": "Cấp", "hi": "ग्रेड", "sw": "Daraja", "no": "Grad", "am": "ደረጃ", "yo": "Ipele", "zu": "Ibanga"},
    "Ceinture": {"en": "Belt", "de": "Gürtel", "es": "Cinturón", "it": "Cintura", "pt": "Faixa", "ja": "帯", "zh": "腰带", "ko": "띠", "ar": "حزام", "ru": "Пояс", "vi": "Đai", "hi": "बेल्ट", "sw": "Mkanda", "no": "Belte", "am": "ቀበቶ", "yo": "Igbanu", "zu": "Ibhande"},

    # Dates et temps
    "Date": {"en": "Date", "de": "Datum", "es": "Fecha", "it": "Data", "pt": "Data", "ja": "日付", "zh": "日期", "ko": "날짜", "ar": "تاريخ", "ru": "Дата", "vi": "Ngày", "hi": "दिनांक", "sw": "Tarehe", "no": "Dato", "am": "ቀን", "yo": "Ọjọ", "zu": "Usuku"},
    "Heure": {"en": "Time", "de": "Zeit", "es": "Hora", "it": "Ora", "pt": "Hora", "ja": "時間", "zh": "时间", "ko": "시간", "ar": "وقت", "ru": "Время", "vi": "Giờ", "hi": "समय", "sw": "Saa", "no": "Tid", "am": "ሰዓት", "yo": "Akoko", "zu": "Isikhathi"},
    "Début": {"en": "Start", "de": "Beginn", "es": "Inicio", "it": "Inizio", "pt": "Início", "ja": "開始", "zh": "开始", "ko": "시작", "ar": "بداية", "ru": "Начало", "vi": "Bắt đầu", "hi": "शुरू", "sw": "Kuanza", "no": "Start", "am": "መጀመሪያ", "yo": "Ibẹrẹ", "zu": "Ukuqala"},
    "Fin": {"en": "End", "de": "Ende", "es": "Fin", "it": "Fine", "pt": "Fim", "ja": "終了", "zh": "结束", "ko": "종료", "ar": "نهاية", "ru": "Конец", "vi": "Kết thúc", "hi": "अंत", "sw": "Mwisho", "no": "Slutt", "am": "መጨረሻ", "yo": "Opin", "zu": "Ukuphela"},
    "Durée": {"en": "Duration", "de": "Dauer", "es": "Duración", "it": "Durata", "pt": "Duração", "ja": "期間", "zh": "时长", "ko": "기간", "ar": "مدة", "ru": "Длительность", "vi": "Thời lượng", "hi": "अवधि", "sw": "Muda", "no": "Varighet", "am": "ቆይታ", "yo": "Iye akoko", "zu": "Isikhathi"},

    # Statuts
    "Actif": {"en": "Active", "de": "Aktiv", "es": "Activo", "it": "Attivo", "pt": "Ativo", "ja": "アクティブ", "zh": "活跃", "ko": "활성", "ar": "نشط", "ru": "Активный", "vi": "Hoạt động", "hi": "सक्रिय", "sw": "Hai", "no": "Aktiv", "am": "ንቁ", "yo": "Ṣiṣẹ", "zu": "Okusebenzayo"},
    "Inactif": {"en": "Inactive", "de": "Inaktiv", "es": "Inactivo", "it": "Inattivo", "pt": "Inativo", "ja": "非アクティブ", "zh": "不活跃", "ko": "비활성", "ar": "غير نشط", "ru": "Неактивный", "vi": "Không hoạt động", "hi": "निष्क्रिय", "sw": "Haifanyi kazi", "no": "Inaktiv", "am": "ንቁ ያልሆነ", "yo": "Aiṣiṣẹ", "zu": "Okungasebenzi"},
    "En cours": {"en": "In progress", "de": "In Bearbeitung", "es": "En progreso", "it": "In corso", "pt": "Em andamento", "ja": "進行中", "zh": "进行中", "ko": "진행 중", "ar": "قيد التنفيذ", "ru": "В процессе", "vi": "Đang tiến hành", "hi": "प्रगति में", "sw": "Inaendelea", "no": "Pågår", "am": "በሂደት ላይ", "yo": "Nṣiṣẹ lọwọ", "zu": "Iyaqhubeka"},
    "Terminé": {"en": "Completed", "de": "Abgeschlossen", "es": "Completado", "it": "Completato", "pt": "Concluído", "ja": "完了", "zh": "已完成", "ko": "완료", "ar": "مكتمل", "ru": "Завершено", "vi": "Hoàn thành", "hi": "पूर्ण", "sw": "Imekamilika", "no": "Fullført", "am": "ተጠናቋል", "yo": "Pari", "zu": "Kuqediwe"},
    "En attente": {"en": "Pending", "de": "Ausstehend", "es": "Pendiente", "it": "In attesa", "pt": "Pendente", "ja": "保留中", "zh": "待处理", "ko": "대기 중", "ar": "معلق", "ru": "Ожидание", "vi": "Đang chờ", "hi": "लंबित", "sw": "Inasubiri", "no": "Venter", "am": "በመጠባበቅ ላይ", "yo": "Nduro", "zu": "Kulindile"},
    "Annulé": {"en": "Cancelled", "de": "Abgesagt", "es": "Cancelado", "it": "Annullato", "pt": "Cancelado", "ja": "キャンセル", "zh": "已取消", "ko": "취소됨", "ar": "ملغى", "ru": "Отменено", "vi": "Đã hủy", "hi": "रद्द", "sw": "Imefutwa", "no": "Avlyst", "am": "ተሰርዟል", "yo": "Ti fagile", "zu": "Kukhanseliwe"},
    "Brouillon": {"en": "Draft", "de": "Entwurf", "es": "Borrador", "it": "Bozza", "pt": "Rascunho", "ja": "下書き", "zh": "草稿", "ko": "초안", "ar": "مسودة", "ru": "Черновик", "vi": "Bản nháp", "hi": "ड्राफ्ट", "sw": "Rasimu", "no": "Utkast", "am": "ረቂቅ", "yo": "Akọsilẹ", "zu": "Uhlelwanombhalo"},
    "Publié": {"en": "Published", "de": "Veröffentlicht", "es": "Publicado", "it": "Pubblicato", "pt": "Publicado", "ja": "公開済み", "zh": "已发布", "ko": "게시됨", "ar": "منشور", "ru": "Опубликовано", "vi": "Đã xuất bản", "hi": "प्रकाशित", "sw": "Imechapishwa", "no": "Publisert", "am": "ታትሟል", "yo": "Ti tẹjade", "zu": "Kushicilelwe"},

    # Messages
    "Succès": {"en": "Success", "de": "Erfolg", "es": "Éxito", "it": "Successo", "pt": "Sucesso", "ja": "成功", "zh": "成功", "ko": "성공", "ar": "نجاح", "ru": "Успех", "vi": "Thành công", "hi": "सफलता", "sw": "Mafanikio", "no": "Suksess", "am": "ስኬት", "yo": "Aṣeyọri", "zu": "Impumelelo"},
    "Erreur": {"en": "Error", "de": "Fehler", "es": "Error", "it": "Errore", "pt": "Erro", "ja": "エラー", "zh": "错误", "ko": "오류", "ar": "خطأ", "ru": "Ошибка", "vi": "Lỗi", "hi": "त्रुटि", "sw": "Hitilafu", "no": "Feil", "am": "ስህተት", "yo": "Aṣiṣe", "zu": "Iphutha"},
    "Avertissement": {"en": "Warning", "de": "Warnung", "es": "Advertencia", "it": "Avviso", "pt": "Aviso", "ja": "警告", "zh": "警告", "ko": "경고", "ar": "تحذير", "ru": "Предупреждение", "vi": "Cảnh báo", "hi": "चेतावनी", "sw": "Onyo", "no": "Advarsel", "am": "ማስጠንቀቂያ", "yo": "Ikilọ", "zu": "Isexwayiso"},
    "Information": {"en": "Information", "de": "Information", "es": "Información", "it": "Informazione", "pt": "Informação", "ja": "情報", "zh": "信息", "ko": "정보", "ar": "معلومات", "ru": "Информация", "vi": "Thông tin", "hi": "जानकारी", "sw": "Habari", "no": "Informasjon", "am": "መረጃ", "yo": "Alaye", "zu": "Ulwazi"},
    "Chargement...": {"en": "Loading...", "de": "Laden...", "es": "Cargando...", "it": "Caricamento...", "pt": "Carregando...", "ja": "読み込み中...", "zh": "加载中...", "ko": "로딩 중...", "ar": "جاري التحميل...", "ru": "Загрузка...", "vi": "Đang tải...", "hi": "लोड हो रहा है...", "sw": "Inapakia...", "no": "Laster...", "am": "በመጫን ላይ...", "yo": "N gbe...", "zu": "Iyalayisha..."},
    "Aucun résultat": {"en": "No results", "de": "Keine Ergebnisse", "es": "Sin resultados", "it": "Nessun risultato", "pt": "Sem resultados", "ja": "結果なし", "zh": "无结果", "ko": "결과 없음", "ar": "لا توجد نتائج", "ru": "Нет результатов", "vi": "Không có kết quả", "hi": "कोई परिणाम नहीं", "sw": "Hakuna matokeo", "no": "Ingen resultater", "am": "ውጤት የለም", "yo": "Ko si abajade", "zu": "Akukho miphumela"},

    # Divers
    "Oui": {"en": "Yes", "de": "Ja", "es": "Sí", "it": "Sì", "pt": "Sim", "ja": "はい", "zh": "是", "ko": "예", "ar": "نعم", "ru": "Да", "vi": "Có", "hi": "हाँ", "sw": "Ndiyo", "no": "Ja", "am": "አዎ", "yo": "Bẹẹni", "zu": "Yebo"},
    "Non": {"en": "No", "de": "Nein", "es": "No", "it": "No", "pt": "Não", "ja": "いいえ", "zh": "否", "ko": "아니오", "ar": "لا", "ru": "Нет", "vi": "Không", "hi": "नहीं", "sw": "Hapana", "no": "Nei", "am": "አይ", "yo": "Rara", "zu": "Cha"},
    "Tous": {"en": "All", "de": "Alle", "es": "Todos", "it": "Tutti", "pt": "Todos", "ja": "すべて", "zh": "全部", "ko": "모두", "ar": "الكل", "ru": "Все", "vi": "Tất cả", "hi": "सभी", "sw": "Zote", "no": "Alle", "am": "ሁሉም", "yo": "Gbogbo", "zu": "Konke"},
    "Aucun": {"en": "None", "de": "Keine", "es": "Ninguno", "it": "Nessuno", "pt": "Nenhum", "ja": "なし", "zh": "无", "ko": "없음", "ar": "لا شيء", "ru": "Нет", "vi": "Không có", "hi": "कोई नहीं", "sw": "Hakuna", "no": "Ingen", "am": "ምንም", "yo": "Ko si", "zu": "Akukho"},
    "Autre": {"en": "Other", "de": "Andere", "es": "Otro", "it": "Altro", "pt": "Outro", "ja": "その他", "zh": "其他", "ko": "기타", "ar": "آخر", "ru": "Другое", "vi": "Khác", "hi": "अन्य", "sw": "Nyingine", "no": "Annet", "am": "ሌላ", "yo": "Miiran", "zu": "Okunye"},
    "Détails": {"en": "Details", "de": "Details", "es": "Detalles", "it": "Dettagli", "pt": "Detalhes", "ja": "詳細", "zh": "详情", "ko": "세부사항", "ar": "تفاصيل", "ru": "Подробности", "vi": "Chi tiết", "hi": "विवरण", "sw": "Maelezo", "no": "Detaljer", "am": "ዝርዝሮች", "yo": "Awọn alaye", "zu": "Imininingwane"},
    "Total": {"en": "Total", "de": "Gesamt", "es": "Total", "it": "Totale", "pt": "Total", "ja": "合計", "zh": "总计", "ko": "총계", "ar": "المجموع", "ru": "Итого", "vi": "Tổng", "hi": "कुल", "sw": "Jumla", "no": "Totalt", "am": "ጠቅላላ", "yo": "Apapọ", "zu": "Isamba"},
    "Description": {"en": "Description", "de": "Beschreibung", "es": "Descripción", "it": "Descrizione", "pt": "Descrição", "ja": "説明", "zh": "描述", "ko": "설명", "ar": "وصف", "ru": "Описание", "vi": "Mô tả", "hi": "विवरण", "sw": "Maelezo", "no": "Beskrivelse", "am": "መግለጫ", "yo": "Apejuwe", "zu": "Incazelo"},
    "Titre": {"en": "Title", "de": "Titel", "es": "Título", "it": "Titolo", "pt": "Título", "ja": "タイトル", "zh": "标题", "ko": "제목", "ar": "عنوان", "ru": "Название", "vi": "Tiêu đề", "hi": "शीर्षक", "sw": "Kichwa", "no": "Tittel", "am": "ርዕስ", "yo": "Akọle", "zu": "Isihloko"},
    "Type": {"en": "Type", "de": "Typ", "es": "Tipo", "it": "Tipo", "pt": "Tipo", "ja": "タイプ", "zh": "类型", "ko": "유형", "ar": "نوع", "ru": "Тип", "vi": "Loại", "hi": "प्रकार", "sw": "Aina", "no": "Type", "am": "ዓይነት", "yo": "Iru", "zu": "Uhlobo"},
    "Statut": {"en": "Status", "de": "Status", "es": "Estado", "it": "Stato", "pt": "Status", "ja": "ステータス", "zh": "状态", "ko": "상태", "ar": "الحالة", "ru": "Статус", "vi": "Trạng thái", "hi": "स्थिति", "sw": "Hali", "no": "Status", "am": "ሁኔታ", "yo": "Ipo", "zu": "Isimo"},

    # Cérémonie podium
    "Cérémonie": {"en": "Ceremony", "de": "Zeremonie", "es": "Ceremonia", "it": "Cerimonia", "pt": "Cerimônia", "ja": "式典", "zh": "仪式", "ko": "시상식", "ar": "حفل", "ru": "Церемония", "vi": "Lễ", "hi": "समारोह", "sw": "Sherehe", "no": "Seremoni", "am": "ስነ-ስርዓት", "yo": "Ayẹyẹ", "zu": "Umcimbi"},
    "Cérémonie de Remise des Prix": {"en": "Award Ceremony", "de": "Preisverleihung", "es": "Ceremonia de Premios", "it": "Cerimonia di Premiazione", "pt": "Cerimônia de Premiação", "ja": "表彰式", "zh": "颁奖典礼", "ko": "시상식", "ar": "حفل توزيع الجوائز", "ru": "Церемония награждения", "vi": "Lễ trao giải", "hi": "पुरस्कार समारोह", "sw": "Sherehe ya Tuzo", "no": "Prisutdeling", "am": "የሽልማት ስነ-ስርዓት", "yo": "Ayẹyẹ Ẹbun", "zu": "Umcimbi Wemiklomelo"},
    "Révéler le podium": {"en": "Reveal podium", "de": "Podium enthüllen", "es": "Revelar podio", "it": "Rivela podio", "pt": "Revelar pódio", "ja": "表彰台を公開", "zh": "揭晓领奖台", "ko": "시상대 공개", "ar": "كشف المنصة", "ru": "Показать подиум", "vi": "Công bố bục", "hi": "पोडियम दिखाएं", "sw": "Onyesha jukwaa", "no": "Vis podium", "am": "መድረክ አሳይ", "yo": "Fi pẹpẹ han", "zu": "Veza ipulatifomu"},
    "Pas encore de résultats": {"en": "No results yet", "de": "Noch keine Ergebnisse", "es": "Aún no hay resultados", "it": "Nessun risultato ancora", "pt": "Ainda sem resultados", "ja": "まだ結果がありません", "zh": "暂无结果", "ko": "아직 결과 없음", "ar": "لا توجد نتائج بعد", "ru": "Пока нет результатов", "vi": "Chưa có kết quả", "hi": "अभी तक कोई परिणाम नहीं", "sw": "Hakuna matokeo bado", "no": "Ingen resultater ennå", "am": "ገና ውጤት የለም", "yo": "Ko si abajade sibẹ", "zu": "Akukho miphumela okwamanje"},

    # Finances
    "Prix": {"en": "Price", "de": "Preis", "es": "Precio", "it": "Prezzo", "pt": "Preço", "ja": "価格", "zh": "价格", "ko": "가격", "ar": "سعر", "ru": "Цена", "vi": "Giá", "hi": "मूल्य", "sw": "Bei", "no": "Pris", "am": "ዋጋ", "yo": "Iye", "zu": "Intengo"},
    "Montant": {"en": "Amount", "de": "Betrag", "es": "Monto", "it": "Importo", "pt": "Valor", "ja": "金額", "zh": "金额", "ko": "금액", "ar": "المبلغ", "ru": "Сумма", "vi": "Số tiền", "hi": "राशि", "sw": "Kiasi", "no": "Beløp", "am": "መጠን", "yo": "Iye owo", "zu": "Inani"},
    "Paiement": {"en": "Payment", "de": "Zahlung", "es": "Pago", "it": "Pagamento", "pt": "Pagamento", "ja": "支払い", "zh": "付款", "ko": "결제", "ar": "دفع", "ru": "Оплата", "vi": "Thanh toán", "hi": "भुगतान", "sw": "Malipo", "no": "Betaling", "am": "ክፍያ", "yo": "Isanwo", "zu": "Inkokhelo"},
    "Facture": {"en": "Invoice", "de": "Rechnung", "es": "Factura", "it": "Fattura", "pt": "Fatura", "ja": "請求書", "zh": "发票", "ko": "청구서", "ar": "فاتورة", "ru": "Счет", "vi": "Hóa đơn", "hi": "बिल", "sw": "Ankara", "no": "Faktura", "am": "ደረሰኝ", "yo": "Iwe isanwo", "zu": "I-invoyisi"},
    "Gratuit": {"en": "Free", "de": "Kostenlos", "es": "Gratis", "it": "Gratuito", "pt": "Grátis", "ja": "無料", "zh": "免费", "ko": "무료", "ar": "مجاني", "ru": "Бесплатно", "vi": "Miễn phí", "hi": "मुफ़्त", "sw": "Bure", "no": "Gratis", "am": "ነጻ", "yo": "Ọfẹ", "zu": "Mahhala"},
}


def translate_po_file(lang_code, translations_dict):
    """Traduit les chaînes manquantes dans un fichier PO."""

    po_path = f'locale/{lang_code}/LC_MESSAGES/django.po'

    if not os.path.exists(po_path):
        return None

    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    translated_count = 0

    for fr_text, lang_translations in translations_dict.items():
        if lang_code not in lang_translations:
            continue

        target_text = lang_translations[lang_code]

        # Pattern 1: msgstr vide
        pattern1 = f'msgid "{fr_text}"\nmsgstr ""'
        replacement1 = f'msgid "{fr_text}"\nmsgstr "{target_text}"'

        if pattern1 in content:
            content = content.replace(pattern1, replacement1)
            translated_count += 1

        # Pattern 2: msgstr identique au msgid (non traduit)
        pattern2 = f'msgid "{fr_text}"\nmsgstr "{fr_text}"'
        replacement2 = f'msgid "{fr_text}"\nmsgstr "{target_text}"'

        if pattern2 in content:
            content = content.replace(pattern2, replacement2)
            translated_count += 1

    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return translated_count


def main():
    """Fonction principale."""

    print("=" * 70)
    print("TRADUCTION AUTOMATIQUE DES FICHIERS PO")
    print("=" * 70)

    # Liste des langues à traduire
    languages = ['en', 'de', 'es', 'it', 'pt', 'ja', 'zh', 'ko', 'ar', 'ru',
                 'vi', 'hi', 'sw', 'no', 'am', 'yo', 'zu']

    results = []

    for lang in languages:
        count = translate_po_file(lang, TRANSLATIONS)
        if count is not None:
            results.append((lang, count))
            print(f"  {lang.upper()}: {count} traductions appliquees")

    print("\n" + "=" * 70)
    print("TRADUCTION TERMINEE")
    print("=" * 70)

    total = sum(r[1] for r in results)
    print(f"Total: {total} traductions appliquees")

    return results


if __name__ == '__main__':
    main()
