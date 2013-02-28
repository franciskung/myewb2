from django.conf.urls.defaults import *

urlpatterns = patterns('rolodex.views',
    url(r'^$', view='home', name="rolodex_home"),
    url(r'^login/$', view='login', name="rolodex_login"),
    url(r'^logout/$', view='logout', name="rolodex_logout"),
    url(r'^search/$', view='search', name="rolodex_search"),
    
    url(r'^new/$', view='profile_edit', name="rolodex_new"),
    url(r'^edit/(?P<profile_id>\d+)/$', view='profile_edit', name="rolodex_edit"),
    url(r'^view/(?P<profile_id>\d+)/$', view='profile_view', name="rolodex_view"),
    
    url(r'^note/new/(?P<profile_id>\d+)/$', view='note_new', name="rolodex_interaction_new"),
    url(r'^note/(?P<note_id>\d+)/ajax/$', view='note_view_ajax', name="rolodex_note_ajax"),
    url(r'^note/(?P<note_id>\d+)/pin/$', view='note_pin', name="rolodex_note_pin"),
    url(r'^note/(?P<note_id>\d+)/unpin/$', view='note_unpin', name="rolodex_note_unpin"),

    url(r'^flag/(?P<profile_id>\d+)/$', view='flag', name="rolodex_flag"),
    url(r'^unflag/(?P<flag_id>\d+)/$', view='unflag', name="rolodex_unflag"),
    url(r'^badge/(?P<profile_id>\d+)/$', view='badge', name="rolodex_badge"),
    url(r'^unbadge/(?P<badge_id>\d+)/$', view='unbadge', name="rolodex_unbadge"),

)
