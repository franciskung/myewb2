"""myEWB winedown URLs

This file is part of myEWB
Copyright 2011 Engineers Without Borders Canada

@author Francis Kung
"""

from django.conf.urls.defaults import *

urlpatterns = patterns('winedown.views',
    url(r'(?P<content_id>[\d]+)/cheers/$', 'cheers', name='winedown_cheers'),
    url(r'all/$', 'all_cheers', name='winedown_all'),
    url(r'latest/$', 'latest_cheers', name='winedown_latest'),
    url(r'(?P<content_id>[\d]+)/summary/$', 'cheers_summary', name='winedown_summary'),
    url(r'(?P<content_id>[\d]+)/remove/$', 'cheers_remove', name='winedown_remove'),
    url(r'summary/$', 'cheers_summary', name='winedown_summary'),
) 
