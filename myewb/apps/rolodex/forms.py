from datetime import date
from django import forms
from rolodex.models import TrackingProfile

class TrackingProfileForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = TrackingProfile
        fields = ('first_name', 'last_name', 'chapter', 'role', 'school', 'workplace')

