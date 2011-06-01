from django import template
from django.conf import settings
from attachments.forms import AttachmentForm
from attachments.models import Attachment

from threadedcomments.models import ThreadedComment

import settings

register = template.Library()

def attachablecomments(context, obj):
    attach_forms = []       # for now, nothing by default
    return {
        'object': obj, 
        'request': context['request'],
        'user': context['user'],
        'attach_forms': attach_forms,
    }

register.inclusion_tag('threadedcomments/comments.html', takes_context=True)(attachablecomments)

def printablecomments(context, obj):
    return {
        'object': obj, 
        'request': context['request'],
        'user': context['user'],
    }
register.inclusion_tag('threadedcomments/printablecomments.html', takes_context=True)(printablecomments)

# for some reason it doesn't load properly...
@register.simple_tag
def get_STATIC_URL():
    return settings.STATIC_URL

@register.simple_tag
def get_comments_since(since):
    if since == None:
        return ""
    comments = ThreadedComment.objects.filter(date_submitted__gt=since).order_by('date_submitted').count()
    if comments == 0:
        return ""
    else:
        return "&nbsp;&nbsp;(%d new)" % comments

@register.simple_tag
def get_comments_for_topic_since(topic, since):
    if topic == None or since == None:
        return ""
    comments = ThreadedComment.objects.all_for_object(topic).filter(date_submitted__gt=since).count()
    if comments == 0:
        return ""
    else:
        return "&nbsp;&nbsp;(%d new)" % comments

def do_get_latest_comments_for(parser, token):
    """
    Gets the latest comments by date_submitted, for a particular object
    """
    error_message = "%r tag must be of format {%% %r NUM_TO_GET as CONTEXT_VARIABLE for OBJECT %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if len(split) != 6:
        raise template.TemplateSyntaxError, error_message
    if split[2] != 'as':
        raise template.TemplateSyntaxError, error_message
    if split[4] != 'for':
        raise template.TemplateSyntaxError, error_message
    
    return LatestCommentsForNode(split[1], split[3], split[5])

class LatestCommentsForNode(template.Node):
    def __init__(self, num, context_name, obj):
        self.num = num
        self.context_name = context_name
        self.object = template.Variable(obj)
        
    def render(self, context):
        object = self.object.resolve(context)
        comments = ThreadedComment.objects.all_for_object(object).order_by('-date_submitted')[:self.num]
        context[self.context_name] = comments
        return ''
register.tag('get_latest_comments_for', do_get_latest_comments_for)

@register.simple_tag
def replies_page_number(numreplies):
    perpage = getattr(settings, 'PAGINATION_DEFAULT_PAGINATION', 20)
    if numreplies and numreplies > perpage:
        pagenum = numreplies / perpage + 1
        return "?page=%d" % pagenum
        
    return ''
