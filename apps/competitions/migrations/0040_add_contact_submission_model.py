from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0039_add_competition_visibility_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nom complet')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('organization', models.CharField(blank=True, help_text="Nom de votre club, ecole ou federation", max_length=200, verbose_name='Organisation')),
                ('subject', models.CharField(choices=[('information', "Demande d'information"), ('partnership', 'Partenariat'), ('federation', 'Federation'), ('club', 'Club / Ecole'), ('support', 'Support technique'), ('other', 'Autre')], default='information', max_length=50, verbose_name='Sujet')),
                ('message', models.TextField(verbose_name='Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de creation')),
                ('is_read', models.BooleanField(default=False, verbose_name='Lu')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Lu le')),
                ('responded', models.BooleanField(default=False, verbose_name='Repondu')),
                ('responded_at', models.DateTimeField(blank=True, null=True, verbose_name='Repondu le')),
            ],
            options={
                'verbose_name': 'Message de contact',
                'verbose_name_plural': 'Messages de contact',
                'ordering': ['-created_at'],
            },
        ),
    ]
