from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

from .models import (
    DocumentFolder, DocumentTag, Document, DocumentShare, 
    DocumentComment, DocumentAccessLog
)
from .forms import (
    DocumentFolderForm, DocumentTagForm, DocumentUploadForm, 
    DocumentEditForm, DocumentShareForm, DocumentCommentForm
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def documents_dashboard(request):
    """Dashboard principal pour la gestion documentaire"""
    # Statistiques rapides
    user_documents = Document.objects.filter(created_by=request.user)
    shared_with_user = request.user.document_shares_received.all()
    
    stats = {
        'my_documents': user_documents.count(),
        'shared_with_me': shared_with_user.count(),
        'recent_uploads': user_documents.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
        'total_size': sum(doc.file_size for doc in user_documents if doc.file_size),
    }
    
    # Documents récents
    recent_documents = user_documents.order_by('-created_at')[:5]
    
    # Documents partagés avec moi récemment
    recent_shared = Document.objects.filter(
        shares__user=request.user,
        shares__created_at__gte=timezone.now() - timedelta(days=30)
    ).distinct().order_by('-shares__created_at')[:5]
    
    # Dossiers racine
    root_folders = DocumentFolder.objects.filter(
        Q(owner=request.user) | Q(is_public=True),
        parent__isnull=True
    ).annotate(
        document_count=Count('documents')
    )
    
    context = {
        'stats': stats,
        'recent_documents': recent_documents,
        'recent_shared': recent_shared,
        'root_folders': root_folders,
        'title': _('Gestion documentaire'),
    }
    
    return render(request, 'documents/dashboard.html', context)


@login_required
def folder_view(request, folder_id=None):
    """Vue d'un dossier spécifique"""
    folder = None
    if folder_id:
        folder = get_object_or_404(DocumentFolder, id=folder_id)
        
        # Vérifier les permissions d'accès
        if not (folder.is_public or folder.owner == request.user or request.user.is_superuser):
            messages.error(request, _("Vous n'avez pas accès Ã  ce dossier."))
            return redirect('documents:dashboard')
    
    # Sous-dossiers
    subfolders = DocumentFolder.objects.filter(
        parent=folder,
        # Permissions d'accès selon le rÃ´le
    ).filter(
        Q(owner=request.user) | Q(is_public=True)
    ).annotate(document_count=Count('documents'))
    
    # Documents dans ce dossier
    documents = Document.objects.filter(
        folder=folder,
        is_latest_version=True
    ).select_related('created_by', 'folder').prefetch_related('tags')
    
    # Filtrage selon les permissions
    if not request.user.is_superuser:
        documents = documents.filter(
            Q(created_by=request.user) | 
            Q(is_public=True) |
            Q(shares__user=request.user)
        ).distinct()
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Fil d'ariane
    breadcrumbs = []
    if folder:
        current = folder
        while current:
            breadcrumbs.insert(0, current)
            current = current.parent
    
    context = {
        'folder': folder,
        'subfolders': subfolders,
        'documents': page_obj,
        'breadcrumbs': breadcrumbs,
        'title': folder.name if folder else _('Documents'),
    }
    
    return render(request, 'documents/folder_view.html', context)


@login_required
def upload_document(request, folder_id=None):
    """Upload d'un nouveau document"""
    folder = None
    if folder_id:
        folder = get_object_or_404(DocumentFolder, id=folder_id)
        
        # Vérifier les permissions d'écriture
        if not (folder.owner == request.user or request.user.is_superuser):
            messages.error(request, _("Vous n'avez pas les permissions pour uploader dans ce dossier."))
            return redirect('documents:folder_view', folder_id=folder_id)
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            document = form.save()
            
            # Associer au dossier si spécifié
            if folder:
                document.folder = folder
                document.save()
            
            # Log de l'action
            DocumentAccessLog.objects.create(
                document=document,
                user=request.user,
                action=DocumentAccessLog.ACTION_EDIT,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'action': 'document_created'}
            )
            
            messages.success(request, _("Document uploadé avec succès."))
            return redirect('documents:folder_view', folder_id=folder_id if folder else None)
    else:
        form = DocumentUploadForm(user=request.user)
        if folder:
            form.fields['folder'].initial = folder
    
    context = {
        'form': form,
        'folder': folder,
        'title': _('Uploader un document'),
    }
    
    return render(request, 'documents/upload.html', context)


