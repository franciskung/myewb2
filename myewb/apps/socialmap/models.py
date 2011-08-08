"""myEWB social mapping

This file is part of myEWB
Copyright 2010 Engineers Without Borders Canada

@author: Francis Kung
"""

import operator
from datetime import timedelta, datetime

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from socialmap.calculate import calculate, SOCIALMAP_BENCHMARK


class RelationshipManager(models.Manager):
    def get(self, user1, user2, auto_update=True):
    
        # convention is that user1.pk < user2.pk (following this saves us a db
        # lookup), so swap users if needed
        if user2.pk < user1.pk:
            temp_user = user1
            user1 = user2
            user2 = temp_user
            
        # get the record, creating a new one if needed
        obj = self.filter(user1=user1, user2=user2)
        if not obj.count():
            r = Relationship(user1=user1, user2=user2)
            r.update()
            r.save()
            obj = [r]
        
        if auto_update and not obj[0].updating:
            # if stale, recalculate the score
            #   (shouldn't happen if we run a nightly cron or an on-login updater,
            #    but just in case...)
            oneday = datetime.now() - timedelta(days=1)
            if SOCIALMAP_BENCHMARK or not obj[0].last_updated or obj[0].last_updated < oneday:
                obj[0].update()
            
        # throw warning if multiple records found??
        return obj[0]
        
    def get_for_user(self, user1, auto_update=True):
        # get all users who have logged in recently (ie recent activity)
        month_ago = datetime.now() - timedelta(days=31)
        all_users = User.objects.filter(last_login__gt=month_ago,
                                        is_active=True,
                                        is_bulk=False)
                                        
        relationships = {}
        if SOCIALMAP_BENCHMARK:
            print datetime.now()
        for u in all_users:
            if u == user1:
                continue
                
            r = self.get(user1, u, auto_update)
            if SOCIALMAP_BENCHMARK:
                print datetime.now(), r.score, r.user1.email, r.user2.email
            relationships[r] = r.score
        
        if SOCIALMAP_BENCHMARK:
            print datetime.now()
            
        # is there a more efficient sort?
        # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
        sorted_relationships = []
        for r in sorted(relationships, key=relationships.get, reverse=True):
            sorted_relationships.append(r)
            
        return sorted_relationships            
    

class Relationship(models.Model):
    user1 = models.ForeignKey(User, db_index=True, related_name='relationships')
    user2 = models.ForeignKey(User, db_index=True, related_name='relationships2')
    
    score = models.IntegerField(default=0)
    
    cumulative = models.IntegerField(default=0)
    groups = models.IntegerField(default=0)
    events = models.IntegerField(default=0)
    friendships = models.IntegerField(default=0)
    other = models.IntegerField(default=0)
    
    updating = models.NullBooleanField(blank=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True)

    objects = RelationshipManager()
    
    def update(self, background=False):
        #self.updating = True
        #self.save()
        
        calculate(self)

