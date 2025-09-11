from django.db import models
from django.contrib.postgres.fields import ArrayField

class Feature(models.Model):
    code = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.label

class Package(models.Model):
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    features = models.ManyToManyField(Feature, related_name='packages')
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.label

class OrganizationPackage(models.Model):
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    active_features = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    def __str__(self):
        return f"{self.organization} - {self.package}" 