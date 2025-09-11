# Créez un fichier migration_script.py
from apps.competitions.models import Federation, Club, FederationAdministrator, ClubAdministrator

def migrate_data():
    print("Migration des propriétaires de fédérations...")
    count_fed = 0
    for federation in Federation.objects.all():
        if federation.owner:
            FederationAdministrator.objects.get_or_create(
                user=federation.owner,
                federation=federation,
                defaults={
                    'role': 'owner',
                    'is_primary': True
                }
            )
            count_fed += 1
    
    print(f"Migré {count_fed} propriétaires de fédérations")
    
    print("Migration des propriétaires de clubs...")
    count_club = 0
    for club in Club.objects.all():
        if hasattr(club, 'owner') and club.owner:
            ClubAdministrator.objects.get_or_create(
                user=club.owner,
                club=club,
                defaults={
                    'role': 'owner',
                    'is_primary': True
                }
            )
            count_club += 1
    
    print(f"Migré {count_club} propriétaires de clubs")

if __name__ == "__main__":
    migrate_data()

