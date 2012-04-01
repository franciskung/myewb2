# -*- coding: utf-8 -*-

from django import forms
from django.forms import widgets
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from lxml.html.clean import clean_html, autolink_html

from dictionary.models import Term
from whiteboard.forms import WhiteboardForm
from wiki.utils import get_ct

# hmm,why can't I extend wiki.forms.ArticleForm ? =(
class TermForm(WhiteboardForm):
    class Meta:
        model = Term
        exclude = ('creator', 'creator_ip', 'removed',
                   'group', 'created_at', 'last_update',
                   'summary', 'slug', 'markup', 'tags', 'parent_group',
                   'converted')

    def clean_title(self):
        return self.cleaned_data['title']

    def save(self, *args, **kwargs):
        result = super(TermForm, self).save(*args, **kwargs)
        
        # we could also trigger an article refresh here...?

        return result
