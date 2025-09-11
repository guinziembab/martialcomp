from datetime import datetime
import random
import string

class LicenseNumberGenerator:
    @staticmethod
    def get_discipline_code(discipline):
        code = getattr(discipline, 'code', None)
        if code:
            return code[:2].upper()
        return discipline.name[:2].upper() if discipline and discipline.name else 'XX'

    @staticmethod
    def get_club_code(club):
        code = getattr(club, 'code', None)
        if code:
            return code[:3].upper()
        return club.name[:3].upper() if club and club.name else 'XXX'

    @staticmethod
    def get_birth_date_code(birth_date):
        if not birth_date:
            return '00000000'
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except Exception:
                return '00000000'
        return birth_date.strftime('%d%m%Y')

    @classmethod
    def generate(cls, practitioner=None, discipline=None, club=None, birth_date=None, discipline_id=None, club_id=None):
        from apps.competitions.models import Discipline as D, Club as C, Practitioner as P
        # Récupérer les objets si on a les IDs
        if not discipline and discipline_id:
            discipline = D.objects.filter(id=discipline_id).first()
        if not club and club_id:
            club = C.objects.filter(id=club_id).first()
        if not practitioner and (discipline is None or club is None or birth_date is None):
            if practitioner:
                if not discipline and hasattr(practitioner, 'primary_discipline'):
                    discipline = practitioner.primary_discipline
                if not club and hasattr(practitioner, 'organization'):
                    club = getattr(practitioner, 'organization', None)
                if not birth_date and hasattr(practitioner, 'birth_date'):
                    birth_date = practitioner.birth_date
        discipline_code = cls.get_discipline_code(discipline)
        club_code = cls.get_club_code(club)
        birth_code = cls.get_birth_date_code(birth_date)
        return f"{discipline_code}-{club_code}-{birth_code}" 

