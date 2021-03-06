# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings

from library.views import *

urlpatterns = patterns('',
#    url(r'^$', splash, name='library_splash'),
#    url(r'^$', splash, name='library_home'),
    url(r'^$', home, name='library_splash'),
    url(r'^library/$', home, name='library_home'),
    url(r'^library/$', home, name='library_home2'),

    url(r'^search/$', search, name='library_search'),

    url(r'^view/(?P<resource_id>\d+)/$', resource, name='library_resource'),
    url(r'^download/(?P<resource_id>\d+)/$', download, name='library_download'),
    url(r'^organize/(?P<resource_id>\d+)/$', organize, name='library_organize'),
    url(r'^rate/(?P<resource_id>\d+)/$', rate, name='library_rate'),
    url(r'^browse/$', browse, name='library_folder_browse'),
    
    url(r'^edit/(?P<resource_id>\d+)/$', resource_edit, name='library_resource_edit'),
    url(r'^edit/(?P<resource_id>\d+)/google/$', resource_google, name='library_resource_google'),
    url(r'^edit/(?P<resource_id>\d+)/google2/$', resource_google2, name='library_resource_google2'),
    url(r'^edit/(?P<resource_id>\d+)/google/save/$', resource_googlesave, name='library_resource_googlesave'),
    url(r'^edit/(?P<resource_id>\d+)/google/close/$', resource_googlesave, name='library_resource_googleclose', kwargs={'save': False}),
    url(r'^edit/(?P<resource_id>\d+)/replace/$', resource_replace, name='library_resource_replace'),
    url(r'^edit/(?P<resource_id>\d+)/revisions/$', resource_revisions, name='library_resource_revisions'),
    url(r'^archive/(?P<resource_id>\d+)/$', resource_archive, name='library_resource_archive'),
    url(r'^unarchive/(?P<resource_id>\d+)/$', resource_unarchive, name='library_resource_unarchive'),
    url(r'^delete/(?P<resource_id>\d+)/$', resource_delete, name='library_resource_delete'),
    
    url(r'^upload/$', upload, name='library_upload'),
    url(r'^upload/(?P<collection_id>\d+)/$', upload, name='library_upload'),
    url(r'^upload/link/$', upload, name='library_upload_link', kwargs={'link': True}),
    url(r'^upload/link/(?P<collection_id>\d+)/$', upload, name='library_upload_link', kwargs={'link': True}),

    url(r'^mine/(?P<sort>\w+)/$', mine, name='library_mine'),    
    url(r'^mine/$', mine, name='library_mine'),    
    
    url(r'^collection/(?P<collection_id>\d+)/sorted$', collection_sorted, name='library_collection_sorted'),
    url(r'^collection/(?P<collection_id>\d+)/edit/$', collection_edit, name='library_collection_edit'),
    url(r'^collection/(?P<collection_id>\d+)/delete/$', collection_delete, name='library_collection_delete'),
    url(r'^collection/(?P<collection_id>\d+)/reorder/$', collection_reorder, name='library_collection_reorder'),
    url(r'^collection/(?P<collection_id>\d+)/reorderfiles/$', collection_reorder_files, name='library_files_reorder'),
    url(r'^collection/(?P<parent_id>\d+)/create/$', collection_create, name='library_collection_create'),
    url(r'^collection/create/$', collection_create, name='library_collection_create'),
    url(r'^collection/(?P<collection_id>\d+)/(?P<slug>[-_\w]+)/$', collection, name='library_collection'),
    url(r'^collection/(?P<collection_id>\d+)/$', collection, name='library_collection'),
)

"""
from dictionary.models import Term
from dictionary.forms import TermForm
from wiki import views
from dictionary import views as dictviews

try:
    WIKI_URL_RE = settings.WIKI_URL_RE
except AttributeError:
    WIKI_URL_RE = r'[-\w]+'

urlpatterns = patterns('',
    url(r'^$', dictviews.home,
        name='dictionary_home'),

    url(r'^edit/(?P<slug>'+ WIKI_URL_RE +r')/$', views.edit_article,
        {'template_dir': 'dictionary',
         'ArticleClass': Term,
         'article_qs': Term.objects.all(),
         'ArticleFormClass': TermForm},
        name='dictionary_edit'),

    url(r'^search/$', dictviews.search,
        name='dictionary_search'),

    url(r'^new/$', dictviews.new_article,
        name='dictionary_new'),

    url(r'^history/(?P<slug>'+ WIKI_URL_RE +r')/$', views.article_history,
        {'template_dir': 'dictionary'},
        name='dictionary_article_history'),

    url(r'^history/(?P<slug>'+ WIKI_URL_RE +r')/changeset/(?P<revision>\d+)/$', views.view_changeset,
        {'template_dir': 'dictionary'},
        name='dictionary_changeset',),

    url(r'^history/(?P<slug>'+ WIKI_URL_RE +r')/revert/$', views.revert_to_revision,
        {'template_dir': 'dictionary'},
        name='dictionary_revert_to_revision'),
        
    url(r'^view/(?P<slug>'+ WIKI_URL_RE +r')/$', views.view_article,
        {'ArticleClass': Term,
         'article_qs': Term.objects.all(),
         'template_dir': 'dictionary'},
        name='dictionary_view'),
        
    url(r'^ajax/(?P<slug>'+ WIKI_URL_RE +r')/$', views.view_article,
        {'ArticleClass': Term,
         'article_qs': Term.objects.all(),
         'template_dir': 'dictionary',
         'template_name': 'ajax.html'},
        name='dictionary_ajax'),
        
    url(r'^w/view/(?P<slug>'+ WIKI_URL_RE +r')/$', dictviews.view_wiki_article,
        name='wiki_article'),
    url(r'^w/history/(?P<slug>'+ WIKI_URL_RE +r')/$', dictviews.article_history,
        name='wiki_article_history'),
)
"""
