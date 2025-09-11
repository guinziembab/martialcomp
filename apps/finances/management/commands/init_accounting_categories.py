from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from apps.finances.models.accounts import AccountingCategory

class Command(BaseCommand):
    help = "Initialise des catégories comptables de base (revenus/dépenses)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--organization-id",
            dest="organization_id",
            default=None,
            help="ID de l'organisation pour créer des catégories spécifiques (sinon: catégories système)",
        )
        parser.add_argument(
            "--organization-model",
            dest="organization_model",
            default="organizations.Organization",
            help="Label du modèle d'organisation (par défaut organizations.Organization)",
        )

    def handle(self, *args, **options):
        organization_id = options.get("organization_id")
        organization_model_label = options.get("organization_model")

        organization = None
        ct = None
        org_pk_str = None

        if organization_id:
            try:
                app_label, model_name = organization_model_label.split(".")
                Model = ContentType.objects.get(app_label=app_label, model=model_name.lower()).model_class()
                organization = Model.objects.get(pk=organization_id)
                ct = ContentType.objects.get_for_model(organization.__class__)
                org_pk_str = str(organization.pk)
                self.stdout.write(self.style.SUCCESS(f"Organisation détectée: {organization} (id={organization.pk})"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Impossible de charger l'organisation ({organization_model_label}, id={organization_id}): {e}. Création de catégories système globales."))

        def create_category(name: str, type_: str, parent=None, code: str = ""):
            kwargs = {
                "name": name,
                "type": type_,
                "defaults": {
                    "code": code or "",
                    "is_active": True,
                    "is_system": organization is None,  # système si pas d'org
                },
            }
            if parent is not None:
                kwargs["defaults"]["parent"] = parent

            if organization is not None:
                kwargs["organization_content_type"] = ct
                kwargs["organization_id"] = org_pk_str

            # get_or_create ne supporte pas GFK directement dans defaults, on passe tout dans kwargs
            obj, created = AccountingCategory.objects.get_or_create(**kwargs)
            return obj, created

        # Racines implicites par type via simple parentage logique (pas d'objet "Income" séparé)
        income_categories = [
            ("Adhésions", "MEMB"),
            ("Ventes", "SALES"),
            ("Dons", "DON"),
            ("Sponsoring", "SPONS"),
            ("Autres revenus", "INC_OTH"),
        ]
        expense_categories = [
            ("Loyers", "RENT"),
            ("Services publics", "UTIL"),
            ("Équipements", "EQUIP"),
            ("Salaires/Honoraires", "PAY"),
            ("Déplacements", "TRAVEL"),
            ("Formations", "TRAIN"),
            ("Frais de compétition", "COMP"),
            ("Frais bancaires", "BANK"),
            ("Autres dépenses", "EXP_OTH"),
        ]

        created_count = 0
        for name, code in income_categories:
            _, created = create_category(name=name, type_="income", parent=None, code=code)
            created_count += 1 if created else 0
        for name, code in expense_categories:
            _, created = create_category(name=name, type_="expense", parent=None, code=code)
            created_count += 1 if created else 0

        scope = f"organisation {organization.pk}" if organization else "système"
        self.stdout.write(self.style.SUCCESS(f"Catégories comptables initialisées ({scope}). Nouvelles catégories créées: {created_count}."))
