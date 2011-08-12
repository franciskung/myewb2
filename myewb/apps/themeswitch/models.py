"""myEWB theme switcher models

This file is part of myEWB
Copyright 2011 Engineers Without Borders Canada

@author: Francis Kung
"""

from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

class RequestLog(models.Model):
    user = models.ForeignKey(User, default=None, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    page = models.CharField(max_length=255)
    theme = models.CharField(max_length=255)
    