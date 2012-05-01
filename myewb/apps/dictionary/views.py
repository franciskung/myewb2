from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.defaultfilters import slugify
from django.template import RequestContext

from dictionary.models import Term

def view_wiki_article(request, slug):
    return HttpResponseRedirect(reverse('dictionary_view', kwargs={'slug': slug}))

def article_history(request, slug):
    return HttpResponseRedirect(reverse('dictionary_article_history', kwargs={'slug': slug}))

def new_article(request):
    term = request.POST.get('term', None)
    
    if term:
        return HttpResponseRedirect(reverse('dictionary_edit', kwargs={'slug': slugify(term)}))
        
    else:
        return HttpResponseRedirect(reverse('dictionary_home'))
        
def home(request):
    terms = Term.objects.all().order_by('-last_update')

    return render_to_response("dictionary/home.html", {
        'terms': terms
    }, context_instance=RequestContext(request))

def search(request):
    search = request.GET.get('term', None)
    
    if search:
        terms = Term.objects.filter(title__icontains=search).order_by('title')
        
        if terms.count() == 1:
            return HttpResponseRedirect(reverse('dictionary_view', kwargs={'slug': terms[0].slug}))
    
    """
    if search and not terms and request.user.is_authenticated():
        request.user.message_set.create(message="Didn't find any matches... expand the dictionary and add it!")
        return HttpResponseRedirect(reverse('dictionary_edit', kwargs={'slug': slugify(search)}))
    """
        
    return render_to_response("dictionary/home.html", {
        'terms': terms,
        'search': search
    }, context_instance=RequestContext(request))


