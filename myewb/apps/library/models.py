from django.db import models

from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import Q
from django.template.defaultfilters import slugify
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
    
    class Meta:
        ordering = ('-date',)
    
class Resource(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    model = models.CharField(max_length=25)
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    creator = models.ForeignKey(User, related_name='library_resources', null=True)
    updator = models.ForeignKey(User, related_name='library_updates', null=True)
    
    #objects = WorkspaceFileManager()
    
    RESOURCE_TYPES = (('article', 'Articles and papers'),
                      ('guide', "Guides and how-to's"),
                      ('media', 'Visual media'),
                      ('website', 'Website'),
                      ('workshop', 'Workshops'),
                      ('other', 'Other')
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
    visible = models.BooleanField(default=True)
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
        
    def get_rating(self, user):
        if not user.is_authenticated():
            return None
            
        return get_object_or_none(Rating, resource=self, user=user)
        
    def add_rating(self, user, rating):
        rating_obj = self.get_rating(user)

        if not rating_obj:
            rating_obj = Rating.objects.create(resource=self, user=user, rating=rating)
            
            ratings = Rating.objects.filter(resource=self)
            num_ratings = len(ratings)
            sum_ratings = 0
            for r in ratings:
                sum_ratings = sum_ratings + r.rating
                # yeah, I could use aggregates for this. probably should.
            
            avg_rating = round(float(sum_ratings) / num_ratings)
            
            self.rating = avg_rating
            self.save()
            
            Activity.objects.create(resource=self,
                                    user=user,
                                    activity_type='rate',
                                    content_object=rating_obj)
            
        return rating_obj
        
    def user_can_see(self, user):
        if self.visible == True:
            return True
            
        if not user.is_authenticated():
            return False

        if user.has_module_perms('library'):
            return True
            
        if self.creator == user:
            return True
            
        return False            
        
    def user_can_edit(self, user):
        if not user.is_authenticated():
            return False
    
        if self.editable == True:
            return True

        if user.has_module_perms('library'):
            return True
            
        if self.creator == user:
            return True
            
        return False            
    
# TODO: regex to use for validating filenames.  For now, anything not alpha-numeric-
# dash-underscore-period-space gets stripped, but would be good to allow accents eventually.
re_filename = re.compile(r'[^A-Za-z0-9\-_. ]')
        
class FileResource(Resource):
    filename = models.CharField(max_length=255)
    checksum = models.CharField(max_length=32, default='')
    
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
        
    def upload(self, uploadedfile):
        # build and validate file name name
        filename = re_filename.sub(r'', uploadedfile.name)
        #self.filename=filename
        fname, dot, extension = filename.rpartition('.')
        self.filename = slugify(self.name) + '.' + extension
            
        # open file
        diskfile = open(self.get_path(), 'wb+')
            
        # write file to disk
        md5 = hashlib.md5()
        
        for chunk in uploadedfile.chunks():
            diskfile.write(chunk)
            md5.update(chunk)
        diskfile.close()
        
        self.checksum = md5.hexdigest()
        self.save()

        return self
        
        
class LinkResource(Resource):
    url = models.URLField(verbose_name='URL')
    
    def save(self, *args, **kwargs):
        self.model = 'linkresource'
        return super(LinkResource, self).save(*args, **kwargs)
        
    def direct_download(self):
        return self.url

class Collection(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    
    parent = models.ForeignKey("self", blank=True, null=True)
    ordering = models.IntegerField(default=1)
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
        return "%s" % (self.name)
    
    def slug(self):
        return slugify(self.name)
    
    def featured_children(self):
        return Collection.objects.filter(featured=True, parent=self).order_by('ordering')

    def has_children(self):
        return Collection.objects.filter(parent=self).count()

    def get_children(self):
        return Collection.objects.filter(parent=self).order_by('ordering', 'name')

    def get_total_resources(self):
        total = self.resources.count()
        for c in self.get_children():
            total = total + 1
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
        if not user.is_authenticated():
            return False
    
        if user.has_module_perms("library"):
            return True
            
        if self.owner == user:
            return True
            
        if user in self.curators.all():
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

class Rating(models.Model):
    resource = models.ForeignKey(Resource, related_name='ratings')
    user = models.ForeignKey(User)
    
    added = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)


