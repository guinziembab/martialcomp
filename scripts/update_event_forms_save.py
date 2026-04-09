# -*- coding: utf-8 -*-
"""Script pour mettre à jour la méthode save d'EventForm."""

file_path = r'c:\martial_hub_django\martialcomp\apps\competitions\forms\event_forms.py'

# Lire le fichier
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver la méthode save dans EventForm (la première occurrence de "def save")
save_start = content.find("    def save(self, commit=True):")
if save_start == -1:
    print("ERROR: Could not find save method")
    exit(1)

# Trouver la fin de la méthode (jusqu'à la prochaine classe)
next_class_idx = content.find("\n\nclass ", save_start)
if next_class_idx == -1:
    print("ERROR: Could not find next class")
    exit(1)

# Nouveau contenu de la méthode save
new_save = '''    def save(self, commit=True):
        instance = super().save(commit=False)
        is_new = not instance.pk

        # Définir le créateur si on crée un nouvel événement
        if self.user and is_new:
            instance.created_by = self.user

        # Mettre à jour l'all_day
        if instance.all_day:
            instance.start_time = None
            instance.end_time = None

        # Mettre à jour la date limite d'inscription
        instance.registration_deadline = self.cleaned_data.get('registration_deadline')

        # Gérer les champs de récurrence
        if instance.is_recurring:
            # Générer la règle RRULE
            instance.generate_rrule()

        if commit:
            instance.save()

            # Générer les occurrences si événement récurrent et nouveau
            if instance.is_recurring and is_new:
                instance.generate_occurrences(months_ahead=6)

        return instance

'''

# Remplacer
new_content = content[:save_start] + new_save + content[next_class_idx+2:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: save method updated")