@login_required
def document_detail(request, document_id):
    """Vue détaillée d'un document"""
    document = get_object_or_404(Document, id=document_id)
    
    # Vérifier les permissions d'accès
    if not (document.created_by == request.user or 
            document.is_public or 
            DocumentShare.objects.filter(document=document, user=request.user).exists() or
            request.user.is_superuser):
        raise Http404(_("Document non trouvé"))
    
    # Enregistrer la consultation
    DocumentAccessLog.objects.create(
        document=document,
        user=request.user,
        action=DocumentAccessLog.ACTION_VIEW,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Incrementer le compteur de vues
    document.view_count += 1
    document.save(update_fields=['view_count'])
    
    # Commentaires
    comments = document.comments.filter(parent__isnull=True).select_related('author')
    comment_form = DocumentCommentForm(document=document, user=request.user)
    
    # Versions du document
    versions = Document.objects.filter(
        Q(id=document.id) | Q(parent=document) | Q(parent=document.parent)
    ).order_by('-version')
    
    # Permissions de l'utilisateur sur ce document
    can_edit = (document.created_by == request.user or 
                request.user.is_superuser or
                DocumentShare.objects.filter(
                    document=document, 
                    user=request.user,
                    access_level__in=[DocumentShare.ACCESS_WRITE, DocumentShare.ACCESS_FULL]
                ).exists())
    
    can_share = (document.created_by == request.user or 
                 request.user.is_superuser or
                 DocumentShare.objects.filter(
                     document=document,
                     user=request.user,
                     access_level=DocumentShare.ACCESS_FULL
                 ).exists())
    
    context = {
        'document': document,
        'comments': comments,
        'comment_form': comment_form,
        'versions': versions,
        'can_edit': can_edit,
        'can_share': can_share,
        'title': document.title,
    }
    
    return render(request, 'documents/detail.html', context)


@login_required
def download_document(request, document_id):
    """Téléchargement d'un document"""
    document = get_object_or_404(Document, id=document_id)
    
    # Vérifier les permissions d'accès
    if not (document.created_by == request.user or 
            document.is_public or 
            DocumentShare.objects.filter(document=document, user=request.user).exists() or
            request.user.is_superuser):
        raise Http404(_("Document non trouvé"))
    
    # Enregistrer le téléchargement
    DocumentAccessLog.objects.create(
        document=document,
        user=request.user,
        action=DocumentAccessLog.ACTION_DOWNLOAD,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Incrementer le compteur de téléchargements
    document.download_count += 1
    document.save(update_fields=['download_count'])
    
    # Servir le fichier
    response = HttpResponse(document.file.read(), content_type=document.mime_type)
    response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
    
    return response


@login_required
def my_documents(request):
    """Liste des documents de l'utilisateur"""
    documents = Document.objects.filter(
        created_by=request.user,
        is_latest_version=True
    ).select_related('folder').prefetch_related('tags').order_by('-created_at')
    
    # Filtres
    folder_id = request.GET.get('folder')
    if folder_id:
        documents = documents.filter(folder_id=folder_id)
    
    document_type = request.GET.get('type')
    if document_type:
        documents = documents.filter(document_type=document_type)
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Options de filtrage
    folders = DocumentFolder.objects.filter(owner=request.user)
    document_types = Document._meta.get_field('document_type').choices
    
    context = {
        'documents': page_obj,
        'folders': folders,
        'document_types': document_types,
        'current_folder': folder_id,
        'current_type': document_type,
        'title': _('Mes documents'),
    }
    
    return render(request, 'documents/my_documents.html', context)


@login_required
def shared_with_me(request):
    """Documents partagés avec l'utilisateur"""
    document_shares = request.user.document_shares_received.select_related(
        'document', 'created_by'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(document_shares, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'document_shares': page_obj,
        'title': _('Documents partagés avec moi'),
    }
    
    return render(request, 'documents/shared_with_me.html', context)


@login_required
@require_http_methods(["POST"])
def add_comment(request, document_id):
    """Ajouter un commentaire Ã  un document"""
    document = get_object_or_404(Document, id=document_id)
    
    # Vérifier les permissions d'accès
    if not (document.created_by == request.user or 
            document.is_public or 
            DocumentShare.objects.filter(document=document, user=request.user).exists() or
            request.user.is_superuser):
        return JsonResponse({'error': _('Permissions insuffisantes')}, status=403)
    
    form = DocumentCommentForm(request.POST, document=document, user=request.user)
    if form.is_valid():
        comment = form.save()
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.get_full_name() or comment.author.username,
                'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
            }
        })
    else:
        return JsonResponse({'error': _('Commentaire invalide')}, status=400)


