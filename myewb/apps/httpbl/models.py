from django.db import models

class Whitelist(models.Model):
    ip = models.CharField(max_length=15, db_index=True)
    validated = models.DateTimeField(auto_now_add=True)

