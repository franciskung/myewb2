from django.contrib.auth.decorators import permission_required, login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template.defaultfilters import slugify
from django.template import RequestContext

from library.forms import ResourceForm, FileResourceForm, LinkResourceForm, CollectionForm
from library.models import Resource, FileResource, LinkResource, Activity, Collection, Membership

def home(request):
    browse = Collection.objects.filter(featured=True, parent__isnull=True).order_by('ordering', '-modified')

    if request.user.is_authenticated():
        collections = Collection.objects.filter(owner=request.user, parent__isnull=True).order_by('-modified', 'name')
    else:
        collections = []
        
    latest = Resource.objects.all().order_by('-modified')[0:10]
    popular = Resource.objects.all().order_by('-downloads')[0:10]

    return render_to_response("library/home.html", {
        'browse': browse,
        'collections': collections,
        'resource_types': Resource.RESOURCE_TYPES,
        'latest': latest,
        'popular': popular
    }, context_instance=RequestContext(request))

def library_sort(resources, sorting):
    if sorting and sorting[0:7] == 'sort_by':
        sorting = sorting[8:]
        if sorting == 'featured':
            resources = resources.order_by('members__ordering')
        elif sorting == 'rating':
            resources = resources.order_by('-rating', '-downloads', '-modified')
        elif sorting == 'modified':
            resources = resources.order_by('-modified')
        elif sorting == 'downloads':
            resources = resources.order_by('-downloads', '-rating', '-modified')
        else:
            resources = resources.order_by(sorting)
    return resources


def search(request):
    keyword = request.GET.get('keyword', None)
    rating = request.GET.get('rating', None)
    resource_type = request.GET.get('type', None)
    language = request.GET.get('language', None)
    sort = request.GET.get('sort', None)
    
    results = Resource.objects.all()
    collections = []
    if keyword:
        collections = Collection.objects.all()
        for word in keyword.split():
            results = results.filter(Q(name__icontains=word) | Q(description__icontains=word))
            collections = collections.filter(Q(name__icontains=word) | Q(description__icontains=word))
    if rating:
        results = results.filter(rating__gte=rating)
    if resource_type:
        results = results.filter(resource_type=resource_type)
    if language:
        results = results.filter(language=language)

    results = library_sort(results, sort)
    
    
    
    return render_to_response("library/search.html", {
        'collections': collections,
        'results': results,
        'keyword': keyword,
        'rating': rating,
        'resource_type': resource_type,
        'language': language,
        'sort': sort,
        'resource_types': Resource.RESOURCE_TYPES,
    }, context_instance=RequestContext(request))

    
