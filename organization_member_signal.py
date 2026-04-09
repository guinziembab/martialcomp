
# Signal à ajouter à apps/organizations/signals.py

@receiver(post_save, sender=Organization)
def create_organization_owner_membership(sender, instance, created, **kwargs):
    """
    Crée automatiquement un OrganizationMember avec le rôle 'owner' 
    pour le créateur de l'organisation.
    """
    if created and instance.created_by:
        try:
            from apps.organizations.models import OrganizationMember
            
            # Vérifier si le membership existe déjà
            existing = OrganizationMember.objects.filter(
                user=instance.created_by,
                organization=instance
            ).first()
            
            if not existing:
                OrganizationMember.objects.create(
                    user=instance.created_by,
                    organization=instance,
                    role='owner',
                    is_active=True,
                    joined_at=timezone.now()
                )
                logger.info(f"OrganizationMember créé automatiquement pour {instance.created_by.username} dans {instance.name}")
            else:
                logger.info(f"OrganizationMember existe déjà pour {instance.created_by.username} dans {instance.name}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'OrganizationMember pour {instance.name}: {e}")
