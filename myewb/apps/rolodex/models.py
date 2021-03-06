from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms.models import model_to_dict

from networks.models import Network
from profiles.models import MemberProfile
from datetime import date, datetime

from siteutils.shortcuts import get_object_or_none
from siteutils.models import Address as MyewbAddress, PhoneNumber as MyewbPhone
from emailconfirmation.models import EmailAddress as MyewbEmail

class TrackingProfile(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    profile = models.ForeignKey(MemberProfile, blank=True, null=True)

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    
    chapter = models.ForeignKey(Network, blank=True, null=True)
    role = models.CharField(max_length=255, blank=True, null=True, verbose_name='Position')
    city = models.CharField(max_length=255, blank=True, null=True)
    
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
    #   phone_set
    #   activity_set
    #   profilehistory_set
    
    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)
    
    def primary_email(self):
        email = self.email_set.filter(primary=True)
        if not email:
            email = self.email_set.all()
            
        if email:
            return email[0].email
        else:
            return None
            
    def primary_address(self):
        address = self.address_set.filter(primary=True)
        if not address:
            address = self.address_set.all()

        if address:
            return address[0].address
        else:
            return None
            
    def get_activities(self, user=None, page=1, per_page=15):
        qry = Q(visibility='anyone')
        qry2 = Q(visibility='private') & Q(added_by=user)
        activities = self.activity_set.filter(qry | qry2)
        
        idx = (page - 1) * per_page
        return activities[idx:idx+(per_page-1)]
        
    def get_flags(self):
        return self.profileflag_set.filter(active=True)
        
    def get_badges(self):
        return self.profilebadge_set.filter(active=True)
        
    def to_dict(self):
        d = model_to_dict(self)
        d['emails'] = [e.email for e in self.email_set.all()]
        d['addresses'] = [a.address for a in self.address_set.all()]
        
        return d
        
    def get_custom_fields(self, user=None, include_blank=False):
        qry = Q(badge__isnull=True) & Q(flag__isnull=True)
        
        badges = self.get_badges().values_list('badge', flat=True)
        qry2 = Q(badge__in=list(badges))

        flags = self.get_flags().values_list('flag', flat=True)
        qry3 = Q(flag__in=list(flags))
        
        if user:
            qry4 = Q(visibility='anyone') | (Q(visibility='private') & Q(owner=user))
        else:
            qry4 = Q(visibility='anyone')
        
        fields = CustomField.objects.filter((qry | qry2 | qry3) & qry4)
        
        result = {}
        for field in fields:
            value = get_object_or_none(CustomValue, profile=self, field=field)
            if value or include_blank:
                result[field] = value
                
        return result
        

    # add a new email address, set it as primary
    def update_email(self, email):
        if email:
            email_obj = get_object_or_none(Email, email=email, profile=self)
            if not email_obj:
                email_obj = Email.objects.create(email=email,
                                                 profile=self,
                                                 updated=datetime.now())
            if not email_obj.primary:
                other_emails = Email.objects.filter(profile=self)
                for e in other_emails:
                    e.primary = False
                    e.save()
                email_obj.primary = True
                email_obj.save()

    # add a new phone number, set it as primary
    def update_phone(self, phone):
        if phone:
            phone_obj = get_object_or_none(Phone, phone=phone, profile=self)
            if not phone_obj:
                phone_obj = Phone.objects.create(phone=phone,
                                                 profile=self,
                                                 updated=datetime.now())
            if not phone_obj.primary:
                other_phones = Phone.objects.filter(profile=self)
                for e in other_phones:
                    e.primary = False
                    e.save()
                phone_obj.primary = True
                phone_obj.save()

class Email(models.Model):
    email = models.EmailField()
    profile = models.ForeignKey(TrackingProfile)
    primary = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    myewbemail = models.ForeignKey(MyewbEmail, null=True, blank=True, related_name='rolodexemail')
    
    class Meta:
        ordering = ('-primary', '-email')

    def __unicode__(self):
        return self.email
    
class Phone(models.Model):
    phone = models.CharField(max_length=50)
    profile = models.ForeignKey(TrackingProfile)
    primary = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    myewbphone = models.ForeignKey(MyewbPhone, null=True, blank=True, related_name='rolodexphone')
    
    class Meta:
        ordering = ('-primary', '-updated')

    def __unicode__(self):
        return self.phone
    
class Address(models.Model):
    address = models.TextField()
    profile = models.ForeignKey(TrackingProfile)
    primary = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    myewbaddress = models.ForeignKey(MyewbAddress, null=True, blank=True, related_name='rolodexaddress')

    class Meta:
        ordering = ('-primary', '-updated')

    def __unicode__(self):
        return self.address
    
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
    description = models.TextField(blank=True, null=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)
    
class ProfileFlag(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    flag = models.ForeignKey(Flag)
    note = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    flagged_by = models.ForeignKey(User, related_name='flags')
    flagged_date = models.DateTimeField(auto_now_add=True)
    unflagged_by = models.ForeignKey(User, related_name='unflags', blank=True, null=True)
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
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ('name',)
        
    def __unicode__(self):
        return self.name
    
class ProfileBadge(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    badge = models.ForeignKey(Badge)
    year = models.CharField(max_length=50, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    current = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, related_name='badges')
    added_date = models.DateTimeField(auto_now_add=True)
    removed_by = models.ForeignKey(User, related_name='unbadges', blank=True, null=True)
    removed_date = models.DateTimeField(blank=True, null=True)
    
VISIBILITY_OPTIONS = (('anyone', 'Anyone with access to the Rolodex (all staff)'),
#                      ('team', 'My team only'),
                      ('private', 'Private - no one else can see this'))
class Activity(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    activity_type = models.CharField(max_length=255)
    date = models.DateField()
    entered = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)
    visibility = models.CharField(max_length=255, choices=VISIBILITY_OPTIONS, default='anyone')
    added_by = models.ForeignKey(User, blank=True, null=True)
    
    content_type = models.ForeignKey(ContentType, blank=True, null=True, related_name='RolodexActivity')
    object_id = models.IntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ('-pinned', '-date','-entered')

INTERACTION_TYPES = (('call', 'Phone call'),
                     ('conversation', 'Conversation'),
                     ('note', 'Note'))
class Interaction(Activity):
    interaction_type = models.CharField(max_length=255, choices=INTERACTION_TYPES, default='note')
    note = models.TextField(blank=True, null=True)
    edited = models.DateTimeField(blank=True, null=True)
    
    def note_trunc(self, length=125):
        if len(self.note) < length:
            return self.note
            
        return self.note[0:length].rsplit(' ', 1)[0] + '...'
    
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
    
class ProfileView(models.Model):
    profile = models.ForeignKey(TrackingProfile)
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    ip = models.IPAddressField()

class CustomField(models.Model):
    badge = models.ForeignKey(Badge, blank=True, null=True)
    flag = models.ForeignKey(Flag, blank=True, null=True)
    name = models.CharField(max_length=50)
    visibility = models.CharField(max_length=255, choices=VISIBILITY_OPTIONS, default='anyone')
    owner = models.ForeignKey(User)
    
class CustomValue(models.Model):
    field = models.ForeignKey(CustomField)
    profile = models.ForeignKey(TrackingProfile)
    value = models.CharField(max_length=255, null=True, blank=True)

