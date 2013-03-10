from django.conf.urls.defaults import *

urlpatterns = patterns('rolodex.views',
    url(r'^$', view='home', name="rolodex_home"),
    url(r'^login/$', view='login', name="rolodex_login"),
    url(r'^logout/$', view='logout', name="rolodex_logout"),
    url(r'^search/$', view='search', name="rolodex_search"),
    
    url(r'^new/$', view='profile_edit', name="rolodex_new"),
    url(r'^edit/(?P<profile_id>\d+)/$', view='profile_edit', name="rolodex_edit"),
    url(r'^editcustom/(?P<profile_id>\d+)/$', view='profile_edit_custom', name="rolodex_edit_custom"),
    url(r'^view/(?P<profile_id>\d+)/$', view='profile_view', name="rolodex_view"),
    
    url(r'^note/new/(?P<profile_id>\d+)/$', view='note_edit', name="rolodex_interaction_new"),
    url(r'^note/edit/(?P<note_id>\d+)/$', view='note_edit', name="rolodex_interaction_edit"),
    url(r'^note/(?P<note_id>\d+)/ajax/$', view='note_view_ajax', name="rolodex_note_ajax"),
    url(r'^note/(?P<note_id>\d+)/pin/$', view='note_pin', name="rolodex_note_pin"),
    url(r'^note/(?P<note_id>\d+)/unpin/$', view='note_unpin', name="rolodex_note_unpin"),

    url(r'^flag/new/(?P<profile_id>\d+)/$', view='flag', name="rolodex_flag"),
    url(r'^flag/edit/(?P<flag_id>\d+)/$', view='flag', name="rolodex_flag_edit"),
    url(r'^flag/remove/(?P<flag_id>\d+)/$', view='unflag', name="rolodex_unflag"),
    url(r'^flag/view/(?P<flag_id>\d+)/ajax/$', view='flag_view_ajax', name="rolodex_flag_ajax"),
    url(r'^flag/browse/(?P<flag_id>\d+)/$', view='browse_flags', name="rolodex_browse_flags"),
    
    url(r'^badge/new/(?P<profile_id>\d+)/$', view='badge', name="rolodex_badge"),
    url(r'^badge/edit/(?P<badge_id>\d+)/$', view='badge', name="rolodex_badge_edit"),
    url(r'^badge/remove/(?P<badge_id>\d+)/$', view='unbadge', name="rolodex_unbadge"),
    url(r'^badge/view/(?P<badge_id>\d+)/ajax/$', view='badge_view_ajax', name="rolodex_badge_ajax"),
    url(r'^badge/browse/(?P<badge_id>\d+)/$', view='browse_badges', name="rolodex_browse_badges"),

    url(r'^custom/$', view='custom_fields', name="rolodex_custom_fields"),
)
