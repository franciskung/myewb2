from datetime import timedelta, datetime

from socialmap.models import Relationship

def calculate(r):
    if r.updating == True:
        return

    # TODO: eventually set r.updating flag, etc        
    #r.updating = True
    #r.save()
    
    user1 = r.user1
    user2 = r.user2
    
    r.groups, c_groups = calculate_groups(user1, user2)
    r.events, c_events = calculate_events(user1, user2)
    r.friendships, c_friends = calculate_friendships(user1, user2)
    r.other, c_other = calculate_other(user1, user2)
    
    r.cumulative = c_groups + c_events + c_friends + c_other
    r.score = r.groups + r.events + r.friendships + r.other
    
    r.save()    
    
    # TODO: when I do an updating flag
    #r.updating = False
    #r.last_updated = datetime.now()
    #r.save()
    
def calculate_groups(self, user1, user2):
    return 0

def calculate_events(self, user1, user2):
    return 0

def calculate_friendships(self, user1, user2):
    return 0

def calculate_other(self, user1, user2):
    return 0

