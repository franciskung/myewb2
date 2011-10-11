from django.template import Library
from django.conf import settings

from winedown.models import Cheers

register = Library()

@register.inclusion_tag("winedown/cheers_for_content.html", takes_context=True)
def show_cheers_for_content(context, content, num=10):
    """
    Show all cheers attached to an object.
    """
    
    cheers = Cheers.objects.get_for_object(content).order-by('-date')
    
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
        "request": context['request']
    }

@register.inclusion_tag("winedown/widget.html", takes_context=True)
def show_cheers_widget(context, content):
    """
    Shows a small widget that counts the cheers and offers a link to cheers more
    """
    
    cheers = Cheers.objects.get_for_object(content).count()

    if context['request'].user.is_authenticated():
        mycheers = Cheers.objects.get_for_object(content).filter(owner=context['request'].user)
    if not context['request'].user.is_authenticated() or mycheers.count():
        link = None
    else:
        link = Cheers.objects.create_link(content)
    
    return {
        "cheers": cheers,
        "link": link,
        "STATIC_URL": settings.STATIC_URL,
        "request": context['request']
    }


