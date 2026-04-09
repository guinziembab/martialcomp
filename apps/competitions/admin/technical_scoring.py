# -*- coding: utf-8 -*-
"""
BUG #3 FIX: Admin pour les Notes Techniques
Permet aux administrateurs de voir les notes attribuées par les juges.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Avg, Count

from apps.competitions.models.technical_scoring import (
    TechnicalScore,
    TechnicalPerformance,
    ScoringCriterion,
    ScoringConfiguration,
    CompetitionRanking
)


class TechnicalScoreInline(admin.TabularInline):
    """Inline pour voir les notes d'une performance"""
    model = TechnicalScore
    extra = 0
    readonly_fields = ['judge', 'criterion', 'value', 'round_number', 'submitted_at', 'is_locked']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TechnicalScore)
class TechnicalScoreAdmin(admin.ModelAdmin):
    """Admin pour les notes techniques individuelles"""
    list_display = [
        'id',
        'get_performance_practitioner',
        'get_competition',
        'get_category',
        'judge_display',
        'criterion_display',
        'value_display',
        'round_number',
        'is_active_for_ranking',
        'submitted_at'
    ]
    list_filter = [
        'round_number',
        'is_active_for_ranking',
        'is_locked',
        'is_training_score',
        'performance__category__competition',
        'criterion',
        ('submitted_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'performance__practitioner__first_name',
        'performance__practitioner__last_name',
        'judge__username',
        'judge__first_name',
        'judge__last_name',
        'criterion__name',
    ]
    ordering = ['-submitted_at']
    readonly_fields = ['submitted_at']
    list_per_page = 50

    fieldsets = (
        (_('Performance'), {
            'fields': ('performance',)
        }),
        (_('Note'), {
            'fields': ('judge', 'criterion', 'value', 'round_number')
        }),
        (_('Statut'), {
            'fields': ('is_locked', 'is_active_for_ranking', 'is_training_score', 'submitted_at')
        }),
    )

    def get_performance_practitioner(self, obj):
        if obj.performance and obj.performance.practitioner:
            return obj.performance.practitioner.full_name
        return '-'
    get_performance_practitioner.short_description = _('Pratiquant')
    get_performance_practitioner.admin_order_field = 'performance__practitioner__last_name'

    def get_competition(self, obj):
        if obj.performance and obj.performance.category and obj.performance.category.competition:
            return obj.performance.category.competition.title
        return '-'
    get_competition.short_description = _('Competition')

    def get_category(self, obj):
        if obj.performance and obj.performance.category:
            return obj.performance.category.name
        return '-'
    get_category.short_description = _('Categorie')

    def judge_display(self, obj):
        if obj.judge:
            return format_html(
                '<span title="{}">{}</span>',
                obj.judge.email,
                obj.judge.get_full_name() or obj.judge.username
            )
        return '-'
    judge_display.short_description = _('Juge')
    judge_display.admin_order_field = 'judge__username'

    def criterion_display(self, obj):
        if obj.criterion:
            return obj.criterion.name
        return '-'
    criterion_display.short_description = _('Critere')
    criterion_display.admin_order_field = 'criterion__name'

    def value_display(self, obj):
        """Affiche la note avec un code couleur"""
        value = float(obj.value)
        if value >= 8:
            color = '#28a745'  # Vert
        elif value >= 6:
            color = '#17a2b8'  # Bleu
        elif value >= 4:
            color = '#ffc107'  # Jaune
        else:
            color = '#dc3545'  # Rouge
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.value
        )
    value_display.short_description = _('Note')
    value_display.admin_order_field = 'value'


