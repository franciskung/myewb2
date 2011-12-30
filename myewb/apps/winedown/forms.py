from django import forms
from django.forms import widgets
from django.contrib.contenttypes.models import ContentType

from winedown.models import Cheers

class CheersForm(forms.ModelForm):
    class Meta:
        model = Cheers
        fields = ('comment',)

