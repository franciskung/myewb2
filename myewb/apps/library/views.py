from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.defaultfilters import slugify
from django.template import RequestContext

from library.forms import FileResourceForm
from library.models import Resource, FileResource, Activity, Collection

def home(request):
    collections = Collection.objects.filter(featured=True, parent__isnull=True).order_by('ordering', '-modified')
    
    allresources = Resource.objects.all()

    return render_to_response("library/home.html", {
        'collections': collections,
        'resources': allresources
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

    
def resource(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    activity = Activity.objects.filter(resource=resource)
    
    return render_to_response("library/resource.html", {
        'resource': resource,
        'activity': activity,
    }, context_instance=RequestContext(request))
    
def download(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    return HttpResponseRedirect(resource.download(request.user))
    

def upload(request):
    if request.method == 'POST':
        form = FileResourceForm(request.POST, request.FILES)
        
        if form.is_valid():
            # save file
            resource = FileResource.objects.upload(request.FILES['resource'])
                                                   
            resource.creator = request.user
            resource.name = form.cleaned_data['name']
            resource.description = form.cleaned_data['description']
            resource.resource_type = form.cleaned_data['resource_type']
            resource.scope = form.cleaned_data['scope']
            resource.save()
                                                
            # redirect to file info display
            return HttpResponseRedirect(reverse('library_resource', kwargs={'resource_id': resource.id}))
    
    else:
        form = FileResourceForm()
    
    return render_to_response("library/upload.html", 
        {'form': form},
        context_instance=RequestContext(request))

def collection(request, collection_id):
    collection = Collection.objects.get(id=collection_id)
    
    return render_to_response("library/collection.html", 
        {'collection': collection},
        context_instance=RequestContext(request))

    
