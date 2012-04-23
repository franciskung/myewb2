from django.conf.urls.defaults import *

urlpatterns = patterns('httpbl.views',
    url(r'^$', view='blacklist', name="httpbl_blacklist"),
    url(r'^validate$', view='validate', name="httpbl_validate"),

)
