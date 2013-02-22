from django.conf.urls.defaults import *

urlpatterns = patterns('profileupdate2013.views',
    url(r'^$', view='intro', name="profileupdate_intro"),
    url(r'^contact/$', view='contact', name="profileupdate_contact"),
    url(r'^workplace/$', view='workplace', name="profileupdate_workplace"),
#    url(r'^school/$', view='school', name="profileupdate_school"),
    url(r'^interests/$', view='interests', name="profileupdate_interests"),
    url(r'^demographics/$', view='demographics', name="profileupdate_demographics"),
    url(r'^complete/$', view='complete', name="profileupdate_complete"),

)
