from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template.defaultfilters import slugify
from django.template import RequestContext

from library.forms import FileResourceForm, CollectionForm
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
    
def organize(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    
    if request.method == 'POST':
        collection_id = request.POST['collection_id']
        if collection_id[0:1] == '/':
            collection_id = collection_id[1:]
        if collection_id[-1:] == '/':
            collection_id = collection_id[:-1]
            
        collection = Collection.objects.get(id=collection_id)
        
        if not collection.user_can_edit(request.user):
            return render_to_response('denied.html', context_instance=RequestContext(request))

        collection.resources.add(resource)
        
        if request.is_ajax():
            return HttpResponse('success')
        else:
            request.user.message_set.create(message="Added to <em>%s</em>" % collection.name)
            return HttpResponseRedirect(reverse('library_resource',
                                                kwargs={'resource_id': resource_id}))

    collections = Collection.objects.filter(Q(owner=request.user) | Q(curators=request.user))
                                                
    if request.is_ajax():
        return render_to_response("library/ajax/organize.html", {
            'resource': resource,
            'collections': collections
        }, context_instance=RequestContext(request))
    else:    
        return render_to_response("library/organize.html", {
            'resource': resource,
            'collections': collections,
        }, context_instance=RequestContext(request))
    
def browse(request):
    collection_id = request.POST.get('dir', None)
    
    collection = None
    if collection_id:
        if collection_id[0:1] == '/':
            collection_id = collection_id[1:]
        if collection_id[-1:] == '/':
            collection_id = collection_id[:-1]
            
        collection = Collection.objects.get(id=collection_id)
        if not collection.user_can_edit(request.user):
            collection_id = None
            collection = None
            
    if collection_id and collection:
        collections = Collection.objects.filter(parent=collection)

    else:
        collections = Collection.objects.filter(Q(owner=request.user) | Q(curators=request.user))
        collections = collections.filter(parent__isnull=True)
    
    
    output = "<ul class='jqueryFileTree' style='display: none;'>\n"
    for c in collections:
        output = "%s<li class='directory collapsed'><a href='#' rel='/%d/'>%s</a></li>\n" % (output, c.id, c.name)
    output = output + "</ul>\n"
    
    return HttpResponse(output)
    
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
        
def mine(request):
    resources = Resource.objects.filter(creator=request.user)    
    edited = Activity.objects.select_related('activity').filter(user=request.user, activity_type='edit')

    return render_to_response("library/mine.html", 
        {'resources': resources,
         'edited': edited},
        context_instance=RequestContext(request))

def collection(request, collection_id):
    collection = Collection.objects.get(id=collection_id)
    
    return render_to_response("library/collection.html", 
        {'collection': collection,
         'can_edit': collection.user_can_edit(request.user)},
        context_instance=RequestContext(request))

def collection_edit(request, collection_id):
    collection = Collection.objects.get(id=collection_id)

    # permissions check
    if not collection.user_can_edit(request.user):
        return render_to_response('denied.html', context_instance=RequestContext(request))
        
    # standard form handling
    if request.method == 'POST':
        form = CollectionForm(request.POST, instance=collection)
        
        if form.is_valid():
            form.save()
            
            request.user.message_set.create(message='Collection updated')
            
            return HttpResponseRedirect(reverse('library_collection',
                                                kwargs={'collection_id': collection_id}
                                               ))
    else:
        form = CollectionForm(instance=collection)
        
    return render_to_response("library/collection_edit.html", 
        {'collection': collection,
         'form': form},
        context_instance=RequestContext(request))

def collection_reorder(request, collection_id):
    if request.method == 'POST' and request.POST.get('collection_id', None) and request.POST.get('new_order', None):
        collection_id = request.POST.get('collection_id', None)
        collection = get_object_or_404(Collection, id=collection_id)
        current_order = collection.ordering
        new_order = request.POST.get('new_order', None)
        
        if current_order != new_order:
            later_collections = Collection.objects.filter(parent=collection.parent,
                                                          ordering__gt=current_order)
            for q in later_collections:
                q.ordering = q.ordering - 1
                q.save()
                
            later_collections = Collection.objects.filter(parent=collection.parent,
                                                          ordering__gte=new_order)
            for q in later_collections:
                q.ordering = q.ordering + 1
                q.save()
                
            collection.ordering = new_order
            collection.save()
            
        return HttpResponse("success")
            
    return HttpResponse("invalid")


