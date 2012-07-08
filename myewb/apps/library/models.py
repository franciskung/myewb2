from django.db import models

from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from lxml.html.clean import clean_html, autolink_html, Cleaner
from datetime import datetime
import settings, os, shutil, datetime, re, types

from group_topics.models import GroupTopic
from champ.models import Activity
from events.models import Event

from wiki.models import Article, QuerySetManager

class Activity(models.Model):
    resource = models.ForeignKey('Resource')
    user = models.ForeignKey(User, related_name="library_actions")
    date = models.DateTimeField(auto_now_add=True)
    
    LIBRARY_ACTIVITIES = (('download', 'download'),
                          ('edit', 'edit'),
                          ('collect', 'collect'),
                          ('rate', 'rate'))
    activity_type = models.CharField(max_length=25, choices=LIBRARY_ACTIVITIES)
    
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey()
    
class Resource(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    model = models.CharField(max_length=25)
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    creator = models.ForeignKey(User, related_name='library_resources', null=True)
    updator = models.ForeignKey(User, related_name='library_updates', null=True)
    
    #objects = WorkspaceFileManager()
    
    RESOURCE_TYPES = (('article', 'Article'),
                      ('workshop', 'Workshop'))
    resource_type = models.CharField(max_length=25,
                                     verbose_name='Type',
                                     choices=RESOURCE_TYPES)

    RESOURCE_SCOPE = (('chapter', 'Chapter'),
                      ('ewb', 'EWB'),
                      ('world', 'World'))                                     
    scope = models.CharField(max_length=10,
                             choices=RESOURCE_SCOPE)

    editable = models.BooleanField(default=True)
    rating = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)

    def download(self, user):
        self.downloads = self.downloads + 1
        self.save()
        
        a = Activity.objects.create(resource=self,
                                    user=user,
                                    activity_type='download')
        a.save()
                                    
        return getattr(self, getattr(self, 'model')).direct_download()
        
    
# TODO: regex to use for validating filenames.  For now, anything not alpha-numeric-
# dash-underscore-period-space gets stripped, but would be good to allow accents eventually.
re_filename = re.compile(r'[^A-Za-z0-9\-_. ]')

class FileResourceManager(models.Manager):
    # Take the uploaded file (typicall from request.FILES['files'])
    # and attach it to a new FileResource instance.
    
    def upload(self, uploadedfile):
        # build and validate file name name
        filename = re_filename.sub(r'', uploadedfile.name)
            
        # create wrapper object
        resource = self.create(filename=filename)
            
        # open file
        diskfile = open(resource.get_path(), 'wb+')
            
        # write file to disk
        for chunk in uploadedfile.chunks():
            diskfile.write(chunk)
        diskfile.close() 

        return resource
        
class FileResource(Resource):
    filename = models.CharField(max_length=255)
    
    objects = FileResourceManager()
    
    def save(self, *args, **kwargs):
        self.model = 'fileresource'
        return super(FileResource, self).save(*args, **kwargs)
    
    def get_path(self):
        path = os.path.join(settings.MEDIA_ROOT, 'library/files', str(self.id))
        
        if not os.path.isdir(path):
            os.makedirs(path, 0755)
            
        return path + '/' + self.filename    
    
    def direct_download(self):
        return os.path.join(settings.STATIC_URL, 'library/files', str(self.id), self.filename)
    
class LinkResource(Resource):
    url = models.URLField()
    
    def save(*args, **kwargs):
        self.model = 'linkresource'
        return super(LinkResource, self).save(*args, **kwargs)
        
    def direct_download(self):
        return self.url
    
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
    
    