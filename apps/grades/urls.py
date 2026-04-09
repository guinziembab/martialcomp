from django.urls import path
from .views import (
    dashboard, history, management, systems,
    bulk, api, core, scoring
)
from apps.grades.views import certificates
from . import views

app_name = 'grades'

urlpatterns = [
    # URL pour la page d'accueil (tableau de bord)
    path('', dashboard.grades_dashboard, name='index'),
    path('dashboard/', dashboard.grades_dashboard, name='dashboard'),
    
    # URLs pour la gestion des clubs
    path('club/management/', management.club_management, name='club_management'),
    
    # URLs pour l'historique des grades
    path('practitioner/<int:practitioner_id>/history/', history.practitioner_grade_history, name='practitioner_history'),
    path('practitioner/<int:practitioner_id>/export/<str:format>/', history.export_grade_history, name='export_history'),
    
    # URLs pour la gestion des grades individuels
    path('practitioner/<int:practitioner_id>/update-grade/', management.update_practitioner_grade, name='update_practitioner_grade'),
    path('practitioner/<int:practitioner_id>/promote/', management.promote_practitioner, name='promote_practitioner'),
    path('practitioner-grade/<int:grade_id>/revoke/', management.revoke_grade, name='revoke_grade'),
    path('practitioner-grade/<int:grade_id>/set-current/', management.set_current_grade, name='set_current_grade'),
    
    # URLs pour la gestion des systèmes de grades
    path('systems/', systems.grade_systems_list, name='systems_list'),
    path('systems/<int:discipline_id>/', systems.grade_system_detail, name='system_detail'),
    path('systems/discipline/<int:discipline_id>/add-category/', systems.add_grade_category, name='add_grade_category'),
    path('systems/category/<int:category_id>/edit/', systems.edit_grade_category, name='edit_grade_category'),
    path('systems/category/<int:category_id>/add-grade/', systems.add_grade, name='add_grade'),
    path('systems/grade/<int:grade_id>/edit/', systems.edit_grade, name='edit_grade'),
    path('systems/grade/<int:grade_id>/delete/', systems.delete_grade, name='delete_grade'),
    path('systems/category/<int:category_id>/reorder-grades/', systems.reorder_grades, name='reorder_grades'),
    
    # Routes pour les Grades (vues CRUD de base)
    path('grade/', core.GradeListView.as_view(), name='grade_list'),
    path('grade/<int:pk>/', core.GradeDetailView.as_view(), name='grade_detail'),
    path('grade/create/', core.GradeCreateView.as_view(), name='grade_create'),
    path('grade/<int:pk>/update/', core.GradeUpdateView.as_view(), name='grade_update'),
    path('grade/<int:pk>/delete/', core.GradeDeleteView.as_view(), name='grade_delete'),
    
    # Routes pour les Catégories de Grade
    path('category/', core.GradeCategoryListView.as_view(), name='category_list'),
    path('category/create/', core.GradeCategoryCreateView.as_view(), name='category_create'),
    path('category/<int:pk>/update/', core.GradeCategoryUpdateView.as_view(), name='category_update'),
    path('category/<int:pk>/delete/', core.GradeCategoryDeleteView.as_view(), name='category_delete'),
    
    # Routes pour les Grades des Pratiquants
    path('practitioner/<int:practitioner_id>/grades/', core.practitioner_grades, name='practitioner_grades'),
    path('practitioner/<int:practitioner_id>/add-grade/', core.add_practitioner_grade, name='add_practitioner_grade'),
    path('practitioner-grade/<int:grade_id>/edit/', core.edit_practitioner_grade, name='edit_practitioner_grade'),
    path('practitioner-grade/<int:grade_id>/delete/', core.delete_practitioner_grade, name='delete_practitioner_grade'),
    
    # Routes pour l'attribution en masse
    path('bulk-assignment/', bulk.bulk_grade_assignment_form, name='bulk_assignment'),
    path('bulk/assignment-form/', bulk.bulk_grade_assignment_form, name='bulk_assignment_form'),
    path('bulk/update-grades/', bulk.batch_update_grades, name='batch_update_grades'),
    path('bulk/import-excel/', bulk.import_grades_from_excel, name='import_excel'),
    
    # Routes pour les Examens de Passage de Grade
    path('exam/', core.GradeExamListView.as_view(), name='exam_list'),
    path('exam/<int:pk>/', core.GradeExamDetailView.as_view(), name='exam_detail'),
    path('exam/create/', core.GradeExamCreateView.as_view(), name='exam_create'),
    path('exam/<int:pk>/update/', core.GradeExamUpdateView.as_view(), name='exam_update'),
    path('exam/<int:pk>/delete/', core.GradeExamDeleteView.as_view(), name='exam_delete'),
    path('exam/<int:exam_id>/register/', core.register_for_exam, name='register_for_exam'),
    path('exam-registration/<int:registration_id>/update-status/', core.update_exam_registration_status, name='update_exam_registration_status'),
    path('exam-registration/<int:registration_id>/cancel/', core.cancel_exam_registration, name='cancel_exam_registration'),
    
    # Routes pour les Exigences de Grade
    path('requirement/', core.GradeRequirementListView.as_view(), name='requirement_list'),
    path('requirement/create/', core.GradeRequirementCreateView.as_view(), name='requirement_create'),
    path('requirement/<int:pk>/update/', core.GradeRequirementUpdateView.as_view(), name='requirement_update'),
    path('requirement/<int:pk>/delete/', core.GradeRequirementDeleteView.as_view(), name='requirement_delete'),
    
    # Routes pour l'API
    path('api/grades-by-disciplines/', api.grades_by_disciplines, name='api_grades_by_disciplines'),
    # path('api/discipline/<int:discipline_id>/grades/', api.get_grades_by_discipline, name='api_discipline_grades'),
    # path('api/create-grade/', api.create_grade_for_discipline, name='api_create_grade'),
    # path('api/search-grades/', api.search_grades, name='api_search_grades'),
    path('api/categories-by-discipline/', api.categories_by_discipline, name='api_categories_by_discipline'),
    
    # Routes pour l'importation/exportation
    path('import/', core.import_grades, name='import_grades'),
    path('export/', core.export_grades, name='export_grades'),
    
    # URLs pour les certificats
    path('certificate/generate/<int:grade_id>/', certificates.certificate_generator, name='certificate_generator'),
    path('certificate/bulk/', certificates.bulk_certificate_generator, name='bulk_certificate_generator'),
    path('certificate/verify/<str:certificate_number>/', certificates.verify_certificate, name='verify_certificate'),
    path('certificate/qr/<str:certificate_number>/', certificates.generate_verification_qr, name='verification_qr'),
    path('certificate/download/<int:grade_id>/', certificates.download_certificate, name='download_certificate'),
    path('api/generate-certificate-number/', certificates.generate_certificate_number_ajax, name='generate_certificate_number_ajax'),

    # Routes pour la notation des examens
    path('exam/<int:exam_id>/scoring/config/', scoring.scoring_config, name='scoring_config'),
    path('exam/<int:exam_id>/scoring/sheet/', scoring.examiner_sheet, name='examiner_sheet'),
    path('exam/<int:exam_id>/scoring/dashboard/', scoring.scoring_dashboard, name='scoring_dashboard'),
    path('exam/<int:exam_id>/scoring/results/', scoring.exam_results, name='exam_results'),
    path('exam/<int:exam_id>/scoring/publish/', scoring.ajax_publish_results, name='ajax_publish_results'),
    path('scoring/save-score/', scoring.ajax_save_score, name='ajax_save_score'),
    path('exam/<int:exam_id>/scoring/module/', scoring.scoring_module_manage, name='scoring_module_manage'),
    path('scoring/module/<int:module_id>/criterion/', scoring.scoring_criterion_manage, name='scoring_criterion_manage'),
]

