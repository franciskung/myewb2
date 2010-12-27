from datetime import timedelta, datetime

from base_groups.models import GroupMemberRecord
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
    
def calculate_groups(user1, user2):
    score = 0
    cumulative = 0
    
    # find all common current groups    
    user1_groups = user1.get_groups()
    for g in user2.get_groups():
        if g in user1_groups:
            score = score + 25
            cumulative = cumulative + 25
            
    # TODO: decay for inactive groups
    
    # find all common past groups
    # TODO: refactor to GroupMemberRecrod, to make easier to manage...
    gmr = GroupMemberRecord.objects.filter(user=user1)
    user1_past_groups = []
    open_groups = {}
    for r in gmr:
        if r.membership_start:
            open_groups[r.group] = r.datetime
        elif r.membership_end:
            if r.group in open_groups:
                starttime = open_groups[r.group]
                user1_past_groups.append((r.group, starttime, r.datetime))
                del(open_groups[r.group])
    for g in open_groups:
        user1_past_groups.append((g, open_groups[g], datetime.now()))

    gmr = GroupMemberRecord.objects.filter(user=user2)
    user2_past_groups = []
    open_groups = {}
    for r in gmr:
        if r.membership_start:
            open_groups[r.group] = r.datetime
        elif r.membership_end:
            if r.group in open_groups:
                starttime = open_groups[r.group]
                user2_past_groups.append((r.group, starttime, r.datetime))
                del(open_groups[r.group])
    for g in open_groups:
        user2_past_groups.append((g, open_groups[g], datetime.now()))

    for group, start, end in user1_past_groups:
        for group2, start2, end2 in user2_past_groups:
            if group == group2 and start < end2 and end > start2:
                # TODO: change this based on how long ago it was...
                score = score + 10
                cumulative = cumulative + 25
                break
                
    # TODO: boost active and flagged groups
    
    # TODO: adjust basd on grou psize
    
    if user1.get_profile().get_chapter() == user2.get_profile().get_chapter():
        score = score + 50
        cumulative = cumulative + 50
                    
    return (score, cumulative)

def calculate_events(user1, user2):
    return 0

def calculate_friendships(user1, user2):
    return 0

def calculate_other(user1, user2):
    return 0

