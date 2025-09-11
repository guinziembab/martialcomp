from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.competitions.models import Discipline, Practitioner, Club
from apps.competitions.utils.decorators import club_required, federation_required
from apps.grades.models import (
    Grade, 
    PractitionerGrade, 
    GradeCategory, 
    GradeExam, 
    GradeExamRegistration,
    GradeRequirement
)
from apps.grades.forms import (
    GradeForm, 
    PractitionerGradeForm, 
    GradeCategoryForm, 
    BulkGradeAssignmentForm,
    GradeExamForm,
    GradeExamRegistrationForm,
    GradeRequirementForm
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


# ========== Vues pour les Grades ==========

class GradeListView(ListView):
    model = Grade
    template_name = 'grades/grade_list.html'
    context_object_name = 'grades'
    paginate_by = 20
    
    def get_queryset(self):
        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Obtenir le queryset de base
        queryset = super().get_queryset()
        
        # Appliquer l'isolation organisationnelle si disponible
        try:
            org_queryset = get_organization_queryset(self.model, self.request.user)
            if org_queryset is not None:
                queryset = org_queryset
        except Exception:
            # En cas d'erreur avec l'isolation, continuer avec le queryset de base
            pass
        
        # Segmentation: limiter aux disciplines de l'organisation courante si disponible
        try:
            from apps.finances.currency_service import _get_request_organization  # lazy import
            org = _get_request_organization(self.request)
            if org is not None and hasattr(org, 'disciplines'):
                allowed = list(org.disciplines.values_list('id', flat=True))
                if allowed:
                    queryset = queryset.filter(discipline_id__in=allowed)
        except Exception:
            pass
        
        # Filtres
        discipline_id = self.request.GET.get('discipline')
        is_active = self.request.GET.get('is_active')
        category_id = self.request.GET.get('category')
        search_query = self.request.GET.get('q')
        
        if discipline_id:
            queryset = queryset.filter(discipline_id=discipline_id)
            
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')
            
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(color__icontains=search_query) |
                Q(discipline__name__icontains=search_query)
            )
            
        return queryset.order_by('discipline', 'level')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Disciplines visibles = celles de l'organisation
        try:
            from apps.finances.currency_service import _get_request_organization
            org = _get_request_organization(self.request)
            if org is not None and hasattr(org, 'disciplines'):
                context['disciplines'] = org.disciplines.all()
                # Segmenter les catégories si relation existante avec discipline
                context['categories'] = GradeCategory.objects.filter(discipline__in=context['disciplines'])
            else:
                context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
                # Pour GradeCategory, filtrer via discipline__organization
                disciplines = context['disciplines']
                context['categories'] = GradeCategory.objects.filter(discipline__in=disciplines)
        except Exception:
            context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
            # Pour GradeCategory, filtrer via discipline__organization
            disciplines = context['disciplines']
            context['categories'] = GradeCategory.objects.filter(discipline__in=disciplines)
        
        # Conserver les paramètres de filtre
        context['selected_discipline'] = self.request.GET.get('discipline', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        return context


class GradeDetailView(DetailView):
    model = Grade
    template_name = 'grades/grade_detail.html'
    context_object_name = 'grade'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grade = self.get_object()
        
        # Récupérer les pratiquants ayant ce grade
        context['practitioners'] = PractitionerGrade.objects.filter(
            grade=grade, 
            is_current=True
        ).select_related('practitioner').order_by('practitioner__last_name')
        
        # Récupérer les exigences du grade correctement
        # Au lieu d'utiliser grade.requirements.all() qui ne fonctionne pas
        context['requirements'] = GradeRequirement.objects.filter(grade=grade).order_by('order')
        
        # Grade précédent et suivant
        context['previous_grade'] = grade.previous_grade if hasattr(grade, 'previous_grade') else None
        context['next_grade'] = grade.next_grade if hasattr(grade, 'next_grade') else None
        
        return context


class GradeCreateView(LoginRequiredMixin, CreateView):
    model = Grade
    form_class = GradeForm
    template_name = 'grades/grade_form.html'
    success_url = reverse_lazy('grades:grade_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Ajouter un grade")
        context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("Le grade a été créé avec succès."))
        return super().form_valid(form)


class GradeUpdateView(LoginRequiredMixin, UpdateView):
    model = Grade
    form_class = GradeForm
    template_name = 'grades/grade_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier le grade")
        context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
        return context
    
    def get_success_url(self):
        return reverse('grades:grade_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, _("Le grade a été mis Ã  jour avec succès."))
        return super().form_valid(form)


class GradeDeleteView(LoginRequiredMixin, DeleteView):
    model = Grade
    template_name = 'grades/grade_confirm_delete.html'
    success_url = reverse_lazy('grades:grade_list')
    context_object_name = 'grade'
    
    def delete(self, request, *args, **kwargs):
        grade = self.get_object()
        
        # Vérifier si le grade est utilisé par des pratiquants
        if PractitionerGrade.objects.filter(grade=grade).exists():
            messages.error(request, _(
                "Ce grade ne peut pas Ãªtre supprimé car il est attribué Ã  des pratiquants. "
                "Veuillez le désactiver plutÃ´t que de le supprimer."
            ))
            return redirect('grades:grade_detail', pk=grade.pk)
        
        messages.success(request, _("Le grade a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)


# ========== Vues pour les Catégories de Grade ==========

class GradeCategoryListView(ListView):
    model = GradeCategory
    template_name = 'grades/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Obtenir le queryset de base
        queryset = super().get_queryset()
        
        # Pour GradeCategory, l'isolation se fait via discipline__organization
        # car le modèle n'a pas de champ organization direct
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            try:
                from apps.competitions.models.users import UserProfile
                profile = UserProfile.objects.get(user=self.request.user)
                if profile.organization:
                    # Filtrer via la relation discipline->organization
                    queryset = queryset.filter(discipline__organization=profile.organization)
                else:
                    queryset = queryset.none()
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
            except Exception:
                # En cas d'erreur, essayer via disciplines autorisées
                try:
                    from apps.finances.currency_service import _get_request_organization
                    org = _get_request_organization(self.request)
                    if org is not None and hasattr(org, 'disciplines'):
                        allowed = list(org.disciplines.values_list('id', flat=True))
                        if allowed:
                            queryset = queryset.filter(discipline_id__in=allowed)
                    else:
                        queryset = queryset.none()
                except Exception:
                    queryset = queryset.none()
        
        # Filtres
        discipline_id = self.request.GET.get('discipline')
        is_active = self.request.GET.get('is_active')
        search_query = self.request.GET.get('q')
        
        if discipline_id:
            queryset = queryset.filter(discipline_id=discipline_id)
            
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')
            
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(discipline__name__icontains=search_query)
            )
            
        return queryset.order_by('discipline', 'order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.finances.currency_service import _get_request_organization
            org = _get_request_organization(self.request)
            if org is not None and hasattr(org, 'disciplines'):
                context['disciplines'] = org.disciplines.all()
            else:
                context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
        except Exception:
            context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
        
        # Conserver les paramètres de filtre
        context['selected_discipline'] = self.request.GET.get('discipline', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        return context


class GradeCategoryCreateView(LoginRequiredMixin, CreateView):
    model = GradeCategory
    form_class = GradeCategoryForm
    template_name = 'grades/category_form.html'
    success_url = reverse_lazy('grades:category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Ajouter une catégorie de grade")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("La catégorie de grade a été créée avec succès."))
        return super().form_valid(form)


class GradeCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = GradeCategory
    form_class = GradeCategoryForm
    template_name = 'grades/category_form.html'
    success_url = reverse_lazy('grades:category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier la catégorie de grade")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("La catégorie de grade a été mise Ã  jour avec succès."))
        return super().form_valid(form)


class GradeCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = GradeCategory
    template_name = 'grades/category_confirm_delete.html'
    success_url = reverse_lazy('grades:category_list')
    context_object_name = 'category'
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        # Vérifier si la catégorie est utilisée par des grades
        if Grade.objects.filter(category=category).exists():
            messages.error(request, _(
                "Cette catégorie ne peut pas Ãªtre supprimée car elle est utilisée par des grades. "
                "Veuillez la désactiver plutÃ´t que de la supprimer."
            ))
            return redirect('grades:category_list')
        
        messages.success(request, _("La catégorie de grade a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)


# ========== Vues pour l'attribution de Grades aux Pratiquants ==========

@login_required
@club_required
def practitioner_grades(request, practitioner_id):
    """Affiche les grades d'un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = request.club
    
    # Récupérer le pratiquant en utilisant l'organisation du club
    organization = club.organization or club.as_organization
    practitioner = get_object_or_404(Practitioner, pk=practitioner_id, organization=organization)
    
    # Récupérer tous les grades du pratiquant
    grades = PractitionerGrade.objects.filter(practitioner=practitioner).order_by('-date_obtained')
    
    # Regrouper par discipline
    grades_by_discipline = {}
    for grade in grades:
        if grade.discipline not in grades_by_discipline:
            grades_by_discipline[grade.discipline] = []
        grades_by_discipline[grade.discipline].append(grade)
    
    context = {
        'practitioner': practitioner,
        'grades_by_discipline': grades_by_discipline,
        'club': club
    }
    
    return render(request, 'grades/practitioner_grades.html', context)


@login_required
@club_required
def add_practitioner_grade(request, practitioner_id):
    """Ajoute un grade Ã  un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = request.club
    
    # Récupérer le pratiquant en utilisant l'organisation du club
    organization = club.organization or club.as_organization
    practitioner = get_object_or_404(Practitioner, pk=practitioner_id, organization=organization)
    
    if request.method == 'POST':
        form = PractitionerGradeForm(request.POST, request.FILES, practitioner=practitioner)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.practitioner = practitioner
            
            # Si le grade actuel est défini, mettre Ã  jour les autres grades dans la mÃªme discipline
            if grade.is_current:
                PractitionerGrade.objects.filter(
                    practitioner=practitioner,
                    discipline=grade.discipline,
                    is_current=True
                ).update(is_current=False)
                
            grade.save()
            messages.success(request, _("Le grade a été attribué avec succès."))
            return redirect('grades:practitioner_grades', practitioner_id=practitioner.id)
    else:
        # Précharger la discipline si spécifiée
        discipline_id = request.GET.get('discipline')
        if discipline_id:
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                form = PractitionerGradeForm(practitioner=practitioner, discipline=discipline)
            except Discipline.DoesNotExist:
                form = PractitionerGradeForm(practitioner=practitioner)
        else:
            form = PractitionerGradeForm(practitioner=practitioner)
    
    # Récupérer les disciplines pratiquées par le pratiquant
    practitioner_disciplines = practitioner.disciplines.all()
    
    context = {
        'form': form,
        'practitioner': practitioner,
        'disciplines': practitioner_disciplines,
        'title': _("Ajouter un grade Ã  {}").format(practitioner.full_name),
        'submit_text': _("Attribuer le grade"),
    }
    
    return render(request, 'grades/assign_grade.html', context)


@login_required
@club_required
def edit_practitioner_grade(request, grade_id):
    """Modifie un grade attribué Ã  un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = request.club
    
    # Récupérer le grade en utilisant l'organisation du club
    organization = club.organization or club.as_organization
    grade = get_object_or_404(PractitionerGrade, pk=grade_id, practitioner__organization=organization)
    
    if request.method == 'POST':
        form = PractitionerGradeForm(request.POST, request.FILES, instance=grade, practitioner=grade.practitioner)
        if form.is_valid():
            updated_grade = form.save(commit=False)
            
            # Si le grade actuel est défini, mettre Ã  jour les autres grades dans la mÃªme discipline
            if updated_grade.is_current:
                PractitionerGrade.objects.filter(
                    practitioner=updated_grade.practitioner,
                    discipline=updated_grade.discipline,
                    is_current=True
                ).exclude(pk=updated_grade.pk).update(is_current=False)
                
            updated_grade.save()
            messages.success(request, _("Le grade a été mis Ã  jour avec succès."))
            return redirect('grades:practitioner_grades', practitioner_id=grade.practitioner.id)
    else:
        form = PractitionerGradeForm(instance=grade, practitioner=grade.practitioner)
    
    context = {
        'form': form,
        'practitioner': grade.practitioner,
        'grade': grade,
        'title': _("Modifier le grade de {}").format(grade.practitioner.full_name),
        'submit_text': _("Mettre Ã  jour le grade"),
    }
    
    return render(request, 'grades/assign_grade.html', context)


@login_required
@club_required
@require_POST
def delete_practitioner_grade(request, grade_id):
    """Supprime un grade attribué Ã  un pratiquant."""
    # Récupérer le club de l'utilisateur
    club = request.club
    
    # Récupérer le grade en utilisant l'organisation du club
    organization = club.organization or club.as_organization
    grade = get_object_or_404(PractitionerGrade, pk=grade_id, practitioner__organization=organization)
    practitioner = grade.practitioner
    
    # Supprimer le grade
    grade.delete()
    
    messages.success(request, _("Le grade a été supprimé avec succès."))
    return redirect('grades:practitioner_grades', practitioner_id=practitioner.id)


@login_required
@club_required
def bulk_grade_assignment(request):
    """Attribution de grades en masse."""
    # Récupérer le club de l'utilisateur
    club = request.club
    
    if request.method == 'POST':
        form = BulkGradeAssignmentForm(request.POST, club=club)
        if form.is_valid():
            discipline = form.cleaned_data['discipline']
            grade = form.cleaned_data['grade']
            practitioners = form.cleaned_data['practitioners']
            date_obtained = form.cleaned_data['date_obtained']
            awarded_by = form.cleaned_data['awarded_by']
            location = form.cleaned_data['location']
            notes = form.cleaned_data['notes']
            set_as_current = form.cleaned_data['set_as_current']
            
            success_count = 0
            error_count = 0
            
            with transaction.atomic():
                for practitioner in practitioners:
                    try:
                        # Vérifier l'Ã¢ge minimum
                        practitioner_age = (date_obtained - practitioner.birth_date).days // 365
                        if practitioner_age < grade.min_age:
                            error_count += 1
                            continue
                        
                        # Si on définit ce grade comme courant, désactiver les autres grades courants
                        if set_as_current:
                            PractitionerGrade.objects.filter(
                                practitioner=practitioner,
                                discipline=discipline,
                                is_current=True
                            ).update(is_current=False)
                        
                        # Créer le nouveau grade
                        PractitionerGrade.objects.create(
                            practitioner=practitioner,
                            grade=grade,
                            discipline=discipline,
                            date_obtained=date_obtained,
                            awarded_by=awarded_by,
                            location=location,
                            notes=notes,
                            is_current=set_as_current
                        )
                        
                        success_count += 1
                    except Exception:
                        error_count += 1
            
            if success_count > 0:
                messages.success(
                    request, 
                    _("{} grades attribués avec succès. {} erreurs.").format(success_count, error_count)
                )
            else:
                messages.error(
                    request,
                    _("Aucun grade n'a pu Ãªtre attribué. Veuillez vérifier les critères d'éligibilité.")
                )
            
            return redirect('grades:bulk_assignment')
    else:
        form = BulkGradeAssignmentForm(club=club)
    
    context = {
        'form': form,
        'title': _("Attribution de grades en masse"),
        'submit_text': _("Attribuer les grades"),
        'club': club
    }
    
    return render(request, 'grades/bulk_management.html', context)



@require_GET
def get_eligible_practitioners(request):
    """API pour récupérer les pratiquants éligibles pour un grade spécifique."""
    grade_id = request.GET.get('grade_id')
    club_id = request.GET.get('club_id')
    
    if not grade_id or not club_id:
        return JsonResponse({'error': 'Grade ID and Club ID are required'}, status=400)
    
    try:
        grade = Grade.objects.get(id=grade_id)
        # Récupérer le club puis son organisation
        club = Club.objects.get(id=club_id)
        organization = club.organization or club.as_organization
        if not organization:
            return JsonResponse({'error': 'Aucune organisation trouvée pour ce club'}, status=404)
        practitioners = Practitioner.objects.filter(organization=organization)
        
        # Filtrer les pratiquants éligibles (Ã¢ge minimum, etc.)
        today = timezone.now().date()
        eligible_practitioners = []
        
        for p in practitioners:
            age = (today - p.birth_date).days // 365
            if age >= grade.min_age:
                eligible_practitioners.append({
                    'id':
                        p.id,
                    'name': p.full_name,
                    'age': age,
                    'grade': p.grade if hasattr(p, 'grade') else ''
                })
        
        return JsonResponse({'practitioners': eligible_practitioners})
    except Grade.DoesNotExist:
        return JsonResponse({'error': 'Grade not found'}, status=404)
    except Club.DoesNotExist:
        return JsonResponse({'error': 'Club not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== Vues pour les Examens de Passage de Grade ==========

class GradeExamListView(ListView):
    model = GradeExam
    template_name = 'grades/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 10
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Obtenir le queryset de base et appliquer l'isolation organisationnelle
        queryset = super().get_queryset()
        try:
            org_queryset = get_organization_queryset(self.model, self.request.user)
            if org_queryset is not None:
                queryset = org_queryset
        except Exception:
            pass
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        
        # Filtres
        discipline_id = self.request.GET.get('discipline')
        status = self.request.GET.get('status')
        search_query = self.request.GET.get('q')
        upcoming = self.request.GET.get('upcoming') == 'true'
        
        if discipline_id:
            queryset = queryset.filter(discipline_id=discipline_id)
            
        if status:
            queryset = queryset.filter(status=status)
            
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(location__icontains=search_query) |
                Q(discipline__name__icontains=search_query)
            )
        
        if upcoming:
            today = timezone.now().date()
            queryset = queryset.filter(date__gte=today)
        
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
        
        # Conserver les paramètres de filtre
        context['selected_discipline'] = self.request.GET.get('discipline', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['upcoming'] = self.request.GET.get('upcoming', 'false')
        
        # Statistiques
        today = timezone.now().date()
        context['upcoming_exams_count'] = GradeExam.objects.filter(date__gte=today).count()
        context['past_exams_count'] = GradeExam.objects.filter(date__lt=today).count()
        
        return context


class GradeExamDetailView(DetailView):
    model = GradeExam
    template_name = 'grades/exam_detail.html'
    context_object_name = 'exam'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.get_object()
        
        # Récupérer les inscriptions Ã  l'examen
        context['registrations'] = exam.registrations.all().select_related('practitioner', 'target_grade')
        
        # Statistiques
        context['total_registrations'] = exam.registrations.count()
        context['approved_registrations'] = exam.registrations.filter(status='approved').count()
        context['pending_registrations'] = exam.registrations.filter(status='pending').count()
        context['passed_registrations'] = exam.registrations.filter(status='passed').count()
        context['failed_registrations'] = exam.registrations.filter(status='failed').count()
        
        # Vérifier si l'inscription est encore ouverte
        context['is_registration_open'] = exam.is_registration_open
        
        return context


class GradeExamCreateView(LoginRequiredMixin, CreateView):
    model = GradeExam
    form_class = GradeExamForm
    template_name = 'grades/exam_form.html'
    success_url = reverse_lazy('grades:exam_list')
    
    def get_initial(self):
        """Préremplir le formulaire avec les valeurs de l'URL."""
        initial = super().get_initial()
        # Récupérer la discipline depuis l'URL et l'ajouter aux valeurs initiales
        discipline_id = self.request.GET.get('discipline')
        if discipline_id:
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                initial['discipline'] = discipline
            except Discipline.DoesNotExist:
                pass
        return initial
    
    def get_form(self, form_class=None):
        """Personnaliser le formulaire avant de le rendre."""
        form = super().get_form(form_class)
        
        # Récupérer la discipline depuis l'URL ou la valeur du formulaire
        discipline_id = self.request.GET.get('discipline')
        if discipline_id and not form.is_bound:
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                form.fields['discipline'].initial = discipline.id
            except Discipline.DoesNotExist:
                pass
                
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Créer un examen de passage de grade")
        
        # Récupérer toutes les disciplines pour le sélecteur
        context['disciplines'] = get_organization_queryset(Discipline, self.request.user).order_by('name')
        
        # Récupérer la discipline sélectionnée (soit depuis l'URL, soit depuis le formulaire)
        discipline_id = self.request.GET.get('discipline')
        form_discipline = None
        
        if hasattr(self, 'object') and self.object and self.object.discipline:
            # Si l'objet existe déjÃ  et a une discipline
            form_discipline = self.object.discipline
        elif self.request.method == 'POST' and 'discipline' in self.request.POST:
            # Si le formulaire a été soumis avec une discipline
            try:
                form_discipline = Discipline.objects.get(id=self.request.POST.get('discipline'))
            except (Discipline.DoesNotExist, ValueError):
                pass
        elif discipline_id:
            # Si une discipline est spécifiée dans l'URL
            try:
                form_discipline = Discipline.objects.get(id=discipline_id)
            except (Discipline.DoesNotExist, ValueError):
                pass
        
        # Si nous avons une discipline, récupérer les grades correspondants
        if form_discipline:
            # Récupérer tous les grades de cette discipline
            available_grades = Grade.objects.filter(
                discipline=form_discipline,
                is_active=True
            ).order_by('level')
            
            context['available_grades'] = available_grades
            
            # Optionnel : organiser les grades par catégorie
            grades_by_category = {}
            for grade in available_grades:
                category_name = grade.category.name if grade.category else _("Sans catégorie")
                if category_name not in grades_by_category:
                    grades_by_category[category_name] = []
                grades_by_category[category_name].append(grade)
            
            context['available_grades_by_category'] = grades_by_category
        else:
            context['available_grades'] = []
            context['available_grades_by_category'] = {}
        
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Ajouter les grades disponibles
        if 'available_grades' in form.cleaned_data:
            self.object.available_grades.set(form.cleaned_data['available_grades'])
        
        messages.success(self.request, _("L'examen de passage de grade a été créé avec succès."))
        return response


class GradeExamUpdateView(LoginRequiredMixin, UpdateView):
    model = GradeExam
    form_class = GradeExamForm
    template_name = 'grades/exam_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier l'examen de passage de grade")
        context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
        return context
    
    def get_success_url(self):
        return reverse('grades:exam_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Mettre Ã  jour les grades disponibles
        if 'available_grades' in form.cleaned_data:
            self.object.available_grades.set(form.cleaned_data['available_grades'])
        
        messages.success(self.request, _("L'examen de passage de grade a été mis Ã  jour avec succès."))
        return response


class GradeExamDeleteView(LoginRequiredMixin, DeleteView):
    model = GradeExam
    template_name = 'grades/exam_confirm_delete.html'
    success_url = reverse_lazy('grades:exam_list')
    context_object_name = 'exam'
    
    def delete(self, request, *args, **kwargs):
        exam = self.get_object()
        
        # Vérifier si l'examen a des inscriptions
        if exam.registrations.exists():
            messages.error(request, _(
                "Cet examen ne peut pas Ãªtre supprimé car il a des inscriptions. "
                "Veuillez annuler l'examen plutÃ´t que de le supprimer."
            ))
            return redirect('grades:exam_detail', pk=exam.pk)
        
        messages.success(request, _("L'examen de passage de grade a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)


@login_required
@club_required
def register_for_exam(request, exam_id):
    """Inscrit un pratiquant Ã  un examen de passage de grade."""
    # Récupérer le club de l'utilisateur
    club = request.club
    
    # Récupérer l'examen
    exam = get_object_or_404(GradeExam, pk=exam_id)
    
    # Vérifier si l'inscription est encore ouverte
    if not exam.is_registration_open:
        messages.error(request, _("Les inscriptions pour cet examen sont fermées."))
        return redirect('grades:exam_detail', pk=exam.pk)
    
    if request.method == 'POST':
        form = GradeExamRegistrationForm(request.POST, exam=exam, club=club)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.exam = exam
            registration.save()
            
            messages.success(request, _("L'inscription Ã  l'examen a été enregistrée avec succès."))
            return redirect('grades:exam_detail', pk=exam.pk)
    else:
        form = GradeExamRegistrationForm(exam=exam, club=club)
    
    context = {
        'form': form,
        'exam': exam,
        'club': club,
        'title': _("Inscription Ã  l'examen de passage de grade"),
        'submit_text': _("S'inscrire Ã  l'examen"),
    }
    
    return render(request, 'grades/exam_registration_form.html', context)


@login_required
@require_POST
def update_exam_registration_status(request, registration_id):
    """Met Ã  jour le statut d'une inscription Ã  un examen."""
    # Récupérer l'inscription
    registration = get_object_or_404(GradeExamRegistration, pk=registration_id)
    
    # Vérifier les autorisations (Ã  adapter selon votre logique d'autorisation)
    if not request.user.is_staff and not hasattr(request.user, 'federation_admin_roles'):
        messages.error(request, _("Vous n'avez pas les autorisations nécessaires pour effectuer cette action."))
        return redirect('grades:exam_detail', pk=registration.exam.pk)
    
    # Récupérer le nouveau statut
    new_status = request.POST.get('status')
    if new_status not in dict(GradeExamRegistration.STATUS_CHOICES):
        messages.error(request, _("Statut invalide."))
        return redirect('grades:exam_detail', pk=registration.exam.pk)
    
    # Mettre Ã  jour le statut
    registration.status = new_status
    
    # Si le statut est "passed", ajouter automatiquement le grade au pratiquant
    if new_status == 'passed':
        # Vérifier si le grade n'a pas déjÃ  été attribué
        if not PractitionerGrade.objects.filter(
            practitioner=registration.practitioner,
            grade=registration.target_grade,
            date_obtained=timezone.now().date()
        ).exists():
            # Créer le grade pour le pratiquant
            PractitionerGrade.objects.create(
                practitioner=registration.practitioner,
                grade=registration.target_grade,
                discipline=registration.target_grade.discipline,
                date_obtained=timezone.now().date(),
                awarded_by=registration.exam.examiners,
                location=registration.exam.location,
                certificate_number=registration.certificate_number,
                is_current=True
            )
            
            # Désactiver les autres grades courants pour cette discipline
            PractitionerGrade.objects.filter(
                practitioner=registration.practitioner,
                discipline=registration.target_grade.discipline,
                is_current=True
            ).exclude(grade=registration.target_grade).update(is_current=False)
            
            # Mettre Ã  jour le statut du certificat
            registration.certificate_issued = True
    
    registration.save()
    
    messages.success(request, _("Le statut de l'inscription a été mis Ã  jour avec succès."))
    return redirect('grades:exam_detail', pk=registration.exam.pk)


@login_required
@require_POST
def cancel_exam_registration(request, registration_id):
    """Annule une inscription Ã  un examen."""
    # Récupérer l'inscription
    registration = get_object_or_404(GradeExamRegistration, pk=registration_id)
    
    # Vérifier les autorisations (Ã  adapter selon votre logique d'autorisation)
    has_permission = (
        request.user.is_staff or
        hasattr(request.user, 'federation_admin_roles') or
        (hasattr(request.user, 'club') and request.user.club == registration.practitioner.organization)
    )
    
    if not has_permission:
        messages.error(request, _("Vous n'avez pas les autorisations nécessaires pour effectuer cette action."))
        return redirect('grades:exam_detail', pk=registration.exam.pk)
    
    # Supprimer l'inscription
    registration.delete()
    
    messages.success(request, _("L'inscription Ã  l'examen a été annulée avec succès."))
    return redirect('grades:exam_detail', pk=registration.exam.pk)


# ========== Vues pour les Exigences de Grade ==========

class GradeRequirementListView(ListView):
    model = GradeRequirement
    template_name = 'grades/requirement_list.html'
    context_object_name = 'requirements'
    paginate_by = 20
    
    def get_queryset(self):
        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Obtenir le queryset de base
        queryset = super().get_queryset()
        
        # Pour GradeRequirement, l'isolation se fait via grade__discipline__organization
        # car le modèle n'a pas de champ organization direct
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            try:
                from apps.competitions.models.users import UserProfile
                profile = UserProfile.objects.get(user=self.request.user)
                if profile.organization:
                    # Filtrer via la relation grade->discipline->organization
                    queryset = queryset.filter(grade__discipline__organization=profile.organization)
                else:
                    queryset = queryset.none()
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
            except Exception:
                # En cas d'erreur, essayer via disciplines autorisées
                try:
                    from apps.finances.currency_service import _get_request_organization
                    org = _get_request_organization(self.request)
                    if org is not None and hasattr(org, 'disciplines'):
                        allowed = list(org.disciplines.values_list('id', flat=True))
                        if allowed:
                            queryset = queryset.filter(grade__discipline_id__in=allowed)
                    else:
                        queryset = queryset.none()
                except Exception:
                    queryset = queryset.none()
        
        # Filtres
        grade_id = self.request.GET.get('grade')
        discipline_id = self.request.GET.get('discipline')
        search_query = self.request.GET.get('q')
        
        if grade_id:
            queryset = queryset.filter(grade_id=grade_id)
            
        if discipline_id:
            queryset = queryset.filter(grade__discipline_id=discipline_id)
            
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(grade__name__icontains=search_query)
            )
            
        return queryset.order_by('grade', 'order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['disciplines'] = get_organization_queryset(Discipline, self.request.user)
        
        # Pour Grade, filtrer via discipline__organization car Grade n'a pas de champ organization
        disciplines = context['disciplines']
        context['grades'] = Grade.objects.filter(discipline__in=disciplines)
        
        # Conserver les paramètres de filtre
        context['selected_discipline'] = self.request.GET.get('discipline', '')
        context['selected_grade'] = self.request.GET.get('grade', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        return context


class GradeRequirementCreateView(LoginRequiredMixin, CreateView):
    model = GradeRequirement
    form_class = GradeRequirementForm
    template_name = 'grades/requirement_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Récupérer le grade si spécifié dans l'URL
        grade_id = self.request.GET.get('grade')
        if grade_id:
            try:
                grade = Grade.objects.get(id=grade_id)
                initial['grade'] = grade
            except Grade.DoesNotExist:
                pass
                
        # Si un grade est présélectionné, récupérer son ordre pour initialiser l'ordre de l'exigence
        if 'grade' in initial:
            # Trouver l'ordre le plus élevé des exigences existantes pour ce grade
            max_order = GradeRequirement.objects.filter(
                grade=initial['grade']
            ).aggregate(Max('order'))['order__max'] or 0
            initial['order'] = max_order + 1
            
        return initial
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Si une discipline est sélectionnée, filtrer les grades disponibles
        discipline_id = self.request.GET.get('discipline')
        if discipline_id:
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                # Filtrer les grades par discipline
                filtered_grades = Grade.objects.filter(
                    discipline=discipline,
                    is_active=True
                ).order_by('level')
                
                # Remplacer le queryset du champ grade
                form.fields['grade'].queryset = filtered_grades
                
                # Définir des attributs data sur le champ pour le débogage cÃ´té client
                form.fields['grade'].widget.attrs['data-discipline'] = discipline.id
                form.fields['grade'].widget.attrs['data-count'] = filtered_grades.count()
            except Discipline.DoesNotExist:
                # Laisser le queryset par défaut si la discipline n'existe pas
                pass
        else:
            # Si pas de discipline sélectionnée, vider le queryset des grades
            # pour forcer l'utilisateur Ã  choisir une discipline d'abord
            form.fields['grade'].queryset = Grade.objects.none()
                
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Ajouter une exigence de grade")
        
        # Ajouter la liste des disciplines pour le sélecteur
        context['disciplines'] = Discipline.objects.filter(is_active=True).order_by('name')
        
        # Récupérer la discipline sélectionnée si présente
        discipline_id = self.request.GET.get('discipline')
        if discipline_id:
            context['selected_discipline'] = discipline_id
            
            # Ajouter les grades filtrés dans le contexte pour vérification
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                filtered_grades = Grade.objects.filter(
                    discipline=discipline,
                    is_active=True
                ).order_by('level')
                context['filtered_grades'] = filtered_grades
                context['filtered_grades_count'] = filtered_grades.count()
            except Discipline.DoesNotExist:
                pass
            
        # Si un grade est spécifié dans l'URL ou le POST, l'ajouter au contexte
        grade_id = self.request.GET.get('grade') or self.request.POST.get('grade')
        if grade_id:
            try:
                grade = Grade.objects.get(id=grade_id)
                context['grade'] = grade
            except Grade.DoesNotExist:
                pass
                
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("L'exigence de grade a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        if self.object and self.object.grade:
            return reverse('grades:grade_detail', kwargs={'pk': self.object.grade.id})
        return reverse_lazy('grades:requirement_list')


class GradeRequirementUpdateView(LoginRequiredMixin, UpdateView):
    model = GradeRequirement
    form_class = GradeRequirementForm
    template_name = 'grades/requirement_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier l'exigence de grade")
        context['grade'] = self.object.grade
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("L'exigence de grade a été mise Ã  jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        grade_id = self.object.grade.id
        return reverse('grades:grade_detail', kwargs={'pk': grade_id})


class GradeRequirementDeleteView(LoginRequiredMixin, DeleteView):
    model = GradeRequirement
    template_name = 'grades/requirement_confirm_delete.html'
    context_object_name = 'requirement'
    
    def get_success_url(self):
        grade_id = self.object.grade.id
        return reverse('grades:grade_detail', kwargs={'pk': grade_id})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("L'exigence de grade a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)


# ========== Vues pour l'API et les requÃªtes AJAX ==========

@require_GET
def search_grade_system(request):
    """API pour rechercher dans le système de grades."""
    search_query = request.GET.get('q', '')
    discipline_id = request.GET.get('discipline', '')
    
    if not search_query and not discipline_id:
        return JsonResponse({'results': []})
    
    # Construire la requÃªte
    queryset = Grade.objects.filter(is_active=True)
    
    if discipline_id:
        queryset = queryset.filter(discipline_id=discipline_id)
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | 
            Q(color__icontains=search_query) |
            Q(discipline__name__icontains=search_query)
        )
    
    # Limiter les résultats pour des performances
    grades = queryset.order_by('discipline', 'level')[:20]
    
    results = []
    for grade in grades:
        results.append({
            'id': grade.id,
            'name': grade.name,
            'discipline': grade.discipline.name,
            'color': grade.color,
            'level': grade.level,
            'category': grade.category.name if grade.category else '',
        })
    
    return JsonResponse({'results': results})


@require_GET
def get_discipline_grade_structure(request, discipline_id):
    """API pour récupérer la structure complète des grades d'une discipline."""
    try:
        discipline = Discipline.objects.get(pk=discipline_id)
        
        # Récupérer les catégories de grade pour cette discipline
        categories = GradeCategory.objects.filter(discipline=discipline).order_by('order')
        
        # Récupérer tous les grades pour cette discipline
        grades = Grade.objects.filter(discipline=discipline).order_by('level')
        
        # Construire la structure
        structure = {
            'discipline': {
                'id': discipline.id,
                'name': discipline.name,
                'country_origin': discipline.country_origin,
            },
            'categories': [],
            'grades': []
        }
        
        # Ajouter les catégories
        for category in categories:
            structure['categories'].append({
                'id': category.id,
                'name': category.name,
                'order': category.order,
                'description': category.description,
            })
        
        # Ajouter les grades
        for grade in grades:
            structure['grades'].append({
                'id': grade.id,
                'name': grade.name,
                'color': grade.color,
                'color_code': grade.color_code,
                'level': grade.level,
                'min_age': grade.min_age,
                'is_dan_grade': grade.is_dan_grade,
                'category_id': grade.category_id if grade.category else None,
                'category_name': grade.category.name if grade.category else None,
            })
        
        return JsonResponse(structure)
    except Discipline.DoesNotExist:
        return JsonResponse({'error': 'Discipline not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def import_grades(request):
    """Vue pour importer des grades en masse."""
    if request.method == 'POST' and request.FILES.get('grades_file'):
        import json
        from django.db import transaction
        
        try:
            grades_file = request.FILES['grades_file']
            grades_data = json.loads(grades_file.read().decode('utf-8'))
            
            with transaction.atomic():
                success_count = 0
                error_count = 0
                
                for grade_data in grades_data.get('grades', []):
                    try:
                        # Récupérer ou créer la discipline
                        discipline_name = grade_data.get('discipline')
                        discipline, _ = Discipline.objects.get_or_create(
                            name=discipline_name,
                            defaults={'description': f'Discipline {discipline_name}'}
                        )
                        
                        # Récupérer ou créer la catégorie de grade
                        category_name = grade_data.get('category')
                        if category_name:
                            category, _ = GradeCategory.objects.get_or_create(
                                name=category_name,
                                discipline=discipline,
                                defaults={'order': 0}
                            )
                        else:
                            category = None
                        
                        # Créer ou mettre Ã  jour le grade
                        grade, created = Grade.objects.update_or_create(
                            name=grade_data.get('name'),
                            discipline=discipline,
                            defaults={
                                'category': category,
                                'color': grade_data.get('color', ''),
                                'color_code': grade_data.get('color_code', ''),
                                'level': grade_data.get('level', 0),
                                'min_age': grade_data.get('min_age', 0),
                                'is_dan_grade': 'dan' in grade_data.get('name', '').lower() or 'dang' in grade_data.get('name', '').lower(),
                                'is_active': True,
                                'order': grade_data.get('level', 0),
                            }
                        )
                        
                        success_count += 1
                    except Exception:
                        error_count += 1
                
                messages.success(
                    request, 
                    _("{} grades importés avec succès. {} erreurs.").format(success_count, error_count)
                )
        except Exception as e:
            messages.error(request, _("Erreur lors de l'importation des grades: {}").format(str(e)))
    
    return render(request, 'grades/import_grades.html')


@login_required
def export_grades(request):
    """Vue pour exporter les grades."""
    import json
    from django.http import HttpResponse
    
    # Filtres
    discipline_id = request.GET.get('discipline')
    
    # Construire la requête via l'isolation par discipline
    try:
        disciplines = get_organization_queryset(Discipline, request.user)
        queryset = Grade.objects.filter(discipline__in=disciplines)
    except Exception:
        # Fallback : tous les grades si erreur
        queryset = Grade.objects.all()
    
    if discipline_id:
        queryset = queryset.filter(discipline_id=discipline_id)
    
    # Récupérer les grades
    grades = queryset.order_by('discipline', 'level')
    
    # Construire les données Ã  exporter
    data = {
        'grades': []
    }
    
    for grade in grades:
        grade_data = {
            'id': grade.id,
            'name': grade.name,
            'discipline': grade.discipline.name,
            'category': grade.category.name if grade.category else '',
            'color': grade.color,
            'color_code': grade.color_code,
            'level': grade.level,
            'min_age': grade.min_age,
            'min_time_in_previous_grade': grade.min_time_in_previous_grade,
            'is_dan_grade': grade.is_dan_grade,
        }
        
        data['grades'].append(grade_data)
    
    # Créer la réponse JSON
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="grades_export.json"'
    
    return response


@require_GET
def categories_by_discipline(request):
    """Vue API pour récupérer les catégories d'une discipline."""
    discipline_id = request.GET.get('discipline_id')
    
    if not discipline_id:
        return JsonResponse({'categories': []})
    
    categories = GradeCategory.objects.filter(
        discipline_id=discipline_id,
        is_active=True
    ).order_by('order', 'name')
    
    data = [{'id': cat.id, 'name': cat.name} for cat in categories]
    
    return JsonResponse({'categories': data})

