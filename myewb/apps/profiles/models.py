"""myEWB profile models
Models to store site-specific profile information.

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors

Created on: 2009-06-22
Last modified: 2009-07-31
@author: Joshua Gorner, Francis Kung, Ben Best
"""


from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import mail_admins
from django.db.models.signals import post_save, pre_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.localflavor.ca.forms import CASocialInsuranceNumberField
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from emailconfirmation.models import EmailAddress

from pinax.apps.profiles.models import Profile, create_profile

from base_groups.models import GroupMember
from communities.models import ExecList
from networks.models import Network  
from profiles import signals
#from networks import emailforwards
from datetime import date, datetime
#from siteutils.countries import CountryField
from siteutils.models import Address, PhoneNumber

class Passport(models.Model):
  profile = models.ForeignKey(Profile, related_name="passports", blank=True)

#  country = CountryField()
  country = models.CharField(blank=True, max_length=2)
  passport_number = models.CharField(blank=True, max_length=100)
  name_on_passport = models.CharField(_('name on passport'), blank=True, max_length=200)
  issued_date = models.DateField(default=datetime.today)
  expiry_date = models.DateField(default=datetime.today)
  issued_city = models.CharField(blank=True, max_length=100)

class OnlineService(models.Model):
  profile = models.ForeignKey(Profile, related_name="online_services", blank=True)

  username = models.CharField(blank=True, max_length=100)
  
  IM_SERVICES = (
      ('AIM', _('AOL Instant Messenger')),
      ('Google Talk', _('Google Talk')),
      ('ICQ', _('ICQ')),
      ('MSN', _('Windows Live')),
      ('Skype', _('Skype')),
      ('Twitter', _('Twitter')),
      ('Yahoo', _('Yahoo!')),
  )
  service = models.CharField(_('online services'), max_length=50, choices=IM_SERVICES, null=True, blank=True)

class WebPage(models.Model):
  profile = models.ForeignKey(Profile, related_name="web_pages", blank=True)
  label = models.CharField(blank=True, max_length=100)
  url = models.URLField(blank=True, verify_exists=True)
  


class MemberProfileManager(models.Manager):
    def get_from_view_args(self, *args, **kwargs):
        username = kwargs.get('username', None) or (len(args) > 0 and args[0])
        if username:
            user = User.objects.get(username=username)
            try:
                return MemberProfile.objects.get(user__id=user.id)
            except MemberProfile.DoesNotExist:
                pass
        return None

