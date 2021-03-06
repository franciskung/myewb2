"""myEWB conference template tags

This file is part of myEWB
Copyright 2010 Engineers Without Borders Canada

@author Francis Kung
"""

from datetime import date, time
from django import template
from conference.constants import *

register = template.Library()

@register.filter
def date_fr(thedate):
    return thedate.strftime('%A le %d %B')
    
@register.filter
def time_fr(thetime):
    return thetime.strftime('%H:%M')
    

@register.simple_tag
def lookup_cost(code, room):
    key = "confreg-2013-" + room + "-" + code
    listing = CONF_OPTIONS.get(key, None)
    
    if listing:
        return "$%d<br/><span style='font-size: 0.75em;'>%s</span>" % (listing['cost'], listing['name'])
    else:
        return ""

@register.simple_tag
def rowspan(length):
    return length / 15

@register.simple_tag
def height(length):
    #return "%fem" % (length / 30 * 1.5)
    return "0.5em"

@register.simple_tag
def colspans(capacity):
    """
    if capacity > 500:
        return "25"
    elif capacity > 250:
        return "4"
    elif capacity > 110:
        return "2"
    else:
        return "1"
    """
    return "1"

@register.simple_tag
def abs_top(hour, minute):
    return ((hour - 8) * 80) + (minute * 80 / 60) + 30
    
@register.simple_tag
def abs_left(day):
    if day == 'thurs':
        return 75
    elif day == 'fri':
        return 245
    elif day == 'sat':
        return 415
    else:
        return 0
    
@register.simple_tag
def abs_height(length):
    return length * 80 / 60 - 10
    
class AttendanceNode(template.Node):
    def __init__(self, session, user, context_attending, context_tentative):
        self.session = template.Variable(session)
        self.user = template.Variable(user)
        self.context_attending = context_attending
        self.context_tentative = context_tentative

    def render(self, context):
        try:
            session = self.session.resolve(context)
            user = self.user.resolve(context)
        except template.VariableDoesNotExist:
            return u''
        
        context[self.context_attending] = session.user_is_attending(user)
        context[self.context_tentative] = session.user_is_tentative(user)
        return u''

def do_attendance(parser, token):
    """
    Provides the template tag {% attendance SESSION USER as ATTENDING TENTATIVE %}
    """
    try:
        _tagname, session, user, _as, context_attending, context_tentative = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u'%(tagname)r tag syntax is as follows: '
            '{%% %(tagname)r SESSION USER as VARIABLE1 VARIABLE2 %%}' % {'tagname': _tagname})
    return AttendanceNode(session, user, context_attending, context_tentative)

register.tag('attendance', do_attendance)
