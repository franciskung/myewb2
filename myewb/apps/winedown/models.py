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
        if not obj:
            return None
            
        ctype = ContentType.objects.get_for_model(obj)
        
        try:
            container, created = CheersContainer.objects.get_or_create(content_type=ctype,
                                                                       object_id = obj.id)
        except CheersContainer.MultipleObjectsReturned:
            containers = CheersContainer.objects.filter(content_type=ctype,
                                                        object_id = obj.id)
            for c in containers[1:]:
                c.delete()
            container = containers[0]
            
        return container

    def get_for_object(self, obj):
        if obj:
            container = self.get_container(obj)
            c = self.get_query_set().filter(content=container)
        else:
            c = self.get_query_set().none()
        return c
        
    def latest(self):
        c = CheersContainer.objects.filter(count__gt=0, hidden=False).order_by('-latest')
        return c
        
    def popular(self):
        c = CheersContainer.objects.filter(count__gt=0, hidden=False).order_by('-count')
        return 
        
    def create_link(self, obj):
        container = self.get_container(obj)
        return reverse('winedown_cheers', kwargs={'content_id': container.id})
        
    def create_from_obj(self, obj, user=None, comment=None):
        container = self.get_container(obj)
        return self.create_from_container(container, user, comment)
        
    def create_from_container(self, container, user, comment=None):
        if not user or not user.is_authenticated():
            return None
    
        try:
            c, created = Cheers.objects.get_or_create(owner=user, content=container)
        except Cheers.MultipleObjectsReturned:
            cheerses = Cheers.objects.filter(owner=user, content=container)
            for c in cheerses[1:]:
                c.delete()
                
            c = cheerses[0]
            created = False
        
        if created:
            c.comment = comment
            c.save()
        
            #container.refresh_count()
            container.count = container.count + 1
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
    hidden = models.BooleanField(default=False)
    
    def refresh_count(self):
        count = Cheers.objects.filter(content=self).count()
        self.count = count
        self.save()
        
    def guess_title(self):
        obj = self.content_object
        
        titles = ('title', 'name', 'subject', 'text')  # any others?
        
        for t in titles:
            if hasattr(obj, t):
                return getattr(obj, t)
                
        return "unnamed object"

    def guess_author(self):
        obj = self.content_object
        
        titles = ('author', 'owner', 'creator', 'user')
        
        for t in titles:
            if hasattr(obj, t):
                return getattr(obj, t)
                
        return {'id': 0, 'visible_name': "unknown user"}
        
    def get_cheers(self):
        cheers = self.cheers_set.all()
        
        cheers2 = []
        for c in cheers:
            if c.model == 'Retweet':
                c = c.retweet
                
            cheers2.append(c)
            
#        cheers2.reverse()
        return cheers2

    def num_cheers(self):
        ct = ContentType.objects.get(app_label='winedown', model='Tweet')
        if self.content_type == ct:
            return self.count - 1
        else:
            return self.count

# a cheers: represents a "like" or "tumbs-up".
# cheers don't stand alone; they are always attached to a container
# (normally a post or a tweet)
class Cheers(models.Model):
    owner = models.ForeignKey(User, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(max_length=120, blank=True, null=True,
                               verbose_name="Comment (optional)")

    content = models.ForeignKey(CheersContainer)
    
    model = models.CharField(max_length=50, default='Cheers')
    
    objects = CheersManager()

    class Meta:
        ordering = ['-date']
        
# ability to do a free-form cheers container... it's like a tweet,
# except you don't need to be on twitter
class CustomCheers(models.Model):
    author = models.ForeignKey(User)
    date = models.DateTimeField(db_index=True, auto_now_add=True)
    text = models.TextField(max_length=120, verbose_name="")
    

class Tweet(models.Model):
    author = models.ForeignKey(User, blank=True, null=True)
    author_name = models.CharField(max_length=255)
    author_username = models.CharField(max_length=255, db_index=True)
    author_userid = models.IntegerField()
    author_image = models.CharField(max_length=255)
    date = models.DateTimeField(db_index=True)
    twitter_id = models.CharField(max_length=255, db_index=True)
    text = models.CharField(max_length=255)

    def get_absolute_url(self):
        return "http://twitter.com/#!/%s/status/%s" % (self.author_username, self.twitter_id)
        
    def retweet(self, twitter_array):
        container = Cheers.objects.get_container(self)
        
        c, created = Retweet.objects.get_or_create(twitter_id=twitter_array['id_str'], content=container,
                                                   defaults={'author_name': twitter_array['user']['name'],
                                                             'author_username': twitter_array['user']['screen_name'],
                                                             'author_userid':  twitter_array['user']['id'],
                                                             'author_image': twitter_array['user']['profile_image_url']})

        if created:
            #container.refresh_count()
            container.count = container.count + 1
            container.latest = datetime.datetime.now()
            container.save()
        
        return c
        
        
class Retweet(Cheers):
    author = models.ForeignKey(User, blank=True, null=True)
    author_name = models.CharField(max_length=255)
    author_username = models.CharField(max_length=255, db_index=True)
    author_userid = models.IntegerField()
    author_image = models.CharField(max_length=255)
    twitter_id = models.CharField(max_length=255, db_index=True)

    def save(self, force_insert=False, force_update=False):
        self.model = "Retweet"
        return super(Retweet, self).save(force_insert, force_update)
        
