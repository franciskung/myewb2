from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict

from networks.models import Network
from profiles.models import MemberProfile
from datetime import date, datetime

class TrackingProfile(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    profile = models.ForeignKey(MemberProfile, blank=True, null=True)

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    
    chapter = models.ForeignKey(Network, blank=True, null=True)
    role = models.CharField(max_length=255, blank=True, null=True)
    
    workplace = models.CharField(max_length=255, blank=True, null=True)
    school = models.CharField(max_length=255, blank=True, null=True)
    workfield = models.CharField(max_length=255, blank=True, null=True, verbose_name='Field / Profession')
    graduation = models.CharField(max_length=255, blank=True, null=True, verbose_name='Expected graduation', help_text="If a student - use mm-yyyy format")

    updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, related_name="trackingprofile_updates")
    
    flags = models.ManyToManyField('Flag', through='ProfileFlag')
    badges = models.ManyToManyField('Badge', through='ProfileBadge')

    # plus these reverse relations:
    #   email_set
    #   address_set
    #   activity_set
    #   profilehistory_set
    
    def primary_email(self):
        email = self.email_set.filter(primary=True)
        if email:
            return email[0].email
        else:
            return None
            
    def get_activities(self, page=1, per_page=15):
        idx = (page - 1) * per_page
        return self.activity_set.filter()[idx:idx+(per_page-1)]
            
    def to_dict(self):
        d = model_to_dict(self)
        d['emails'] = [e.email for e in self.email_set.all()]
        d['addresses'] = [a.address for a in self.address_set.all()]
        
        return d

class Email(models.Model):
    email = models.EmailField()
    profile = models.ForeignKey(TrackingProfile)
    primary = models.BooleanField(default=False)
    updated = models.DateTimeField()
    
    class Meta:
        ordering = ('-primary', '-email')

class Address(models.Model):
    address = models.TextField()
    profile = models.ForeignKey(TrackingProfile)
    primary = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-primary', '-updated')

class Donation(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    date = models.DateTimeField()
    amount = models.DecimalField(decimal_places=2, max_digits=20)
    campaign = models.CharField(max_length=255, blank=True, null=True)

FLAG_COLOURS = (('red', 'red'),
                ('green', 'green'),
                ('blue', 'blue'),
                ('yellow', 'yellow'),
                ('grey', 'grey'),
                ('black', 'black'))
class Flag(models.Model):
    name = models.CharField(max_length=255)
    colour = models.CharField(max_length=255, choices=FLAG_COLOURS)
    
class ProfileFlag(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    flag = models.ForeignKey(Flag)
    note = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    flagged_by = models.ForeignKey(User, related_name='flags')
    flagged_date = models.DateTimeField(auto_now_add=True)
    unflagged_by = models.ForeignKey(User, related_name='unflags')
    unflagged_date = models.DateTimeField(blank=True, null=True)
    
BADGE_COLOURS = (('red', 'red'),
                 ('green', 'green'),
                 ('blue', 'blue'),
                 ('yellow', 'yellow'),
                 ('grey', 'grey'),
                 ('black', 'black'))
class Badge(models.Model):
    name = models.CharField(max_length=255)
    colour = models.CharField(max_length=255, choices=BADGE_COLOURS)
    
class ProfileBadge(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    badge = models.ForeignKey(Badge)
    note = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, related_name='badges')
    added_date = models.DateTimeField(auto_now_add=True)
    removed_by = models.ForeignKey(User, related_name='unbadges')
    removed_date = models.DateTimeField(blank=True, null=True)
    
class Activity(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    activity_type = models.CharField(max_length=255)
    date = models.DateField()
    entered = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)
    
    content_type = models.ForeignKey(ContentType, blank=True, null=True, related_name='RolodexActivity')
    object_id = models.IntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ('-pinned', '-date',)

INTERACTION_TYPES = (('call', 'Phone call'),
                     ('conversation', 'Conversation'),
                     ('note', 'Note'))
class Interaction(Activity):
    added_by = models.ForeignKey(User)
    interaction_type = models.CharField(max_length=255, choices=INTERACTION_TYPES)
    note = models.TextField(blank=True, null=True)
    
class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    description = models.TextField()
    
class EventAttendance(Activity):
    event = models.ForeignKey(Event)
    
class ProfileHistory(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    editor = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    
    revision = models.TextField(blank=True, null=True)
    
