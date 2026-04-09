"""Add organization FK and is_public flag to Product for shop isolation."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
        ('organizations', '0014_add_organization_news_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='organization',
            field=models.ForeignKey(
                blank=True,
                help_text="Organisation propriétaire du produit. Si vide, le produit est global.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='shop_products',
                to='organizations.Organization',
                verbose_name='Organisation',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='is_public',
            field=models.BooleanField(
                default=False,
                help_text="Si activé, le produit est visible par tous les utilisateurs, pas seulement les membres de l'organisation.",
                verbose_name='Public',
            ),
        ),
    ]
