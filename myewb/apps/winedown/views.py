from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context, loader
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.core.urlresolvers import reverse

from winedown.forms import CheersForm
from winedown.models import Cheers, CheersContainer

def cheers(request, content_id):
    container = get_object_or_404(CheersContainer, id=content_id)
    
    comment = None
    if request.method == 'POST':
        if request.POST.get('comment', None):
            comment = request.POST['comment']
        
        c = Cheers.objects.create_from_container(container, request.user, comment=comment)
        
        if request.is_ajax():
            return HttpResponse(container.count)
        else:
            return HttpResponseRedirect(reverse('winedown_all'))

    else:
        form = CheersForm()

        if request.is_ajax():
            template = "winedown/new-ajax.html"
        else:
            template = "winedown/new.html"
            
        return render_to_response(template,
                                  {"form": form,
                                   "container": container},
                                  context_instance=RequestContext(request)
                                 )
    
    
def all_cheers(request):
    cheers = Cheers.objects.latest()

    return render_to_response('winedown/all.html',
                              {'cheers': cheers},
                              context_instance=RequestContext(request)
                             )
                             
def latest_cheers(request):
    return render_to_response('winedown/latest_cheers.html',
                              {},
                              context_instance=RequestContext(request)
                             )
                             
def cheers_summary(request, content_id=None):
    if content_id:
        pass
    elif not content_id and request.GET.get('id'):
        content_id=request.GET['id']
    else:
        return HttpResponseNotFound('bad ID')
        
    container = get_object_or_404(CheersContainer, id=content_id)
    
    return render_to_response('winedown/summary.html',
                              {'container': container},
                              context_instance=RequestContext(request)
                             )
                             

