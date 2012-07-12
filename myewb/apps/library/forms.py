# -*- coding: utf-8 -*-

from django import forms
from django.forms import widgets
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from lxml.html.clean import clean_html, autolink_html, Cleaner
from siteutils.helpers import autolink_email

from library.models import Resource, FileResource, LinkResource, Collection

class ResourceForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'class':'tinymce '}))

    scope = forms.CharField(widget=forms.CheckboxInput,
                            required=False,
                            label='Is this resource EWB-specific?')

    PERMS_CHOICES = (('public', 'Public: anyone can see and update this resource'),
                     ('protected', 'Protected: anyone can see this, but only I can edit it'),
                     ('private', 'Private: only people I share this with can see or update it'))
    permissions = forms.CharField(widget=forms.RadioSelect(choices=PERMS_CHOICES),
                                  required=True,
                                  initial=True)

    class Meta:
        model = Resource
        fields = ('name', 'description', 'language',
                  'resource_type', 'scope', 'editable')

    def clean_name(self):
        return self.cleaned_data['name']
        
    def clean_scope(self):
        if self.cleaned_data['scope'] == 'on':
            self.cleaned_data['scope'] = 'ewb'
        else:
            self.cleaned_data['scope'] = 'world'
            
        return self.cleaned_data['scope']
        
    def clean_permissions(self):
        p = self.cleaned_data.get('permissions', None)
        if p == 'public':
            self.cleaned_data['editable'] = True
            self.cleaned_data['visible'] = True
        elif p == 'public':
            self.cleaned_data['editable'] = False
            self.cleaned_data['visible'] = True
        else:
            self.cleaned_data['editable'] = False
            self.cleaned_data['visible'] = False
            
        return p

    # do HTML validation and auto-linking
    def clean_description(self):
        body = self.cleaned_data.get('description', '')
        
        # validate HTML content
        # Additional options at http://codespeak.net/lxml/lxmlhtml.html#cleaning-up-html
        body = clean_html(body)
        body = autolink_html(body)
        
        # emails too
        body = autolink_email(body)
        
        self.cleaned_data['description'] = body
        return body

class FileResourceForm(ResourceForm):
    resource = forms.FileField()

    class Meta:
        model = FileResource
        fields = ('name', 'description', 'language',
                  'resource_type', 'scope', 'editable')

class LinkResourceForm(ResourceForm):
    class Meta:
        model = LinkResource
        fields = ('name', 'description', 'language',
                  'resource_type', 'scope', 'editable', 'url')

        
class CollectionForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'class':'tinymce '}))

    class Meta:
        model = Collection
        fields = ('name', 'description')

    # do HTML validation and auto-linking
    def clean_description(self):
        body = self.cleaned_data.get('description', '')
        
        # validate HTML content
        # Additional options at http://codespeak.net/lxml/lxmlhtml.html#cleaning-up-html
        body = clean_html(body)
        body = autolink_html(body)
        
        # emails too
        body = autolink_email(body)
        
        self.cleaned_data['description'] = body
        return body
    

