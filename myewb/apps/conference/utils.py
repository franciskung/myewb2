from datetime import date

from conference.constants import *
from profiles.models import MemberProfile

def needsToRenew(profile, type=None):
    """
    if profile.user.is_staff:
        return False
    
    if profile.user2.is_bulk:
        return False

    if not type or type != 'nohotel':
        return False
    
    """
    if profile.membership_expiry == None:
        return True
    
    conf_end = date(2014, 01, 12)
    if profile.membership_expiry < conf_end:
        return True
    else:
        return False

def getName(sku):
    return CONF_OPTIONS[sku]['name']

def getCost(sku):
    return CONF_OPTIONS[sku]['cost']
