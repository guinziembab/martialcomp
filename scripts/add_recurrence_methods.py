# -*- coding: utf-8 -*-
"""Script pour ajouter les méthodes de récurrence au modèle Event."""

file_path = r'c:\martial_hub_django\martialcomp\apps\competitions\models\event.py'

# Lire le fichier
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Le texte à trouver
old_text = '''        return self.participants.filter(user=user).exists()


class EventParticipant(models.Model):'''

# Le nouveau texte avec les méthodes de récurrence
new_text = '''        return self.participants.filter(user=user).exists()

    # =========================================================================
    # MÉTHODES DE RÉCURRENCE
    # =========================================================================

    def generate_rrule(self):
        """Génère une règle RRULE iCalendar à partir des paramètres."""
        if not self.is_recurring or not self.recurrence_frequency:
            self.recurrence_rule = ''
            return ''

        freq_map = {
            'daily': 'DAILY',
            'weekly': 'WEEKLY',
            'biweekly': 'WEEKLY',
            'monthly': 'MONTHLY',
            'yearly': 'YEARLY',
        }

        parts = [f"FREQ={freq_map.get(self.recurrence_frequency, 'WEEKLY')}"]

        interval = self.recurrence_interval or 1
        if self.recurrence_frequency == 'biweekly':
            interval = 2
        if interval > 1:
            parts.append(f"INTERVAL={interval}")

        if self.recurrence_frequency in ['weekly', 'biweekly'] and self.recurrence_days:
            days = ','.join(self.recurrence_days)
            parts.append(f"BYDAY={days}")

        if self.recurrence_frequency == 'monthly':
            if self.recurrence_week_of_month and self.recurrence_days:
                week = self.recurrence_week_of_month
                day = self.recurrence_days[0] if self.recurrence_days else 'MO'
                parts.append(f"BYDAY={week}{day}")
            elif self.recurrence_day_of_month:
                parts.append(f"BYMONTHDAY={self.recurrence_day_of_month}")

        if self.recurrence_end_type == 'after' and self.recurrence_end_after:
            parts.append(f"COUNT={self.recurrence_end_after}")
        elif self.recurrence_end_type == 'on_date' and self.recurrence_end_date:
            end_date = self.recurrence_end_date.strftime('%Y%m%d')
            parts.append(f"UNTIL={end_date}")

        self.recurrence_rule = ';'.join(parts)
        return self.recurrence_rule

    def generate_occurrences(self, months_ahead=6, save=True):
        """Génère les occurrences pour les N prochains mois."""
        if not self.is_recurring:
            return []

        try:
            from dateutil.rrule import rrulestr
            from dateutil.relativedelta import relativedelta
            from datetime import datetime as dt_datetime
        except ImportError:
            return self._generate_occurrences_simple(months_ahead, save)

        if not self.recurrence_rule:
            self.generate_rrule()
            if save:
                self.save(update_fields=['recurrence_rule'])

        if not self.recurrence_rule:
            return []

        start_dt = dt_datetime.combine(
            self.start_date,
            self.start_time or dt_datetime.min.time()
        )

        end_gen = timezone.now() + relativedelta(months=months_ahead)

        if self.start_time and self.end_time:
            duration = dt_datetime.combine(dt_datetime.min, self.end_time) - dt_datetime.combine(dt_datetime.min, self.start_time)
        else:
            duration = timedelta(hours=1)

        try:
            rrule_full = f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}\\nRRULE:{self.recurrence_rule}"
            rule = rrulestr(rrule_full)
            dates = list(rule.between(timezone.now(), end_gen, inc=True))
        except Exception:
            return self._generate_occurrences_simple(months_ahead, save)

        occurrences = []

        for occ_date in dates:
            existing = self.occurrences.filter(start_datetime__date=occ_date.date()).first()

            if existing:
                occurrences.append(existing)
                continue

            end_dt = occ_date + duration

            occurrence = EventOccurrence(
                event=self,
                start_datetime=occ_date,
                end_datetime=end_dt,
                status=OccurrenceStatus.PLANNED
            )

            if save:
                occurrence.save()

            occurrences.append(occurrence)

        return occurrences

    def _generate_occurrences_simple(self, months_ahead=6, save=True):
        """Génération simplifiée sans python-dateutil."""
        from datetime import datetime as dt_datetime
        from dateutil.relativedelta import relativedelta

        if not self.is_recurring or not self.recurrence_frequency:
            return []

        occurrences = []
        today = timezone.now().date()
        end_gen = today + relativedelta(months=months_ahead)

        if self.start_time and self.end_time:
            duration = dt_datetime.combine(dt_datetime.min, self.end_time) - dt_datetime.combine(dt_datetime.min, self.start_time)
        else:
            duration = timedelta(hours=1)

        day_map = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
        current_date = max(self.start_date, today)

        if self.recurrence_frequency == 'daily':
            interval_days = self.recurrence_interval or 1
        elif self.recurrence_frequency in ['weekly', 'biweekly']:
            interval_days = 7 * (2 if self.recurrence_frequency == 'biweekly' else (self.recurrence_interval or 1))
        else:
            interval_days = 30

        if self.recurrence_frequency in ['weekly', 'biweekly'] and self.recurrence_days:
            week_start = current_date - timedelta(days=current_date.weekday())

            while week_start <= end_gen:
                for day_code in self.recurrence_days:
                    day_offset = day_map.get(day_code, 0)
                    occ_date = week_start + timedelta(days=day_offset)

                    if occ_date >= today and occ_date <= end_gen:
                        if (self.recurrence_end_type == 'after' and
                            self.recurrence_end_after and
                            len(occurrences) >= self.recurrence_end_after):
                            break

                        if (self.recurrence_end_type == 'on_date' and
                            self.recurrence_end_date and
                            occ_date > self.recurrence_end_date):
                            break

                        existing = self.occurrences.filter(start_datetime__date=occ_date).first()

                        if existing:
                            occurrences.append(existing)
                        else:
                            start_dt = dt_datetime.combine(occ_date, self.start_time or dt_datetime.min.time())
                            if timezone.is_naive(start_dt):
                                start_dt = timezone.make_aware(start_dt)

                            occurrence = EventOccurrence(
                                event=self,
                                start_datetime=start_dt,
                                end_datetime=start_dt + duration,
                                status=OccurrenceStatus.PLANNED
                            )
                            if save:
                                occurrence.save()
                            occurrences.append(occurrence)

                week_start += timedelta(days=interval_days)
        else:
            while current_date <= end_gen:
                if (self.recurrence_end_type == 'after' and
                    self.recurrence_end_after and
                    len(occurrences) >= self.recurrence_end_after):
                    break

                if (self.recurrence_end_type == 'on_date' and
                    self.recurrence_end_date and
                    current_date > self.recurrence_end_date):
                    break

                existing = self.occurrences.filter(start_datetime__date=current_date).first()

                if existing:
                    occurrences.append(existing)
                else:
                    start_dt = dt_datetime.combine(current_date, self.start_time or dt_datetime.min.time())
                    if timezone.is_naive(start_dt):
                        start_dt = timezone.make_aware(start_dt)

                    occurrence = EventOccurrence(
                        event=self,
                        start_datetime=start_dt,
                        end_datetime=start_dt + duration,
                        status=OccurrenceStatus.PLANNED
                    )
                    if save:
                        occurrence.save()
                    occurrences.append(occurrence)

                current_date += timedelta(days=interval_days)

        return occurrences

    def get_next_occurrence(self):
        """Retourne la prochaine occurrence à venir."""
        return self.occurrences.filter(
            start_datetime__gte=timezone.now(),
            status__in=[OccurrenceStatus.PLANNED, OccurrenceStatus.CONFIRMED]
        ).order_by('start_datetime').first()

    def get_upcoming_occurrences(self, limit=10):
        """Retourne les prochaines occurrences."""
        return self.occurrences.filter(
            start_datetime__gte=timezone.now()
        ).exclude(
            status=OccurrenceStatus.CANCELLED
        ).order_by('start_datetime')[:limit]

    @property
    def is_online(self):
        """Vérifie si événement est en ligne."""
        return self.event_format in [EventFormat.ONLINE, EventFormat.HYBRID]

    @property
    def is_hybrid(self):
        """Vérifie si événement est hybride."""
        return self.event_format == EventFormat.HYBRID


class EventParticipant(models.Model):'''

if old_text in content:
    new_content = content.replace(old_text, new_text)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Methods added to Event model")
else:
    print("ERROR: Pattern not found")
    idx = content.find('return self.participants.filter(user=user)')
    if idx != -1:
        print(f"Found at position {idx}")
        print(f"Context: {repr(content[idx:idx+150])}")
