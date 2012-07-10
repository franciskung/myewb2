# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings

from library.views import *

urlpatterns = patterns('',
    url(r'^$', home, name='library_home'),

    url(r'^search/$', search, name='library_search'),

    url(r'^view/(?P<resource_id>\d+)/$', resource, name='library_resource'),
    url(r'^download/(?P<resource_id>\d+)/$', download, name='library_download'),
    
    url(r'^upload/$', upload, name='library_upload'),

    url(r'^mine/$', mine, name='library_mine'),    
    url(r'^collection/(?P<collection_id>\d+)/$', collection, name='library_collection'),
    url(r'^collection/(?P<collection_id>\d+)/edit/$', collection_edit, name='library_collection_edit'),
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
