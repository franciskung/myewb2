from django.db import models

from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from lxml.html.clean import clean_html, autolink_html, Cleaner
from datetime import datetime
import settings, os, shutil, datetime, re, types, hashlib

from group_topics.models import GroupTopic
from champ.models import Activity
from events.models import Event

from siteutils.shortcuts import get_object_or_none

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
    
    RESOURCE_TYPES = (('article', 'Articles and papers'),
                      ('guide', "Guides and how-to's"),
                      ('media', 'Visual media'),
                      ('workshop', 'Workshops')
                     )
    resource_type = models.CharField(max_length=25,
                                     verbose_name='Type',
                                     choices=RESOURCE_TYPES)

    RESOURCE_SCOPE = (('chapter', 'Chapter'),
                      ('ewb', 'EWB'),
                      ('world', 'World'))                                     
    scope = models.CharField(max_length=10,
                             choices=RESOURCE_SCOPE)
                             
    RESOURCE_LANGUAGES = (('en', 'English'),
                          ('fr', 'Francais'))
    language = models.CharField(max_length=2, default='en',
                                choices=RESOURCE_LANGUAGES)

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
        md5 = hashlib.md5()
        
        for chunk in uploadedfile.chunks():
            diskfile.write(chunk)
            md5.update(chunk)
        diskfile.close()
        
        resource.checksum = md5.hexdigest()
        resource.save()

        return resource
        
class FileResource(Resource):
    filename = models.CharField(max_length=255)
    checksum = models.CharField(max_length=32, default='')
    
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
    name = models.CharField(max_length=50)
    description = models.TextField()
    
    parent = models.ForeignKey("self", blank=True, null=True)
    ordering = models.IntegerField(null=True)
    featured = models.BooleanField(default=False)
    autolink = models.BooleanField(default=False)

    resources = models.ManyToManyField(Resource, blank=True, through='Membership')
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, related_name='collections_owned')
    curators = models.ManyToManyField(User, related_name='collections')
    
    class Meta:
        ordering = ['ordering', 'name']
    
    def __unicode__(self):
        return "%s" % (self.title)
    
    def featured_children(self):
        return Collection.objects.filter(featured=True, parent=self).order_by('ordering')

    def has_children(self):
        return Collection.objects.filter(parent=self).count()

    def get_children(self):
        return Collection.objects.filter(parent=self).order_by('ordering', 'name')

    def get_total_resources(self):
        total = self.resources.count()
        for c in self.get_children():
            total += c.get_total_resources()
            
        return total

    def get_breadcrumbs(self):
        crumbs = []
        collection = self
        while collection.parent:
            collection = collection.parent
            crumbs.append(collection)
            
        crumbs.reverse()
        return crumbs 

    def user_can_edit(self, user):
        if user.has_module_perms("library"):
            return True
            
        if collection.owner == request.user:
            return True
            
        if request.user in collection.curators.all():
            return True
        
        return False
        
    def get_ordered_resources(self):
        m = Membership.objects.select_related().filter(collection=self).order_by('ordering')
        
        resources = []
        for mp in m:
            resources.append(mp.resource)
        return resources
        
    def add_resource(self, resource, user=None):
        m = get_object_or_none(Membership, collection=self, resource=resource)
        
        if not m:
            orderings = Membership.objects.filter(collection=self)
            order = 0
            for o in orderings:
                if o.ordering > order:
                    order = o.ordering
                    
            order = order + 1
            m = Membership.objects.create(collection=self, resource=resource, user=user, ordering=order)
            
            Activity.objects.create(resource=resource,
                                    user=user,
                                    activity_type='collect',
                                    content_object=self)
            
        return m

class Membership(models.Model):
    resource = models.ForeignKey(Resource, related_name='members')
    collection = models.ForeignKey(Collection, related_name='members')
    
    added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    
    ordering = models.IntegerField(default=0)

