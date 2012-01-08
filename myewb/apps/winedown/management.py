"""myEWB winedown management

This file is part of myEWB
Copyright 2011 Engineers Without Borders Canada

@author Francis Kung
"""

from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from permissions.models import PermissionGroup
from winedown import models as wd
from winedown.models import Cheers

def create_perm_group(sender, **kwargs):
    group, created = PermissionGroup.objects.get_or_create(name="Cheers / Winedown admin",
                                                           description="Full control over the cheers/winedown listing")
    if created:
        cheers = ContentType.objects.get_for_model(Cheers)
        perm, created = Permission.objects.get_or_create(name="Cheers admin",
                                                         content_type=cheers,
                                                         codename="admin")
        group.permissions.add(perm)
signals.post_syncdb.connect(create_perm_group, sender=wd)

