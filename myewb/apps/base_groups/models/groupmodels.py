"""myEWB base groups models declarations

This file is part of myEWB
Copyright 2009 Engineers Without Borders Canada
Some code derived from Pinax, copyright 2008-2009 James Tauber and Pinax Team, licensed under the MIT License

Last modified on 2010-08-28
@author Joshua Gorner, Benjamin Best, Francis Kung
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
from messages.models import Message
from base_groups.models.membermodels import GroupMember

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

class BaseGroupManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)
    
    def get_for_user(self, user, admin=False):
        if admin:
            return self.active().filter(members__user=user,
                                      members__is_admin=True)
        else:
            return self.active().filter(member_users=user)

class BaseGroup(Group):
    """Base group (from which networks, communities, projects, etc. derive).
    
    Not intended to be instantiated by itself.
    """
    
    model = models.CharField(_('group model'), max_length=500, null=True, blank=True)
    parent = models.ForeignKey('self', related_name="children",
                               verbose_name=_('parent'), null=True, blank=True)
    
    member_users = models.ManyToManyField(User, through=GroupMember, verbose_name=_('members'))
    
    from_name = models.CharField(_('From name'), max_length=255, blank=True,
                                 help_text='"From" name when sending emails to group members')
    from_email = models.CharField(_('From email'), max_length=255, blank=True,
                                  help_text='"From" email address when sending emails to group members')
    
    welcome_email = models.TextField(_('Welcome email'), blank=True, null=True,
                                     help_text='Welcome email to send when someone joins or is added to this group (leave blank for none)')
    
    is_project = models.BooleanField(blank=True, null=True, editable=False) # to save info during migration. not really used.
    is_active = models.BooleanField(_("Is active? (false means deleted group"),
                                    default=True,
                                    editable=False)
    
    objects = BaseGroupManager()
    class Meta:
        app_label = 'base_groups'

    def is_visible(self, user):
        return self.user_is_member(user) or self.user_is_admin(user)
    
    # setting admin_override = True means that admins will be considered group members
    def user_is_member(self, user, admin_override = False):
        if admin_override and user.has_module_perms("base_groups"):
            return True
        if self.slug == 'ewb':
            return True
        return user.is_authenticated() and (self.members.filter(user=user).count() > 0)
        
    def user_is_admin(self, user):
        if user.is_authenticated():
            # site-wide group admins are admins here...
            if user.has_module_perms("base_groups"):
                return True
                
            # admins of the parent group are admins here...
            if self.parent and self.parent.user_is_admin(user):
                return True
            
            # and check for regular admins
            if self.members.filter(user=user, is_admin=True).count() > 0:
                return True
        
        return False
    
    # subclasses should override this...
    def can_bulk_add(self, user):
        return False

    def get_absolute_url(self):
        return reverse('group_detail', kwargs={'group_slug': self.slug})

    def get_member_emails(self):
        members_with_emails = self.members.all().select_related(depth=1)
        return [member.user.email for member in members_with_emails if member.user.email]

    def add_member(self, user):
        """
        Adds a member to a group.
        Retained for backwards compatibility with request_status days.
        Wait, should I not be actively using this?  Because it's a very useful function =)
        """
        member = GroupMember.objects.filter(user=user, group=self)
        if member.count() > 0:
            return member[0]
        else:
            return GroupMember.objects.create(user=user, group=self)
    
    def add_email(self, email):
        """
        Adds an email address to the group, creating the new bulk user if needed
        """
        email_user = get_email_user(email)
        if email_user is None:
            email_user = User.extras.create_bulk_user(email)
        
        self.add_member(email_user)
    
    def remove_member(self, user):
        member = GroupMember.objects.filter(user=user, group=self)
        for m in member:
            m.delete()
            
    def send_mail_to_members(self, subject, htmlBody,
                             fail_silently=False, sender=None,
                             context=None):
        """
        Creates and sends an email to all members of a network using Django's
        EmailMessage.
        Takes in a a subject and a message and an optional fail_silently flag.
        Automatically sets:
        from_email: the sender param, or group_name <group_slug@ewb.ca>
                (note, NO validation is done on "sender" - it is assumed clean!!)
        to: list-group_slug@ewb.ca
        bcc: list of member emails
        """
        
        if sender == None:
            sender = '%s <%s@ewb.ca>' % (self.name, self.slug)
            
        lang = 'en'
        try:
            # is there a cleaner way to do this???!!!
            if self.network.chapter_info.francophone:
                lang = 'fr'
        except:
            pass

        send_mail(subject=subject,
                  txtMessage=None,
                  htmlMessage=htmlBody,
                  fromemail=sender,
                  recipients=self.get_member_emails(),
                  context=context,
                  shortname=self.slug,
                  lang=lang)
    
    def save(self, force_insert=False, force_update=False):
        # if we are updating a group, don't change the slug (for consistency)
        created = False
        if not self.id:
            created = True
            slug = self.slug
            slug = slug.replace(' ', '-')
            
            # translates accents into their regular-character equivalent
            # (http://snippets.dzone.com/posts/show/5499)
            slug = unicodedata.normalize('NFKD', unicode(slug)).encode('ASCII', 'ignore')
            
            #(?P<group_slug>[-\w]+) This is the
            # regex definition of a slug so if we don't match on this we 
            # should remove illegal characters.
            match = re.match(r'[-\w]+', slug)
            if match is None or not match.group(0) == slug:
                slug = re.sub(r'[^-\w]+', '', slug)
            
            # check if slug is in use; increment until we find a good one.
            # (is there anything better than numerical incrementing?)
            temp_groups = BaseGroup.objects.filter(slug__contains=slug)
            #temp_groups = BaseGroup.objects.filter(slug__contains=slug, model=self.model)

            if (temp_groups.count() != 0):
                slugs = [n.slug for n in temp_groups]
                old_slug = slug
                i = 0
                while slug in slugs:
                    i = i + 1
                    slug = old_slug + "%d" % (i, )
                
            self.slug = slug
            
        # also give from_name and from_email reasonable defaults if needed
        if not self.from_name:
            self.from_name = "myEWB notices"
        if not self.from_email:
            self.from_email = "notices@my.ewb.ca"
        
        super(BaseGroup, self).save(force_insert=force_insert, force_update=force_update)
        post_save.send(sender=BaseGroup, instance=self, created=created)

        if created and self.creator:
            gm = GroupMember.objects.filter(user=self.creator,
                                            group=self)
            if gm.count() == 0:
                GroupMember.objects.create(
                        user=self.creator, 
                        group=self,
                        is_admin=True,
                        admin_title='%s Creator' % self.name,
                        admin_order = 1)

    def delete(self):
        for m in self.member_users.all():
            self.remove_member(m)

        self.is_active = False
        self.save()

    def get_url_kwargs(self):
        return {'group_slug': self.slug}
        
    def get_accepted_members(self):
        """
        Accepted members are members that are not bulk (i.e. mailing list)
        users. They have a profile on the site and have signed up for MyEWB.
        """
        # is_bulk is set to True for bulk members
        return self.members.filter(user__is_bulk=False)

    def workspace_view_perms(self, user):
        return self.user_is_member(user, admin_override=True)
        
    def workspace_edit_perms(self, user):
        return self.user_is_admin(user)
    
"""
A hidden, private group that does not show up in any listing except for admins.
Used for logistical purposes, etc.
"""
class LogisticalGroup(BaseGroup):
    objects = BaseGroupManager()
    class Meta:
        app_label = 'base_groups'

    def save(self, force_insert=False, force_update=False):
        self.model = "LogisticalGroup"
        self.visibility = 'M'
        self.invite_only = True
        self.parent = None
        return super(LogisticalGroup, self).save(force_insert, force_update)


"""
A group that users can see, join, etc.  (The opposite of LogisticalGroup)
"""
class VisibleGroup(BaseGroup):
    # if true, members can only join if invited
    invite_only = models.BooleanField(_('invite only'), default=False)
    
    VISIBILITY_CHOICES = (
        ('E', _("everyone")),
        ('P', _("group members and members of parent network only")),
        ('M', _("group members only"))
    )
    visibility = models.CharField(_('visibility'), max_length=1, choices=VISIBILITY_CHOICES, default='E')
    
    EMAIL_TYPE = (('a', "Announcement list"),
                  ('d', "Discussion list"))
    list_type = models.CharField(max_length=1, choices=EMAIL_TYPE, default='d')
    
    whiteboard = models.ForeignKey('whiteboard.Whiteboard', related_name="group", verbose_name=_('whiteboard'), null=True)

    objects = BaseGroupManager()
    class Meta:
        app_label = 'base_groups'

    def is_visible(self, user):
        visible = False
        
        # public groups are always visible
        if self.visibility == 'E' or self.slug == 'ewb':
            visible = True
            
        elif user.is_authenticated():
            # site-wide group admins can see everything
            if user.has_module_perms("base_groups"):
                return True
                
            # admins of the parent group are automatically admins here
            if self.parent and self.parent.user_is_admin(user):
                return True
            
            # members of the group can see the group...
            member_list = self.members.filter(user=user)
            if member_list.count() > 0:
                visible = True
                
            # and the last option, members of the parent group can see this one
            elif self.visibility == 'P':
                parent_member_list = self.parent.members.filter(user=user)
                if parent_member_list.count() > 0:
                    visible = True
                    
        return visible
    
    
    def user_is_member_or_pending(self, user):
        return user.is_authenticated() and ((self.members.filter(user=user).count() > 0) or self.pending_members.filter(user=user).count() > 0)

    def user_is_pending_member(self, user):
        return user.is_authenticated() and self.pending_members.filter(user=user).count() > 0
    
    def num_pending_members(self):
        return self.pending_members.all().count()

    def get_visible_children(self, user):
        if not user.is_authenticated():
            return VisibleGroup.objects.active().filter(parent=self, visibility='E')
        elif user.has_module_perms("base_groups") | self.user_is_admin(user):
            return VisibleGroup.objects.active().filter(parent=self)
        else:
            children = VisibleGroup.objects.active().filter(parent=self, visibility='E') | VisibleGroup.objects.get_for_user(user).filter(parent=self)
            if self.user_is_member(user):
                children = children | VisibleGroup.objects.active().filter(parent=self, visibility='P')
            return children.distinct()
