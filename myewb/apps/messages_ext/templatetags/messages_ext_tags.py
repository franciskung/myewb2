from django import template
from django.conf import settings

from messages.models import Message

import settings

register = template.Library()

def messages_inbox(obj):

    messages = Message.objects.inbox_for(obj)
    
    return {
        'messages': messages,
        'user': obj
    }
register.inclusion_tag('messages/widget_inbox.html', takes_context=False)(messages_inbox)