class MemberProfile(Profile):
    """ Extends Pinax's Profile object to provide additional information stored in the previous myEWB application.
    
    Note that Django and/or Pinax already handle language, email addresses, and 'additional info'.
    """
    
    # necessary hack.  this mirrors the user attribute in Profile, but is 
    # re-defined here so that we can do database joins
    user2 = models.ForeignKey(User, unique=True, verbose_name=_('user2'), blank=True)
    #user2 = models.ForeignKey(User, verbose_name=_('user2'), blank=True, default=0) # may need to use this for evolution to work
    
    # This will be copied to the respective fields in the User object
    first_name = models.CharField(_('first name'), max_length=100, blank=True, null=True)
    preferred_first_name = models.CharField(_('preferred first name (if different)'), max_length=100, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True, null=True)

    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
    )
    gender = models.CharField(_('gender'), max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    LANG_CHOICES = (
        ('E', _('English')),
        ('F', _('French')),
    )
    language = models.CharField(_('preferred language'), max_length=1, choices=LANG_CHOICES, null=True, blank=True)
    
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    # student = models.BooleanField(_('student'), null=True, blank=True)        # see below
    membership_expiry = models.DateField(_('membership expiry'), null=True, blank=True)
    timezone = models.CharField(_('Timezone'), max_length=50, null=True, blank=True)
    
    current_login = models.DateTimeField(_('current login'), null=True, blank=True)
    previous_login = models.DateTimeField(_('previous login'), null=True, blank=True)
    login_count = models.IntegerField(_('login count'), null=False, default=0)
    adminovision = models.BooleanField(_('admin-o-vision'), null=False, blank=True)
    last_updated = models.DateTimeField(editable=False, blank=True, null=True, auto_now=True)
    
    social_insurance = CASocialInsuranceNumberField()
    health_card = models.CharField(blank=True, max_length=100)
    
    show_emails = models.BooleanField(_('show emails'), null=False, blank=True)
    show_replies = models.BooleanField(_('show replies'), null=False, blank=True)
    #sort_by_last_reply = models.BooleanField(_('sort by last reply'), null=False, blank=True)
    SORTING_CHOICES = (('p', _('Original post date')),
                       ('r', _('Latest reply date')))
    sort_by = models.CharField(_('sort by'), choices=SORTING_CHOICES, default='r', max_length=1)
    address_updated = models.DateField(_('address updated'), null=True, blank=True)
    replies_as_emails = models.BooleanField(_('replies as emails'), null=False, blank=True, default=True)
    replies_as_emails2 = models.BooleanField(_('replies as emails two'), null=False, blank=True, default=True)
    watchlist_as_emails = models.BooleanField(_('watchlist replies as emails'), null=False, blank=True, default=True)
    messages_as_emails = models.BooleanField(_('private messages as emails'), null=False, blank=True, default=True)
    
    chapter = models.ForeignKey(Network, null=True, blank=True, default=None)

    #addresses = generic.GenericRelation(Address)
    addresses = models.ManyToManyField(Address)
    phone_numbers = generic.GenericRelation(PhoneNumber)
    sending_groups = models.ManyToManyField("apply.SendingGroup", blank=True)
    
    grandfathered = models.BooleanField(_('grandfathered'),
                                        help_text=_('imported from old myewb and has not accepted new terms of service'),
                                        default=False)
    
    ldap_sync = models.BooleanField("Needs LDAP sync",
                                    default=False,
                                    editable=False)

    objects = MemberProfileManager()
    
    def __unicode__(self):
      if self.name:
        return self.name
      else:
        return ""
        
    def in_canada(self):
        return self.country == "CA"
    
    def email_addresses(self):
        return EmailAddress.objects.filter(verified=True, user=self.user).order_by('-primary')
    
    def unverified_email_addresses(self):
        return EmailAddress.objects.filter(verified=False, user=self.user)
    
    def save(self, force_insert=False, force_update=False):
        if self.first_name or self.last_name:
            # Because nothing is set, this block should NOT be called on the save resulting from create_member_profile
            # If it does it could cause recursion problems
            self.user.first_name = self.first_name
            self.user.last_name = self.last_name
            self.user.save()
        
        if self.preferred_first_name:
            if self.last_name:
                self.name = self.preferred_first_name + " " + self.last_name
            else:
                self.name = self.preferred_first_name
        elif self.first_name:
            if self.last_name:
                self.name = self.first_name + " " + self.last_name
            else:
                self.name = self.first_name
        elif self.last_name:
            self.name = self.last_name
        else:
            self.name = None
            
        self.user2 = self.user
        
        return models.Model.save(self, force_insert, force_update)

    def location(self):
      current_address = default_address()
      
      if current_address:
        location = current_address.city
        if current_address.province:
          location += ", %s" % (current_address.province)
      
      else:
        location = ""
      
      return location
  
    def default_address(self):
        current_address = None
        
        addresses = self.addresses.all()
        if (len(addresses) > 0):
            home_addresses = addresses.filter(label='home')
            if (len(home_addresses) > 0):
                addresses = home_addresses
            
            current_address = addresses[0]
        
        return current_address
    
    def default_phone(self):
        current_phone = None
        
        phones = self.phone_numbers.all()
        if (len(phones) > 0):
            home_phone = phones.filter(label='home')
            if (len(home_phone) > 0):
                phones = home_phone
            
            current_phone = phones[0]
        
        return current_phone
    
            
    def student(self):
        """Determine whether the instant user is a student based on the user's student records"""
        student_records = StudentRecord.objects.filter(user=self.user)
        today = date.today()
        for record in student_records:
            # If no start date listed, assume student unless end date is listed and past end date. 
            # If start date (before today) listed but no end date, assume student.
            # Otherwise, deem student only if between start and end dates.
            # For greater clarity, if neither date is listed, assume student.
            if (record.start_date is None or record.start_date <= today) \
                    and (record.graduation_date is None or record.graduation_date >= today):
                return True
        return False

    def is_owner(self, user):
        """
        Determine whether or not a given user owns this profile.
        @params: user - user object
        @returns: True if user is the profile owner, False otherwise
        """
        return (user.id == self.user.id)
    
    # add a year of membership: either starting today if last membership
    # is already expired, or a year after the current membership expires
    def pay_membership(self):
        if self.membership_expiry == None or self.membership_expiry < date.today():
            self.membership_expiry = date.today()
            signals.regularmember.send(sender=self, user=self.user)
        else:
            signals.renewal.send(sender=self, user=self.user)
            
        self.membership_expiry = date(self.membership_expiry.year + 1,
                                      self.membership_expiry.month,
                                      self.membership_expiry.day)
        self.save()
        
    def is_paid_member(self):
        if self.membership_expiry and date.today() < self.membership_expiry:
            return True
        return False
        
    def chapters(self):
        return self.user2.get_networks()
            
    # get primary chapter
    def get_chapter(self):
        user = self.user2

        # quick check to see if chapter flag makes sense...
        if self.chapter and self.chapter.user_is_member(user):
            return self.chapter
        
        # if it's not set, or if the user isn't a member of that group (any more),
        # take an educated guess at primary chapter
        self.chapter = None
        
        networks = user.get_networks()
        if networks.count() == 1:
            # if you're only a member of one chapter, it's gotta be your primary
            self.chapter = networks[0]
            
        elif networks.count():
            for n in networks:
                # if you're a chapter exec, that should be your primary chapter
                # (and you *should* only ever be exec of one chapter)
                if n.user_is_admin(user, admin_override=False):
                    self.chapter = n

            # if, somehow, you're on an exec list but not marked as a leader
            if self.chapter is None:
                execs = ExecList.objects.filter(member_users=user, is_active=True)
                if execs.count():
                    self.chapter = execs[0].parent.network

            # last resort... take the first chapter they joined as the primary
            if self.chapter is None:
                gm = GroupMember.objects.filter(group__in=list(networks), user=user).order_by('joined')
                self.chapter = gm[0].group.network

        if self.chapter is not None:
            self.save()
            
        return self.chapter

def create_member_profile(sender, instance=None, **kwargs):
    """Automatically creates a MemberProfile for a new User."""
    if instance is None:
        return
    profile, created = MemberProfile.objects.get_or_create(user=instance)

post_save.disconnect(create_profile, sender=User)
post_save.connect(create_member_profile, sender=User)

#def set_primary_email(sender, instance=None, **kwargs):
#    """
#    Automatically sets a verified email to primary if no verified address exists yet.
#    Also updates LDAP for email forwards if the primary emai
#    """
#    if instance is not None and instance.verified:
#        user = instance.user
#        if instance.primary == False:
#            # if we only have one email it is this one
#            if user.emailaddress_set.count() == 1:
#                instance.set_as_primary()
#                emailforwards.updateUser(user, instance.email)
#        else:
#            emailforwards.updateUser(user, instance.email)
#
#post_save.connect(set_primary_email, sender=EmailAddress)

def update_ldap_email(sender, instance=None, **kwargs):
    if instance is not None and instance.verified and instance.primary:
        try:
            profile = instance.user.get_profile() 
            profile.ldap_sync = True
            profile.save()
        except:
            mail_admins("LDAP sync fail",
                        "Can't update ldap sync setting for %s" % instance.user.username,
                        fail_silently=True)
post_save.connect(update_ldap_email, sender=EmailAddress)
    
class StudentRecordManager(models.Manager):
    def get_from_view_args(self, *args, **kwargs):
        username = kwargs.get('username') or (len(args) > 0 and args[0])
        id = kwargs.get('student_record_id', None) or kwargs.get('record_id', None) or (len(args) > 1 and args[1])
        if id and username:
            try:
                return StudentRecord.objects.get(pk=id, user__username=username)
            except StudentRecord.DoesNotExist:
                pass
        return None

class StudentRecord(models.Model):
    """ Represents a record of a member's current or past attendance at a university or other educational institution.
    A member may have one or more such records.
    """
    
    user = models.ForeignKey(User, verbose_name=_('user'))
    network = models.ForeignKey("networks.Network", verbose_name=_('network'), blank=True, null=True)
    
    institution = models.CharField(_('institution'), max_length=255, null=True, blank=True)
    student_number = models.CharField(_('student number'), max_length=255, null=True, blank=True)
    field = models.CharField(_('field'), max_length=255, null=True, blank=True)
    
    STUDENT_LEVELS = (
        ('HS', _('High school')),
        ('CL', _('College')),
        ('UG', _('Undergraduate')),
        ('GR', _('Graduate')),
        ('OT', _('Other')),
    )
    level = models.CharField(_('level'), max_length=2, choices=STUDENT_LEVELS, null=True, blank=True)
    start_date = models.DateField(_('start date'), null=True, blank=True)
    graduation_date = models.DateField(_('graduation date'), null=True, blank=True)
    
    objects = StudentRecordManager()

    def is_owner(self, user):
        """
        Determine whether or not a given user owns this record.
        @params: user - user object
        @returns: True if user is the profile owner, False otherwise
        """
        return (user.id == self.user_id)

class WorkRecordManager(models.Manager):
    def get_from_view_args(self, *args, **kwargs):
        username = kwargs.get('username', None) or (len(args) > 0 and args[0])
        id = kwargs.get('work_record_id', None) or kwargs.get('record_id', None) or (len(args) > 1 and args[1])
        if id and username:
            try:
                return WorkRecord.objects.get(pk=id, user__username=username)
            except WorkRecord.DoesNotExist:
                pass
        return None

class WorkRecord(models.Model):
    """ Represents a record of a member's current or past employment. A member may have one or more such records.
    """
    
    user = models.ForeignKey(User, verbose_name=_('user'))
    network = models.ForeignKey("networks.Network", verbose_name=_('network'), blank=True, null=True)
    
    employer = models.CharField(_('employer'), max_length=255, null=True, blank=True)
    sector = models.CharField(_('sector'), max_length=255, null=True, blank=True)
    position = models.CharField(_('position'), max_length=255, null=True, blank=True)
    start_date = models.DateField(_('start date'), null=True, blank=True)
    end_date = models.DateField(_('end date'), null=True, blank=True)
    
    COMPANY_SIZES = (
        ('tiny', _('1 - 5 employees')),
        ('small', _('6 - 20 employees')),
        ('medium', _('21 - 100 employees')),
        ('large', _('over 100 employees')),
    )
    company_size = models.CharField(_('company size'), max_length=10, choices=COMPANY_SIZES, null=True, blank=True)
    
    INCOME_LEVELS = (
        ('low', _('under $30,000')),
        ('lower_mid', _('$30,000 to $45,000')),
        ('upper_mid', _('$45,000 to $75,000')),
        ('high', _('over $75,000')),
    )
    income_level = models.CharField(_('income level'), max_length=10, choices=INCOME_LEVELS, null=True, blank=True)
    
    objects = WorkRecordManager()
    
    def is_owner(self, user):
        """
        Determine whether or not a given user owns this record.
        @params: user - user object
        @returns: True if user is the profile owner, False otherwise
        """
        return (user.id == self.user_id)

class ToolbarState(models.Model):
    user = models.ForeignKey(User, verbose_name=_('user'),
                             db_index=True)
    toolbar = models.CharField(max_length=255,
                               db_index=True)
    state = models.CharField(max_length=1)
