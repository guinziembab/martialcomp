from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0051_add_combat_duration_to_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='airecombat',
            name='couleur_interieur',
            field=models.CharField(
                choices=[('blue', 'Bleu'), ('red', 'Rouge'), ('green', 'Vert'),
                         ('yellow', 'Jaune'), ('purple', 'Violet'), ('orange', 'Orange'),
                         ('teal', 'Turquoise'), ('pink', 'Rose')],
                default='red',
                help_text="Couleur intérieure du tatami",
                max_length=20,
                verbose_name='Couleur intérieure'
            ),
        ),
    ]
