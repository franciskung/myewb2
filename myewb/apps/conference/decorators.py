from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

class conference_login_required(object):
    """
    Checks to see whether the user is an admin. 
    Requires that group_slug is first non-request argument. Used with BaseGroup.
    """
    def __call__(self, f):
        def newf(request, *args, **kwargs):            
            if not request.user.is_authenticated():
                return HttpResponseRedirect(reverse('conference_login'))
            else:            
                return f(request, *args, **kwargs)
                
        return newf

