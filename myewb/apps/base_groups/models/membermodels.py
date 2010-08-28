"""myEWB base groups models declarations

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors
Some code derived from Pinax, copyright 2008-2009 James Tauber and Pinax Team, licensed under the MIT License

Last modified on 2009-07-29
@author Joshua Gorner, Benjamin Best
"""

import datetime
import re
import unicodedata

from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models, connection
from django.db.models.signals import post_save, pre_delete
from django.conf import settings

from mailer import send_mail
from emailconfirmation.models import EmailAddress

from siteutils.helpers import get_email_user
from manager_extras.models import ExtraUserManager
from groups.base import Group
#from whiteboard.models import Whiteboard
from messages.models import Message

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

class BaseGroupMember(models.Model):
    is_admin = models.BooleanField(_('Exec / Leader'), default=False)
    admin_title = models.CharField(_('Title'), max_length=500, null=True, blank=True)
    admin_order = models.IntegerField(_('admin order (smallest numbers come first)'), default=999, blank=True, null=True)
    joined = models.DateTimeField(_('joined'), default=datetime.datetime.now)
    imported = models.BooleanField(default=False, editable=False)
    
    class Meta:
        abstract = True
        ordering = ('is_admin', 'admin_order')
        app_label = 'base_groups'

    def __unicode__(self):
        return "%s - %s" % (self.user, self.group,)

class GroupMemberManager(models.Manager):
    """
    Adds custom manager methods for accepted and bulk members.
    """
    use_for_related_fields = True
    def accepted(self):
        return self.get_query_set().filter(user__is_bulk=False)

    def bulk(self):
        return self.get_query_set().filter(user__is_bulk=True)

class GroupMember(BaseGroupMember):
    """
    Non-abstract representation of BaseGroupMember. Base class is required
    for GroupMemberRecord.
    """
    # had to double these two fields in this model and GroupMemberRecord due to issues with related_name. 
    # See http://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    group = models.ForeignKey('base_groups.BaseGroup', related_name="members", verbose_name=_('group'))
    user = models.ForeignKey(User, related_name="member_groups", verbose_name=_('user'))
    # away = models.BooleanField(_('away'), default=False)
    # away_message = models.CharField(_('away_message'), max_length=500)
    # away_since = models.DateTimeField(_('away since'), default=datetime.now)

    objects = GroupMemberManager()

    class Meta:
        app_label = 'base_groups'

    @property
    def is_accepted(self):
        return not self.user.is_bulk

    @property
    def is_bulk(self):
        return self.user.is_bulk

class GroupMemberRecord(BaseGroupMember):
    """
    A snapshot of a user's group status at a particular point in time.
    """
    # had to double these two fields in this model and GroupMember due to issues with related_name. 
    # See http://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    group = models.ForeignKey('base_groups.BaseGroup', related_name="member_records", verbose_name=_('group'))
    user = models.ForeignKey(User, related_name="group_records", verbose_name=_('user'))
    datetime = models.DateTimeField(auto_now_add=True)
    #datetime = models.DateTimeField(default=datetime.datetime.now())
    membership_start = models.BooleanField(default=False, help_text=_('Whether this record signifies the start of a membership or not.'))
    membership_end = models.BooleanField(default=False, help_text=_('Whether this record signifies the end of a membership or not.'))

    class Meta(BaseGroupMember.Meta):
        get_latest_by = 'datetime'
        app_label = 'base_groups'

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        super(GroupMemberRecord, self).__init__(*args, **kwargs)
        if instance is not None:
            # copy over all properties from the instance provided
            # note that these override any values passed to the constructor
            self.group = instance.group
            self.user = instance.user
            self.is_admin = instance.is_admin
            self.admin_title = instance.admin_title
            self.admin_order = instance.admin_order
            self.joined = instance.joined
            self.datetime = instance.joined


def group_member_snapshot(sender, instance, created, **kwargs):
    """
    Takes a snapshot of a GroupMember object each time is
    saved.
    """
    record = GroupMemberRecord(instance=instance)
    if created:
        record.membership_start = True
    record.save()
post_save.connect(group_member_snapshot, sender=GroupMember, dispatch_uid='groupmembersnapshot')

