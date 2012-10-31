from django.conf.urls.defaults import *

urlpatterns = patterns('whosonline.views',
    url(r'^$', view='whosonline', name="whosonline"),
    url(r'^(?P<username>[\w\._-]+)/$', view='whosonline', name="whosonline"),

)