def resource(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    activity = Activity.objects.filter(resource=resource)[0:10]
    
    return render_to_response("library/resource.html", {
        'resource': resource,
        'activity': activity,
        'rating': resource.get_rating(request.user)
    }, context_instance=RequestContext(request))
    
def download(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    return HttpResponseRedirect(resource.download(request.user))

@login_required
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

        collection.add_resource(resource, user=request.user)
        
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

@login_required
def rate(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    rating = request.POST.get('rating', None)
    
    if rating:
        resource.add_rating(request.user, rating)
    
    return HttpResponse(resource.rating)

@login_required
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
        if request.user.has_module_perms('library'):
            collections = Collection.objects.filter(Q(owner=request.user) | Q(curators=request.user) | Q(featured=True))
        else:
            collections = Collection.objects.filter(Q(owner=request.user) | Q(curators=request.user))
        collections = collections.filter(parent__isnull=True)
    
    
    output = "<ul class='jqueryFileTree' style='display: none;'>\n"
    for c in collections:
        output = "%s<li class='directory collapsed'><a href='#' rel='/%d/'>%s</a></li>\n" % (output, c.id, c.name)
    output = output + "</ul>\n"
    
    return HttpResponse(output)

@login_required
def upload(request, link=False, collection_id=None):

    collection = None
    if collection_id:
        collection = Collection.objects.get(id=collection_id)
        
    if request.method == 'POST':
        if link:
            form = LinkResourceForm(request.POST)
        else:
            form = FileResourceForm(request.POST, request.FILES)
        
        if form.is_valid():
            resource = form.save()
            
            if not link:
                resource.upload(request.FILES['resource'])
                
            resource.creator = request.user
            resource.save()
            
            duplicate = None
            if link:
                duplicate = LinkResource.objects.filter(url=resource.url).exclude(id=resource.id)
            else:
                duplicate = FileResource.objects.filter(checksum=resource.checksum).exclude(id=resource.id)
                
            if duplicate:
                msg = "This resource already exists in the library!<br/><a href='%s'>Click here to view the resource</a>" % reverse('library_resource', kwargs={'resource_id': duplicate[0].id})
                request.user.message_set.create(message=msg)
                
            else:
                if collection and collection.user_can_edit(request.user):
                    collection.add_resource(resource, request.user)
                                                    
                # redirect to file info display
                return HttpResponseRedirect(reverse('library_resource', kwargs={'resource_id': resource.id}))
    
    else:
        if link:
            form = LinkResourceForm()
        else:
            form = FileResourceForm()
    
    return render_to_response("library/upload.html", 
        {'form': form,
         'is_link': link,
         'collection': collection},
        context_instance=RequestContext(request))

@login_required
def resource_edit(request, resource_id):
    resource = Resource.objects.get(id=resource_id)
    
    if resource.model == 'linkresource':
        form_class = LinkResourceForm
        resource = resource.linkresource
    else:
        form_class = ResourceForm
    
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=resource)
        
        if form.is_valid():
            form.save()
            
            Activity.objects.create(resource=resource,
                                    user=request.user,
                                    activity_type='edit')
            
            request.user.message_set.create(message='Resource updated!')
            return HttpResponseRedirect(reverse('library_resource', kwargs={'resource_id': resource.id}))
        
    else:
        form = form_class(instance=resource)
        
    return render_to_response("library/upload.html", 
        {'form': form,
         'editing': True,
         'resource': resource},
        context_instance=RequestContext(request))

def resource_google(request, resource_id):
    pass
    
def resource_replace(request, resource_id): 
    pass
    
def resource_delete(request, resource_id):
    pass

@login_required
def mine(request, sort=None):
    resources = Resource.objects.filter(creator=request.user)    
#    edited = Activity.objects.select_related('activity').filter(user=request.user, activity_type='edit')
    edited = []
    
    if sort:
        resources = library_sort(resources, "sort_by_%s" % sort)

    return render_to_response("library/mine.html", 
        {'resources': resources,
         'edited': edited,
         'sort': sort},
        context_instance=RequestContext(request))

def collection(request, collection_id, slug=None):
    collection = Collection.objects.get(id=collection_id)
    
    return render_to_response("library/collection.html", 
        {'collection': collection,
         'can_edit': collection.user_can_edit(request.user),
         'resource_types': Resource.RESOURCE_TYPES,
        },
        context_instance=RequestContext(request))
        
def collection_sorted(request, collection_id):
    collection = Collection.objects.get(id=collection_id)
    
    resources = Resource.objects.filter(members__collection=collection_id)
    
    if request.GET.get('type', None):
        resources = resources.filter(resource_type=request.GET['type'])
    if request.GET.get('language', None):
        resources = resources.filter(language=request.GET['language'])
    if request.GET.get('scope', None):
        resources = resources.filter(scope='ewb')
    if request.GET.get('sort_by', None):
        resources = library_sort(resources, request.GET['sort_by'])
    
    return render_to_response("library/ajax/collection_sorted.html", 
        {'collection': collection,
         'resources': resources},
        context_instance=RequestContext(request))
        
@login_required
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
                                                kwargs={'collection_id': collection_id,
                                                        'slug': collection.slug()}
                                               ))
    else:
        form = CollectionForm(instance=collection)
        
    return render_to_response("library/collection_edit.html", 
        {'collection': collection,
         'form': form},
        context_instance=RequestContext(request))

@login_required
def collection_create(request, parent_id=None):
    parent = None
    if parent_id:
        parent = Collection.objects.get(id=parent_id)
        if not parent.user_can_edit(request.user):
            return render_to_response('denied.html', context_instance=RequestContext(request))

    if request.method == 'POST':
        form = CollectionForm(request.POST)
        
        if form.is_valid():
            collection = form.save(commit=False)
            collection.owner = request.user
            
            if parent:
                collection.parent = parent
                
                order = 0
                children = parent.get_children()
                for c in children:
                    if c.ordering > order:
                        order = c.ordering
                order = order + 1
                collection.ordering = order
            
            collection.save()
        
            request.user.message_set.create(message='Collection created!')
            return HttpResponseRedirect(reverse('library_collection',
                                        kwargs={'collection_id': collection.id,
                                                'slug': collection.slug()}
                                       ))

    else:
        form = CollectionForm()
        
    return render_to_response("library/collection_edit.html", 
        {'form': form,
         'create': True,
         'parent': parent},
        context_instance=RequestContext(request))

@login_required
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

@login_required
def collection_reorder_files(request, collection_id):
    if request.method == 'POST' and request.POST.get('file_id', None) and request.POST.get('new_order', None):
        file_id = request.POST.get('file_id', None)
        collection = get_object_or_404(Collection, id=collection_id)
        
        # TODO perms check here
        
        m = Membership.objects.get(collection=collection, resource__id=file_id)
        current_order = m.ordering
        new_order = request.POST.get('new_order', None)
        
        if current_order != new_order:
            later_files = Membership.objects.filter(collection=collection,
                                                    ordering__gt=current_order)
            for q in later_files:
                q.ordering = q.ordering - 1
                q.save()
                
            later_files = Membership.objects.filter(collection=collection,
                                                    ordering__gte=new_order)
            for q in later_files:
                q.ordering = q.ordering + 1
                q.save()
                
            m.ordering = new_order
            m.save()
            
        return HttpResponse("success")

    return HttpResponse("invalid")


