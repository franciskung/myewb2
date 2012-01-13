"""myEWB communities models declarations

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors
Some code derived from Pinax, copyright 2008-2009 James Tauber and Pinax Team, licensed under the MIT License

Created on 2009-07-30
@author Joshua Gorner, Benjamin Best
"""
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from base_groups.models import BaseGroup, GroupMember, add_creator_to_group

# ugly to add a dependency, but need to do this so the add_to_class calls happen before the subclassing...
from mailchimp.models import MailchimpEvent

class CommunityManager(models.Manager):
    def listing(self):
        return self.get_query_set().filter(parent__isnull=True, is_active=True)
        
class Community(BaseGroup):
    objects = CommunityManager()
    
    def get_absolute_url(self):
        return reverse('community_detail', kwargs={'group_slug': self.slug})
    
    def can_bulk_add(self, user):
        if user.has_module_perms("base_groups"):
            return True
        
        if self.parent:
            try:
                return self.parent.network.can_bulk_add(user)   # bit of a hack... but self.parent
            except:                                             # is a BaseGroup when we want to access
                return self.parent.can_bulk_add(user)           # the overridden Network.can_bulk_add
        else:
            return False
       
    def save(self, force_insert=False, force_update=False):
        self.model = "Community"
        return super(Community, self).save(force_insert, force_update)
        
    class Meta:
        verbose_name_plural = "communities"
# use same add_creator_to_group from base_groups
post_save.connect(add_creator_to_group, sender=Community)

class NationalRepList(Community):
    visibility = models.CharField(_('visibility'), max_length=1,
                                  choices=BaseGroup.VISIBILITY_CHOICES,
                                  default='M', editable=False)
    invite_only = models.BooleanField(_('invite only'), default=True,
                                      editable=False)
    
class ExecList(Community):
    visibility = models.CharField(_('visibility'), max_length=1,
                                  choices=BaseGroup.VISIBILITY_CHOICES,
                                  default='M', editable=False)
    invite_only = models.BooleanField(_('invite only'), default=True,
                                      editable=False)
