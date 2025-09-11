from django.db import models
from django.contrib.auth.models import User

class OrganisateurNonMembre(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.OneToOneField('organizations.Organization', on_delete=models.CASCADE)
    contact_phone = models.CharField(max_length=30, blank=True)
    statut_validation = models.CharField(max_length=30, default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Organisateur non-membre: {self.user.username} ({self.organization})" 