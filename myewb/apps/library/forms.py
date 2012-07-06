# -*- coding: utf-8 -*-

from django import forms
from django.forms import widgets
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from lxml.html.clean import clean_html, autolink_html

from library.models import FileResource

class FileResourceForm(forms.ModelForm):
    resource = forms.FileField()

    class Meta:
        model = FileResource
        fields = ('name', 'description',
                  'resource_type', 'scope')

    def clean_name(self):
        return self.cleaned_data['name']

    def save(self, *args, **kwargs):
        result, changeset = super(FileResourceForm, self).save(*args, **kwargs)
        
        # we could also trigger an article refresh here...?

        return result, changeset
