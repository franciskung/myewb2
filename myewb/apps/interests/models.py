"""myEWB interst models

This file is part of myEWB
Copyright 2011 Engineers Without Borders Canada

"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from base_groups.models import BaseGroup
from group_topics.models import GroupTopic
from profiles.models import MemberProfile

class InterestManager(models.Manager):
    pass
    #def get_for_group(self, group):
    #    """
    #    Returns all posts belonging to a given group
    #    """
    #    return self.get_query_set().filter(pending=False, parent_group=group).order_by('-last_reply')
    
    
class Interest(models.Model):
    """
    a topic of discussion/interest, that posts/etc can be tagged with
    """

    tag = models.CharField(max_length=50, blank=False)
    topics = models.ManyToManyField(GroupTopic, blank=True)
    users = models.ManyToManyField(MemberProfile, blank=True)
    groups = models.ManyToManyField(BaseGroup, blank=True)
    primary_group = models.ForeignKey(BaseGroup, blank=True, null=True, related_name='primary_interest')

    highlighted = models.BooleanField(default=False)

    related_tags = models.ManyToManyField('self', blank=True)
    
    objects = InterestManager()
    
    class Meta:
        ordering = ['tag',]

    def __unicode(self):
        return self.tag
    
class InterestAlias(models.Model):
    """A simple class to hold aliased tags.  The idea is to link similar tags:
    if someone types "hso" for example, it should be linked to "school outreach"
    which is the proper term.
    """
    interest = models.ForeignKey(Interest, related_name="aliased_tags", verbose_name=_('tag'))
    alias = models.TextField(_('alias'), blank=False)

    def __unicode__(self):
        return "%s => %s" % (self.alias, self.tag)


