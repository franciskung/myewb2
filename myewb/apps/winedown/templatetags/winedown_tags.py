from django import template
from django.template import Library
from django.conf import settings

from winedown.models import Cheers

register = Library()

@register.inclusion_tag("winedown/cheers_for_content.html", takes_context=True)
def show_cheers_for_content(context, content, num=None):
    """
    Show all cheers attached to an object.
    """
    
    cheers = Cheers.objects.get_for_object(content).order_by('-date')
    
    if num:
        cheers = cheers[0:num]
    
    return {
        "cheers": cheers,
        "num": num,
        "STATIC_URL": settings.STATIC_URL,
        "request": context['request']
    }

@register.inclusion_tag("winedown/latest.html", takes_context=True)
def show_latest_cheers(context, num=10):
    """
    Show latest cheers
    """
    
    cheers = Cheers.objects.latest()
    
    if num:
        cheers = cheers[0:num]
    
    return {
        "cheers": cheers,
        "num": num,
        "STATIC_URL": settings.STATIC_URL,
        "request": context['request'],
        "perms": context['perms']
    }

@register.inclusion_tag("winedown/widget.html", takes_context=True)
def show_cheers_widget(context, content):
    """
    Shows a small widget that counts the cheers and offers a link to cheers more
    """
    
    container = Cheers.objects.get_container(content)
    cheers = Cheers.objects.get_for_object(content).count()

    if context['request'].user.is_authenticated():
        mycheers = Cheers.objects.get_for_object(content).filter(owner=context['request'].user)
    if not context['request'].user.is_authenticated() or mycheers.count():
        link = None
    else:
        link = Cheers.objects.create_link(content)
    
    return {
        "cheers": cheers,
        "container": container,
        "link": link,
        "STATIC_URL": settings.STATIC_URL,
        "request": context['request']
    }


def do_get_cheers_link(parser, token):
    """
    Gets the link to cheers this item
    """
    error_message = "%r tag must be of format {%% %r CHEERS_CONTAINER USER as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if len(split) != 5:
        raise template.TemplateSyntaxError, error_message
    if split[3] != 'as':
        raise template.TemplateSyntaxError, error_message
    
    return CheersLinkNode(split[1], split[2], split[4])

class CheersLinkNode(template.Node):
    def __init__(self, container, user, context_name):
        self.container = template.Variable(container)
        self.user = template.Variable(user)
        self.context_name = context_name
        
    def render(self, context):
        container = self.container.resolve(context)
        user = self.user.resolve(context)
        obj  = container.content_object
        
        link = None
        if user.is_authenticated():
            mycheers = Cheers.objects.get_for_object(obj).filter(owner=user)
            if mycheers.count() == 0:
                link = Cheers.objects.create_link(obj)
        
        context[self.context_name] = link
        return ''
register.tag('get_cheers_link', do_get_cheers_link)


