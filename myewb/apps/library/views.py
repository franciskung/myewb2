from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.defaultfilters import slugify
from django.template import RequestContext

from library.models import Collection

def home(request):
    collections = Collection.objects.all().order_by('-modified')

    return render_to_response("library/home.html", {
        'collections': collections
    }, context_instance=RequestContext(request))

def search(request):
    keyword = request.GET.get('keyword', None)
    rating = request.GET.get('rating', None)
    topic = request.GET.get('topic', None)
    resource_type = request.GET.get('type', None)
    
    results = []
    
    return render_to_response("library/search.html", {
        'results': results
    }, context_instance=RequestContext(request))

    