def send_welcome_email(sender, instance, created, **kwargs):
    """
    Sends a welcome email to new members of a group
    """
    group = instance.group

    if created and group.welcome_email:
        user = instance.user
        
        sender = '"%s" <%s>' % (group.from_name, group.from_email)

        # TODO: template-ize
        txtMessage = """You have been added to the %s group on myEWB, the Engineers Without Borders online community.

"%s"
""" % (group.name, group.welcome_email)
         
        send_mail(subject="Welcome to '%s'" % group.name,
                  txtMessage=txtMessage, # TODO: make this text-only!
                  htmlMessage=None,
                  fromemail=sender,
                  recipients=[user.email])
        
post_save.connect(send_welcome_email, sender=GroupMember, dispatch_uid='groupmemberwelcomeemail')
        

def end_group_member_snapshot(sender, instance, **kwargs):
    """
    Takes the final snapshot of a group member as it is deleted.
    Sets the membership_end = True to signify the end.
    """
    record = GroupMemberRecord(instance=instance)
    record.membership_end = True
    record.save()
pre_delete.connect(end_group_member_snapshot, sender=GroupMember, dispatch_uid='endgroupmembersnapshot')
            
class PendingMember(models.Model):
    user = models.ForeignKey(User, related_name='pending_memberships')
    group = models.ForeignKey('base_groups.VisibleGroup', related_name='pending_members')
    request_date = models.DateField(auto_now_add=True)
    message = models.TextField(help_text=_("Message indicating reason for request."))

    class Meta:
        app_label = 'base_groups'

    @property
    def is_invited(self):
        return hasattr(self, 'invitationtojoingroup')

    @property
    def is_requested(self):
        return hasattr(self, 'requesttojoingroup')

    def accept(self):
        """
        Accepts the current request or invitation.
        """
        GroupMember.objects.create(user=self.user, group=self.group)
        self.delete()

    def reject(self):
        """
        Rejects the current request or invitation.
        """
        self.delete()

class RequestToJoinGroup(PendingMember):
    class Meta:
        app_label = 'base_groups'

class InvitationToJoinGroup(PendingMember):
    invited_by = models.ForeignKey(User, related_name='invitations_issued', default=0)

    class Meta:
        app_label = 'base_groups'

def invitation_notify(sender, instance, created, **kwargs):
    user = instance.user
    group = instance.group
    issuer = instance.invited_by
    message = instance.message
    
    if notification and False:  # need to create the notice type for this to work
        notification.send([user], "group_invite", {"invitation": instance})
    else:
        # TODO: templatize this
        # TODO: i18n this (trying to causes db errors right now)
        msgbody = "%s has invited you to join the \"%s\" group.<br/><br/>" % (issuer.visible_name(), group)
        if message:
            msgbody += message + "<br/><br/>"
        msgbody += "<a href='%s'>click here to respond</a>" % group.get_absolute_url()
        
        Message.objects.create(subject="%s has invited you to join the \"%s\" group" % (issuer.visible_name(), group),
                               body=msgbody,
                               sender=issuer,
                               recipient=user)

post_save.connect(invitation_notify, sender=InvitationToJoinGroup)
    
class GroupLocation(models.Model):
    group = models.ForeignKey('base_groups.BaseGroup', related_name="locations", verbose_name=_('group'))
    place = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        app_label = 'base_groups'

def clean_up_bulk_users(sender, instance, created, **kwargs):
    if instance.verified:
        # XXX Warning! This only works because get_email_user returns
        # the user with their email set to the argument before it returns
        # users with EmailAddress's with the argument
        email_user = get_email_user(instance.email)
        user = instance.user
        # a 
        if email_user and not email_user == user:
            # update group memberships
            for membership in email_user.member_groups.all():
                if not user.member_groups.filter(group=membership.group):
                    membership.user = instance.user
                    membership.save()
                else:
                    membership.delete()
                    
            # update membership records (should we just delete them instead?)
            for record in email_user.group_records.all():
                record.user = instance.user
                record.save()
                
            # update invitations
            for invitation in email_user.pending_memberships.all():
                if not user.pending_memberships.filter(group=invitation.group):
                    invitation.user = instance.user
                    invitation.save()
                else:
                    invitation.delete()
                
            # delete old bulk user
            email_user.delete()

post_save.connect(clean_up_bulk_users, sender=EmailAddress)
