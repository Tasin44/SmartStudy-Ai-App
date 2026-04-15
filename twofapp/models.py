
# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ParentalControl(models.Model):
    RELATION_CHOICES = [
        ('parent', 'Parent'),
        ('child', 'Child'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parental_controls')
    related_email = models.EmailField()
    relation_type = models.CharField(max_length=10, choices=RELATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hello, Grettings from Smart Study AI app team. The user {self.user.email} added you {self.related_email} as {self.relation_type}"