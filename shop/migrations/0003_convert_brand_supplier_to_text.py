# Generated migration for converting brand and supplier fields to text

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_alter_product_brand_alter_product_supplier'),
    ]

    operations = [
        # Ajouter les nouveaux champs texte temporaires
        migrations.AddField(
            model_name='product',
            name='brand_text',
            field=models.CharField(
                blank=True, 
                help_text='Nom de la marque du produit (ex: Nike, Adidas, Venum)', 
                max_length=100, 
                verbose_name='Marque'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='supplier_text',
            field=models.CharField(
                blank=True, 
                help_text='Nom du fournisseur ou distributeur', 
                max_length=100, 
                verbose_name='Fournisseur'
            ),
        ),
        
        # La migration des données sera faite par un script séparé
        
        # Supprimer les anciens champs FK (si ils existent)
        # migrations.RemoveField(
        #     model_name='product',
        #     name='brand',
        # ),
        # migrations.RemoveField(
        #     model_name='product',
        #     name='supplier',
        # ),
        
        # Renommer les nouveaux champs
        # migrations.RenameField(
        #     model_name='product',
        #     old_name='brand_text',
        #     new_name='brand',
        # ),
        # migrations.RenameField(
        #     model_name='product',
        #     old_name='supplier_text',
        #     new_name='supplier',
        # ),
    ]