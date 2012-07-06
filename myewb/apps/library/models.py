from django.db import models

from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from lxml.html.clean import clean_html, autolink_html, Cleaner
from datetime import datetime
import re, types

from group_topics.models import GroupTopic
from champ.models import Activity
from events.models import Event

from wiki.models import Article, QuerySetManager

class Resource(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    model = models.CharField(max_length=25)
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    creator = models.ForeignKey(User, related_name='library_resources', null=True)
    updator = models.ForeignKey(User, related_name='library_updates', null=True)
    
    #objects = WorkspaceFileManager()
    
    RESOURCE_TYPES = (('article', 'Article'),
                      ('workshop', 'Workshop'))
    resource_type = models.CharField(max_length=10,
                                     choices=RESOURCE_TYPES)

    RESOURCE_SCOPE = (('chapter', 'Chapter'),
                      ('ewb', 'EWB'),
                      ('world', 'World'))                                     
    scope = models.CharField(max_length=10,
                             choices=RESOURCE_SCOPE)

    editable = models.BooleanField(default=True)
    rating = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    
class FileResource(Resource):
    pass
    
class LinkResource(Resource):
    url = models.URLField()
    
class Collection(models.Model):
    title = models.CharField(max_length='50')
    description = models.CharField(max_length='255')
    
    parent = models.ForeignKey("self", null=True)
    ordering = models.IntegerField(null=True)

    resources = models.ManyToManyField(Resource)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, related_name='collections_owned')
    curators = models.ManyToManyField(User, related_name='collections')
    
    
