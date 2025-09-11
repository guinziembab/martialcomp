import uuid
from datetime import datetime

class CertificateNumberGenerator:
    @staticmethod
    def get_discipline_code(discipline):
        # Utilise le champ code si présent, sinon les 2 premières lettres du nom
        code = getattr(discipline, 'code', None)
        if code:
            return code[:2].upper()
        return discipline.name[:2].upper() if discipline and discipline.name else 'XX'

    @staticmethod
    def get_organization_code(organization):
        # Utilise le champ code si présent, sinon les 3 premières lettres du nom
        code = getattr(organization, 'code', None)
        if code:
            return code[:3].upper()
        return organization.name[:3].upper() if organization and organization.name else 'XXX'

    @staticmethod
    def get_birth_date_code(birth_date):
        # birth_date doit Ãªtre un objet date ou string au format YYYY-MM-DD
        if not birth_date:
            return '00000000'
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except Exception:
                return '00000000'
        return birth_date.strftime('%d%m%Y')

    @classmethod
    def generate(cls, practitioner=None, discipline=None, practitioner_id=None, discipline_id=None, organization=None, organization_id=None, birth_date=None):
        """
        Génère un numéro de certificat selon la structure :
        [Code Discipline (2)]-[Code Organisation (3)]-[Date naissance inversée (JJMMAAAA)]
        """
        # Importations locales pour éviter les problèmes de dépendances circulaires
        from apps.competitions.models import Discipline as D, Club as C, Practitioner as P
        from apps.organizations.models import Organization as O
        
        # Récupérer les objets si on a les IDs
        if not discipline and discipline_id:
            discipline = D.objects.filter(id=discipline_id).first()
        if not organization and organization_id:
            organization = O.objects.filter(id=organization_id).first()
        if not practitioner and practitioner_id:
            practitioner = P.objects.filter(id=practitioner_id).first()
        
        # Discipline code
        discipline_code = cls.get_discipline_code(discipline)
        # Organisation code
        if not organization and practitioner and hasattr(practitioner, 'organization'):
            organization = practitioner.organization
        organization_code = cls.get_organization_code(organization)
        # Date de naissance
        if not birth_date and practitioner and hasattr(practitioner, 'birth_date'):
            birth_date = practitioner.birth_date
        birth_code = cls.get_birth_date_code(birth_date)
        
        return f"{discipline_code}-{organization_code}-{birth_code}" 

class CertificateFileNamer:
    @staticmethod
    def generate_code(practitioner=None, discipline=None, date=None, practitioner_id=None, discipline_id=None):
        from apps.competitions.models import Practitioner as P, Discipline as D
        # Récupérer les objets si besoin
        if not practitioner and practitioner_id:
            practitioner = P.objects.filter(id=practitioner_id).first()
        if not discipline and discipline_id:
            discipline = D.objects.filter(id=discipline_id).first()
        # Code discipline
        discipline_code = (getattr(discipline, 'code', None) or (discipline.name[:2] if discipline and discipline.name else 'XX')).upper()
        # Code pratiquant (ID ou initiales)
        prac_code = f"{practitioner.id:05d}" if practitioner and hasattr(practitioner, 'id') else '00000'
        # Date JJMMYYYY
        if not date and practitioner and hasattr(practitioner, 'birth_date'):
            date = practitioner.birth_date
        if not date:
            date_code = datetime.now().strftime('%d%m%Y')
        elif isinstance(date, str):
            try:
                date_code = datetime.strptime(date, '%Y-%m-%d').strftime('%d%m%Y')
            except Exception:
                date_code = '00000000'
        else:
            date_code = date.strftime('%d%m%Y')
        # 4 caractères aléatoires
        rand = uuid.uuid4().hex[:4].upper()
        return f"{discipline_code}-{prac_code}-{date_code}-{rand}"

    @staticmethod
    def generate_filename(practitioner=None, discipline=None, date=None, extension='pdf', **kwargs):
        code = CertificateFileNamer.generate_code(practitioner=practitioner, discipline=discipline, date=date, **kwargs)
        return f"CERT-{code}.{extension}" 

