from django.conf.urls.defaults import *

urlpatterns = patterns('rolodex.views',
    url(r'^$', view='home', name="rolodex_home"),
    url(r'^login/$', view='login', name="rolodex_login"),
    url(r'^logout/$', view='logout', name="rolodex_logout"),
    url(r'^search/$', view='search', name="rolodex_search"),
    url(r'^new/$', view='profile_edit', name="rolodex_new"),
    url(r'^edit/(?P<profile_id>\d+)/$', view='profile_edit', name="rolodex_edit"),
    url(r'^view/(?P<profile_id>\d+)/$', view='profile_view', name="rolodex_view"),
)