# Intégration spécifique pour les dashboards de rÃ´les

@login_required
def practitioner_documents(request):
    """Documents spécifiques aux pratiquants"""
    from apps.competitions.models import Practitioner
    
    try:
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Profil de pratiquant non trouvé."))
        return redirect('competitions:dashboard')
    
    # Documents associés au pratiquant
    documents = Document.objects.filter(
        Q(created_by=request.user) |
        Q(content_type=ContentType.objects.get_for_model(Practitioner), object_id=str(practitioner.id)) |
        Q(shares__user=request.user)
    ).filter(
        document_type__in=['certificate', 'diploma', 'license', 'medical']
    ).distinct().order_by('-created_at')
    
    # Documents par type
    certificates = documents.filter(document_type='certificate')
    medical_docs = documents.filter(document_type='medical')
    licenses = documents.filter(document_type='license')
    
    context = {
        'documents': documents[:10],  # 10 plus récents
        'certificates': certificates[:5],
        'medical_docs': medical_docs[:5],
        'licenses': licenses[:5],
        'practitioner': practitioner,
        'title': _('Mes documents de pratiquant'),
    }
    
    return render(request, 'documents/practitioner_documents.html', context)


@login_required
def judge_documents(request):
    """Documents spécifiques aux juges"""
    from apps.competitions.models import Judge
    
    try:
        judge = Judge.objects.get(practitioner__user=request.user)
    except Judge.DoesNotExist:
        messages.error(request, _("Profil de juge non trouvé."))
        return redirect('competitions:dashboard')
    
    # Documents associés au juge
    documents = Document.objects.filter(
        Q(created_by=request.user) |
        Q(content_type=ContentType.objects.get_for_model(Judge), object_id=str(judge.id)) |
        Q(shares__user=request.user)
    ).filter(
        document_type__in=['certificate', 'technical', 'training']
    ).distinct().order_by('-created_at')
    
    # Documents techniques
    technical_docs = documents.filter(document_type='technical')
    certifications = documents.filter(document_type='certificate')
    
    context = {
        'documents': documents[:10],
        'technical_docs': technical_docs[:5],
        'certifications': certifications[:5],
        'judge': judge,
        'title': _('Mes documents de juge'),
    }
    
    return render(request, 'documents/judge_documents.html', context)


@login_required
def club_documents(request):
    """Documents spécifiques aux clubs"""
    from apps.competitions.models import Club, Organization
    
    # Trouver les clubs/organisations gérés par l'utilisateur
    managed_orgs = Organization.objects.filter(
        members__user=request.user,
        members__role__in=['owner', 'admin', 'manager']
    )
    
    if not managed_orgs.exists():
        messages.error(request, _("Vous ne gérez aucun club ou organisation."))
        return redirect('competitions:dashboard')
    
    # Documents associés aux organisations
    documents = Document.objects.filter(
        Q(created_by=request.user) |
        Q(content_type=ContentType.objects.get_for_model(Organization), 
          object_id__in=[str(org.id) for org in managed_orgs]) |
        Q(shares__user=request.user)
    ).filter(
        document_type__in=['administrative', 'competition', 'training']
    ).distinct().order_by('-created_at')
    
    context = {
        'documents': documents[:10],
        'organizations': managed_orgs,
        'title': _('Documents de mes clubs'),
    }
    
    return render(request, 'documents/club_documents.html', context)

