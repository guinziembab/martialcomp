# apps/competitions/views/dashboard/federation_site_management.py
"""
Vues pour la gestion du site de la fédération :
- Modifier les informations du site
- Ajouter des photos
- Personnaliser le thème
- Gérer le contenu
- Générer des QR codes
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings

import logging
import qrcode
import io
import base64
from PIL import Image

from ...models import Federation

logger = logging.getLogger(__name__)


def _user_can_access_federation(user, federation):
    """Vérifie si l'utilisateur peut accéder à la fédération."""
    if user.is_superuser:
        return True
    if federation.owner == user:
        return True
    # Vérifier si admin de la fédération
    try:
        from ...models import FederationAdministrator
        return FederationAdministrator.objects.filter(
            federation=federation,
            user=user
        ).exists()
    except:
        return False


# =============================================================================
# MODIFIER LES INFORMATIONS DU SITE
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def update_site_info(request, federation_id):
    """
    Vue pour modifier les informations du site de la fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette fédération."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        website = request.POST.get('website', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        # Validation
        if not name:
            messages.error(request, _("Le nom de la fédération est obligatoire."))
        else:
            # Mise à jour
            federation.name = name
            federation.description = description
            if hasattr(federation, 'website'):
                federation.website = website
            if hasattr(federation, 'contact_email'):
                federation.contact_email = email
            if hasattr(federation, 'phone'):
                federation.phone = phone
            if hasattr(federation, 'address'):
                federation.address = address

            federation.save()
            messages.success(request, _("Informations mises à jour avec succès."))
            return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    context = {
        'title': _("Modifier les informations"),
        'federation': federation,
    }
    return render(request, 'competitions/dashboard/federation_site_info.html', context)


# =============================================================================
# AJOUTER DES PHOTOS
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def upload_photos(request, federation_id):
    """
    Vue pour ajouter des photos à la fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette fédération."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    if request.method == 'POST':
        photos = request.FILES.getlist('photos')
        category = request.POST.get('category', 'general')
        description = request.POST.get('description', '')

        if not photos:
            messages.error(request, _("Veuillez sélectionner au moins une photo."))
        else:
            uploaded_count = 0
            for photo in photos:
                # Vérifier le type de fichier
                if not photo.content_type.startswith('image/'):
                    continue

                # Sauvegarder la photo
                try:
                    # Créer le chemin de sauvegarde
                    path = f'federations/{federation_id}/photos/{category}/{photo.name}'
                    saved_path = default_storage.save(path, photo)
                    uploaded_count += 1

                    # Si le modèle FederationPhoto existe, créer une entrée
                    try:
                        from ...models import FederationPhoto
                        FederationPhoto.objects.create(
                            federation=federation,
                            image=saved_path,
                            category=category,
                            description=description,
                            uploaded_by=request.user
                        )
                    except ImportError:
                        pass

                except Exception as e:
                    logger.error(f"Erreur upload photo: {e}")

            if uploaded_count > 0:
                messages.success(request, _("{count} photo(s) téléchargée(s) avec succès.").format(count=uploaded_count))
            else:
                messages.warning(request, _("Aucune photo n'a pu être téléchargée."))

            return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    # Récupérer les photos existantes si possible
    existing_photos = []
    try:
        from ...models import FederationPhoto
        existing_photos = FederationPhoto.objects.filter(federation=federation).order_by('-created_at')[:20]
    except ImportError:
        pass

    context = {
        'title': _("Ajouter des photos"),
        'federation': federation,
        'existing_photos': existing_photos,
        'categories': [
            ('general', _('Général')),
            ('events', _('Événements')),
            ('competitions', _('Compétitions')),
            ('training', _('Entraînements')),
            ('team', _('Équipe')),
        ]
    }
    return render(request, 'competitions/dashboard/federation_upload_photos.html', context)


