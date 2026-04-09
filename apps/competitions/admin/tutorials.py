from django.contrib import admin
from apps.competitions.models.tutorials import TutorialSection, Tutorial


class TutorialInline(admin.TabularInline):
    model = Tutorial
    extra = 0
    fields = ('number', 'title', 'audience', 'format', 'duration', 'youtube_url', 'order', 'is_active')
    ordering = ('order', 'number')


@admin.register(TutorialSection)
class TutorialSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'order', 'tutorial_count', 'is_active')
    list_editable = ('order', 'is_active')
    ordering = ('order',)
    inlines = [TutorialInline]

    def tutorial_count(self, obj):
        return obj.tutorials.count()
    tutorial_count.short_description = 'Tutoriels'


@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'section', 'audience', 'format', 'duration', 'youtube_url', 'is_active')
    list_filter = ('section', 'audience', 'format', 'is_active')
    search_fields = ('title', 'title_fr', 'title_en', 'tip')
    list_editable = ('youtube_url',)
    ordering = ('section__order', 'order', 'number')
