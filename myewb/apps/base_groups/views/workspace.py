"""myEWB group workspaces

This file is part of myEWB
Copyright 2010 Engineers Without Borders Canada

Last modified on 2010-08-18
@author Francis Kung
"""

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from base_groups.models import BaseGroup
from base_groups.helpers import group_search_filter, get_counts, get_recent_counts, enforce_visibility 
from base_groups.decorators import group_admin_required, visibility_required

import settings, os

@group_admin_required()
def browse(request, group_slug):
    """
    Browse a group's workspace
    """
    group = get_object_or_404(BaseGroup, slug=group_slug)
    
    response = []
    if request.method == 'POST':
        # create folder for the group's workspace if needed
        dir = os.path.join(settings.MEDIA_ROOT, 'workspace', 'groups', group_slug)
        if not os.path.isdir(dir):
            os.mkdir(dir, 0755)
        
        # find the requested directory, performing some security checks
        requestdir = request.POST.get('dir', '/')
        if requestdir.find('.') > -1:       # do not allow any periods
            return HttpResponse('')

        # build directory listing
        dir = dir + requestdir
        if os.path.isdir(dir):
            response = ['<ul class="jqueryFileTree" style="display: none;">']
            
            # take all files/subdirectories and build lists
            files = []
            dirs = []
            for f in os.listdir(dir):
                if os.path.isdir(os.path.join(dir, f)):
                    dirs.append(f)
                else:
                    files.append(f)
                    
            # sort lists
            dirs.sort()
            files.sort()
                
            # output directories...
            for f in dirs:
                full_file = os.path.join(requestdir, f)
                response.append('<li class="directory collapsed"><a href="#" rel="%s/">%s</a></li>' % (full_file, f))
                
            # output files
            for f in files:
                full_file = os.path.join(requestdir, f)
                fname, ext = os.path.splitext(f)
                ext = ext[1:]
                response.append('<li class="file ext_%s"><a href="#" rel="%s/">%s</a></li>' % (ext, full_file, f))
    
            response.append('</ul>')
        
    # return listing
    return HttpResponse(''.join(response))
