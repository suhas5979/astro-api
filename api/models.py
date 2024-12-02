from django.db import models
# Create your models here.
from django.db import models
from django.core.exceptions import ValidationError

class CustomerDetails(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=50, null=True)
    mobile_no = models.CharField(max_length=15, null=True)
    birth_date = models.DateField()
    birth_time = models.TimeField(auto_now=False, auto_now_add=False)  
    birth_place = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    longitude = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['mobile_no']),
            models.Index(fields=['email']),
            models.Index(fields=['name']),
        ]

    def clean(self):
        # Validation will be handled in the API view
        pass

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class Planet(models.Model):
    planet = models.CharField(max_length=10, primary_key=True)
    significance = models.TextField()

    class Meta:
        db_table = 'planet' 
        managed = False 

    def __str__(self):
        return f"{self.planet}: {self.significance[:200]}"
    


