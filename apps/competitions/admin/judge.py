from django.contrib import admin

# Tentative d'importation directe
try:
    from apps.competitions.models import JudgeQualification, JudgeAssignment
except ImportError:
    JudgeQualification = None
    JudgeAssignment = None

# Si JudgeCompetitionAssignment existe dans registrations.py
try:
    from apps.competitions.models import JudgeCompetitionAssignment
except ImportError:
    JudgeCompetitionAssignment = None

# Enregistrement conditionnel des modèles
if JudgeQualification:
    @admin.register(JudgeQualification)
    class JudgeQualificationAdmin(admin.ModelAdmin):
        list_display = ('practitioner', 'qualification_type', 'level', 'discipline', 'certified_date', 'is_valid')
        list_filter = ('qualification_type', 'level', 'discipline')
        search_fields = ('practitioner__first_name', 'practitioner__last_name', 'certificate_number')

if JudgeAssignment:
    @admin.register(JudgeAssignment)
    class JudgeAssignmentAdmin(admin.ModelAdmin):
        list_display = ('registration', 'category', 'assignment_type', 'status', 'start_time')
        list_filter = ('status', 'assignment_type')
        search_fields = ('registration__practitioner__first_name', 'registration__practitioner__last_name')

# Si JudgeCompetitionAssignment existe
if JudgeCompetitionAssignment:
    @admin.register(JudgeCompetitionAssignment)
    class JudgeCompetitionAssignmentAdmin(admin.ModelAdmin):
        list_display = ('registration', 'category', 'assignment_type')
        list_filter = ('assignment_type',)
        search_fields = ('registration__practitioner__first_name', 'registration__practitioner__last_name')