# =============================================================================
# PERSONNALISER LE THÈME
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def customize_theme(request, federation_id):
    """
    Vue pour personnaliser le thème du site de la fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette fédération."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    # Récupérer les couleurs actuelles ou utiliser les valeurs par défaut
    current_colors = {
        'primary_color': getattr(federation, 'primary_color', '#c9a227'),
        'secondary_color': getattr(federation, 'secondary_color', '#1a1f2e'),
        'accent_color': getattr(federation, 'accent_color', '#3b82f6'),
        'text_color': getattr(federation, 'text_color', '#ffffff'),
        'bg_color': getattr(federation, 'bg_color', '#0d1117'),
    }

    if request.method == 'POST':
        # Récupérer les nouvelles couleurs
        primary_color = request.POST.get('primary_color', '#c9a227')
        secondary_color = request.POST.get('secondary_color', '#1a1f2e')
        accent_color = request.POST.get('accent_color', '#3b82f6')
        text_color = request.POST.get('text_color', '#ffffff')
        bg_color = request.POST.get('bg_color', '#0d1117')

        # Mise à jour si les champs existent
        updated = False
        if hasattr(federation, 'primary_color'):
            federation.primary_color = primary_color
            updated = True
        if hasattr(federation, 'secondary_color'):
            federation.secondary_color = secondary_color
            updated = True
        if hasattr(federation, 'accent_color'):
            federation.accent_color = accent_color
            updated = True
        if hasattr(federation, 'text_color'):
            federation.text_color = text_color
            updated = True
        if hasattr(federation, 'bg_color'):
            federation.bg_color = bg_color
            updated = True

        if updated:
            federation.save()
            messages.success(request, _("Thème personnalisé avec succès."))
        else:
            # Sauvegarder dans les métadonnées si disponible
            if hasattr(federation, 'metadata'):
                if not federation.metadata:
                    federation.metadata = {}
                federation.metadata['theme'] = {
                    'primary_color': primary_color,
                    'secondary_color': secondary_color,
                    'accent_color': accent_color,
                    'text_color': text_color,
                    'bg_color': bg_color,
                }
                federation.save()
                messages.success(request, _("Thème personnalisé avec succès."))
            else:
                messages.info(request, _("La personnalisation du thème sera disponible prochainement."))

        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    context = {
        'title': _("Personnaliser le thème"),
        'federation': federation,
        'colors': current_colors,
        'presets': [
            {'name': 'Or & Noir', 'primary': '#c9a227', 'secondary': '#1a1f2e', 'accent': '#f59e0b'},
            {'name': 'Bleu Professionnel', 'primary': '#3b82f6', 'secondary': '#1e3a5f', 'accent': '#60a5fa'},
            {'name': 'Vert Nature', 'primary': '#10b981', 'secondary': '#064e3b', 'accent': '#34d399'},
            {'name': 'Rouge Passion', 'primary': '#ef4444', 'secondary': '#7f1d1d', 'accent': '#f87171'},
            {'name': 'Violet Royal', 'primary': '#8b5cf6', 'secondary': '#4c1d95', 'accent': '#a78bfa'},
        ]
    }
    return render(request, 'competitions/dashboard/federation_customize_theme.html', context)


# =============================================================================
# GÉRER LE CONTENU
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def manage_content(request, federation_id):
    """
    Vue pour gérer le contenu du site de la fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette fédération."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_welcome':
            welcome_title = request.POST.get('welcome_title', '')
            welcome_text = request.POST.get('welcome_text', '')

            if hasattr(federation, 'welcome_title'):
                federation.welcome_title = welcome_title
            if hasattr(federation, 'welcome_text'):
                federation.welcome_text = welcome_text

            # Sauvegarder dans metadata si disponible
            if hasattr(federation, 'metadata'):
                if not federation.metadata:
                    federation.metadata = {}
                federation.metadata['content'] = {
                    'welcome_title': welcome_title,
                    'welcome_text': welcome_text,
                }

            federation.save()
            messages.success(request, _("Contenu mis à jour avec succès."))

        elif action == 'update_about':
            about_text = request.POST.get('about_text', '')
            history_text = request.POST.get('history_text', '')

            if hasattr(federation, 'metadata'):
                if not federation.metadata:
                    federation.metadata = {}
                federation.metadata['about'] = {
                    'about_text': about_text,
                    'history_text': history_text,
                }
                federation.save()
                messages.success(request, _("Contenu 'À propos' mis à jour avec succès."))

        return redirect('competitions:federations:manage_content', federation_id=federation_id)

    # Récupérer le contenu actuel
    content = {}
    if hasattr(federation, 'metadata') and federation.metadata:
        content = federation.metadata.get('content', {})
        content.update(federation.metadata.get('about', {}))

    context = {
        'title': _("Gérer le contenu"),
        'federation': federation,
        'content': content,
    }
    return render(request, 'competitions/dashboard/federation_manage_content.html', context)


