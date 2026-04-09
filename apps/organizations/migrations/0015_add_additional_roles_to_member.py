from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0014_add_organization_news_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmember',
            name='additional_roles',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Liste de codes de rôles supplémentaires, ex: ['treasurer', 'coach']",
                verbose_name='Rôles additionnels',
            ),
        ),
    ]
