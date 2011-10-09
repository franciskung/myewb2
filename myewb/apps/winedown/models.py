"""myEWB winedown models

This file is part of myEWB
Copyright 2011 Engineers Without Borders Canada
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.db import models

import settings, os, shutil, datetime, re

from siteutils.helpers import fix_encoding

class CheersManager(models.Manager):
    def get_container(self, obj):
        ctype = ContentType.objects.get_for_model(obj)
        container, created = CheersContainer.objects.get_or_create(content_type=ctype,
                                                                   object_id = obj.id)
        return container

    def get_for_object(self, obj):
        container = self.get_container(obj)
        c = self.get_query_set().filter(content=container)
        return c
        
    def latest(self):
        c = CheersContainer.objects.all().order_by('-latest')
        return c
        
    def popular(self):
        c = CheersContainer.objects.all().order_by('-count')
        return 
        
    def create_link(self, obj):
        container = self.get_container(obj)
        return reverse('winedown_cheers', kwargs={'content_id': container.id})
        
    def create_from_obj(self, obj, user, comment=None):
        container = self.get_container(obj)
        return self.create_from_container(container, user, comment)
        
    def create_from_container(self, container, user, comment=None):
        c, created = Cheers.objects.get_or_create(owner=user, content=container)
        
        if created:
            c.comment = comment
            c.save()
        
            container.refresh_count()
            container.latest = datetime.datetime.now()
            container.save()
        
        return c

class CheersContainer(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    
    created = models.DateTimeField(auto_now_add=True)
    count = models.PositiveIntegerField(default=0)
    latest = models.DateTimeField(default=datetime.datetime.now())
    
    def refresh_count(self):
        count = Cheers.objects.filter(content=self).count()
        self.count = count
        self.save()
        
    def guess_title(self):
        return "test"

class Cheers(models.Model):
    owner = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(max_length=140, blank=True, null=True)

    content = models.ForeignKey(CheersContainer)
    objects = CheersManager()

