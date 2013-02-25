from django.conf.urls.defaults import *

urlpatterns = patterns('rolodex.views',
    url(r'^$', view='home', name="rolodex_home"),
    url(r'^login/$', view='login', name="rolodex_login"),
    url(r'^logout/$', view='logout', name="rolodex_logout"),
    url(r'^search/$', view='search', name="rolodex_search"),
    url(r'^new/$', view='new', name="rolodex_new"),
#    url(r'^view/$', view='view', name="rolodex_view"),
)