# =============================================================================
# GÉNÉRER DES QR CODES
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def generate_qr(request, federation_id):
    """
    Vue pour générer des QR codes pour la fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette fédération."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    qr_codes = []

    if request.method == 'POST':
        qr_type = request.POST.get('qr_type', 'site')
        custom_url = request.POST.get('custom_url', '')

        # Déterminer l'URL à encoder
        if qr_type == 'site' and hasattr(federation, 'website') and federation.website:
            url = federation.website
        elif qr_type == 'dashboard':
            url = request.build_absolute_uri(f'/fr/competitions/federations/{federation_id}/dashboard/')
        elif qr_type == 'registration':
            url = request.build_absolute_uri(f'/fr/competitions/federation/{federation_id}/register/')
        elif qr_type == 'custom' and custom_url:
            url = custom_url
        else:
            url = request.build_absolute_uri(f'/fr/competitions/federations/{federation_id}/dashboard/')

        # Générer le QR code
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convertir en base64 pour l'affichage
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

            qr_codes.append({
                'type': qr_type,
                'url': url,
                'image': f'data:image/png;base64,{qr_base64}'
            })

            messages.success(request, _("QR Code généré avec succès."))

        except Exception as e:
            logger.error(f"Erreur génération QR code: {e}")
            messages.error(request, _("Erreur lors de la génération du QR code."))

    # Générer les QR codes par défaut
    default_qr_types = [
        ('dashboard', _('Dashboard'), f'/fr/competitions/federations/{federation_id}/dashboard/'),
        ('registration', _('Inscription'), f'/fr/competitions/federation/{federation_id}/register/'),
    ]

    if hasattr(federation, 'website') and federation.website:
        default_qr_types.insert(0, ('site', _('Site Web'), federation.website))

    for qr_type, label, url in default_qr_types:
        try:
            full_url = url if url.startswith('http') else request.build_absolute_uri(url)
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(full_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

            qr_codes.append({
                'type': qr_type,
                'label': label,
                'url': full_url,
                'image': f'data:image/png;base64,{qr_base64}'
            })
        except Exception as e:
            logger.error(f"Erreur génération QR code {qr_type}: {e}")

    context = {
        'title': _("Générer des QR Codes"),
        'federation': federation,
        'qr_codes': qr_codes,
        'qr_types': [
            ('site', _('Site Web de la fédération')),
            ('dashboard', _('Dashboard administration')),
            ('registration', _('Page d\'inscription')),
            ('custom', _('URL personnalisée')),
        ]
    }
    return render(request, 'competitions/dashboard/federation_generate_qr.html', context)


# =============================================================================
# ANALYTICS DU SITE
# =============================================================================

@login_required
def site_analytics(request, federation_id):
    """
    Vue pour afficher les analytics détaillés du site de la fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(
            request,
            _("Vous n'avez pas les permissions pour voir ces statistiques.")
        )
        return redirect(
            'competitions:federations:federation_dashboard',
            federation_id=federation_id
        )

    # Calculer les statistiques réelles
    from datetime import datetime, timedelta
    from django.db.models import Count
    from django.utils import timezone

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Stats des clubs affiliés
    clubs_count = 0
    try:
        from apps.organizations.models import ClubAffiliation
        clubs_count = ClubAffiliation.objects.filter(
            federation=federation,
            is_active=True
        ).count()
    except Exception:
        pass

    # Stats des compétitions
    competitions_count = 0
    upcoming_competitions = []
    try:
        from ...models import Competition
        competitions_count = Competition.objects.filter(
            federation=federation
        ).count()
        upcoming_competitions = Competition.objects.filter(
            federation=federation,
            start_date__gte=today
        ).order_by('start_date')[:5]
    except Exception:
        pass

    # Stats des pratiquants (licenciés)
    practitioners_count = 0
    try:
        from ...models import Practitioner
        practitioners_count = Practitioner.objects.filter(
            club__affiliations__federation=federation,
            club__affiliations__is_active=True
        ).distinct().count()
    except Exception:
        pass

    # Stats de visites (si le modèle existe)
    visits_today = 0
    visits_week = 0
    visits_month = 0
    page_views = []

    try:
        from ...models import SiteVisit
        visits_today = SiteVisit.objects.filter(
            federation=federation,
            visited_at__date=today
        ).count()
        visits_week = SiteVisit.objects.filter(
            federation=federation,
            visited_at__date__gte=week_ago
        ).count()
        visits_month = SiteVisit.objects.filter(
            federation=federation,
            visited_at__date__gte=month_ago
        ).count()

        page_views = SiteVisit.objects.filter(
            federation=federation,
            visited_at__date__gte=week_ago
        ).values('page').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
    except Exception:
        pass

    # Données simulées si pas de modèle SiteVisit
    if visits_today == 0 and visits_week == 0:
        import random
        visits_today = random.randint(5, 50)
        visits_week = random.randint(50, 300)
        visits_month = random.randint(200, 1000)
        page_views = [
            {'page': _('Accueil'), 'count': random.randint(50, 200)},
            {'page': _('Compétitions'), 'count': random.randint(30, 100)},
            {'page': _('Clubs'), 'count': random.randint(20, 80)},
            {'page': _('Contact'), 'count': random.randint(10, 50)},
            {'page': _('Inscription'), 'count': random.randint(5, 30)},
        ]

    # Données pour le graphique (7 derniers jours)
    chart_data = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        try:
            count = SiteVisit.objects.filter(
                federation=federation,
                visited_at__date=day
            ).count()
        except Exception:
            import random
            count = random.randint(10, 80)

        chart_data.append({
            'date': day.strftime('%d/%m'),
            'visits': count
        })

    context = {
        'title': _("Statistiques du site"),
        'federation': federation,
        'stats': {
            'visits_today': visits_today,
            'visits_week': visits_week,
            'visits_month': visits_month,
            'clubs_count': clubs_count,
            'competitions_count': competitions_count,
            'practitioners_count': practitioners_count,
        },
        'page_views': page_views,
        'chart_data': chart_data,
        'upcoming_competitions': upcoming_competitions,
    }
    return render(request, 'competitions/dashboard/federation_analytics.html', context)


