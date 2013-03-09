from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save, pre_delete
from emailconfirmation.signals import email_confirmed

from account_extra.signals import listsignup, deletion
from base_groups.models import BaseGroup, GroupMember
from profiles.models import MemberProfile
from emailconfirmation.models import EmailAddress as MyewbEmail
from siteutils.models import Address as MyewbAddress, PhoneNumber as MyewbPhone

from rolodex.models import TrackingProfile, ProfileBadge, ProfileHistory, Address, Email

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
    
def address_update(sender, instance, **kwargs):
    # quick hack to see if the address (instance.content_object) is connected to a MemberProfile
    if hasattr(instance.content_object, 'user2'):
        memberprofile = instance.content_object
        user = memberprofile.user2
        
        profile = get_object_or_none(TrackingProfile, user=user)
    
        if not profile:
            return
    
        profile_pickle = pickle.dumps(profile.to_dict())

        # this address is already in the rolodex; just update it
        address = get_object_or_none(Address, myewbaddress=instance)
        if address:
            address.address = "%s\n%s %s\n%s\n%s" % (instance.street, instance.city, instance.province, instance.postal_code, instance.country)
            address.save()

        # add new address to rolodex
        else:
            address = Address.objects.create(address = "%s\n%s %s\n%s\n%s" % (instance.street, instance.city, instance.province, instance.postal_code, instance.country),
                                             profile = profile,
                                             myewbaddress=instance)
        
        history = ProfileHistory.objects.create(profile=profile,
                                                editor=user,
                                                revision=profile_pickle)
    

def email_update(sender, instance, **kwargs):
    if not instance.verified:
        return

    user = instance.user
    profile = get_object_or_none(TrackingProfile, user=user)
    
    if not profile:
        return
    
    profile_pickle = pickle.dumps(profile.to_dict())

    # this address is already in the rolodex; just update it
    email = get_object_or_none(Email, myewbemail=instance)
    if email:
        email.email = instance.email
        email.save()

    # add new address to rolodex
    else:
        email = Email.objects.create(email=instance.email,
                                     profile = profile,
                                     myewbemail=instance)
                                     
    if instance.primary:
        profile.update_email(instance.email)
    
    history = ProfileHistory.objects.create(profile=profile,
                                            editor=user,
                                            revision=profile_pickle)

# only connect listeners if mailchimp is enabled
post_save.connect(group_join, sender=GroupMember, dispatch_uid='rolodex-group-join')
pre_delete.connect(group_leave, sender=GroupMember, dispatch_uid='rolodex-group-leave')

post_save.connect(user_update, sender=User, dispatch_uid='rolodex-user-postupdate')
post_save.connect(profile_update, sender=MemberProfile, dispatch_uid='rolodex-profile-update')
post_save.connect(address_update, sender=MyewbAddress, dispatch_uid='rolodex-address-update')
post_save.connect(email_update, sender=MyewbEmail, dispatch_uid='rolodex-email-update')

