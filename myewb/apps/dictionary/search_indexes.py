import datetime
import settings
from haystack.indexes import *
from haystack import site
from dictionary.models import Term

if settings.REALTIME_SEARCH:
    index_class = RealTimeSearchIndex
else:
    index_class = SearchIndex

class TermIndex(index_class):
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='creator')
    pub_date = DateTimeField(model_attr='created_at')
    
    def prepare_author(self, obj):
        return obj.creator.visible_name()
    
    def get_updated_field(self):
        return 'last_update'

# not currently used; see apps/search/view.py, create_queryset()
#    def load_all_queryset(self):
#        return GroupTopic.objects.visible()

site.register(Term, TermIndex)
