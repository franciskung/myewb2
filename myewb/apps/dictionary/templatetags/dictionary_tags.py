from django import template
from django.core.urlresolvers import reverse
from django.template.defaultfilters import striptags, stringfilter
from django.db.models import Q

register = template.Library()

from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from siteutils import helpers
from dictionary.models import Term, Container, Match
import settings, types, re

from dictionary.models import Term, Match, Container

def dictionary_search(context):
    search = context.get('search', None)
    return {'search': search}
register.inclusion_tag('dictionary/tags/search.html', takes_context=True)(dictionary_search)
    
@register.inclusion_tag('dictionary/tags/latest_long.html')
def dictionary_latest_long():
    terms = Term.objects.all().order_by('-last_update')[0:3]
    return {'terms': terms}
    
@register.inclusion_tag('dictionary/tags/latest_short.html')
def dictionary_latest_short():
    terms = Term.objects.all().order_by('-last_update')[0:10]
    return {'terms': terms}

class DictionaryNode(template.Node):
    def __init__(self, obj, field, context_name, dostriptags=False):
        self.obj = template.Variable(obj)
        self.field = field
        self.context_name = context_name
        self.dostriptags = dostriptags

    def render(self, context):
        try:
            obj = self.obj.resolve(context)
        except template.VariableDoesNotExist:
            print "aha!"
            return u''
        
        result = ""
        try:
            original_text = getattr(obj, self.field)
            if type(original_text) == types.MethodType:
                original_text = original_text()

        """                
        # use this to hackily disable dictionary matching
        except:
            pass 
            
        if self.dostriptags:
            original_text = striptags(original_text)
        context[self.context_name] = original_text
        
        return u''
        """
        
        try:
            container = Container.objects.refresh(obj, self.field)
            
            #matches = Match.objects.filter(container=container).order_by('-position')
            matches = container.match_set.order_by('-position')

            # run through all matches in reverse order, copying chunks of the 
            # original text (with dictionary term linked) to the result, one at a time            
            last_idx = len(original_text)
            for match in matches:
                idx = match.position + 1
                if self.dostriptags:
                    replace = striptags(original_text[idx:last_idx])
                else:
                    replace = original_text[idx:last_idx]
                
                #url = "<a href=\"%s\" class=\"dictionary\">%s</a>" % (reverse('dictionary_view', kwargs={'slug': match.term.slug}), match.term.title)
                #url = "<span href=\"%s\" rel=\"%s\" class=\"dictionary\">%s</span>" % \
                #    (reverse('dictionary_view', kwargs={'slug': match.term.slug}),
                #     reverse('dictionary_ajax', kwargs={'slug': match.term.slug}),
                #     match.term.title)
                url = "<span href=\"%s\" rel=\"%s\" class=\"dictionary\">" % \
                    (reverse('dictionary_view', kwargs={'slug': match.term.slug}),
                     reverse('dictionary_ajax', kwargs={'slug': match.term.slug}))
                
                #result = replace.replace(match.term.title, url, 1) + result
                #result = re.sub(r"(%s)" % match.term.title, r"%s\1</span>" % url, replace, 1, re.I) + result
                expr = re.compile(r"(%s)" % match.term.title, re.I)
                result = expr.sub(r"%s\1</span>" % url, replace, 1) + result
                last_idx = idx
                
            if self.dostriptags:
                result = striptags(original_text[0:last_idx]) + result
            else:
                result = original_text[0:last_idx] + result
        except:
            pass
            
        context[self.context_name] = result
        
        return u''

def dictionary(parser, token):
    """
    Provides the template tag {% dictionary OBJECT FIELD as VARIABLE %}
    Scans the FIELD field of OBJECT (assumed to be a HTML-formatted text field
    and inserts links for dictionary terms, returning the result in VARIABLE
    """
    try:
        _tagname, obj, field, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u'%(tagname)r tag syntax is as follows: '
            '{%% %(tagname)r OBJECT FIELD as VARIABLE %%}' % {'tagname': _tagname})
    return DictionaryNode(obj, field, context_name)

register.tag('dictionary', dictionary)


def dictionary_striptags(parser, token):
    """
    Provides the template tag {% dictionary OBJECT FIELD as VARIABLE %}
    Scans the FIELD field of OBJECT (assumed to be a HTML-formatted text field
    and inserts links for dictionary terms, returning the result in VARIABLE
    """
    try:
        _tagname, obj, field, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u'%(tagname)r tag syntax is as follows: '
            '{%% %(tagname)r OBJECT FIELD as VARIABLE %%}' % {'tagname': _tagname})
    return DictionaryNode(obj, field, context_name, dostriptags=True)

register.tag('dictionary_striptags', dictionary_striptags)

class DictionaryPostNode(template.Node):
    def __init__(self, term, context_name):
        self.term = template.Variable(term)
        self.context_name = context_name

    def render(self, context):
        try:
            term = self.term.resolve(context)
        except template.VariableDoesNotExist:
            return u''
        
        containers = Container.objects.filter(match__term=term)
        q1 = Q(content_text_field='body')
        q2 = Q(content_text_field='comment')
        containers = containers.filter(q1 | q2).distinct().order_by('-refreshed')[0:25]
        context[self.context_name] = containers
        
        return u''

def dictionary_posts(parser, token):
    """
    Provides the template tag {% dictionary_posts TERM as VARIABLE %}
    Finds posts that contain TERM, and populates them in VARIABLE
    """
    try:
        _tagname, term, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u'%(tagname)r tag syntax is as follows: '
            '{%% %(tagname)r TERM as VARIABLE %%}' % {'tagname': _tagname})
    return DictionaryPostNode(term, context_name)

register.tag('dictionary_posts', dictionary_posts)


@register.filter
@stringfilter
def truncate(value):
    if len(value) < 100:
        return value
        
    return value[0:97] + "..."



