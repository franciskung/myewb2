from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context, loader
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse

from winedown.models import Cheers, CheersContainer

def cheers(request, content_id):
    container = get_object_or_404(CheersContainer, id=content_id)
    
    comment = None
    if request.method == 'POST' and request.POST.get('comment', None):
        comment = request.POST['comment']
        
    c = Cheers.objects.create_from_container(container, request.user, comment=comment)
    
    if request.is_ajax():
        return HttpResponse(container.count)
    else:
        return HttpResponseRedirect(reverse('winedown_all'))
    
    
def all_cheers(request):
    cheers = Cheers.objects.latest()

    return render_to_response('winedown/all.html',
                              {'cheers': cheers},
                              context_instance=RequestContext(request)
                             )
