"""myEWB social mapping

This file is part of myEWB
Copyright 2010 Engineers Without Borders Canada

@author: Francis Kung
"""

from datetime import timedelta, datetime

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

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
            obj[0] = r
        
        if auto_update and not obj[0].updating:
            # if stale, recalculate the score
            #   (shouldn't happen if we run a nightly cron or an on-login updater,
            #    but just in case...)
            oneday = datetime.now() - timedelta(days=1)
            if (not obj[0].last_updated or obj[0].last_updated < oneday)
                obj[0].update()
            
        # throw warning if multiple records found??
        return obj[0]
    

class Relationship(models.Model):
    user1 = models.ForeignKey(User, db_index=True)
    user2 = models.ForeignKey(User, db_index=True)
    
    score = models.IntegerField(default=0)
    
    cumulative = models.IntegerField(default=0)
    groups = models.IntegerField(default=0)
    events = models.IntegerField(default=0)
    friendships = models.IntegerField(default=0)
    other = models.IntegerField(default=0)
    
    updating = models.BooleanField(null=True, blank=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True)

    objects = RelationshipManager()
    
    def update(self, background=False):
        #self.updating = True
        #self.save()
        
        calculate(self)

