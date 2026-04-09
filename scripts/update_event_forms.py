# -*- coding: utf-8 -*-
"""Script pour mettre à jour la méthode clean d'EventForm."""

file_path = r'c:\martial_hub_django\martialcomp\apps\competitions\forms\event_forms.py'

# Lire le fichier
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver la méthode clean et la remplacer
old_clean_start = "    def clean(self):"
old_clean_end = "        return cleaned_data\n    \n    def save"

# Nouveau contenu de la méthode clean
new_clean = '''    def clean(self):
        cleaned_data = super().clean()

        # Validation des dates
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _("La date de fin doit être égale ou postérieure à la date de début."))

        # Validation des heures
        all_day = cleaned_data.get('all_day')
        if not all_day:
            start_time = cleaned_data.get('start_time')
            end_time = cleaned_data.get('end_time')

            if start_time and end_time and start_date == end_date and start_time >= end_time:
                self.add_error('end_time', _("L'heure de fin doit être postérieure à l'heure de début pour un événement le même jour."))

        # Gérer la date limite d'inscription
        registration_required = cleaned_data.get('registration_required')
        registration_deadline_date = cleaned_data.get('registration_deadline_date')
        registration_deadline_time = cleaned_data.get('registration_deadline_time')

        if registration_required and registration_deadline_date:
            if not registration_deadline_time:
                registration_deadline_time = timezone.datetime.max.time().replace(microsecond=0)

            registration_deadline = timezone.datetime.combine(
                registration_deadline_date,
                registration_deadline_time
            )
            registration_deadline = timezone.make_aware(registration_deadline)

            if start_date:
                event_start = timezone.datetime.combine(
                    start_date,
                    cleaned_data.get('start_time') or timezone.datetime.min.time()
                )
                event_start = timezone.make_aware(event_start)

                if registration_deadline >= event_start:
                    self.add_error('registration_deadline_date',
                        _("La date limite d'inscription doit être antérieure à la date de début de l'événement."))

            cleaned_data['registration_deadline'] = registration_deadline
        else:
            cleaned_data['registration_deadline'] = None

        # =========================================================================
        # VALIDATION DE LA RÉCURRENCE
        # =========================================================================
        is_recurring = cleaned_data.get('is_recurring')

        if is_recurring:
            recurrence_frequency = cleaned_data.get('recurrence_frequency')

            if not recurrence_frequency:
                self.add_error('recurrence_frequency', _("Veuillez sélectionner une fréquence de récurrence."))

            if recurrence_frequency in ['weekly', 'biweekly']:
                recurrence_days = cleaned_data.get('recurrence_days')
                if not recurrence_days:
                    self.add_error('recurrence_days', _("Veuillez sélectionner au moins un jour de la semaine."))

            recurrence_end_type = cleaned_data.get('recurrence_end_type')

            if recurrence_end_type == 'after':
                recurrence_end_after = cleaned_data.get('recurrence_end_after')
                if not recurrence_end_after or recurrence_end_after < 1:
                    self.add_error('recurrence_end_after', _("Veuillez spécifier un nombre d'occurrences valide."))

            elif recurrence_end_type == 'on_date':
                recurrence_end_date = cleaned_data.get('recurrence_end_date')
                if not recurrence_end_date:
                    self.add_error('recurrence_end_date', _("Veuillez spécifier une date de fin de récurrence."))
                elif start_date and recurrence_end_date <= start_date:
                    self.add_error('recurrence_end_date', _("La date de fin de récurrence doit être postérieure à la date de début."))

        # =========================================================================
        # VALIDATION DES CHAMPS EN LIGNE
        # =========================================================================
        event_format = cleaned_data.get('event_format')

        if event_format in [EventFormat.ONLINE, EventFormat.HYBRID]:
            online_url = cleaned_data.get('online_url')
            if not online_url:
                self.add_error('online_url', _("Veuillez spécifier l'URL de la visioconférence."))

        return cleaned_data

    def save'''

# Trouver l'index de début de clean
start_idx = content.find(old_clean_start)
if start_idx == -1:
    print("ERROR: Could not find clean method start")
else:
    # Trouver l'index de fin (return cleaned_data suivi de def save)
    end_pattern = "return cleaned_data"
    search_start = start_idx
    end_idx = content.find(end_pattern, search_start)

    if end_idx == -1:
        print("ERROR: Could not find clean method end")
    else:
        # Trouver la fin de la ligne return cleaned_data et le début de save
        end_idx = end_idx + len(end_pattern)
        # Avancer jusqu'à def save
        save_idx = content.find("def save", end_idx)
        if save_idx == -1:
            print("ERROR: Could not find save method")
        else:
            # Remplacer tout entre start_idx et save_idx
            new_content = content[:start_idx] + new_clean + content[save_idx + 8:]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("SUCCESS: clean method updated")