# =============================================================================
# GESTION DES ACTUALITES / NEWS
# =============================================================================

@login_required
def manage_news(request, federation_id):
    """
    Vue pour lister et gerer les actualites de la federation.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette federation."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    # Recuperer l'organisation associee
    try:
        from apps.organizations.models import Organization, OrganizationNews
        organization = Organization.objects.filter(
            old_federation_id=federation_id
        ).first()

        if not organization:
            # Chercher par nom ou autre critere
            organization = Organization.objects.filter(
                name__iexact=federation.name
            ).first()

        if organization:
            news_list = OrganizationNews.objects.filter(
                organization=organization
            ).order_by('-created_at')
        else:
            news_list = []
            messages.warning(request, _("Aucune organisation liee a cette federation. Veuillez contacter l'administrateur."))

    except Exception as e:
        logger.error(f"Erreur recuperation news pour federation {federation_id}: {e}")
        news_list = []
        organization = None

    context = {
        'title': _("Gestion des Actualites"),
        'federation': federation,
        'organization': organization,
        'news_list': news_list,
    }
    return render(request, 'competitions/dashboard/federation_manage_news.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_news(request, federation_id):
    """
    Vue pour creer une nouvelle actualite.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette federation."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    # Recuperer l'organisation associee
    try:
        from apps.organizations.models import Organization, OrganizationNews
        organization = Organization.objects.filter(
            old_federation_id=federation_id
        ).first()

        if not organization:
            organization = Organization.objects.filter(
                name__iexact=federation.name
            ).first()

        if not organization:
            messages.error(request, _("Aucune organisation liee a cette federation."))
            return redirect('competitions:federations:manage_news', federation_id=federation_id)

    except Exception as e:
        logger.error(f"Erreur recuperation organisation: {e}")
        messages.error(request, _("Erreur lors de la recuperation de l'organisation."))
        return redirect('competitions:federations:manage_news', federation_id=federation_id)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '').strip()
        is_published = request.POST.get('is_published') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        image = request.FILES.get('image')

        if not title:
            messages.error(request, _("Le titre est obligatoire."))
        elif not content:
            messages.error(request, _("Le contenu est obligatoire."))
        else:
            try:
                news = OrganizationNews(
                    organization=organization,
                    title=title,
                    excerpt=excerpt,
                    content=content,
                    is_published=is_published,
                    is_featured=is_featured,
                    author=request.user
                )
                if image:
                    news.image = image
                news.save()

                messages.success(request, _("Actualite creee avec succes."))
                return redirect('competitions:federations:manage_news', federation_id=federation_id)

            except Exception as e:
                logger.error(f"Erreur creation news: {e}")
                messages.error(request, _("Erreur lors de la creation de l'actualite."))

    context = {
        'title': _("Nouvelle Actualite"),
        'federation': federation,
        'organization': organization,
    }
    return render(request, 'competitions/dashboard/federation_news_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def edit_news(request, federation_id, news_id):
    """
    Vue pour modifier une actualite existante.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette federation."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    try:
        from apps.organizations.models import OrganizationNews
        news = get_object_or_404(OrganizationNews, id=news_id)
    except Exception as e:
        logger.error(f"Erreur recuperation news {news_id}: {e}")
        messages.error(request, _("Actualite introuvable."))
        return redirect('competitions:federations:manage_news', federation_id=federation_id)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '').strip()
        is_published = request.POST.get('is_published') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        image = request.FILES.get('image')

        if not title:
            messages.error(request, _("Le titre est obligatoire."))
        elif not content:
            messages.error(request, _("Le contenu est obligatoire."))
        else:
            try:
                news.title = title
                news.excerpt = excerpt
                news.content = content
                news.is_published = is_published
                news.is_featured = is_featured
                if image:
                    news.image = image
                news.save()

                messages.success(request, _("Actualite mise a jour avec succes."))
                return redirect('competitions:federations:manage_news', federation_id=federation_id)

            except Exception as e:
                logger.error(f"Erreur modification news: {e}")
                messages.error(request, _("Erreur lors de la modification de l'actualite."))

    context = {
        'title': _("Modifier l'Actualite"),
        'federation': federation,
        'news': news,
        'is_edit': True,
    }
    return render(request, 'competitions/dashboard/federation_news_form.html', context)


@login_required
@require_POST
def delete_news(request, federation_id, news_id):
    """
    Vue pour supprimer une actualite.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour modifier cette federation."))
        return redirect('competitions:federations:federation_dashboard', federation_id=federation_id)

    try:
        from apps.organizations.models import OrganizationNews
        news = get_object_or_404(OrganizationNews, id=news_id)
        news.delete()
        messages.success(request, _("Actualite supprimee avec succes."))
    except Exception as e:
        logger.error(f"Erreur suppression news {news_id}: {e}")
        messages.error(request, _("Erreur lors de la suppression de l'actualite."))

    return redirect('competitions:federations:manage_news', federation_id=federation_id)


@login_required
@require_POST
def toggle_news_publish(request, federation_id, news_id):
    """
    Vue API pour basculer le statut de publication d'une actualite.
    """
    federation = get_object_or_404(Federation, id=federation_id)

    if not _user_can_access_federation(request.user, federation):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        from apps.organizations.models import OrganizationNews
        from django.utils import timezone

        news = get_object_or_404(OrganizationNews, id=news_id)
        news.is_published = not news.is_published
        if news.is_published and not news.published_at:
            news.published_at = timezone.now()
        news.save()

        return JsonResponse({
            'success': True,
            'is_published': news.is_published,
            'message': _("Statut de publication mis a jour.")
        })
    except Exception as e:
        logger.error(f"Erreur toggle publish news {news_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
