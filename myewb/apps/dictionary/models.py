from django.db import models

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from lxml.html.clean import clean_html, autolink_html, Cleaner
from datetime import datetime
import re, types

from group_topics.models import GroupTopic
from champ.models import Activity
from events.models import Event

from wiki.models import Article, QuerySetManager

class Term(Article):
#    slug = models.SlugField(editable=False)
    
    """
    topics = models.ManyToManyField(GroupTopic)
    champ = models.ManyToManyField(Activity)
    events = models.ManyToManyField(Event)
    terms = models.ManyToManyField('self')
    """

    refreshing = models.BooleanField(default=True, editable=False)
    nickname = models.CharField(max_length=50, default='')
    
    objects = QuerySetManager()
    
class ContainerManager(models.Manager):

    # searchs for matches for a given object
    def search(self, container, terms):
        # mal-formed container (field does not exist in object), bail
        if not hasattr(container.content_object, container.content_text_field):
            return False

        # clear out old matches
        matches = Match.objects.filter(container=container, term__in=terms)
        for m in matches:
            m.delete()
            
        # grab the text
        text = getattr(container.content_object, container.content_text_field)
        if type(text) == types.MethodType:
            text = text()
        
        # and refresh for all terms...
        for t in terms:
        
            # regex is nice and efficient for the search (we ensure we only do full-word matches)
            regex = re.compile("\W%s\W" % t.title, re.I)
            hits = regex.finditer(text)
            
            # run through hits
            for hit in hits:
                # only do the insert if it's not within an HTML tag
                startbrace = text[0:hit.start()].count('<')
                endbrace = text[0:hit.start()].count('>')

                if startbrace == endbrace:
                    Match.objects.create(container=container,
                                         term=t,
                                         position=hit.start())

        return True

    # returns a refreshed container for an object, creating if needed
    def refresh(self, obj, field):
        ctype = ContentType.objects.get_for_model(obj)
        container = Container.objects.filter(content_type=ctype, object_id=obj.id, content_text_field=field)
        
        if not container:
            ctype = ContentType.objects.get_for_model(obj)
            container = self.create(content_type=ctype, object_id=obj.id, content_text_field=field)
            terms = Term.objects.all()
        else:
            container = container[0]
            terms = Term.objects.filter(last_update__gt=container.refreshed)

        if terms:            
            self.search(container, terms)
            container.refreshed = datetime.now()
            container.save()

        return container    

class Container(models.Model):
    content_type = models.ForeignKey(ContentType, db_index=True)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    content_text_field = models.CharField(max_length=50)
    
    date = models.DateTimeField(auto_now_add=True)
    refreshed = models.DateTimeField(default=datetime.now())
    
    objects = ContainerManager()

class Match(models.Model):
    term = models.ForeignKey(Term, db_index=True)
    container = models.ForeignKey(Container, db_index=True)
    
    position = models.IntegerField()

