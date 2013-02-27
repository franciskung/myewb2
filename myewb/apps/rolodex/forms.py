from datetime import date
from django import forms

from siteutils.shortcuts import get_object_or_none

from rolodex.models import TrackingProfile, Email, Interaction

class TrackingProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = TrackingProfile
        fields = ('first_name', 'last_name', 'email', 'chapter', 'role', 'workfield', 'school', 'graduation', 'workplace')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        
        if instance:
            email = Email.objects.filter(profile=instance, primary=True)
            if email:
                initial = kwargs.get('initial', {})
                initial['email'] = email[0].email
                kwargs['initial'] = initial
            
        return super(TrackingProfileForm, self).__init__(*args, **kwargs)
    
class NoteForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = ('interaction_type', 'pinned', 'note')
