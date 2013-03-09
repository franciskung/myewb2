from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save, pre_delete
from emailconfirmation.signals import email_confirmed

from account_extra.signals import listsignup, deletion
from base_groups.models import BaseGroup, GroupMember
from mailchimp.models import ListEvent, GroupEvent, ProfileEvent
from profiles.models import MemberProfile

from rolodex.models import TrackingProfile, ProfileBadge, ProfileHistory

from siteutils.shortcuts import get_object_or_none

import settings, pickle

def group_join(sender, instance, created, **kwargs):
    user = instance.user
    group = instance.group
    
    profile = get_object_or_none(TrackingProfile, user=user)
    
    if not profile:
        return

    # messy hack.  but what the heck, it'll work...
    badge = None
    if group.slug == 'exec':
        badge = Badge.objects.get(name='Exec')
    elif group.slug == 'presidents' or group.slug == 'citynetworkpres':
        badge = Badge.objects.get(name='President')
        
    if badge:
        pb = get_object_or_none(ProfileBadge, profile=profile, badge=badge, active=True)
        
        if not pb:
            ProfileBadge.objects.create(profile=profile,
                                        badge=badge,
                                        added_by=user,
                                        note='Automatic addition - sync from myEWB')
            
    # basically... "if they're a chapter exec, update their title"
    if instance.is_admin and hasattr(group, 'network'):
        if profile.chapter != group.network or profile.role != instance.admin_title:
            profile_pickle = pickle.dumps(profile.to_dict())
            profile.chapter = group.network
            profile.role = instance.admin_title
            profile.save()
            history = ProfileHistory.objects.create(profile=profile,
                                                    editor=user,
                                                    revision=profile_pickle)



def group_leave(sender, instance, **kwargs):
    if created:
        user = instance.user
        group = instance.group
        
        profile = get_object_or_none(TrackingProfile, user=user)
        
        if not profile:
            return

        # messy hack.  but what the heck, it'll work...
        badge = None
        if group.slug == 'exec':
            badge = Badge.objects.get(name='Exec')
        elif group.slug == 'presidents' or group.slug == 'citynetworkpres':
            badge = Badge.objects.get(name='President')
            
        if badge:
            pb = get_object_or_none(ProfileBadge, profile=profile, badge=badge, active=True)
            
            if pb:
                pb.active = False
                pb.removed_date = datetime.now()
                pb.note = "%s%s" % (pb.note, "\n\nAutomatic removal - sync from myEWB")
                pb.save()


def user_update(sender, instance, created=None, **kwargs):
    user = instance
    
    profile = get_object_or_none(TrackingProfile, user=user)
    
    if not profile:
        return
    
    modified = False
    profile_pickle = pickle.dumps(profile.to_dict())
    
    if profile.primary_email() != user.email:
        profile.update_email(user.email)
        modified = True
        
    if profile.first_name != user.first_name:
        profile.first_name = user.first_name
        modified = True
        
    if profile.last_name != user.last_name:
        profile.last_name = user.last_name
        modified = True
        
    if modified:
        profile.save()
        history = ProfileHistory.objects.create(profile=profile,
                                                editor=user,
                                                revision=profile_pickle)
    
def profile_update(sender, instance, **kwargs):
    return user_update(sender, instance.user2, kwargs)

# only connect listeners if mailchimp is enabled
post_save.connect(group_join, sender=GroupMember, dispatch_uid='rolodex-group-join')
pre_delete.connect(group_leave, sender=GroupMember, dispatch_uid='rolodex-group-leave')

post_save.connect(user_update, sender=User, dispatch_uid='rolodex-user-postupdate')
post_save.connect(profile_update, sender=MemberProfile, dispatch_uid='rolodex-profile-update')

