from django.conf.urls.defaults import *

urlpatterns = patterns('themeswitch.views',
    url(r'^$', view='dashboard', name="themeswitch"),
    url(r'^(?P<theme>[-\w]+)/$', view='switch', name="themeswitch_select"),
    url(r'^up/(?P<theme>[-\w]+)/$', view='vote_up', name="themeswitch_voteup"),
    url(r'^down/(?P<theme>[-\w]+)/$', view='vote_down', name="themeswitch_votedown"),
)
