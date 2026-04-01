from django.db import models
from django.contrib.auth.models import User

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trips")
    start_location = models.CharField(max_length=255, blank=True, null=True)
    destination = models.CharField(max_length=500)
    country = models.CharField(max_length=100, default="India")
    country_code = models.CharField(max_length=5, default="in")
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True)

    ai_plan = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.destination} - {self.country}"