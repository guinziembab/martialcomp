
@login_required
def register_for_exam(request, exam_id):
    """Inscrit des pratiquants a un examen via coches."""
    exam = get_object_or_404(GradeExam, pk=exam_id)

    if not exam.is_registration_open:
        messages.error(
            request,
            _("Les inscriptions pour cet examen sont fermees.")
        )
        return redirect('grades:exam_detail', pk=exam.pk)

    # Trouver l'organisation de l'utilisateur (GDPR)
    user_org = None

    # 1) Via le profil Practitioner de l'utilisateur
    user_pract = Practitioner.objects.filter(
        user=request.user
    ).select_related('organization').first()
    if user_pract and user_pract.organization:
        user_org = user_pract.organization

    # 2) Via le UserProfile.organization
    if not user_org:
        try:
            profile = request.user.userprofile
            if profile and profile.organization:
                user_org = profile.organization
        except Exception:
            pass

    # 3) Via les clubs administres par l'utilisateur
    if not user_org:
        try:
            administered_clubs = request.user.get_administered_clubs()
            if administered_clubs.exists():
                club = administered_clubs.first()
                user_org = club.organization or club.as_organization
        except Exception:
            pass

    # 4) Via OrganizationMember
    if not user_org:
        try:
            from apps.organizations.models import OrganizationMember
            membership = OrganizationMember.objects.filter(
                user=request.user
            ).select_related('organization').first()
            if membership:
                user_org = membership.organization
        except Exception:
            pass

    # 5) Via le club de la request (middleware)
    if not user_org:
        if hasattr(request, 'club') and request.club:
            club = request.club
            user_org = (getattr(club, 'organization', None)
                        or getattr(club, 'as_organization', None))

    # Filtrer les pratiquants par organisation (GDPR)
    if user_org:
        practitioners = Practitioner.objects.filter(
            organization=user_org
        ).select_related('grade', 'organization')
    elif request.user.is_staff or request.user.is_superuser:
        practitioners = Practitioner.objects.all().select_related(
            'grade', 'organization'
        )
    else:
        practitioners = Practitioner.objects.none()

    # Exclure les deja inscrits
    already = exam.registrations.values_list(
        'practitioner_id', flat=True
    )
    practitioners = practitioners.exclude(
        id__in=already
    ).order_by('last_name', 'first_name')

    available_grades = exam.available_grades.select_related(
        'discipline'
    ).order_by('level')

    if request.method == 'POST':
        selected_ids = request.POST.getlist('practitioners')
        target_grade_id = request.POST.get('target_grade')

        if not selected_ids:
            messages.error(
                request,
                _("Veuillez selectionner au moins un pratiquant.")
            )
        elif not target_grade_id:
            messages.error(
                request,
                _("Veuillez selectionner un grade vise.")
            )
        else:
            target_grade = get_object_or_404(
                Grade, pk=target_grade_id
            )
            count = 0
            for pid in selected_ids:
                pract = Practitioner.objects.filter(
                    pk=pid
                ).first()
                already_reg = GradeExamRegistration.objects.filter(
                    exam=exam, practitioner=pract
                ).exists()
                if pract and not already_reg:
                    GradeExamRegistration.objects.create(
                        exam=exam,
                        practitioner=pract,
                        target_grade=target_grade,
                        status='pending',
                    )
                    count += 1
            if count > 0:
                messages.success(
                    request,
                    _("%(count)d pratiquant(s) inscrit(s).")
                    % {'count': count}
                )
            return redirect(
                'grades:exam_detail', pk=exam.pk
            )

    context = {
        'exam': exam,
        'practitioners': practitioners,
        'available_grades': available_grades,
        'title': _("Inscription a l'examen"),
        'submit_text': _(
            "Inscrire les pratiquants selectionnes"
        ),
    }
    return render(
        request,
        'grades/exam_registration_form.html',
        context
    )