@admin.register(TechnicalPerformance)
class TechnicalPerformanceAdmin(admin.ModelAdmin):
    """Admin pour les prestations techniques"""
    list_display = [
        'id',
        'practitioner_display',
        'get_competition',
        'category',
        'performance_order',
        'status',
        'scores_summary',
        'average_score',
        'created_at'
    ]
    list_filter = [
        'status',
        'category__competition',
        'category',
        ('created_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'practitioner__first_name',
        'practitioner__last_name',
        'category__name',
        'category__competition__title',
    ]
    ordering = ['-created_at']
    inlines = [TechnicalScoreInline]
    list_per_page = 30

    def practitioner_display(self, obj):
        if obj.practitioner:
            return obj.practitioner.full_name
        return '-'
    practitioner_display.short_description = _('Pratiquant')
    practitioner_display.admin_order_field = 'practitioner__last_name'

    def get_competition(self, obj):
        if obj.category and obj.category.competition:
            return obj.category.competition.title
        return '-'
    get_competition.short_description = _('Competition')

    def scores_summary(self, obj):
        """Affiche le nombre de notes reçues"""
        count = obj.scores.filter(is_active_for_ranking=True).count()
        if count == 0:
            return format_html('<span class="text-muted">0 notes</span>')
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">{} notes</span>',
            count
        )
    scores_summary.short_description = _('Notes')

    def average_score(self, obj):
        """Calcule et affiche la moyenne des notes"""
        avg = obj.scores.filter(is_active_for_ranking=True).aggregate(avg=Avg('value'))['avg']
        if avg is None:
            return '-'
        avg = float(avg)
        if avg >= 8:
            color = '#28a745'
        elif avg >= 6:
            color = '#17a2b8'
        elif avg >= 4:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{:.2f}</span>',
            color,
            avg
        )
    average_score.short_description = _('Moyenne')


@admin.register(ScoringCriterion)
class ScoringCriterionAdmin(admin.ModelAdmin):
    """Admin pour les critères de notation"""
    list_display = ['name', 'category', 'weight', 'min_score', 'max_score', 'step', 'is_active']
    list_filter = ['is_active', 'category__competition']
    search_fields = ['name', 'description', 'category__name']
    ordering = ['category', 'order', 'name']


@admin.register(ScoringConfiguration)
class ScoringConfigurationAdmin(admin.ModelAdmin):
    """Admin pour les configurations de notation"""
    list_display = [
        'category',
        'min_score',
        'max_score',
        'score_step',
        'exclude_extreme_scores',
        'allow_ties',
        'real_time_results'
    ]
    list_filter = ['exclude_extreme_scores', 'allow_ties', 'real_time_results']
    search_fields = ['category__name', 'category__competition__title']


@admin.register(CompetitionRanking)
class CompetitionRankingAdmin(admin.ModelAdmin):
    """Admin pour les classements de competition"""
    list_display = [
        'rank_display',
        'practitioner_display',
        'competition',
        'category',
        'final_score_display',
        'first_places',
        'is_tie',
        'generated_at'
    ]
    list_filter = [
        'competition',
        'category',
        'is_tie',
        ('generated_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'practitioner__first_name',
        'practitioner__last_name',
        'competition__title',
        'category__name',
    ]
    ordering = ['competition', 'category', 'rank']
    list_per_page = 50

    def rank_display(self, obj):
        """Affiche le rang avec des médailles pour le top 3"""
        if obj.rank == 1:
            return format_html('<span style="font-size: 1.5em;">🥇</span> 1')
        elif obj.rank == 2:
            return format_html('<span style="font-size: 1.5em;">🥈</span> 2')
        elif obj.rank == 3:
            return format_html('<span style="font-size: 1.5em;">🥉</span> 3')
        return str(obj.rank)
    rank_display.short_description = _('Rang')
    rank_display.admin_order_field = 'rank'

    def practitioner_display(self, obj):
        if obj.practitioner:
            return obj.practitioner.full_name
        return '-'
    practitioner_display.short_description = _('Pratiquant')
    practitioner_display.admin_order_field = 'practitioner__last_name'

    def final_score_display(self, obj):
        """Affiche le score final avec couleur"""
        score = float(obj.final_score)
        if score >= 8:
            color = '#28a745'
        elif score >= 6:
            color = '#17a2b8'
        elif score >= 4:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.final_score
        )
    final_score_display.short_description = _('Score Final')
    final_score_display.admin_order_field = 'final_score'
