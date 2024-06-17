from django.db import models
import os
from django.db import models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

class Review(models.Model):
    author = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.author
