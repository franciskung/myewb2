from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader

from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.core.cache import cache

from whosonline.middleware import get_cache_key_for_session, get_cache_history_key, CACHE_ONLINE_USERS_KEY

@permission_required('profiles')
def whosonline(request, username=None):
    user = None
    history = None
    registered_users = {}
    
    if username:
        user = User.objects.get(username=username)
        history = cache.get(get_cache_history_key(user.id))
        
        if not history:
            request.user.message_set.create(message='User not found - perhaps they have logged off...')
            

    if not history:
        # Iterating users.
        try:
            users = cache.get(CACHE_ONLINE_USERS_KEY, {})
        except:
            users = {}
        for sessid, user in users.iteritems():
            cached_user = cache.get(get_cache_key_for_session(sessid), False)
            if cached_user:
                if isinstance(cached_user, User):
                    registered_users[cached_user] = len(cache.get(get_cache_history_key(cached_user.id), []))
    else:
        history.reverse()

    return render_to_response("whosonline/whosonline.html",
                              {'registered_users': registered_users.iteritems(),
                               'history': history,
                               'target_user': user},
                              context_instance=RequestContext(request))

