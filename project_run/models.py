from django.db import models
from django.contrib.auth.models import User

class Run(models.Model):
    athlete = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    comment = models.TextField()

    def __str__(self):
        return f"Run by {self.athlete.username} on {self.created_at}"