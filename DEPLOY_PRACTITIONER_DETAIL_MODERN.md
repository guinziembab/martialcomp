# DÉPLOIEMENT - Nouveau Template Practitioner Detail (Design Moderne)

## Description

Ce déploiement met à jour la page de détail d'un pratiquant avec un nouveau design moderne inspiré de l'interface avec fond sombre, photo circulaire avec bordure dorée, et onglets Parcours/Documents/ID Card.

## Fichiers à déployer

1. **Nouveau template**: `apps/competitions/templates/competitions/club/practitioner_detail_modern.html`
2. **Vue mise à jour**: `apps/competitions/views/club/practitioners.py`

## Commandes de déploiement

```bash
ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "=== DÉPLOIEMENT NOUVEAU TEMPLATE PRACTITIONER DETAIL ==="
echo "Date: $(date)"

# 1. Backup des fichiers existants
echo ""
echo "=== 1. SAUVEGARDE ==="
cp apps/competitions/views/club/practitioners.py apps/competitions/views/club/practitioners.py.backup_$(date +%Y%m%d_%H%M%S)
cp apps/competitions/templates/competitions/club/practitioner_detail.html apps/competitions/templates/competitions/club/practitioner_detail.html.backup_$(date +%Y%m%d_%H%M%S)
echo "Backups créés"

# 2. Créer le nouveau template
echo ""
echo "=== 2. CRÉATION DU NOUVEAU TEMPLATE ==="
cat > apps/competitions/templates/competitions/club/practitioner_detail_modern.html << 'TEMPLATE'
{% extends "base.html" %}
{% load i18n %}
{% load static %}
{% load custom_filters %}

{% block title %}{{ practitioner.full_name }} | {% trans "Profil du pratiquant" %}{% endblock %}

{% block extra_css %}
<style>
    .practitioner-profile-page {
        --profile-bg: #1a1a2e;
        --profile-card-bg: #16213e;
        --profile-card-border: #0f3460;
        --profile-accent: #e94560;
        --profile-accent-gold: #c9a227;
        --profile-text: #eaeaea;
        --profile-text-muted: #a0a0a0;
        --profile-success: #00d26a;
        --profile-warning: #ffc107;
        background-color: var(--profile-bg);
        min-height: 100vh;
        padding: 2rem 0;
    }
    .profile-container { max-width: 900px; margin: 0 auto; }
    .profile-modal-card {
        background: var(--profile-card-bg);
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }
    .profile-left-section {
        background: linear-gradient(180deg, var(--profile-card-bg) 0%, #0f0f23 100%);
        padding: 2rem;
        text-align: center;
        border-right: 1px solid var(--profile-card-border);
    }
    .profile-photo-wrapper { position: relative; width: 150px; height: 150px; margin: 0 auto 1.5rem; }
    .profile-photo {
        width: 150px; height: 150px; border-radius: 50%; object-fit: cover;
        border: 4px solid var(--profile-accent-gold);
        box-shadow: 0 8px 25px rgba(201, 162, 39, 0.3);
    }
    .profile-photo-placeholder {
        width: 150px; height: 150px; border-radius: 50%;
        background: linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%);
        display: flex; align-items: center; justify-content: center;
        border: 4px solid var(--profile-accent-gold);
    }
    .profile-photo-placeholder i { font-size: 4rem; color: var(--profile-text-muted); }
    .profile-name { color: var(--profile-text); font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
    .profile-license { color: var(--profile-text-muted); font-size: 0.875rem; margin-bottom: 1.5rem; }
    .system-selector {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--profile-card-border);
        border-radius: 10px; padding: 0.75rem 1rem;
        color: var(--profile-text); width: 100%; margin-bottom: 1rem;
        cursor: pointer; appearance: none;
    }
    .profile-info-item {
        display: flex; align-items: center; gap: 0.75rem;
        padding: 0.5rem 0; color: var(--profile-text-muted);
        font-size: 0.9rem; text-align: left;
    }
    .profile-info-item i { width: 20px; color: var(--profile-text-muted); }
    .profile-action-btn {
        width: 100%; padding: 0.875rem 1.5rem; border-radius: 10px;
        font-weight: 600; transition: all 0.3s ease; margin-bottom: 0.75rem;
        display: flex; align-items: center; justify-content: center; gap: 0.5rem;
    }
    .btn-edit-profile {
        background: linear-gradient(135deg, var(--profile-accent-gold) 0%, #d4a42a 100%);
        border: none; color: #1a1a2e;
    }
    .btn-edit-profile:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(201, 162, 39, 0.4); color: #1a1a2e; }
    .btn-member-space { background: transparent; border: 1px solid var(--profile-card-border); color: var(--profile-text); }
    .btn-member-space:hover { background: rgba(255, 255, 255, 0.05); color: var(--profile-text); }
    .profile-right-section { padding: 2rem; background: var(--profile-card-bg); }
    .profile-tabs { display: flex; gap: 0; border-bottom: 1px solid var(--profile-card-border); margin-bottom: 1.5rem; }
    .profile-tab {
        flex: 1; padding: 1rem; background: transparent; border: none;
        color: var(--profile-text-muted); font-weight: 500; cursor: pointer;
        transition: all 0.3s ease; position: relative;
        display: flex; align-items: center; justify-content: center; gap: 0.5rem;
    }
    .profile-tab:hover { color: var(--profile-text); }
    .profile-tab.active { color: var(--profile-accent-gold); }
    .profile-tab.active::after {
        content: ''; position: absolute; bottom: -1px; left: 0; right: 0;
        height: 3px; background: var(--profile-accent-gold); border-radius: 3px 3px 0 0;
    }
    .profile-section-title {
        color: var(--profile-accent-gold); font-size: 1.1rem; font-weight: 600;
        margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;
    }
    .profile-content-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--profile-card-border);
        border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem;
    }
    .profile-info-row {
        display: flex; justify-content: space-between; padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .profile-info-row:last-child { border-bottom: none; }
    .profile-info-label { color: var(--profile-text-muted); font-size: 0.875rem; }
    .profile-info-value { color: var(--profile-text); font-weight: 500; }
    .profile-info-value.success { color: var(--profile-success); }
    .profile-info-value.warning { color: var(--profile-warning); }
    .discipline-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--profile-accent) 0%, #d63384 100%);
        color: white; padding: 0.35rem 0.75rem; border-radius: 20px;
        font-size: 0.8rem; font-weight: 600; margin: 0.25rem;
    }
    .grade-badge {
        display: inline-block; background: rgba(255, 255, 255, 0.1);
        color: var(--profile-text); padding: 0.35rem 0.75rem;
        border-radius: 8px; font-size: 0.875rem;
    }
    .id-card-container {
        background: linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%);
        border-radius: 15px; padding: 1.5rem;
        border: 2px solid var(--profile-accent-gold);
        position: relative; overflow: hidden;
    }
    .status-badge {
        display: inline-flex; align-items: center; gap: 0.35rem;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        font-size: 0.8rem; font-weight: 600;
    }
    .status-badge.active { background: rgba(0, 210, 106, 0.15); color: var(--profile-success); }
    body { background-color: #1a1a2e !important; }
    @media (max-width: 768px) {
        .profile-modal-card { margin: 1rem; }
        .profile-left-section { border-right: none; border-bottom: 1px solid var(--profile-card-border); }
        .profile-tab span { display: none; }
    }
</style>
{% endblock %}

{% block content %}
<div class="practitioner-profile-page">
    <div class="profile-container">
        <div class="profile-modal-card">
            <div class="row g-0">
                <div class="col-lg-4">
                    <div class="profile-left-section">
                        <div class="profile-photo-wrapper">
                            {% if practitioner.photo %}
                                <img src="{{ practitioner.photo.url }}" alt="{{ practitioner.full_name }}" class="profile-photo">
                            {% else %}
                                <div class="profile-photo-placeholder"><i class="fas fa-user"></i></div>
                            {% endif %}
                        </div>
                        <h2 class="profile-name">{{ practitioner.full_name }}</h2>
                        {% if practitioner.license_number %}<p class="profile-license">{{ practitioner.license_number }}</p>{% endif %}
                        <select class="system-selector"><option>{% trans "Pratiquant" %}</option></select>
                        <select class="system-selector"><option>{% trans "Changer système..." %}</option></select>
                        <div class="profile-quick-info mt-4">
                            <div class="profile-info-item"><i class="fas fa-birthday-cake"></i><span>{{ practitioner.age }} {% trans "ans" %}</span></div>
                            <div class="profile-info-item"><i class="fas fa-envelope"></i><span>{{ practitioner.email|default:"Non renseigné" }}</span></div>
                            <div class="profile-info-item"><i class="fas fa-phone"></i><span>{{ practitioner.phone|default:"Non renseigné" }}</span></div>
                            <div class="profile-info-item"><i class="fas fa-ambulance"></i><span>{% trans "Contact:" %} {{ practitioner.emergency_contact_name|default:"N/A" }}</span></div>
                        </div>
                        <div class="mt-4">
                            <a href="{% url 'competitions:club:practitioner_edit' pk=practitioner.id %}" class="profile-action-btn btn-edit-profile"><i class="fas fa-edit"></i> {% trans "Modifier les détails" %}</a>
                            <a href="{% url 'competitions:qr:view_qr' practitioner_id=practitioner.id %}" class="profile-action-btn btn-member-space">{% trans "Voir l'espace membre" %} <i class="fas fa-external-link-alt"></i></a>
                        </div>
                    </div>
                </div>
                <div class="col-lg-8">
                    <div class="profile-right-section">
                        <div class="profile-tabs" role="tablist">
                            <button class="profile-tab active" data-bs-toggle="tab" data-bs-target="#parcours-tab"><i class="fas fa-road"></i> <span>{% trans "Parcours" %}</span></button>
                            <button class="profile-tab" data-bs-toggle="tab" data-bs-target="#documents-tab"><i class="fas fa-file-alt"></i> <span>{% trans "Documents" %}</span></button>
                            <button class="profile-tab" data-bs-toggle="tab" data-bs-target="#idcard-tab"><i class="fas fa-id-card"></i> <span>{% trans "ID Card" %}</span></button>
                        </div>
                        <div class="tab-content">
                            <div class="tab-pane fade show active" id="parcours-tab">
                                <h4 class="profile-section-title"><i class="fas fa-medal"></i> {% trans "Historique des Grades" %}</h4>
                                <div class="profile-content-card">
                                    {% if grade_history %}{% for grade in grade_history %}<div class="profile-info-row"><span class="profile-info-label">{{ grade.date|date:"d/m/Y" }}</span><span class="profile-info-value">{{ grade.grade_name }} - {{ grade.discipline_name }}</span></div>{% endfor %}{% else %}<p class="text-muted mb-0">{% trans "Aucun historique de grade." %}</p>{% endif %}
                                </div>
                                <h4 class="profile-section-title"><i class="fas fa-heartbeat"></i> {% trans "Informations Médicales" %}</h4>
                                <div class="profile-content-card">
                                    <div class="profile-info-row"><span class="profile-info-label">{% trans "Dernier contrôle" %}</span><span class="profile-info-value">{% if practitioner.medical_certificate_date %}{{ practitioner.medical_certificate_date|date:"d/m/Y" }}{% else %}N/A{% endif %}</span></div>
                                    <div class="profile-info-row"><span class="profile-info-label">{% trans "Statut" %}</span><span class="profile-info-value {% if practitioner.is_medical_certificate_valid %}success{% else %}warning{% endif %}">{% if practitioner.is_medical_certificate_valid %}{% trans "Apte" %}{% else %}{% trans "À renouveler" %}{% endif %}</span></div>
                                    <div class="profile-info-row"><span class="profile-info-label">{% trans "Notes" %}</span><span class="profile-info-value">{{ practitioner.medical_conditions|default:"Aucune" }}</span></div>
                                </div>
                                <h4 class="profile-section-title"><i class="fas fa-dumbbell"></i> {% trans "Informations Sportives" %}</h4>
                                <div class="profile-content-card">
                                    <div class="profile-info-row"><span class="profile-info-label">{% trans "Grades" %}</span><span class="profile-info-value">{% if practitioner.computed_grade_display %}<span class="grade-badge">{{ practitioner.computed_grade_display }}</span>{% else %}N/A{% endif %}</span></div>
                                    <div class="profile-info-row"><span class="profile-info-label">{% trans "Disciplines" %}</span><span class="profile-info-value">{% for discipline in practitioner.disciplines.all %}<span class="discipline-badge">{{ discipline.name }}</span>{% empty %}N/A{% endfor %}</span></div>
                                </div>
                            </div>
                            <div class="tab-pane fade" id="documents-tab">
                                <h4 class="profile-section-title"><i class="fas fa-folder-open"></i> {% trans "Documents" %}</h4>
                                <div class="profile-content-card">
                                    <div class="profile-info-row"><span class="profile-info-label"><i class="fas fa-file-medical me-2"></i>{% trans "Certificat médical" %}</span><span class="profile-info-value">{% if practitioner.medical_certificate %}<a href="{{ practitioner.medical_certificate.url }}" target="_blank" class="btn btn-sm btn-outline-light"><i class="fas fa-eye"></i></a>{% else %}<span class="text-warning">{% trans "Non téléchargé" %}</span>{% endif %}</span></div>
                                    <div class="profile-info-row"><span class="profile-info-label"><i class="fas fa-portrait me-2"></i>{% trans "Photo" %}</span><span class="profile-info-value">{% if practitioner.photo %}<span class="text-success"><i class="fas fa-check"></i></span>{% else %}<span class="text-warning">{% trans "Non" %}</span>{% endif %}</span></div>
                                </div>
                                <div class="text-center mt-4"><a href="{% url 'competitions:club:practitioner_edit' pk=practitioner.id %}?tab=other" class="btn btn-outline-light"><i class="fas fa-upload me-2"></i>{% trans "Gérer les documents" %}</a></div>
                            </div>
                            <div class="tab-pane fade" id="idcard-tab">
                                <h4 class="profile-section-title"><i class="fas fa-id-badge"></i> {% trans "Carte d'identité sportive" %}</h4>
                                <div class="id-card-container">
                                    <div class="row">
                                        <div class="col-4 text-center">
                                            {% if practitioner.photo %}<img src="{{ practitioner.photo.url }}" style="width:80px;height:100px;object-fit:cover;border-radius:8px;">{% else %}<div style="width:80px;height:100px;background:#2d2d44;border-radius:8px;display:flex;align-items:center;justify-content:center;"><i class="fas fa-user fa-2x" style="color:#666;"></i></div>{% endif %}
                                        </div>
                                        <div class="col-8">
                                            <h5 style="color:var(--profile-text);">{{ practitioner.full_name }}</h5>
                                            <p style="color:var(--profile-text-muted);font-size:0.85rem;"><strong>{% trans "Licence:" %}</strong> {{ practitioner.license_number|default:"N/A" }}</p>
                                            <p style="color:var(--profile-text-muted);font-size:0.85rem;"><strong>{% trans "Club:" %}</strong> {{ practitioner.club.name|default:"N/A" }}</p>
                                            <div class="mt-2">{% for d in practitioner.disciplines.all %}<span class="discipline-badge" style="font-size:0.7rem;padding:0.2rem 0.5rem;">{{ d.name }}</span>{% endfor %}</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="text-center mt-4">
                                    <a href="{% url 'competitions:qr:view_qr' practitioner_id=practitioner.id %}" class="btn btn-outline-light me-2"><i class="fas fa-qrcode me-2"></i>{% trans "QR Code" %}</a>
                                    <button class="btn btn-outline-light" onclick="window.print()"><i class="fas fa-print me-2"></i>{% trans "Imprimer" %}</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="text-center mt-4"><a href="{% url 'competitions:club:practitioners' %}" class="btn btn-outline-light"><i class="fas fa-arrow-left me-2"></i>{% trans "Retour" %}</a></div>
    </div>
</div>
{% endblock %}
TEMPLATE

echo "Template créé"

# 3. Mettre à jour la vue practitioners.py
echo ""
echo "=== 3. MISE À JOUR DE LA VUE ==="

# Changer le template utilisé dans practitioners.py
sed -i "s/practitioner_detail_safe.html/practitioner_detail_modern.html/g" apps/competitions/views/club/practitioners.py

# Vérifier
grep -n "practitioner_detail_modern" apps/competitions/views/club/practitioners.py

echo "Vue mise à jour"

# 4. Redémarrer gunicorn
echo ""
echo "=== 4. REDÉMARRAGE ==="
pkill -f gunicorn
sleep 2
/var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8888 --workers 3 --daemon

echo ""
echo "=== TERMINÉ ==="
echo "Testez sur: https://martialcomp.com/en/competitions/club/practitioners/88/"
EOF
```

## Test après déploiement

1. Aller sur `https://martialcomp.com/en/competitions/club/practitioners/88/`
2. Vérifier que le nouveau design avec fond sombre s'affiche
3. Tester les onglets Parcours, Documents, ID Card
4. Vérifier les boutons "Modifier les détails" et "Voir l'espace membre"

## Rollback si problème

```bash
ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Restaurer le backup de practitioners.py
BACKUP=$(ls -t apps/competitions/views/club/practitioners.py.backup_* | head -1)
cp "$BACKUP" apps/competitions/views/club/practitioners.py

# Redémarrer
pkill -f gunicorn && sleep 2 && /var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8888 --workers 3 --daemon

echo "Rollback effectué"
EOF
```
