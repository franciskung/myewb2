from datetime import date
from django import forms

from siteutils.shortcuts import get_object_or_none

from rolodex.models import TrackingProfile, Email, Phone, Interaction, ProfileFlag, ProfileBadge

class TrackingProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=50, required=False)

    class Meta:
        model = TrackingProfile
        fields = ('first_name', 'last_name', 'email', 'phone', 'chapter', 'role', 'city', 'workfield', 'school', 'graduation', 'workplace')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        
        if instance:
            email = Email.objects.filter(profile=instance, primary=True)
            if email:
                initial = kwargs.get('initial', {})
                initial['email'] = email[0].email
                kwargs['initial'] = initial
            
            phone = Phone.objects.filter(profile=instance, primary=True)
            if phone:
                initial = kwargs.get('initial', {})
                initial['phone'] = phone[0].phone
                kwargs['initial'] = initial
            
        return super(TrackingProfileForm, self).__init__(*args, **kwargs)
    
class NoteForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = ('interaction_type', 'visibility', 'pinned', 'note')
        
class FlagForm(forms.ModelForm):
    class Meta:
        model = ProfileFlag
        fields = ('flag', 'note')
        
class BadgeForm(forms.ModelForm):
    class Meta:
        model = ProfileBadge
        fields = ('badge', 'note')
        

