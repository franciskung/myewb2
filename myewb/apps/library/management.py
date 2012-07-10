"""myEWB library management

This file is part of myEWB
Copyright 2012 Engineers Without Borders Canada

@author Francis Kung
"""

from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from permissions.models import PermissionGroup
from library.models import Collection
from library import models as lm

def create_perm_group(sender, **kwargs):
    group, created = PermissionGroup.objects.get_or_create(name="Library admin",
                                                           description="Full control over resource library")
    if created:
        collection = ContentType.objects.get_for_model(Collection)
        perm, created = Permission.objects.get_or_create(name="Library admin",
                                                         content_type=collection,
                                                         codename="admin")
        group.permissions.add(perm)
signals.post_syncdb.connect(create_perm_group, sender=lm)
