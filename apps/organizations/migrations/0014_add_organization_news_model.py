# Generated migration for OrganizationNews model
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0012_add_membership_status_and_approval'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationNews',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Titre de l\'actualite', max_length=255, verbose_name='Titre')),
                ('slug', models.SlugField(blank=True, help_text='URL-friendly version du titre (genere automatiquement)', max_length=255, verbose_name='Slug')),
                ('excerpt', models.CharField(blank=True, help_text='Court resume affiche dans les listes (optionnel)', max_length=500, verbose_name='Resume')),
                ('content', models.TextField(help_text='Contenu complet de l\'actualite (supporte le HTML)', verbose_name='Contenu')),
                ('image', models.ImageField(blank=True, help_text='Image d\'illustration (recommande: 800x400px)', null=True, upload_to='organizations/news/', verbose_name='Image principale')),
                ('is_published', models.BooleanField(default=False, help_text='Cocher pour rendre l\'article visible sur le site', verbose_name='Publie')),
                ('is_featured', models.BooleanField(default=False, help_text='Afficher en priorite sur la page d\'accueil', verbose_name='A la une')),
                ('published_at', models.DateTimeField(blank=True, help_text='Date de publication (peut etre dans le futur)', null=True, verbose_name='Date de publication')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Cree le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis a jour le')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organization_news', to=settings.AUTH_USER_MODEL, verbose_name='Auteur')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='news_articles', to='organizations.organization', verbose_name='Organisation')),
            ],
            options={
                'verbose_name': 'Actualite',
                'verbose_name_plural': 'Actualites',
                'ordering': ['-published_at', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='organizationnews',
            index=models.Index(fields=['organization', 'is_published', '-published_at'], name='org_news_published_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationnews',
            index=models.Index(fields=['organization', 'is_featured'], name='org_news_featured_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='organizationnews',
            unique_together={('organization', 'slug')},
        ),
    ]
