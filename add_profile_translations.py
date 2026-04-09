#!/usr/bin/env python3
"""
Add new profile translation keys to 7 language files.
Only adds keys that don't already exist in each file (no overwrites).
"""

import json
import os


BASE_DIR = os.path.join(
    "c:\\martial_hub_django\\martialcomp",
    "mobile", "src", "i18n", "locales",
)


def set_nested_key(data, dotted_key, value):
    """Set a value in a nested dict using a dot-separated key path.
    Only sets the value if the key does NOT already exist."""
    keys = dotted_key.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    # Only add if key is missing
    if keys[-1] not in current:
        current[keys[-1]] = value
        return True
    return False


# ──────────────────────────────────────────────────────────
# Translations per language
# ──────────────────────────────────────────────────────────

TRANSLATIONS = {
    # ===================== GERMAN (de) =====================
    "de": {
        "title": "Profil",
        "loading": "Profil wird geladen...",
        "detail.disciplinesAndGrades": "Disziplinen & Graduierungen",
        "detail.license": "Lizenz:",
        "detail.obtained": "Erlangt am:",
        "detail.martialArtsInfo": "Kampfsport-Informationen",
        "detail.contactInfo": "Kontaktinformationen",
        "detail.notProvided": "Nicht angegeben",
        "detail.dateOfBirth": "Geburtsdatum",
        "detail.nationality": "Nationalität",
        "detail.medicalCertificate": "Ärztliches Attest",
        "detail.valid": "Gültig",
        "detail.expired": "Abgelaufen",
        "detail.issuedOn": "Ausgestellt am",
        "detail.expiresOn": "Läuft ab am",
        "detail.viewCertificate": "Zertifikat anzeigen",
        "detail.editProfile": "Profil bearbeiten",
        "settings.title": "Einstellungen",
        "settings.changePassword": "Passwort ändern",
        "settings.notifications": "Benachrichtigungen",
        "settings.privacy": "Datenschutz",
        "settings.language": "Sprache",
        "settings.deleteAccount": "Konto löschen",
        "offlineMode.active": "Offline-Modus aktiv",
        "offlineMode.online": "Online-Modus",
        "offlineMode.download": "Profile herunterladen",
        "offlineMode.manage": "Profile verwalten",
        "offlineMode.profilesAvailable": "{{count}} Profile für Offline-Nutzung verfügbar",
        "offlineMode.noProfiles": "Keine Profile für Offline-Nutzung heruntergeladen",
        "offlineMode.downloadSuccess": "Profile wurden für Offline-Nutzung heruntergeladen",
        "offlineMode.downloadFailed": "Download fehlgeschlagen",
        "offlineMode.downloadFailedMessage": "Profile konnten nicht für Offline-Nutzung heruntergeladen werden",
        "imageUpload.success": "Profilbild erfolgreich aktualisiert",
        "imageUpload.failed": "Upload fehlgeschlagen",
        "imageUpload.failedMessage": "Profilbild konnte nicht hochgeladen werden",
        "permissions.required": "Berechtigung erforderlich",
        "permissions.photosMessage": "Bitte erlauben Sie den Zugriff auf Ihre Fotos",
        "confirmLogout.title": "Abmelden",
        "confirmLogout.message": "Möchten Sie sich wirklich abmelden?",
        "confirmLogout.cancel": "Abbrechen",
        "confirmLogout.confirm": "Abmelden",
        "stats.title": "Statistiken",
        "stats.competitions": "Wettkämpfe",
        "stats.medals": "Medaillen",
        "stats.wins": "Siege",
        "stats.trainingSessions": "Trainingseinheiten",
        "achievements.title": "Erfolge",
        "achievements.empty": "Noch keine Erfolge",
        "achievements.unlocked": "Freigeschaltet am {{date}}",
        "documents.title": "Meine Dokumente",
        "documents.license": "Lizenz",
        "documents.medicalCertificate": "Ärztliches Attest",
        "documents.insurance": "Versicherung",
        "documents.upload": "Dokument hochladen",
    },

    # ===================== SPANISH (es) =====================
    "es": {
        "title": "Perfil",
        "loading": "Cargando perfil...",
        "detail.disciplinesAndGrades": "Disciplinas y Graduaciones",
        "detail.license": "Licencia:",
        "detail.obtained": "Obtenida el:",
        "detail.martialArtsInfo": "Información de artes marciales",
        "detail.contactInfo": "Información de contacto",
        "detail.notProvided": "No proporcionado",
        "detail.dateOfBirth": "Fecha de nacimiento",
        "detail.nationality": "Nacionalidad",
        "detail.medicalCertificate": "Certificado médico",
        "detail.valid": "Válido",
        "detail.expired": "Expirado",
        "detail.issuedOn": "Emitido el",
        "detail.expiresOn": "Expira el",
        "detail.viewCertificate": "Ver certificado",
        "detail.editProfile": "Editar perfil",
        "settings.title": "Configuración",
        "settings.changePassword": "Cambiar contraseña",
        "settings.notifications": "Notificaciones",
        "settings.privacy": "Privacidad",
        "settings.language": "Idioma",
        "settings.deleteAccount": "Eliminar cuenta",
        "offlineMode.active": "Modo sin conexión activo",
        "offlineMode.online": "Modo en línea",
        "offlineMode.download": "Descargar perfiles",
        "offlineMode.manage": "Gestionar perfiles",
        "offlineMode.profilesAvailable": "{{count}} perfiles disponibles sin conexión",
        "offlineMode.noProfiles": "No se han descargado perfiles para uso sin conexión",
        "offlineMode.downloadSuccess": "Los perfiles se han descargado para uso sin conexión",
        "offlineMode.downloadFailed": "Error en la descarga",
        "offlineMode.downloadFailedMessage": "No se pudieron descargar los perfiles para uso sin conexión",
        "imageUpload.success": "Imagen de perfil actualizada correctamente",
        "imageUpload.failed": "Error al subir",
        "imageUpload.failedMessage": "No se pudo subir la imagen de perfil",
        "permissions.required": "Permiso requerido",
        "permissions.photosMessage": "Por favor, conceda permiso para acceder a sus fotos",
        "confirmLogout.title": "Cerrar sesión",
        "confirmLogout.message": "¿Está seguro de que desea cerrar sesión?",
        "confirmLogout.cancel": "Cancelar",
        "confirmLogout.confirm": "Cerrar sesión",
        "stats.title": "Estadísticas",
        "stats.competitions": "Competiciones",
        "stats.medals": "Medallas",
        "stats.wins": "Victorias",
        "stats.trainingSessions": "Sesiones de entrenamiento",
        "achievements.title": "Logros",
        "achievements.empty": "Sin logros aún",
        "achievements.unlocked": "Desbloqueado el {{date}}",
        "documents.title": "Mis documentos",
        "documents.license": "Licencia",
        "documents.medicalCertificate": "Certificado médico",
        "documents.insurance": "Seguro",
        "documents.upload": "Subir documento",
    },

    # ===================== ITALIAN (it) =====================
    "it": {
        "title": "Profilo",
        "loading": "Caricamento profilo...",
        "detail.disciplinesAndGrades": "Discipline e Gradi",
        "detail.license": "Licenza:",
        "detail.obtained": "Ottenuto il:",
        "detail.martialArtsInfo": "Informazioni arti marziali",
        "detail.contactInfo": "Informazioni di contatto",
        "detail.notProvided": "Non fornito",
        "detail.dateOfBirth": "Data di nascita",
        "detail.nationality": "Nazionalità",
        "detail.medicalCertificate": "Certificato medico",
        "detail.valid": "Valido",
        "detail.expired": "Scaduto",
        "detail.issuedOn": "Rilasciato il",
        "detail.expiresOn": "Scade il",
        "detail.viewCertificate": "Visualizza certificato",
        "detail.editProfile": "Modifica profilo",
        "settings.title": "Impostazioni",
        "settings.changePassword": "Cambia password",
        "settings.notifications": "Notifiche",
        "settings.privacy": "Privacy",
        "settings.language": "Lingua",
        "settings.deleteAccount": "Elimina account",
        "offlineMode.active": "Modalità offline attiva",
        "offlineMode.online": "Modalità online",
        "offlineMode.download": "Scarica profili",
        "offlineMode.manage": "Gestisci profili",
        "offlineMode.profilesAvailable": "{{count}} profili disponibili offline",
        "offlineMode.noProfiles": "Nessun profilo scaricato per l'uso offline",
        "offlineMode.downloadSuccess": "I profili sono stati scaricati per l'uso offline",
        "offlineMode.downloadFailed": "Download non riuscito",
        "offlineMode.downloadFailedMessage": "Impossibile scaricare i profili per l'uso offline",
        "imageUpload.success": "Immagine del profilo aggiornata con successo",
        "imageUpload.failed": "Caricamento non riuscito",
        "imageUpload.failedMessage": "Impossibile caricare l'immagine del profilo",
        "permissions.required": "Autorizzazione necessaria",
        "permissions.photosMessage": "Concedi l'autorizzazione per accedere alle tue foto",
        "confirmLogout.title": "Disconnessione",
        "confirmLogout.message": "Sei sicuro di volerti disconnettere?",
        "confirmLogout.cancel": "Annulla",
        "confirmLogout.confirm": "Disconnetti",
        "stats.title": "Statistiche",
        "stats.competitions": "Competizioni",
        "stats.medals": "Medaglie",
        "stats.wins": "Vittorie",
        "stats.trainingSessions": "Sessioni di allenamento",
        "achievements.title": "Traguardi",
        "achievements.empty": "Nessun traguardo ancora",
        "achievements.unlocked": "Sbloccato il {{date}}",
        "documents.title": "I miei documenti",
        "documents.license": "Licenza",
        "documents.medicalCertificate": "Certificato medico",
        "documents.insurance": "Assicurazione",
        "documents.upload": "Carica documento",
    },

    # ===================== PORTUGUESE (pt) =====================
    "pt": {
        "title": "Perfil",
        "loading": "Carregando perfil...",
        "detail.disciplinesAndGrades": "Disciplinas e Graduações",
        "detail.license": "Licença:",
        "detail.obtained": "Obtida em:",
        "detail.martialArtsInfo": "Informações de artes marciais",
        "detail.contactInfo": "Informações de contato",
        "detail.notProvided": "Não informado",
        "detail.dateOfBirth": "Data de nascimento",
        "detail.nationality": "Nacionalidade",
        "detail.medicalCertificate": "Atestado médico",
        "detail.valid": "Válido",
        "detail.expired": "Expirado",
        "detail.issuedOn": "Emitido em",
        "detail.expiresOn": "Expira em",
        "detail.viewCertificate": "Ver certificado",
        "detail.editProfile": "Editar perfil",
        "settings.title": "Configurações",
        "settings.changePassword": "Alterar senha",
        "settings.notifications": "Notificações",
        "settings.privacy": "Privacidade",
        "settings.language": "Idioma",
        "settings.deleteAccount": "Excluir conta",
        "offlineMode.active": "Modo offline ativo",
        "offlineMode.online": "Modo online",
        "offlineMode.download": "Baixar perfis",
        "offlineMode.manage": "Gerenciar perfis",
        "offlineMode.profilesAvailable": "{{count}} perfis disponíveis para uso offline",
        "offlineMode.noProfiles": "Nenhum perfil baixado para uso offline",
        "offlineMode.downloadSuccess": "Os perfis foram baixados para uso offline",
        "offlineMode.downloadFailed": "Falha no download",
        "offlineMode.downloadFailedMessage": "Não foi possível baixar os perfis para uso offline",
        "imageUpload.success": "Imagem de perfil atualizada com sucesso",
        "imageUpload.failed": "Falha no envio",
        "imageUpload.failedMessage": "Não foi possível enviar a imagem de perfil",
        "permissions.required": "Permissão necessária",
        "permissions.photosMessage": "Por favor, conceda permissão para acessar suas fotos",
        "confirmLogout.title": "Sair",
        "confirmLogout.message": "Tem certeza de que deseja sair?",
        "confirmLogout.cancel": "Cancelar",
        "confirmLogout.confirm": "Sair",
        "stats.title": "Estatísticas",
        "stats.competitions": "Competições",
        "stats.medals": "Medalhas",
        "stats.wins": "Vitórias",
        "stats.trainingSessions": "Sessões de treino",
        "achievements.title": "Conquistas",
        "achievements.empty": "Nenhuma conquista ainda",
        "achievements.unlocked": "Desbloqueado em {{date}}",
        "documents.title": "Meus documentos",
        "documents.license": "Licença",
        "documents.medicalCertificate": "Atestado médico",
        "documents.insurance": "Seguro",
        "documents.upload": "Enviar documento",
    },

    # ===================== ARABIC (ar) =====================
    "ar": {
        "title": "الملف الشخصي",
        "loading": "جاري تحميل الملف الشخصي...",
        "detail.disciplinesAndGrades": "التخصصات والدرجات",
        "detail.license": "الرخصة:",
        "detail.obtained": "تم الحصول عليها:",
        "detail.martialArtsInfo": "معلومات الفنون القتالية",
        "detail.contactInfo": "معلومات الاتصال",
        "detail.notProvided": "غير مُدخل",
        "detail.dateOfBirth": "تاريخ الميلاد",
        "detail.nationality": "الجنسية",
        "detail.medicalCertificate": "الشهادة الطبية",
        "detail.valid": "ساري",
        "detail.expired": "منتهي الصلاحية",
        "detail.issuedOn": "صادر بتاريخ",
        "detail.expiresOn": "ينتهي بتاريخ",
        "detail.viewCertificate": "عرض الشهادة",
        "detail.editProfile": "تعديل الملف الشخصي",
        "settings.title": "الإعدادات",
        "settings.changePassword": "تغيير كلمة المرور",
        "settings.notifications": "الإشعارات",
        "settings.privacy": "الخصوصية",
        "settings.language": "اللغة",
        "settings.deleteAccount": "حذف الحساب",
        "offlineMode.active": "وضع عدم الاتصال مفعّل",
        "offlineMode.online": "وضع الاتصال",
        "offlineMode.download": "تنزيل الملفات الشخصية",
        "offlineMode.manage": "إدارة الملفات الشخصية",
        "offlineMode.profilesAvailable": "{{count}} ملفات شخصية متاحة للاستخدام بدون اتصال",
        "offlineMode.noProfiles": "لم يتم تنزيل ملفات شخصية للاستخدام بدون اتصال",
        "offlineMode.downloadSuccess": "تم تنزيل الملفات الشخصية للاستخدام بدون اتصال",
        "offlineMode.downloadFailed": "فشل التنزيل",
        "offlineMode.downloadFailedMessage": "تعذّر تنزيل الملفات الشخصية للاستخدام بدون اتصال",
        "imageUpload.success": "تم تحديث صورة الملف الشخصي بنجاح",
        "imageUpload.failed": "فشل الرفع",
        "imageUpload.failedMessage": "تعذّر رفع صورة الملف الشخصي",
        "permissions.required": "إذن مطلوب",
        "permissions.photosMessage": "يرجى منح إذن الوصول إلى صورك",
        "confirmLogout.title": "تسجيل الخروج",
        "confirmLogout.message": "هل أنت متأكد أنك تريد تسجيل الخروج؟",
        "confirmLogout.cancel": "إلغاء",
        "confirmLogout.confirm": "تسجيل الخروج",
        "stats.title": "الإحصائيات",
        "stats.competitions": "المسابقات",
        "stats.medals": "الميداليات",
        "stats.wins": "الانتصارات",
        "stats.trainingSessions": "جلسات التدريب",
        "achievements.title": "الإنجازات",
        "achievements.empty": "لا توجد إنجازات بعد",
        "achievements.unlocked": "تم فتحه في {{date}}",
        "documents.title": "مستنداتي",
        "documents.license": "الرخصة",
        "documents.medicalCertificate": "الشهادة الطبية",
        "documents.insurance": "التأمين",
        "documents.upload": "رفع مستند",
    },

    # ===================== RUSSIAN (ru) =====================
    "ru": {
        "title": "Профиль",
        "loading": "Загрузка профиля...",
        "detail.disciplinesAndGrades": "Дисциплины и пояса",
        "detail.license": "Лицензия:",
        "detail.obtained": "Получена:",
        "detail.martialArtsInfo": "Спортивная информация",
        "detail.contactInfo": "Контактные данные",
        "detail.notProvided": "Не указано",
        "detail.dateOfBirth": "Дата рождения",
        "detail.nationality": "Гражданство",
        "detail.medicalCertificate": "Медицинская справка",
        "detail.valid": "Действительна",
        "detail.expired": "Истекла",
        "detail.issuedOn": "Выдана",
        "detail.expiresOn": "Истекает",
        "detail.viewCertificate": "Просмотреть сертификат",
        "detail.editProfile": "Редактировать профиль",
        "settings.title": "Настройки",
        "settings.changePassword": "Изменить пароль",
        "settings.notifications": "Уведомления",
        "settings.privacy": "Конфиденциальность",
        "settings.language": "Язык",
        "settings.deleteAccount": "Удалить аккаунт",
        "offlineMode.active": "Офлайн-режим активен",
        "offlineMode.online": "Онлайн-режим",
        "offlineMode.download": "Скачать профили",
        "offlineMode.manage": "Управление профилями",
        "offlineMode.profilesAvailable": "{{count}} профилей доступно для офлайн-использования",
        "offlineMode.noProfiles": "Нет скачанных профилей для офлайн-использования",
        "offlineMode.downloadSuccess": "Профили скачаны для офлайн-использования",
        "offlineMode.downloadFailed": "Ошибка загрузки",
        "offlineMode.downloadFailedMessage": "Не удалось скачать профили для офлайн-использования",
        "imageUpload.success": "Фото профиля успешно обновлено",
        "imageUpload.failed": "Ошибка загрузки",
        "imageUpload.failedMessage": "Не удалось загрузить фото профиля",
        "permissions.required": "Требуется разрешение",
        "permissions.photosMessage": "Предоставьте разрешение на доступ к вашим фотографиям",
        "confirmLogout.title": "Выход",
        "confirmLogout.message": "Вы уверены, что хотите выйти?",
        "confirmLogout.cancel": "Отмена",
        "confirmLogout.confirm": "Выйти",
        "stats.title": "Статистика",
        "stats.competitions": "Соревнования",
        "stats.medals": "Медали",
        "stats.wins": "Победы",
        "stats.trainingSessions": "Тренировки",
        "achievements.title": "Достижения",
        "achievements.empty": "Пока нет достижений",
        "achievements.unlocked": "Получено {{date}}",
        "documents.title": "Мои документы",
        "documents.license": "Лицензия",
        "documents.medicalCertificate": "Медицинская справка",
        "documents.insurance": "Страховка",
        "documents.upload": "Загрузить документ",
    },

    # ===================== JAPANESE (ja) =====================
    "ja": {
        "title": "プロフィール",
        "loading": "プロフィールを読み込み中...",
        "detail.disciplinesAndGrades": "武道・段位",
        "detail.license": "ライセンス：",
        "detail.obtained": "取得日：",
        "detail.martialArtsInfo": "武道情報",
        "detail.contactInfo": "連絡先",
        "detail.notProvided": "未登録",
        "detail.dateOfBirth": "生年月日",
        "detail.nationality": "国籍",
        "detail.medicalCertificate": "診断書",
        "detail.valid": "有効",
        "detail.expired": "期限切れ",
        "detail.issuedOn": "発行日",
        "detail.expiresOn": "有効期限",
        "detail.viewCertificate": "証明書を見る",
        "detail.editProfile": "プロフィールを編集",
        "settings.title": "設定",
        "settings.changePassword": "パスワードを変更",
        "settings.notifications": "通知",
        "settings.privacy": "プライバシー",
        "settings.language": "言語",
        "settings.deleteAccount": "アカウントを削除",
        "offlineMode.active": "オフラインモード有効",
        "offlineMode.online": "オンラインモード",
        "offlineMode.download": "プロフィールをダウンロード",
        "offlineMode.manage": "プロフィールを管理",
        "offlineMode.profilesAvailable": "{{count}}件のプロフィールがオフラインで利用可能",
        "offlineMode.noProfiles": "オフライン用にダウンロードされたプロフィールはありません",
        "offlineMode.downloadSuccess": "プロフィールをオフライン用にダウンロードしました",
        "offlineMode.downloadFailed": "ダウンロード失敗",
        "offlineMode.downloadFailedMessage": "プロフィールのオフライン用ダウンロードに失敗しました",
        "imageUpload.success": "プロフィール画像を更新しました",
        "imageUpload.failed": "アップロード失敗",
        "imageUpload.failedMessage": "プロフィール画像のアップロードに失敗しました",
        "permissions.required": "権限が必要です",
        "permissions.photosMessage": "写真へのアクセスを許可してください",
        "confirmLogout.title": "ログアウト",
        "confirmLogout.message": "ログアウトしてよろしいですか？",
        "confirmLogout.cancel": "キャンセル",
        "confirmLogout.confirm": "ログアウト",
        "stats.title": "統計",
        "stats.competitions": "大会",
        "stats.medals": "メダル",
        "stats.wins": "勝利",
        "stats.trainingSessions": "稽古",
        "achievements.title": "実績",
        "achievements.empty": "まだ実績がありません",
        "achievements.unlocked": "{{date}}に達成",
        "documents.title": "マイドキュメント",
        "documents.license": "ライセンス",
        "documents.medicalCertificate": "診断書",
        "documents.insurance": "保険",
        "documents.upload": "書類をアップロード",
    },
}


def process_language(locale, new_keys):
    """Read, merge new keys, and write back a single locale file."""
    filepath = os.path.join(BASE_DIR, locale, "profile.json")

    # Read existing data
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    added_count = 0
    skipped_count = 0

    for dotted_key, value in new_keys.items():
        was_added = set_nested_key(data, dotted_key, value)
        if was_added:
            added_count += 1
        else:
            skipped_count += 1

    # Write back with proper formatting
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")  # trailing newline

    print(f"  [{locale}] {filepath}")
    print(f"       Added: {added_count} keys  |  Skipped (already exist): {skipped_count} keys")
    return added_count, skipped_count


def main():
    print("=" * 70)
    print("  Adding new profile translation keys to 7 language files")
    print("=" * 70)

    total_added = 0
    total_skipped = 0

    for locale, keys in TRANSLATIONS.items():
        added, skipped = process_language(locale, keys)
        total_added += added
        total_skipped += skipped
        print()

    print("=" * 70)
    print(f"  TOTAL: {total_added} keys added  |  {total_skipped} keys skipped (already existed)")
    print("=" * 70)


if __name__ == "__main__":
    main()
