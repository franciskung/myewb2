from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models.signals import post_save

from base_groups.models import BaseGroup, GroupMember, GroupLocation

class Network(BaseGroup):
    
    TYPE_CHOICES = (
	    ('N', _('National')),
        ('R', _('Regional')),
        ('U', _('University')),
        ('C', _('Company')),
    )
    network_type = models.CharField(_('network type'), max_length=1, null=True, blank=True, choices=TYPE_CHOICES)
    
    def get_absolute_url(self):
        return reverse('network_detail', kwargs={'group_slug': self.slug})
    
    def get_url_kwargs(self):
        return {'group_slug': self.slug}
        
class NetworkMember(GroupMember):
    parent_model = Network
    
def create_network_location(sender, instance=None, **kwargs):
    """Automatically creates a GroupLocation for a new Network."""
    if instance is None:
        return
    location, created = GroupLocation.objects.get_or_create(group=instance)

post_save.connect(create_network_location, sender=Network)